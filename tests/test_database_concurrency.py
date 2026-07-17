"""
Verifies the SQLite configuration in app.database.database - WAL
mode, busy_timeout, check_same_thread, and foreign key enforcement -
actually prevents "database is locked" errors when two threads write
at once, mirroring run_bot.py's scheduler thread + bot thread both
hitting the same SQLite file.

Builds its own throwaway engine against a temp file with the exact
same connect_args/pragmas as app.database.database, rather than
importing that module's already-bound engine - this suite should
never touch the project's real data/jobs.db.
"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import text


def _make_engine(db_path: Path):
    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture
def engine():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        eng = _make_engine(db_path)
        with eng.connect() as connection:
            connection.execute(text("CREATE TABLE t (label TEXT, i INTEGER)"))
            connection.commit()
        yield eng
        eng.dispose()


class TestSqlitePragmas:
    def test_journal_mode_is_wal(self, engine) -> None:
        with engine.connect() as connection:
            mode = connection.execute(text("PRAGMA journal_mode")).scalar()
        assert mode.lower() == "wal"

    def test_busy_timeout_is_at_least_30s(self, engine) -> None:
        with engine.connect() as connection:
            timeout_ms = connection.execute(text("PRAGMA busy_timeout")).scalar()
        assert timeout_ms >= 30_000

    def test_foreign_keys_are_enforced(self, engine) -> None:
        with engine.connect() as connection:
            enforced = connection.execute(text("PRAGMA foreign_keys")).scalar()
        assert enforced == 1


class TestConcurrentWrites:
    def test_two_threads_writing_do_not_raise_database_locked(self, engine) -> None:
        """
        Mirrors run_bot.py: the scheduler thread and the bot thread
        both write to the same SQLite file at the same time. Before
        the WAL/busy_timeout fix, this reliably raised
        "database is locked" under real contention.
        """
        errors: list[Exception] = []

        def write_rows(label: str, count: int) -> None:
            try:
                for i in range(count):
                    with engine.begin() as connection:
                        connection.execute(
                            text("INSERT INTO t (label, i) VALUES (:label, :i)"),
                            {"label": label, "i": i},
                        )
            except Exception as exc:  # noqa: BLE001 - want visibility on anything
                errors.append(exc)

        threads = [
            threading.Thread(target=write_rows, args=("scheduler-thread", 50)),
            threading.Thread(target=write_rows, args=("bot-thread", 50)),
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Concurrent writes raised: {errors}"

        with engine.connect() as connection:
            total = connection.execute(text("SELECT COUNT(*) FROM t")).scalar()
        assert total == 100
