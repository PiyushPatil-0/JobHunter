"""
Database initialization.
"""

from app.database.database import Base
from app.database.database import engine

# Importing this module registers every ORM model (Job, User,
# Preference, UserNotification, ...) on Base.metadata. It must
# happen before create_all() runs, regardless of which entry
# point (run.py, run_bot.py, run_scheduler.py) starts the app.
from app.database import models  # noqa: F401

from app.utils.logger import logger


def init_database() -> None:
    """
    Create database tables if they don't exist.
    """

    logger.info("Initializing database...")

    Base.metadata.create_all(bind=engine)

    logger.success("Database initialized.")
