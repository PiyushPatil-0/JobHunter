"""
Greenhouse API Collector.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger


class GreenhouseCollector(BaseCollector):

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, companies: list[str]) -> None:

        self.client = HttpClient()

        self.companies = companies

    @property
    def name(self) -> str:
        return "Greenhouse"

    def collect(self) -> list[Job]:

        jobs: list[Job] = []

        for company in self.companies:

            url = f"{self.BASE_URL}/{company}/jobs"

            logger.info(f"Loading {company}")

            try:

                data = self.client.get_json(url)

                for item in data.get("jobs", []):
                    
                    title = item.get("title", "")

                    from app.collectors.pre_filter import PreFilter

                    if not PreFilter.accept(title):
                        continue

                    jobs.append(

                        Job(

                            title=item.get("title", ""),

                            company=company,

                            location=item.get(
                                "location",
                                {}
                            ).get(
                                "name",
                                ""
                            ),

                            experience="Unknown",

                            source=JobSource.COMPANY,

                            url=item.get(
                                "absolute_url",
                                ""
                            ),

                            employment_type=EmploymentType.FULL_TIME,

                            description=item.get("content", "")
                        )
                    )

            except Exception:

                logger.exception(
                    f"Failed: {company}"
                )

        logger.success(
            f"Collected {len(jobs)} jobs "
            f"from Greenhouse."
        )

        return jobs