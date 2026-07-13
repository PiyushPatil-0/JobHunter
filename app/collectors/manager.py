"""
Collector manager.

Responsible for executing registered collectors, optionally scoped
to a single scheduling group (see app.collectors.groups).
"""

from __future__ import annotations

from app.collectors.base import BaseCollector
from app.models.job import Job
from app.utils.logger import logger


class CollectorManager:

    def __init__(self) -> None:
        self.collectors: list[tuple[str, BaseCollector]] = []

    def register(self, collector: BaseCollector, group: str) -> None:

        logger.info(
            f"Registered collector: {collector.name} (group={group})"
        )

        self.collectors.append((group, collector))

    def groups(self) -> set[str]:
        """
        Every scheduling group with at least one collector registered.
        Used by the scheduler to skip tiers with nothing to run.
        """

        return {group for group, _ in self.collectors}

    def collect_jobs(self, group: str | None = None) -> list[Job]:
        """
        Run collectors and return their combined jobs.

        Parameters
        ----------
        group:
            If given, only collectors registered under this group
            run. If None, every registered collector runs - this is
            what manual scans (/scan, run.py) use.
        """

        jobs: list[Job] = []

        targets = [
            collector
            for collector_group, collector in self.collectors
            if group is None or collector_group == group
        ]

        for collector in targets:

            logger.info(f"Running collector: {collector.name}")

            try:
                jobs.extend(collector.collect())

            except Exception:

                logger.exception(
                    f"Collector failed: {collector.name}"
                )

        logger.info(
            f"Collected {len(jobs)} jobs"
            + (f" (group={group})" if group else "")
            + "."
        )

        return jobs
