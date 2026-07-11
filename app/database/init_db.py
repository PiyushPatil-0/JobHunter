"""
Database initialization.
"""

from app.database.database import Base
from app.database.database import engine
from app.utils.logger import logger


def init_database() -> None:
    """
    Create database tables if they don't exist.
    """

    logger.info("Initializing database...")

    Base.metadata.create_all(bind=engine)

    logger.success("Database initialized.")