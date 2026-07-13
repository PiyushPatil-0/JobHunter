"""
Centralized scan service.
"""

from __future__ import annotations

from threading import Lock

from app.engine.engine_result import EngineResult
from app.engine.job_engine import JobEngine
from app.utils.logger import logger


class ScanService:

    def __init__(self, engine: JobEngine) -> None:
        self.engine = engine
        self._lock = Lock()

    def run_scan(self, group: str | None = None) -> EngineResult | None:
        """
        Run a scan, optionally scoped to a single collector group.

        The lock is shared across every group so two scheduled
        tiers (e.g. "ats" and "job_boards") can never write to
        SQLite at the same time - a concurrent trigger is simply
        skipped rather than queued.
        """

        if not self._lock.acquire(blocking=False):
            logger.warning("Scan already running.")
            return None

        try:
            logger.info(
                f"Starting scan (group={group or 'all'})..."
            )
            return self.engine.run(group=group)

        finally:
            self._lock.release()
