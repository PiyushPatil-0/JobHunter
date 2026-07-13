"""
SmartRecruiters API Collector.

Uses SmartRecruiters' public Posting API - no auth required. The
list endpoint doesn't include a full job description (that needs a
separate per-posting detail call), so this collector deliberately
doesn't fetch descriptions to avoid an N+1 request pattern against
every company on every scan.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger


class SmartRecruitersCollector(BaseCollector):

    BASE_URL = "https://api.smartrecruiters.com/v1/companies"

    def __init__(self, companies: list[str]) -> None:

        self.client = HttpClient()

        self.companies = companies

    @property
    def name(self) -> str:
        return "SmartRecruiters"

    def collect(self) -> list[Job]:

        jobs: list[Job] = []

        for company in self.companies:

            url = f"{self.BASE_URL}/{company}/postings?limit=100"

            logger.info(f"Loading {company}")

            try:

                data = self.client.get_json(url)

                for item in data.get("content", []):

                    title = item.get("name", "")

                    try:

                        jobs.append(

                            Job(

                                title=title,

                                company=company,

                                location=self._format_location(
                                    item.get("location", {}) or {}
                                ),

                                experience="Unknown",

                                source=JobSource.SMARTRECRUITERS,

                                url=(
                                    "https://jobs.smartrecruiters.com/"
                                    f"{company}/{item.get('id', '')}"
                                ),

                                employment_type=self._map_employment_type(
                                    (
                                        item.get("typeOfEmployment")
                                        or {}
                                    ).get("label", "")
                                ),
                            )
                        )

                    except Exception:

                        logger.warning(
                            f"Skipped malformed job at {company}: "
                            f"{title!r}"
                        )

            except Exception:

                logger.exception(
                    f"Failed: {company}"
                )

        logger.success(
            f"Collected {len(jobs)} jobs from SmartRecruiters."
        )

        return jobs

    @staticmethod
    def _format_location(location: dict) -> str:

        if location.get("remote"):
            return "Remote"

        parts = [
            location.get("city", ""),
            location.get("country", ""),
        ]

        return ", ".join(part for part in parts if part)

    @staticmethod
    def _map_employment_type(label: str) -> EmploymentType:

        label = (label or "").lower()

        if "intern" in label:
            return EmploymentType.INTERNSHIP

        if "contract" in label or "temporary" in label:
            return EmploymentType.CONTRACT

        if "part" in label:
            return EmploymentType.PART_TIME

        if "full" in label:
            return EmploymentType.FULL_TIME

        return EmploymentType.UNKNOWN
