import logging
import os

from .settings import EASE_DEBUG


def get_log_level():
    if os.environ.get(EASE_DEBUG) is not None:
        return logging.DEBUG
    else:
        return logging.INFO


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(get_log_level())
    return logger


def get_console_handler():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(get_log_level())
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(filename)s:%(lineno)d] - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    return console_handler


logger = get_logger()
logger.addHandler(get_console_handler())
