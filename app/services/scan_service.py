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

    def run_scan(self) -> EngineResult | None:

        if not self._lock.acquire(blocking=False):
            logger.warning("Scan already running.")
            return None

        try:
            logger.info("Starting scan...")
            return self.engine.run()

        finally:
            self._lock.release()