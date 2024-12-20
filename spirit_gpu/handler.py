import inspect
import json
from typing import Callable, Coroutine, Any
import aiohttp
from attr import dataclass

from .manager import TaskManager
from .env import Env
from .task import MsgHeader, Operation, Status, getStatus
from .log import logger

from .utils import current_unix_milli


@dataclass
class HandlerConfig:
    handler: Callable[[Any], Coroutine[Any, Any, Any]]
    task_manager: TaskManager
    session: aiohttp.ClientSession


def init_handler_config(handler_config: HandlerConfig):
    global HANDLER_CONFIG
    HANDLER_CONFIG = handler_config


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
        # add meta info
        if "meta" not in request:
            request["meta"] = {"requestID": header.request_id}
        else:
            logger.warn(f"meta info already exists in request, cannot add meta info", request_id=header.request_id)
    except Exception as e:
        error = f"failed to parse input by using json, err: {e}"
        logger.error(error + f", data: {str(data)}", request_id=header.request_id)
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
        await HANDLER_CONFIG.task_manager.report_status(
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
