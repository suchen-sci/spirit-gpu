from . import conf
from .log import logger


class Env:
    """
    Env class provides a runtime environment for the user to interact with models and other services.
    """

    def __init__(self, config: conf.Config):
        logger.info("prepare environment.")
        self.config = config
