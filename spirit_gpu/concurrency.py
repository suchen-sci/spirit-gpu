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
        try:
            self.allowed_concurrency = self.concurrency_modifier(
                self.allowed_concurrency
            )
        except Exception as e:
            logger.error(f"failed to get concurrency: {e}", exc_info=True)
            self.allowed_concurrency = 1
        return len(self.current_jobs) < self.allowed_concurrency

    def add_job(self, request_id: str):
        self.current_jobs.add(request_id)
        logger.debug(
            f"add job, allowed concurrency: {self.allowed_concurrency}, current jobs: {self.current_jobs}, num: {len(self.current_jobs)}"
        )

    def get_jobs(self):
        return list(self.current_jobs)

    def remove_job(self, request_id: str):
        try:
            self.current_jobs.remove(request_id)
        except Exception as e:
            logger.error(f"failed to remove job {request_id}: {e}", exc_info=True)
        logger.debug(
            f"remove job, allowed concurrency: {self.allowed_concurrency}, current jobs: {self.current_jobs}, num: {len(self.current_jobs)}"
        )
