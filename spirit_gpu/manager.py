from enum import Enum
from urllib.parse import urljoin

import aiohttp

from . import settings, task
from .log import logger
from typing import Any, Callable, Dict


HOP_BY_HOP_HEADERS = [
    "Connection",
    "Proxy-Connection",
    "Keep-Alive",
    "Proxy-Authenticate",
    "Proxy-Authorization",
    "Te",
    "Trailer",
    "Transfer-Encoding",
    "Upgrade",
]


class ReportType(Enum):
    STATUS = 1
    ACK = 2
    RESULT = 3


class TaskManager:
    async def init(self):
        self._settings = settings.SETTINGS

        self._session = aiohttp.ClientSession()

        self._request_url = urljoin(self._settings.agent_url(), "/apis/v1/request")
        self._ack_url: Callable[[str], str] = lambda request_id: urljoin(
            self._settings.agent_url(), f"/apis/v1/request-ack/{request_id}"
        )
        self._status_url: Callable[[str], str] = lambda request_id: urljoin(
            self._settings.agent_url(), f"/apis/v1/request-metric/{request_id}"
        )
        self._result_url: Callable[[str], str] = lambda request_id: urljoin(
            self._settings.agent_url(), f"/apis/v1/request-result/{request_id}"
        )

        self._proxy_url: Callable[[str, int], str] = lambda request_id, status_code: urljoin(
            self._settings.agent_url(), f"/apis/v1/request-proxy/{request_id}?statusCode={status_code}"
        )

    async def next(self):
        request, health = await self._get_request()
        if request is None:
            return None, health
        return task.Task.parse(request), health

    async def _get_request(self):
        async with self._session.get(self._request_url) as resp:
            h = resp.headers.get(settings.HEADER_HEALTH, "true")
            if h == "false":
                health = False
            else:
                health = True

            if resp.status != 200:
                if resp.status == 404:
                    return None, health
                raise Exception(
                    f"failed to get task: {resp.status}, {await resp.text()}"
                )
            body: Dict[str, Any] = await resp.json()
            return body, health

    async def ack(self, request_id: str):
        # after receive ack, agent will delete request.
        # make sure metric is reported before ack
        try:
            await self._ack_request(request_id)
        except Exception as e:
            logger.error(f"failed to ack request, err: {e}", request_id=request_id, exc_info=True)

    async def _ack_request(self, request_id: str):
        async with self._session.post(self._ack_url(request_id)) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"failed to ack request, status code: {resp.status}, body: {text}", request_id=request_id)
                return

    async def _send_result(self, request_id: str, data: bytes):
        async with self._session.post(self._result_url(request_id), data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"failed to send result, status code: {resp.status}, body: {text}", request_id=request_id)
                return

    async def send_result(self, request_id: str, data: bytes):
        try:
            await self._send_result(request_id, data)
        except Exception as e:
            logger.error(f"failed to send result, err: {e}", request_id=request_id, exc_info=True)

    async def _send_proxy(self, request_id: str, resp: aiohttp.ClientResponse):
        headers = resp.headers.copy()
        for key in HOP_BY_HOP_HEADERS:
            headers.pop(key, None)
        if "Content-Length" in headers:
            data = await resp.read()
        else:
            data = TaskManager._stream_response(resp)
        async with self._session.post(self._proxy_url(request_id, resp.status), data=data, headers=headers) as resp:
            await resp.text()
            return resp
    
    async def send_proxy_result(self, request_id: str, status_code: int, data: bytes):
        try:
            async with self._session.post(self._proxy_url(request_id, status_code), data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"failed to send proxy result, status code: {resp.status}, body: {text}", request_id=request_id)
        except Exception as e:
            logger.error(f"failed to send proxy result, err: {e}", request_id=request_id, exc_info=True)

    async def send_proxy(self, request_id: str, resp: aiohttp.ClientResponse) -> aiohttp.ClientResponse | str:
        try:
            await self._send_proxy(request_id, resp)
            return resp
        except Exception as e:
            logger.error(f"failed to send proxy, err: {e}", request_id=request_id, exc_info=True)
            return f"failed to send proxy, err: {e}"

    async def report_status(self, request_id: str, data: bytes):
        try:
            await self._report_status(request_id, data)
        except Exception as e:
            logger.error(f"failed to report status, err: {e}", request_id=request_id, exc_info=True)

    async def _report_status(self, request_id: str, data: bytes):
        async with self._session.post(self._status_url(request_id), data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"failed to report status, status code: {resp.status}, body: {text}", request_id=request_id)
                return

    async def close(self):
        await self._session.close()

    @staticmethod
    async def _stream_response(resp: aiohttp.ClientResponse):
        async for data in resp.content.iter_any():
            yield data
