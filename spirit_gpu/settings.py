import os

EASE_TEST_MODE = "EASE_TEST_MODE"
EASE_LOG_LEVEL = "EASE_LOG_LEVEL"
EASE_TEST_PORT = "EASE_TEST_PORT"
EASE_AGENT_URL = "EASE_AGENT_URL"
EASE_HEARTBEAT_INTERVAL = "EASE_HEARTBEAT_INTERVAL"

HEADER_HEALTH = "X-Agent-Health"


class _Settings:
    def __init__(self):
        self._agent_url = ""

    def agent_url(self) -> str:
        if self._agent_url != "":
            return self._agent_url
        self._agent_url = os.environ.get(EASE_AGENT_URL, "http://localhost:8087")
        return self._agent_url

    def heartbeat_interval(self) -> int:
        hb = os.environ.get(EASE_HEARTBEAT_INTERVAL, "5")
        try:
            hbi = int(hb)
        except Exception as e:
            print(f"failed to get heartbeat interval: {e}, use default 5")
            hbi = 5
        return hbi


SETTINGS = _Settings()
