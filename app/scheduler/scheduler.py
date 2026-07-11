"""
Application scheduler.
"""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config.settings import settings
from app.services.scan_service import ScanService
from app.utils.logger import logger


class JobScheduler:

    def __init__(
        self,
        scan_service: ScanService,
    ) -> None:

        self.scan_service = scan_service

        self.scheduler = BlockingScheduler()

    def start(self) -> None:

        interval = settings.scheduler.interval_minutes

        logger.success(
            f"Scheduler started ({interval} minutes)"
        )

        self.scheduler.add_job(
            func=self.scan_service.run_scan,
            trigger="interval",
            minutes=interval,
            id="job_scan",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
            replace_existing=True,
        )

        # Run immediately on startup
        self.scan_service.run_scan()

        self.scheduler.start()