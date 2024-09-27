from typing import Callable, Optional
from .log import logger


class Concurrency:
    def __init__(self, concurrency_modifier: Optional[Callable[[int], int]]):
        if concurrency_modifier is not None:
            self.concurrency_modifier = concurrency_modifier
        else:
            self.concurrency_modifier: Callable[[int], int] = lambda x: x

        self.allowed_concurrency = 1
        self.current_jobs: set[str] = set()

    def is_available(self) -> bool:
        current = self.allowed_concurrency
        try:
            self.allowed_concurrency = self.concurrency_modifier(current)
            self.allowed_concurrency = int(self.allowed_concurrency)
        except Exception as e:
            logger.error(f"failed to call concurrency_modifier with input {current}, set concurrency to default 1, err: {e}", exc_info=True)
            self.allowed_concurrency = 1
        return len(self.current_jobs) < self.allowed_concurrency

    def add_job(self, request_id: str):
        self.current_jobs.add(request_id)
        logger.info(f"added, allowed concurrency: {self.allowed_concurrency}, current jobs: {len(self.current_jobs)}", request_id=request_id)

    def get_jobs(self):
        return list(self.current_jobs)

    def remove_job(self, request_id: str):
        try:
            self.current_jobs.remove(request_id)
        except Exception as e:
            logger.error(f"failed to remove request from concurrency, err: {e}", request_id=request_id, exc_info=True)
        logger.info(f"remove request from concurrency, allowed concurrency: {self.allowed_concurrency}, current jobs: {len(self.current_jobs)}", request_id=request_id) 