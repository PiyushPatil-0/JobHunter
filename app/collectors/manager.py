"""
Collector manager.

Responsible for executing all registered collectors.
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.models.job import Job
from app.utils.logger import logger


class CollectorManager:

    def __init__(self) -> None:
        self.collectors: list[BaseCollector] = []

    def register(self, collector: BaseCollector) -> None:
        logger.info(f"Registered collector: {collector.name}")
        self.collectors.append(collector)

    def collect_jobs(self) -> list[Job]:

        jobs: list[Job] = []

        for collector in self.collectors:

            logger.info(f"Running collector: {collector.name}")

            try:
                jobs.extend(collector.collect())

            except Exception:

                logger.exception(
                    f"Collector failed: {collector.name}"
                )

        logger.info(f"Collected {len(jobs)} jobs.")

        return jobs