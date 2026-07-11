"""
JobHunter AI Entry Point.
"""

from __future__ import annotations

from app.collectors.greenhouse import GreenhouseCollector
from app.collectors.manager import CollectorManager
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
            )
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
    # Run one scan
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