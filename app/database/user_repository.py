"""
Repository layer for User persistence.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.database.database import get_session
from app.database.models import User as UserEntity
from app.models.user import UserProfile


class UserRepository:

    @staticmethod
    def get_by_chat_id(chat_id: str) -> UserProfile | None:

        with get_session() as session:

            stmt = select(UserEntity).where(
                UserEntity.telegram_chat_id == chat_id
            )

            entity = session.scalar(stmt)

            if entity is None:
                return None

            return UserProfile.model_validate(entity)

    @staticmethod
    def get_by_id(user_id: int) -> UserProfile | None:

        with get_session() as session:

            entity = session.get(UserEntity, user_id)

            if entity is None:
                return None

            return UserProfile.model_validate(entity)

    @classmethod
    def get_or_create(
        cls,
        chat_id: str,
        username: str | None,
    ) -> UserProfile:

        existing = cls.get_by_chat_id(chat_id)

        if existing is not None:
            return existing

        with get_session() as session:

            entity = UserEntity(
                telegram_chat_id=chat_id,
                telegram_username=username,
                is_active=True,
                onboarding_completed=False,
            )

            session.add(entity)
            session.commit()
            session.refresh(entity)

            return UserProfile.model_validate(entity)

    @staticmethod
    def mark_onboarding_completed(user_id: int) -> None:

        with get_session() as session:

            entity = session.get(UserEntity, user_id)

            if entity is None:
                return

            entity.onboarding_completed = True
            entity.updated_at = datetime.utcnow()

            session.commit()

    @staticmethod
    def set_active(user_id: int, active: bool) -> None:

        with get_session() as session:

            entity = session.get(UserEntity, user_id)

            if entity is None:
                return

            entity.is_active = active
            entity.updated_at = datetime.utcnow()

            session.commit()

    @staticmethod
    def list_active_users() -> list[UserProfile]:
        """
        Users who finished onboarding and are still active.

        This is the set the Job Engine will notify once
        per-user dispatch is wired in.
        """

        with get_session() as session:

            stmt = select(UserEntity).where(
                UserEntity.is_active.is_(True),
                UserEntity.onboarding_completed.is_(True),
            )

            entities = session.scalars(stmt)

            return [
                UserProfile.model_validate(entity)
                for entity in entities
            ]
