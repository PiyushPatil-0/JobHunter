"""
Run JobHunter scheduler.
"""

from app.collectors.greenhouse import GreenhouseCollector
from app.collectors.manager import CollectorManager
from app.config.settings import settings
from app.database.init_db import init_database
from app.database.repository import JobRepository
from app.engine.job_engine import JobEngine
from app.notifications.telegram import TelegramNotifier
from app.scheduler.scheduler import JobScheduler
from app.services.scan_service import ScanService


def main():

    init_database()

    manager = CollectorManager()

    manager.register(
        GreenhouseCollector(
            settings.sources.greenhouse.companies
        )
    )

    engine = JobEngine(
        collector_manager=manager,
        repository=JobRepository(),
        notifier=TelegramNotifier(),
    )

    scan_service = ScanService(engine)

    scheduler = JobScheduler(scan_service)

    scheduler.start()


if __name__ == "__main__":
    main()