"""
Application scheduler.
"""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.collectors.groups import CollectorGroup
from app.collectors.manager import CollectorManager
from app.config.settings import settings
from app.services.scan_service import ScanService
from app.utils.logger import logger


class JobScheduler:

    def __init__(
        self,
        scan_service: ScanService,
        collector_manager: CollectorManager,
    ) -> None:

        self.scan_service = scan_service
        self.collector_manager = collector_manager
        self.scheduler = BlockingScheduler()

    def start(self) -> None:

        # Each scheduling group gets its own interval, read from
        # config. Adding a new group here (or a new collector to an
        # existing one) never requires touching JobEngine.
        interval_by_group = {
            CollectorGroup.ATS: settings.scheduler.ats_interval_minutes,
            CollectorGroup.JOB_BOARDS: settings.scheduler.job_board_interval_minutes,
        }

        active_groups = self.collector_manager.groups()

        scheduled_groups = [
            group
            for group in interval_by_group
            if group in active_groups
        ]

        if not scheduled_groups:
            logger.warning(
                "No collectors registered - scheduler has nothing to run."
            )
            return

        for group in scheduled_groups:

            interval = interval_by_group[group]

            logger.success(
                f"Scheduling '{group}' scans every {interval} minutes"
            )

            self.scheduler.add_job(
                func=self.scan_service.run_scan,
                trigger="interval",
                minutes=interval,
                id=f"job_scan_{group}",
                kwargs={"group": group},
                max_instances=1,
                coalesce=True,
                misfire_grace_time=60,
                replace_existing=True,
            )

        # Run each active group once immediately on startup,
        # sequentially - ScanService's shared lock means these
        # never overlap even if triggered close together.
        for group in scheduled_groups:
            self.scan_service.run_scan(group=group)

        self.scheduler.start()
