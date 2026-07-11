"""
Database models.
"""

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String

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