"""
Wellfound collector.

Currently uses the public Wellfound jobs feed when available.
The implementation is intentionally isolated so the rest of the
application never depends on the source.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.collectors.pre_filter import PreFilter
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger


class WellfoundCollector(BaseCollector):

    BASE_URL = "https://wellfound.com/jobs"

    def __init__(self) -> None:

        self.client = HttpClient()

    @property
    def name(self) -> str:

        return "Wellfound"

    def collect(self) -> list[Job]:

        logger.info(
            "Wellfound collector is currently disabled."
        )

        logger.info(
            "Waiting for configured search endpoint."
        )

        return []