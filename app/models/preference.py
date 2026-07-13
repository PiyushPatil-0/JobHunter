"""
Domain model representing a user's job-matching preferences.

Collected through the Telegram onboarding flow and stored in SQLite.
Never stored in configuration files.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class UserPreference(BaseModel):

    model_config = {"from_attributes": True}

    user_id: int

    preferred_role: str = ""

    skills: list[str] = Field(default_factory=list)

    locations: list[str] = Field(default_factory=list)

    experience_level: str = ""

    employment_types: list[str] = Field(default_factory=list)

    enabled_sources: list[str] = Field(default_factory=list)

    minimum_match_score: int = 60
