import os

EASE_TEST_MODE = "EASE_TEST_MODE"
EASE_DEBUG = "EASE_DEBUG"
EASE_TEST_PORT = "EASE_TEST_PORT"
EASE_AGENT_URL = "EASE_AGENT_URL"
EASE_DOCKER_COMMAND = "docker"

HEADER_HEALTH = "X-Agent-Health"


class _Settings:
    def __init__(self):
        self._serverless_id = ""
        self._worker_id = ""
        self._agent_url = ""

    def agent_url(self) -> str:
        if self._agent_url != "":
            return self._agent_url
        self._agent_url = os.environ.get(EASE_AGENT_URL, "http://localhost:8087")
        return self._agent_url


SETTINGS = _Settings()
