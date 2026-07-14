"""
Ashby API Collector.

Uses Ashby's documented public Job Board API - no auth required,
same pattern as Greenhouse.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.datetime_utils import parse_posted_at
from app.utils.logger import logger


class AshbyCollector(BaseCollector):

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

    def __init__(self, companies: list[str]) -> None:

        self.client = HttpClient()

        self.companies = companies

    @property
    def name(self) -> str:
        return "Ashby"

    def collect(self) -> list[Job]:

        jobs: list[Job] = []

        for company in self.companies:

            url = f"{self.BASE_URL}/{company}"

            logger.info(f"Loading {company}")

            try:

                data = self.client.get_json(url)

                for item in data.get("jobs", []):

                    title = item.get("title", "")

                    try:

                        jobs.append(

                            Job(

                                title=title,

                                company=company,

                                location=item.get("location", ""),

                                experience="Unknown",

                                source=JobSource.ASHBY,

                                url=item.get("jobUrl", ""),

                                employment_type=self._map_employment_type(
                                    item.get("employmentType", "")
                                ),

                                description=item.get(
                                    "descriptionPlain", ""
                                ),

                                posted_at=parse_posted_at(item.get("publishedAt")),
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
            f"Collected {len(jobs)} jobs from Ashby."
        )

        return jobs

    @staticmethod
    def _map_employment_type(value: str) -> EmploymentType:

        value = (value or "").lower()

        if "intern" in value:
            return EmploymentType.INTERNSHIP

        if "contract" in value:
            return EmploymentType.CONTRACT

        if "part" in value:
            return EmploymentType.PART_TIME

        if "full" in value:
            return EmploymentType.FULL_TIME

        return EmploymentType.UNKNOWN
