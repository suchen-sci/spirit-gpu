import asyncio
from dataclasses import dataclass
import dataclasses
import inspect
import json
import sys
from typing import Dict, Any
import aiohttp
import backoff
import base64

from . import settings
from .manager import TaskManager
from .env import Env
from .task import MsgHeader, Operation, Status, Task
from .concurrency import Concurrency
from .log import logger

from .utils import current_unix_milli


@dataclass
class RequestStatus:
    timestamp: int

    requestID: str
    webhook: str

    status: str
    operation: str

    enqueueTimestamp: int
    queueingDuration: int
    executionDuration: int
    totalDuration: int
    requestCreateAt: int
    message: str

    def json(self):
        return json.dumps(dataclasses.asdict(self))


class WorkConfig:
    async def init(self, handlers: Dict[str, Any], env: Env):
        self.settings = settings.SETTINGS

        self.handlers = handlers
        self.handler = await wrap_handler(handlers["handler"], env)
        self.concurrency = Concurrency(handlers.get("concurrency_modifier", None))
        self.env = env

        self.task_manager = TaskManager()
        await self.task_manager.init()
        self.session = aiohttp.ClientSession()


async def run(handlers: Dict[str, Any], env: Env):
    global WORKER
    WORKER = WorkConfig()
    await WORKER.init(handlers, env)

    while True:
        if WORKER.concurrency.is_available():
            try:
                task, health = await WORKER.task_manager.next()
            except Exception as e:
                logger.error(f"failed to get task: {e}", exc_info=True)
                await asyncio.sleep(1)
                continue

            if WORKER.concurrency.current_jobs == 0 and not health:
                logger.error("agent is not healthy, exit worker")
                sys.exit(1)

            if task is None:
                await asyncio.sleep(0.5)
                continue

            if task.header.request_id == "":
                logger.error(f"request id of {task} is empty")
                await asyncio.sleep(0.5)
                continue

            WORKER.concurrency.add_job()
            asyncio.create_task(do_task(task))

        await asyncio.sleep(0.05)


async def do_task(task: Task):
    try:
        await handle_msg(task)
    except Exception as e:
        logger.error(f"failed to handle message: {e}", exc_info=True)

    await WORKER.task_manager.ack(task.header.request_id)
    WORKER.concurrency.remove_job()


async def report_exec(
    header: MsgHeader,
    execStartTs: int,
):
    status = getStatus(
        header,
        execStartTs,
        "",
        Status.Executing.value,
        execStartTs - header.enqueue_at,
        0,
        0,
        "start executing",
    )
    await WORKER.task_manager.report_status(header.request_id, status.json().encode())


async def parse_data(
    header: MsgHeader,
    execStartTs: int,
    data: bytes,
) -> tuple[Any, str, bool]:
    webhook = header.webhook
    try:
        request = json.loads(data)
        _ = request["input"]
        if header.mode == Operation.Async.value:
            webhook = str(request["webhook"])
    except Exception as e:
        error = f"failed to parse input {header.request_id}: {e}"
        logger.error(error + str(data))
        status = getStatus(
            header,
            current_unix_milli(),
            "",
            Status.Failed.value,
            execStartTs - header.enqueue_at,
            0,
            0,
            error,
        )
        await WORKER.task_manager.report_status(
            header.request_id, status.json().encode()
        )
        return None, "", False
    return request, webhook, True


async def wrap_handler(handler: Any, env: Env):
    if inspect.isasyncgenfunction(handler):

        async def async_gen_handler(request: Any):
            res: Any = []
            async for r in handler(request, env):
                res.append(r)
            return res

        return async_gen_handler

    elif inspect.iscoroutinefunction(handler):

        async def coroutine_handler(request: Any):
            return await handler(request, env)

        return coroutine_handler

    elif inspect.isgeneratorfunction(handler):

        async def generator_handler(request: Any):
            res: Any = []
            for r in handler(request, env):
                res.append(r)
            return res

        return generator_handler

    else:

        async def normal_handler(request: Any):
            return handler(request, env)

        return normal_handler


