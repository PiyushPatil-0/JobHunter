"""
JobHunter AI Entry Point.
"""

from __future__ import annotations

from app.collectors.ashby import AshbyCollector
from app.collectors.greenhouse import GreenhouseCollector
from app.collectors.groups import CollectorGroup
from app.collectors.lever import LeverCollector
from app.collectors.linkedin import LinkedInCollector
from app.collectors.manager import CollectorManager
from app.collectors.naukri import NaukriCollector
from app.collectors.smartrecruiters import SmartRecruitersCollector
from app.collectors.workday import WorkdayCollector
from app.config.settings import settings
from app.database.init_db import init_database
from app.database.repository import JobRepository
from app.engine.job_engine import JobEngine
from app.notifications.telegram import TelegramNotifier
from app.services.scan_service import ScanService
from app.utils.logger import logger


def main() -> None:

    logger.info("=" * 60)
    logger.info("Starting JobHunter AI")
    logger.info("=" * 60)

    # ----------------------------------------
    # Initialize database
    # ----------------------------------------

    init_database()

    # ----------------------------------------
    # Collector Manager
    # ----------------------------------------

    collector_manager = CollectorManager()

    if settings.sources.greenhouse.enabled:
        collector_manager.register(
            GreenhouseCollector(
                settings.sources.greenhouse.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.lever.enabled:
        collector_manager.register(
            LeverCollector(
                settings.sources.lever.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.ashby.enabled:
        collector_manager.register(
            AshbyCollector(
                settings.sources.ashby.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.smartrecruiters.enabled:
        collector_manager.register(
            SmartRecruitersCollector(
                settings.sources.smartrecruiters.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.workday.enabled:
        collector_manager.register(
            WorkdayCollector(
                [
                    tenant.model_dump()
                    for tenant in settings.sources.workday.tenants
                ]
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.linkedin.enabled:
        collector_manager.register(
            LinkedInCollector(
                max_pages=settings.sources.linkedin.max_pages,
            ),
            group=CollectorGroup.JOB_BOARDS,
        )

    if settings.sources.naukri.enabled:
        collector_manager.register(
            NaukriCollector(
                max_pages=settings.sources.naukri.max_pages,
            ),
            group=CollectorGroup.JOB_BOARDS,
        )

    # ----------------------------------------
    # Dependencies
    # ----------------------------------------

    repository = JobRepository()

    notifier = TelegramNotifier()

    engine = JobEngine(
        collector_manager=collector_manager,
        repository=repository,
        notifier=notifier,
    )

    scan_service = ScanService(engine)

    # ----------------------------------------
    # Run one scan (all groups - manual runs
    # are never scoped to a single tier)
    # ----------------------------------------

    result = scan_service.run_scan()

    if result is None:
        logger.warning("Another scan is already running.")
        return

    logger.success(
        f"""
Summary

Scanned      : {result.scanned}
Inserted     : {result.inserted}
Duplicates   : {result.duplicates}
Filtered     : {result.filtered}
Notified     : {result.notified}
Failed       : {result.failed}
"""
    )


if __name__ == "__main__":
    main()
