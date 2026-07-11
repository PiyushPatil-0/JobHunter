"""
Dummy collector used during development.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource


class DummyCollector(BaseCollector):

    @property
    def name(self) -> str:
        return "Dummy Collector"

    def collect(self) -> list[Job]:

        return [

            Job(
                title="Java Backend Developer",
                company="Google",
                location="Bangalore",
                experience="0-2 Years",
                source=JobSource.COMPANY,
                url="https://example.com/google",
                employment_type=EmploymentType.FULL_TIME,
            ),

            Job(
                title="Senior Java Architect",
                company="Microsoft",
                location="Hyderabad",
                experience="8+ Years",
                source=JobSource.COMPANY,
                url="https://example.com/microsoft",
                employment_type=EmploymentType.FULL_TIME,
            ),
        ]