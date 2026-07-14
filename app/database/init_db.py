"""
Database initialization.
"""

from app.database.database import Base
from app.database.database import engine
from sqlalchemy import inspect
from sqlalchemy import text

# Importing this module registers every ORM model (Job, User,
# Preference, UserNotification, ...) on Base.metadata. It must
# happen before create_all() runs, regardless of which entry
# point (run.py, run_bot.py, run_scheduler.py) starts the app.
from app.database import models  # noqa: F401

from app.utils.logger import logger


def _migrate_existing_database() -> None:
    """Apply safe, additive SQLite migrations for previously created DBs."""
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "employment_type" not in columns:
        logger.info("Migrating jobs table: adding employment_type.")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE jobs ADD COLUMN employment_type "
                    "VARCHAR(32) NOT NULL DEFAULT 'Unknown'"
                )
            )


def init_database() -> None:
    """
    Create database tables if they don't exist.
    """

    logger.info("Initializing database...")

    Base.metadata.create_all(bind=engine)
    _migrate_existing_database()

    # Fail at startup with a clear remediation path if an existing
    # database predates the current schema. create_all() only creates
    # missing tables; it cannot add missing columns safely.
    inspector = inspect(engine)
    for table in Base.metadata.sorted_tables:
        existing_columns = {
            column["name"]
            for column in inspector.get_columns(table.name)
        }
        required_columns = {column.name for column in table.columns}
        missing_columns = required_columns - existing_columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise RuntimeError(
                f"Database table '{table.name}' is missing columns: {missing}. "
                "Create and run a schema migration before starting the app."
            )

    logger.success("Database initialized.")
