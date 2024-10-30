import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional

from .settings import EASE_LOG_LEVEL

MAX_LOG_LENGTH = 4096


_levelToName = {
    logging.CRITICAL: "CRITICAL",
    logging.ERROR: "ERROR",
    logging.WARN: "WARN",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
    logging.NOTSET: "NOTSET",
}

_nameToLevel = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARN,
    "WARNING": logging.WARN,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _valid_log_level(level: Any) -> int:
    if isinstance(level, str):
        name = level.upper()
        l = _nameToLevel.get(name)
        if l is None:
            print(
                f"Invalid log level {level}, use default INFO, available levels: {list(_nameToLevel.keys())}",
                flush=True,
            )
            return logging.INFO
        return l

    if isinstance(level, int):
        if level not in _levelToName:
            print(
                f"Invalid log level {level}, use default INFO, available levels: logging.DEBUG, logging.INFO etc.",
                flush=True,
            )
            return logging.INFO
        return level

    print(
        f"Invalid log level type {type(level)} {level}, use default INFO, should be either str or int",
        flush=True,
    )
    return logging.INFO


def _get_log_level():
    level = os.environ.get(EASE_LOG_LEVEL, _levelToName[logging.INFO])
    print(f"Log level: {level}", flush=True)
    return _valid_log_level(level)


class Logger:
    """Singleton class for logging in spirit-gpu"""

    __instance = None
    _level = _get_log_level()

    def __new__(cls):
        if Logger.__instance is None:
            Logger.__instance = object.__new__(cls)
        return Logger.__instance

    def _get_level_name(self, level: int) -> str:
        return _levelToName.get(level, "UNKNOWN")

    def _limit_message(self, message: Any) -> str:
        message = str(message)
        if len(message) <= MAX_LOG_LENGTH:
            return message

        half = MAX_LOG_LENGTH // 2
        truncated = len(message) - MAX_LOG_LENGTH
        return (
            message[:half]
            + f"\n... EXCEED MAX LOG LENGTH, TRUNCATED {truncated} CHARACTERS...\n"
            + message[-half:]
        )

    def set_level(self, level: int | str):
        """
        level can be string of "CRITICAL", "ERROR", "WARNING", "INFO", or "DEBUG" or
        int of levels in python logging library, like logging.WARN etc.
        ```
        """
        l = _valid_log_level(level)
        print(f"Set log level to {self._get_level_name(l)}", flush=True)
        self._level = l

    def _log(
        self,
        message: Any,
        level: int,
        request_id: Optional[str],
        caller: bool,
        exc_info: bool,
    ):

        if level < self._level:
            return

        level_name = self._get_level_name(level)

        if caller:
            # IronPython doesn't track Python frames, so findCaller raises an
            # exception on some versions of IronPython. We trap it here so that
            # IronPython can use logging.
            try:
                pathname, lno, _, _ = logging.root.findCaller(stack_info=False, stacklevel=3)
                try:
                    filename = os.path.basename(pathname)
                except (TypeError, ValueError, AttributeError):
                    filename = pathname
            except ValueError:  # pragma: no cover
                filename, lno = "(unknown file)", 0
            message = f"[{filename}:{lno}] {message}"

        message = self._limit_message(message)
        request_id = str(request_id) if request_id is not None else ""
        log: Dict[str, str] = {
            "message": message,
            "requestID": request_id,
            "level": level_name,
        }
        print(json.dumps(log, ensure_ascii=False), flush=True)
    
        if exc_info:
            exc = sys.exc_info()
            if exc[0] is None:
                return # no exception
            info = "".join(traceback.format_exception(*exc))
            print(info, end="", flush=True)

    def critical(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an critical message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.CRITICAL, request_id, caller, exc_info)

    def error(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an error message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.ERROR, request_id, caller, exc_info)

    def warn(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an warn message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.WARN, request_id, caller, exc_info)
    
    def warning(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an warn message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.WARN, request_id, caller, exc_info)

    def info(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an info message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.INFO, request_id, caller, exc_info)

    def debug(self, message: Any, request_id: Optional[str] = None, caller: bool = False, exc_info: bool = False):
        """
        Log an debug message with optional request ID, caller information (filename and line number), and exception traceback.
        """
        self._log(message, logging.DEBUG, request_id, caller, exc_info)

logger = Logger()