import asyncio
import os
from typing import Dict, Any, Optional


from .conf import Config, load_config
from .env import Env
from .worker import run
from .log import logger
from . import utils, server, manage

__all__ = ["start", "utils", "manage"]


def start(handlers: Dict[str, Any], custom_wd: Optional[str] = None):
    """
    handlers: {"handler": async_handler, "concurrency_modifier": concurrency_modifier}
    custom_wd: the working directory of the custom code
    """

    if custom_wd:
        config_file = os.path.join(custom_wd, "config.yaml")
        config = load_config(config_file)
    else:
        config = Config()
    env = Env(config)

    if utils.is_test_mode():
        server.run(handlers, env)
        return

    logger.info(f"start worker")
    asyncio.run(run(handlers, env))
