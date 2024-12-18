import asyncio
from enum import Enum
import json
import sys
from typing import Dict, Any
from urllib.parse import urlparse
import aiohttp

from . import settings
from .manager import TaskManager
from .env import Env
from .task import MsgHeader, Status, Task, getStatus
from .concurrency import Concurrency
from .log import logger
from .heartbeat import Heartbeat
from .handler import HandlerConfig, init_handler_config, parse_data, wrap_handler, send_request
from .proxy import parse_proxy_data, proxy_handler, wrap_check_start, ProxyConfig, init_proxy_config
from .utils import current_unix_milli


class WorkerMode(Enum):
    Default = "default"
    Proxy = "proxy"


class WorkConfig:
    async def init(self, handlers: Dict[str, Any], env: Env):
        await self._validate_handlers(handlers)
        self.settings = settings.SETTINGS
        self.handlers = handlers
        self.env = env
        self.concurrency = Concurrency(handlers.get("concurrency_modifier", None))

        # start heartbeat
        self.heartbeat = Heartbeat(self.concurrency)
        self.heartbeat.start()

        # init task manager
        self.task_manager = TaskManager()
        await self.task_manager.init()

        # init handler or proxy
        self.mode = self._get_mode(handlers)
        if self.mode == WorkerMode.Proxy:
            await self._init_proxy()
        else:
            await self._init_handler()

    async def _validate_handlers(self, handlers: Dict[str, Any]):
        mode = self._get_mode(handlers)
        if mode == WorkerMode.Proxy:
            if "base_url" not in handlers:
                raise ValueError("base_url is required in proxy mode")
            if not isinstance(handlers["base_url"], str):
                raise ValueError("base_url must be a string")
            base_url = handlers["base_url"]
            res = urlparse(base_url)
            if res.scheme == "" or res.netloc == "":
                raise ValueError("base_url is invalid")

            if "check_start" not in handlers:
                raise ValueError("check_start is required in proxy mode")
            if not callable(handlers["check_start"]):
                raise ValueError("check_start must be a callable")
            await wrap_check_start(handlers["check_start"])

        else:
            if "handler" not in handlers:
                raise ValueError("handler is required in default mode")
            if not callable(handlers["handler"]):
                raise ValueError("handler must be a callable")

    async def _init_proxy(self):
        base_url = self.handlers.get("base_url", "")
        session = aiohttp.ClientSession()
        check_start = await wrap_check_start(self.handlers["check_start"])
        self.proxy_config = ProxyConfig(
            base_url=base_url,
            session=session,
            task_manager=self.task_manager,
            check_start=check_start,
        )
        init_proxy_config(self.proxy_config)
        while True:
            started = await self.proxy_config.check_start()
            if started:
                break
            else:
                logger.info("check_start return False, local server is not ready")
            await asyncio.sleep(0.5)

    async def _init_handler(self):
        handler = await wrap_handler(self.handlers["handler"], self.env)
        self.handler_config = HandlerConfig(
            handler=handler,
            task_manager=self.task_manager,
            session=aiohttp.ClientSession()
        )
        init_handler_config(self.handler_config)

    def _get_mode(self, handlers: Dict[str, Any]) -> WorkerMode:
        mode = handlers.get("mode", WorkerMode.Default.value)
        if mode == WorkerMode.Proxy.value:
            return WorkerMode.Proxy
        else:
            mode = WorkerMode.Default.value
        logger.info(f"worker mode is {mode}")
        return WorkerMode.Default


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
        header=header,
        ts=execStartTs,
        webhook="",
        status=Status.Executing.value,
        queueDur=execStartTs - header.enqueue_at,
        execDur=0,
        totalDur=0,
        msg="start executing",
    )
    await WORKER.task_manager.report_status(header.request_id, status.json().encode())


async def check_wait_time(header: MsgHeader, execStartTs: int, webhook: str) -> bool:
    if execStartTs - header.enqueue_at > header.ttl:
        error = f"request enqueue time exceed ttl {header.ttl} milliseconds, drop it to reduce worker running time"
        logger.error(error, request_id=header.request_id)
        status = getStatus(
            header=header,
            ts=current_unix_milli(),
            webhook="",
            status=Status.Failed.value,
            queueDur=execStartTs - header.enqueue_at,
            execDur=0,
            totalDur=0,
            msg=error,
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


async def handle_task(task: Task):
    header = task.header
    is_proxy_mode = WORKER.mode == WorkerMode.Proxy
    logger.info(f"handle request", request_id=task.header.request_id)

    execStartTs = max(current_unix_milli(), header.enqueue_at)

    if is_proxy_mode:
        request, webhook, ok = await parse_proxy_data(header, execStartTs, task.data)
    else:
        request, webhook, ok = await parse_data(header, execStartTs, task.data)
    if not ok:
        return

    ok = await check_wait_time(header, execStartTs, webhook)
    if not ok:
        return

    await report_exec(header, execStartTs)

    # handle
    res = b""
    try:
        if is_proxy_mode:
            await proxy_handler(task, request)
        else:
            res = await WORKER.handler_config.handler(request)
            if not isinstance(res, bytes):
                res = json.dumps(res).encode()

    except Exception as e:
        error = f"custom handler raise exception during running, err: {e}"
        logger.error(error, request_id=header.request_id, exc_info=True)
        status = getStatus(
            header=header,
            ts=current_unix_milli(),
            webhook=webhook,
            status=Status.Failed.value,
            queueDur=execStartTs - header.enqueue_at,
            execDur=0,
            totalDur=0,
            msg=error,
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

    if is_proxy_mode:
        pass
    else:
        err = await send_request(
            header=header, webhook=webhook, status_code=200, message="", data=res
        )
        if err is not None:
            error = f"failed to send result to user, err: {err}"
            logger.error(error, request_id=header.request_id)

            status = getStatus(
                header=header,
                ts=current_unix_milli(),
                webhook=webhook,
                status=Status.Failed.value,
                queueDur=execStartTs - header.enqueue_at,
                execDur=execFinishTs - execStartTs,
                totalDur=execFinishTs - header.enqueue_at,
                msg=error,
            )
            await WORKER.task_manager.report_status(
                header.request_id, status.json().encode()
            )
            return

    status = getStatus(
        header=header,
        ts=current_unix_milli(),
        webhook=webhook,
        status=Status.Succeed.value,
        queueDur=execStartTs - header.enqueue_at,
        execDur=execFinishTs - execStartTs,
        totalDur=execFinishTs - header.enqueue_at,
        msg="succeed",
    )
    await WORKER.task_manager.report_status(header.request_id, status.json().encode())
