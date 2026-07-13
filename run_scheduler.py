"""
Run JobHunter scheduler.
"""

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
from app.scheduler.scheduler import JobScheduler
from app.services.scan_service import ScanService


def main():

    init_database()

    manager = CollectorManager()

    if settings.sources.greenhouse.enabled:
        manager.register(
            GreenhouseCollector(
                settings.sources.greenhouse.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.lever.enabled:
        manager.register(
            LeverCollector(
                settings.sources.lever.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.ashby.enabled:
        manager.register(
            AshbyCollector(
                settings.sources.ashby.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.smartrecruiters.enabled:
        manager.register(
            SmartRecruitersCollector(
                settings.sources.smartrecruiters.companies
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.workday.enabled:
        manager.register(
            WorkdayCollector(
                [
                    tenant.model_dump()
                    for tenant in settings.sources.workday.tenants
                ]
            ),
            group=CollectorGroup.ATS,
        )

    if settings.sources.linkedin.enabled:
        manager.register(
            LinkedInCollector(
                keywords=settings.sources.linkedin.keywords,
                locations=settings.sources.linkedin.locations,
                max_pages=settings.sources.linkedin.max_pages,
            ),
            group=CollectorGroup.JOB_BOARDS,
        )

    if settings.sources.naukri.enabled:
        manager.register(
            NaukriCollector(
                keywords=settings.sources.naukri.keywords,
                locations=settings.sources.naukri.locations,
                max_pages=settings.sources.naukri.max_pages,
            ),
            group=CollectorGroup.JOB_BOARDS,
        )

    engine = JobEngine(
        collector_manager=manager,
        repository=JobRepository(),
        notifier=TelegramNotifier(),
    )

    scan_service = ScanService(engine)

    scheduler = JobScheduler(scan_service, manager)

    scheduler.start()


if __name__ == "__main__":
    main()
