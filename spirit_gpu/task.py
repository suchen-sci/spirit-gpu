import base64
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict
import json
import dataclasses


class Status(Enum):
    Failed = "failed"
    Succeed = "succeed"
    Executing = "executing"


class Operation(Enum):
    Async = "async"
    Sync = "sync"


class MsgHeaderKey(Enum):
    Mode = "Ease-Mode"
    Webhook = "Ease-Webhook"
    RequestID = "Ease-Request-Id"
    EnqueueAt = "Ease-Enqueue-At"
    CreateAt = "Ease-Create-At"
    StatusSubject = "Ease-Status-Subject"
    TTL = "Ease-Time-To-Live"


@dataclass
class MsgHeader:
    mode: str
    webhook: str
    request_id: str
    status_subject: str

    enqueue_at: int
    create_at: int
    ttl: int

    @staticmethod
    def parse(headers: Dict[str, str]):
        getValue: Callable[[str, str], str] = lambda key, default: headers.get(key, default).split(",")[0]
        return MsgHeader(
            mode=getValue(MsgHeaderKey.Mode.value, ""),
            webhook=getValue(MsgHeaderKey.Webhook.value, ""),
            request_id=getValue(MsgHeaderKey.RequestID.value, ""),
            enqueue_at=int(getValue(MsgHeaderKey.EnqueueAt.value, "0")),
            create_at=int(getValue(MsgHeaderKey.CreateAt.value, "0")),
            status_subject=getValue(MsgHeaderKey.StatusSubject.value, ""),
            ttl=int(getValue(MsgHeaderKey.TTL.value, "600000")),
        )


@dataclass
class Task:
    header: MsgHeader
    data: bytes

    @staticmethod
    def parse(request: Dict[str, Any]):
        header: Dict[str, str] = request.get("headers", {})
        body: str = request.get("body", "")
        data: bytes = base64.b64decode(body)
        return Task(header=MsgHeader.parse(header), data=data)


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


def getStatus(
    *,
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
