"""
Core domain model representing a collected job.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class JobSource(str, Enum):
    NAUKRI = "Naukri"
    WELLFOUND = "Wellfound"
    LINKEDIN = "LinkedIn"
    GREENHOUSE = "Greenhouse"
    LEVER = "Lever"
    WORKDAY = "Workday"
    SMARTRECRUITERS = "SmartRecruiters"
    ASHBY = "Ashby"
    # Generic fallback - used by collectors (e.g. the dev-only
    # DummyCollector) that don't map to a specific real ATS.
    COMPANY = "Company"


class EmploymentType(str, Enum):
    FULL_TIME = "Full Time"
    INTERNSHIP = "Internship"
    CONTRACT = "Contract"
    PART_TIME = "Part Time"
    UNKNOWN = "Unknown"


class Job(BaseModel):
    title: str = Field(..., min_length=2)

    company: str = Field(..., min_length=2)

    location: str

    experience: str

    source: JobSource

    url: str

    description: str = ""

    hash: str = ""

    employment_type: EmploymentType = EmploymentType.UNKNOWN

    posted_at: datetime | None = None

    collected_at: datetime = Field(default_factory=datetime.utcnow)

    # Engine metadata
    match_score: float = 0.0

    resume_score: float = 0.0

    notified: bool = False
