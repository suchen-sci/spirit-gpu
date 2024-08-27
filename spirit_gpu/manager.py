from enum import Enum
from urllib.parse import urljoin

import aiohttp

from . import settings, task
from .log import logger
from typing import Any, Callable, Dict


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
            logger.error(f"failed to ack request {request_id}: {e}", exc_info=True)

    async def _ack_request(self, request_id: str):
        async with self._session.post(self._ack_url(request_id)) as resp:
            if resp.status != 200:
                logger.error(
                    f"failed to ack request {request_id}: {resp.status}, {await resp.text()}"
                )
                return
            logger.debug(f"ack request {request_id}")

    async def _send_result(self, request_id: str, data: bytes):
        async with self._session.post(self._result_url(request_id), data=data) as resp:
            if resp.status != 200:
                logger.error(
                    f"failed to report result for request {request_id}: {resp.status}, {await resp.text()}"
                )
                return

    async def send_result(self, request_id: str, data: bytes):
        try:
            await self._send_result(request_id, data)
        except Exception as e:
            logger.error(
                f"failed to send result for request {request_id}: {e}", exc_info=True
            )

    async def report_status(self, request_id: str, data: bytes):
        try:
            await self._report_status(request_id, data)
        except Exception as e:
            logger.error(
                f"failed to report status for request {request_id}: {e}", exc_info=True
            )

    async def _report_status(self, request_id: str, data: bytes):
        async with self._session.post(self._status_url(request_id), data=data) as resp:
            if resp.status != 200:
                logger.error(
                    f"failed to report status for request {request_id}: {resp.status}, {await resp.text()}"
                )
                return
            logger.debug(f"report status for request {request_id}")

    async def close(self):
        await self._session.close()