async def check_wait_time(header: MsgHeader, execStartTs: int):
    if execStartTs - header.enqueue_at > header.ttl:
        error = f"message enqueue time exceed ttl {header.ttl}"
        logger.error(error)
        status = getStatus(
            header,
            current_unix_milli(),
            "",
            Status.Failed.value,
            execStartTs - header.enqueue_at,
            0,
            0,
            error,
        )
        await WORKER.task_manager.report_status(
            header.request_id, status.json().encode()
        )
        return False
    return True


async def handle_msg(
    task: Task,
):
    header = task.header
    logger.info(f"handle request id: {header.request_id}")

    execStartTs = max(current_unix_milli(), header.enqueue_at)
    ok = await check_wait_time(header, execStartTs)
    if not ok:
        return

    await report_exec(header, execStartTs)

    request, webhook, ok = await parse_data(header, execStartTs, task.data)
    if not ok:
        return

    # handle
    try:
        res = await WORKER.handler(request)
        if not isinstance(res, bytes):
            res = json.dumps(res).encode()

    except Exception as e:
        error = f"failed to handle message {header.request_id}: {e}"
        logger.error(error)
        status = getStatus(
            header,
            current_unix_milli(),
            webhook,
            Status.Failed.value,
            execStartTs - header.enqueue_at,
            0,
            0,
            error,
        )
        await WORKER.task_manager.report_status(
            header.request_id, status.json().encode()
        )
        await send_request(
            header=header,
            webhook=webhook,
            status_code=500,
            message=error,
            data=json.dumps({"error": error}).encode(),
        )
        return

    execFinishTs = current_unix_milli()
    err = await send_request(
        header=header, webhook=webhook, status_code=200, message="", data=res
    )
    if err is not None:
        error = f"failed to send request {header.request_id}: {err}"
        logger.error(error)

        status = getStatus(
            header,
            current_unix_milli(),
            webhook,
            Status.Failed.value,
            execStartTs - header.enqueue_at,
            execFinishTs - execStartTs,
            execFinishTs - header.enqueue_at,
            error,
        )
        await WORKER.task_manager.report_status(
            header.request_id, status.json().encode()
        )
        return

    status = getStatus(
        header,
        current_unix_milli(),
        webhook,
        Status.Succeed.value,
        execStartTs - header.enqueue_at,
        execFinishTs - execStartTs,
        execFinishTs - header.enqueue_at,
        "succeed",
    )
    await WORKER.task_manager.report_status(header.request_id, status.json().encode())


async def send_request(
    *,
    header: MsgHeader,
    webhook: str,
    status_code: int,
    message: str,
    data: bytes,
):

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_tries=3,
    )
    async def do_send():
        async with WORKER.session.post(
            webhook,
            params={"requestID": header.request_id, "statusCode": str(status_code)},
            data=data,
            headers={"Content-Type": "application/json"},
        ) as resp:
            text = await resp.text()
            return resp, text

    resp, text, err = None, None, None

    if webhook != "":
        try:
            resp, text = await do_send()
        except Exception as e:
            err = str(e)
        if resp is not None:
            if resp.status != 200:
                err = f"request {header.request_id} failed {resp.status}: {text}"

    try:
        result = getResult(status_code, message, data)
        json_result = json.dumps(result).encode()
        await WORKER.task_manager.send_result(
            header.request_id,
            json_result,
        )
    except Exception as e:
        if err is not None:
            err = f"{err}, failed to send result to agent: {e}"
        else:
            err = f"failed to send result to agent: {e}"
        logger.error(f"failed to send result to agent: {e}", exc_info=True)

    return err


def getResult(status_code: int, message: str, data: bytes):
    return {
        "statusCode": status_code,
        "message": message,
        "data": base64.b64encode(data).decode("utf-8"),
    }


def getStatus(
    header: MsgHeader,
    ts: int,
    webhook: str,
    status: str,
    queueDur: int,
    execDur: int,
    totalDur: int,
    msg: str,
):
    return RequestStatus(
        timestamp=ts,
        requestID=header.request_id,
        webhook=webhook,
        status=status,
        operation=header.mode,
        enqueueTimestamp=header.enqueue_at,
        queueingDuration=queueDur,
        executionDuration=execDur,
        totalDuration=totalDur,
        requestCreateAt=header.create_at,
        message=msg,
    )
