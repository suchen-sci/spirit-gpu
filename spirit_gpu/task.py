import base64
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict


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
        getValue : Callable[[str, str], str] = lambda key, default: headers.get(key, default).split(",")[0]
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