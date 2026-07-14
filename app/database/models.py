"""
Database models.
"""

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.database import Base


class Job(Base):

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String)

    company: Mapped[str] = mapped_column(String)

    location: Mapped[str] = mapped_column(String)

    experience: Mapped[str] = mapped_column(String)

    source: Mapped[str] = mapped_column(String)

    employment_type: Mapped[str] = mapped_column(
        String(32),
        default="Unknown",
    )

    url: Mapped[str] = mapped_column(String)

    match_score: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    resume_score: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    description: Mapped[str] = mapped_column(
        String,
        default=""
    )

    notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    notification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


class User(Base):
    """
    A Telegram user of JobHunter AI.

    Preferences are never stored in configuration files;
    they live here, one row per user via the `Preference` table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_chat_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    telegram_username: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Preference(Base):
    """
    A user's job-matching preferences.

    One row per user, collected through the Telegram onboarding flow.
    """

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    preferred_role: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    skills: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    locations: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    experience_level: Mapped[str] = mapped_column(
        String(64),
        default="",
    )

    employment_types: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    enabled_sources: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    minimum_match_score: Mapped[int] = mapped_column(
        Integer,
        default=60,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class UserNotification(Base):
    """
    Tracks which jobs have already been sent to which user,
    so nobody is notified about the same job twice.
    """

    __tablename__ = "user_notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    job_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_hash",
            name="uq_user_job_notification",
        ),
    )
