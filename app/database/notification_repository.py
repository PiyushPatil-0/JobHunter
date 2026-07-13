"""
Repository layer for per-user notification history.

Ensures the same job is never sent twice to the same user.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.database import get_session
from app.database.models import UserNotification as UserNotificationEntity


class UserNotificationRepository:

    @staticmethod
    def already_notified(user_id: int, job_hash: str) -> bool:

        with get_session() as session:

            stmt = select(UserNotificationEntity).where(
                UserNotificationEntity.user_id == user_id,
                UserNotificationEntity.job_hash == job_hash,
            )

            return session.scalar(stmt) is not None

    @staticmethod
    def record(user_id: int, job_hash: str) -> None:

        with get_session() as session:

            entity = UserNotificationEntity(
                user_id=user_id,
                job_hash=job_hash,
            )

            session.add(entity)

            try:
                session.commit()

            except IntegrityError:
                # Already recorded (unique constraint) - safe to ignore.
                session.rollback()

    @staticmethod
    def cleanup(days: int) -> int:
        """
        Placeholder for cleanup, matching JobRepository.cleanup().

        Will be implemented alongside configurable job retention.
        """
        return 0
