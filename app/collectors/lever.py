"""
Lever API Collector.

Uses Lever's public postings API - no auth required, same pattern
as Greenhouse.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger


class LeverCollector(BaseCollector):

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, companies: list[str]) -> None:

        self.client = HttpClient()

        self.companies = companies

    @property
    def name(self) -> str:
        return "Lever"

    def collect(self) -> list[Job]:

        jobs: list[Job] = []

        for company in self.companies:

            url = f"{self.BASE_URL}/{company}?mode=json"

            logger.info(f"Loading {company}")

            try:

                data = self.client.get_json(url)

                for item in data:

                    title = item.get("text", "")

                    categories = item.get("categories", {}) or {}

                    try:

                        jobs.append(

                            Job(

                                title=title,

                                company=company,

                                location=categories.get("location", ""),

                                experience="Unknown",

                                source=JobSource.LEVER,

                                url=item.get("hostedUrl", ""),

                                employment_type=self._map_employment_type(
                                    categories.get("commitment", "")
                                ),

                                description=(
                                    item.get("descriptionPlain", "")
                                    or item.get("description", "")
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
            f"Collected {len(jobs)} jobs from Lever."
        )

        return jobs

    @staticmethod
    def _map_employment_type(commitment: str) -> EmploymentType:

        commitment = (commitment or "").lower()

        if "intern" in commitment:
            return EmploymentType.INTERNSHIP

        if "contract" in commitment:
            return EmploymentType.CONTRACT

        if "part" in commitment:
            return EmploymentType.PART_TIME

        if "full" in commitment:
            return EmploymentType.FULL_TIME

        return EmploymentType.UNKNOWN
