"""
Domain model representing a Telegram user.
"""

from __future__ import annotations

from pydantic import BaseModel


class UserProfile(BaseModel):

    model_config = {"from_attributes": True}

    id: int | None = None

    telegram_chat_id: str

    telegram_username: str | None = None

    is_active: bool = True

    onboarding_completed: bool = False
