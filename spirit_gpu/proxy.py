from dataclasses import dataclass
import inspect
from urllib.parse import urljoin
from aiohttp import ClientSession
from typing import Callable, Coroutine, Dict, Optional, Any
import json
import base64
import multidict

from .utils import current_unix_milli
from .task import MsgHeader, Status, getStatus, Task
from .log import logger
from .task import MsgHeader
from .manager import TaskManager


@dataclass
class ProxyConfig:
    base_url: str
    session: ClientSession
    task_manager: TaskManager
    check_start: Callable[[], Coroutine[Any, Any, Any]]


def init_proxy_config(proxy_config: ProxyConfig):
    global PROXY_CONFIG
    PROXY_CONFIG = proxy_config


@dataclass
class ProxyRequestData:
    method: str
    uri: str
    header: dict[str, list[str]]
    body: Optional[bytes] = None


async def parse_proxy_data(header: MsgHeader, execStartTs: int, data: bytes) -> tuple[Any, str, bool]:
    try:
        request = json.loads(data)
        _ = request["method"]
        _ = request["uri"]
        request["header"] = request.get("header", {})
        if "body" in request:
            request["body"] = base64.b64decode(request["body"])

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
        await PROXY_CONFIG.task_manager.report_status(header.request_id, status.json().encode())
        return None, "", False
    return request, "", True


async def proxy_handler(task: Task, request: Dict[str, Any]):
    proxy_request_data = ProxyRequestData(**request)
    url = urljoin(PROXY_CONFIG.base_url, proxy_request_data.uri)

    headers = multidict.CIMultiDict[str]()
    for key, values in proxy_request_data.header.items():
        for value in values:
            headers.add(key, value)

    logger.info(f"proxy request: {proxy_request_data.method} {url}", request_id=task.header.request_id)
    async with PROXY_CONFIG.session.request(
        proxy_request_data.method,
        url,
        data=proxy_request_data.body,
        headers=headers,
    ) as response:
        # aiohttp streams responses by default
        resp = await PROXY_CONFIG.task_manager.send_proxy(task.header.request_id, response)
        if isinstance(resp, str):
            raise Exception(f"failed to send to proxy for request_id: {task.header.request_id}, err: {resp}")
        else:
            if resp.status != 200:
                raise Exception(f"failed to send to proxy for request_id: {task.header.request_id}, status code: {resp.status}, body: {await resp.text()}")


async def wrap_check_start(handler: Any):
    if inspect.iscoroutinefunction(handler):
        async def coroutine_check():
            return await handler()
        return coroutine_check

    elif inspect.isfunction(handler):
        async def normal_check():
            return handler()
        return normal_check

    else:
        raise Exception(f"unsupported check_start function: {handler}")
