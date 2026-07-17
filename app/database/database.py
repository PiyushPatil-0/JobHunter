"""
Database configuration.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

ROOT_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = ROOT_DIR / settings.database.path

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # run_bot.py runs the Telegram bot's polling loop and the
    # scheduler's scan loop on separate threads of the same process,
    # both reading/writing this same SQLite file. Without the
    # settings below, that split can raise "database is locked"
    # errors, or a ProgrammingError if a pooled connection opened on
    # one thread gets handed to the other.
    connect_args={
        # SQLAlchemy's connection pool can check a connection out on
        # a different thread than the one that opened it; SQLite's
        # default same-thread check would reject that even though
        # our own session usage (one Session per call, closed right
        # after) never actually shares a connection across threads
        # at the same time.
        "check_same_thread": False,
        # Belt-and-suspenders alongside the busy_timeout PRAGMA
        # below: have the sqlite3 driver itself retry for up to 30s
        # on a locked database before giving up.
        "timeout": 30,
    },
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    """
    Applied to every new connection the pool opens.

    - journal_mode=WAL: readers no longer block writers and vice
      versa. This is the main fix for lock contention between the
      bot thread and the scheduler thread.
    - busy_timeout: if a write still collides (e.g. two writers at
      the exact same instant), SQLite retries internally for up to
      30s instead of raising immediately.
    - foreign_keys=ON: off by default in SQLite; on so the
      ForeignKey constraints declared in app.database.models (User
      <- Preference, User <- UserNotification) are actually
      enforced, not just documented.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_session():
    return SessionLocal()
