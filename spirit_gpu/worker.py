import asyncio
import json
import sys
from typing import Dict, Any
import aiohttp

from . import settings
from .manager import TaskManager
from .env import Env
from .task import MsgHeader, Status, Task, getStatus
from .concurrency import Concurrency
from .log import logger
from .heartbeat import Heartbeat
from .handler import parse_data, wrap_handler, send_request

from .utils import current_unix_milli


class WorkConfig:
    async def init(self, handlers: Dict[str, Any], env: Env):
        self.settings = settings.SETTINGS

        self.handlers = handlers
        self.handler = await wrap_handler(handlers["handler"], env)
        self.concurrency = Concurrency(handlers.get("concurrency_modifier", None))
        self.env = env
        self.heartbeat = Heartbeat(self.concurrency)

        self.task_manager = TaskManager()
        await self.task_manager.init()
        self.session = aiohttp.ClientSession()


async def run(handlers: Dict[str, Any], env: Env):
    global WORKER
    WORKER = WorkConfig()
    await WORKER.init(handlers, env)
    WORKER.heartbeat.start()

    while True:
        if WORKER.concurrency.is_available():
            try:
                task, health = await WORKER.task_manager.next()
            except Exception as e:
                logger.error(f"failed to get task: {e}", exc_info=True)
                await asyncio.sleep(0.5)
                continue

            if len(WORKER.concurrency.current_jobs) == 0 and not health:
                logger.error("agent is unhealthy, and no task is running, exit")
                sys.exit(1)

            if task is None:
                await asyncio.sleep(0.2)
                continue

            if task.header.request_id == "":
                logger.error(f"request id of {task} is empty")
                await asyncio.sleep(0.2)
                continue

            WORKER.concurrency.add_job(task.header.request_id)
            asyncio.create_task(do_task(task))

        await asyncio.sleep(0.05)


async def do_task(task: Task):
    try:
        await handle_task(task)
        logger.info(f"finish handle request", request_id=task.header.request_id)
    except Exception as e:
        logger.error(f"failed to handle request, err: {e}", request_id=task.header.request_id, exc_info=True)

    await WORKER.task_manager.ack(task.header.request_id)
    WORKER.concurrency.remove_job(task.header.request_id)


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


async def check_wait_time(header: MsgHeader, execStartTs: int, webhook: str) -> bool:
    if execStartTs - header.enqueue_at > header.ttl:
        error = f"request enqueue time exceed ttl {header.ttl} milliseconds, drop it to reduce worker running time"
        logger.error(error, request_id=header.request_id)
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
        await send_request(
            header=header,
            webhook=webhook,
            status_code=408,
            message=error,
            data=json.dumps({"error": error}).encode(),
        )
        return False
    return True


async def handle_task(
    task: Task,
):
    header = task.header
    logger.info(f"handle request", request_id=task.header.request_id)

    execStartTs = max(current_unix_milli(), header.enqueue_at)
    request, webhook, ok = await parse_data(header, execStartTs, task.data)
    if not ok:
        return

    ok = await check_wait_time(header, execStartTs, webhook)
    if not ok:
        return

    await report_exec(header, execStartTs)

    # handle
    try:
        res = await WORKER.handler(request)
        if not isinstance(res, bytes):
            res = json.dumps(res).encode()

    except Exception as e:
        error = f"custom handler raise exception during running, err: {e}"
        logger.error(error, request_id=header.request_id, exc_info=True)
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
        error = f"failed to send result to user, err: {err}"
        logger.error(error, request_id=header.request_id)

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
