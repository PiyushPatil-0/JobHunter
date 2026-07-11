"""
Core JobHunter Engine.
"""

from __future__ import annotations

from app.collectors.manager import CollectorManager
from app.database.repository import JobRepository
from app.engine.engine_result import EngineResult
from app.filters.job_filter import JobFilter
from app.notifications.telegram import TelegramNotifier
from app.utils.hash_utils import assign_job_hash
from app.utils.logger import logger


class JobEngine:

    def __init__(
        self,
        collector_manager: CollectorManager,
        repository: JobRepository,
        notifier: TelegramNotifier,
    ) -> None:

        self.collector_manager = collector_manager
        self.repository = repository
        self.notifier = notifier
        self.filter = JobFilter()

    def run(self) -> EngineResult:

        logger.info("Starting JobHunter Engine...")

        result = EngineResult()

        jobs = self.collector_manager.collect_jobs()

        result.scanned = len(jobs)

        logger.info(
            f"Collected {result.scanned} jobs."
        )

        jobs_to_notify: list = []

        for job in jobs:

            try:

                # ----------------------------------
                # Filter
                # ----------------------------------

                if not self.filter.accept(job):

                    result.filtered += 1

                    continue

                # ----------------------------------
                # Hash
                # ----------------------------------

                assign_job_hash(job)

                # ----------------------------------
                # Repository
                # ----------------------------------

                process = self.repository.process(job)

                if process.duplicate:

                    result.duplicates += 1

                    continue

                result.inserted += 1

                jobs_to_notify.append(job)

            except Exception:

                logger.exception(
                    f"Failed processing {job.title}"
                )

                result.failed += 1

        # ------------------------------------------
        # Send ONE Telegram digest
        # ------------------------------------------

        if jobs_to_notify:

            if self.notifier.send_jobs(jobs_to_notify):

                for job in jobs_to_notify:

                    self.repository.mark_notified(
                        job.hash
                    )

                result.notified = len(
                    jobs_to_notify
                )

            else:

                result.failed += len(
                    jobs_to_notify
                )

        logger.success(
            f"""
================ Scan Completed ================

Scanned      : {result.scanned}
Filtered     : {result.filtered}
Inserted     : {result.inserted}
Duplicates   : {result.duplicates}
Notified     : {result.notified}
Failed       : {result.failed}

===============================================
"""
        )

        return result