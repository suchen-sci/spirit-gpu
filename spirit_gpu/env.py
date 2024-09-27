from . import conf


class Env:
    """
    Env class provides a runtime environment for the user to interact with models and other services.
    """

    def __init__(self, config: conf.Config):
        self.config = config
