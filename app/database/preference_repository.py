"""
Repository layer for user preference persistence.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.database.database import get_session
from app.database.models import Preference as PreferenceEntity
from app.database.models import User as UserEntity
from app.models.preference import UserPreference


class PreferenceRepository:

    @staticmethod
    def get_by_user_id(user_id: int) -> UserPreference | None:

        with get_session() as session:

            stmt = select(PreferenceEntity).where(
                PreferenceEntity.user_id == user_id
            )

            entity = session.scalar(stmt)

            if entity is None:
                return None

            return UserPreference.model_validate(entity)

    @staticmethod
    def upsert(preference: UserPreference) -> UserPreference:
        """
        Insert or update the single preference row for a user.
        """

        with get_session() as session:

            stmt = select(PreferenceEntity).where(
                PreferenceEntity.user_id == preference.user_id
            )

            entity = session.scalar(stmt)

            if entity is None:
                entity = PreferenceEntity(user_id=preference.user_id)
                session.add(entity)

            entity.preferred_role = preference.preferred_role
            entity.skills = preference.skills
            entity.locations = preference.locations
            entity.experience_level = preference.experience_level
            entity.employment_types = preference.employment_types
            entity.enabled_sources = preference.enabled_sources
            entity.minimum_match_score = preference.minimum_match_score
            entity.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(entity)

            return UserPreference.model_validate(entity)

    @staticmethod
    def list_all_active() -> list[UserPreference]:
        """
        Preferences for users who completed onboarding and are active.

        Used by the Job Engine to fan a matched job out to every
        interested user.
        """

        with get_session() as session:

            stmt = (
                select(PreferenceEntity)
                .join(
                    UserEntity,
                    UserEntity.id == PreferenceEntity.user_id,
                )
                .where(
                    UserEntity.is_active.is_(True),
                    UserEntity.onboarding_completed.is_(True),
                )
            )

            entities = session.scalars(stmt)

            return [
                UserPreference.model_validate(entity)
                for entity in entities
            ]
