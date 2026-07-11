"""
Run JobHunter Telegram Bot.
"""

from app.bot.telegram_bot import TelegramBot
from app.collectors.greenhouse import GreenhouseCollector
from app.collectors.manager import CollectorManager
from app.config.settings import settings
from app.database.init_db import init_database
from app.database.repository import JobRepository
from app.engine.job_engine import JobEngine
from app.notifications.telegram import TelegramNotifier
from app.services.scan_service import ScanService


def main() -> None:

    init_database()

    manager = CollectorManager()

    if settings.sources.greenhouse.enabled:
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

    bot = TelegramBot(scan_service)

    bot.start()


if __name__ == "__main__":
    main()