"""
Core JobHunter Engine.
"""

from __future__ import annotations

from app.collectors.manager import CollectorManager
from app.config.settings import settings
from app.database.notification_repository import UserNotificationRepository
from app.database.preference_repository import PreferenceRepository
from app.database.repository import JobRepository
from app.database.user_repository import UserRepository
from app.engine.engine_result import EngineResult
from app.filters.job_filter import JobFilter
from app.matching.preference_matcher import PreferenceMatcher
from app.models.job import Job
from app.notifications.telegram import TelegramNotifier
from app.notifications.message_builder import MessageBuilder
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

    def run(self, group: str | None = None) -> EngineResult:

        logger.info("Starting JobHunter Engine...")

        result = EngineResult()

        removed = self.repository.cleanup(settings.database.job_retention_days)
        if removed:
            logger.info(f"Removed {removed} expired jobs.")

        jobs = self.collector_manager.collect_jobs(group=group)

        result.scanned = len(jobs)

        logger.info(
            f"Collected {result.scanned} jobs."
        )

        # Jobs that passed the (deliberately thin) global filter
        # this run, whether freshly inserted or already stored from
        # a previous scan. A job already in the DB can still be
        # brand new to a user who onboarded after it was first
        # collected, so both stay eligible for per-user matching.
        matchable_jobs: list[Job] = []

        for job in jobs:

            try:

                # ----------------------------------
                # Global operational filter (company
                # blacklist + geographic scope only)
                # ----------------------------------

                if not self.filter.accept(job):

                    result.filtered += 1

                    continue

                # ----------------------------------
                # Hash + dedup against the jobs table
                # ----------------------------------

                assign_job_hash(job)

                process = self.repository.process(job)

                if process.duplicate:
                    result.duplicates += 1
                else:
                    result.inserted += 1

                matchable_jobs.append(job)

            except Exception:

                logger.exception(
                    f"Failed processing {job.title}"
                )

                result.failed += 1

        # ------------------------------------------
        # Fan matched jobs out to each onboarded user
        # ------------------------------------------

        if matchable_jobs:

            result.notified, result.failed = self._notify_users(
                matchable_jobs,
                result.failed,
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

    def _notify_users(
        self,
        jobs: list[Job],
        failed_so_far: int,
    ) -> tuple[int, int]:
        """
        For every onboarded, active user: find jobs matching their
        own preferences that they haven't been sent yet, score each
        one for that user specifically, deliver a digest, and
        record what was sent so it never repeats.

        Returns (notified_count, failed_count).
        """

        notified = 0
        failed = failed_so_far

        preferences = PreferenceRepository.list_all_active()

        if not preferences:

            logger.info(
                "No onboarded users to notify."
            )

            return notified, failed

        for preference in preferences:

            user = UserRepository.get_by_id(preference.user_id)

            if user is None or not user.telegram_chat_id:
                continue

            unseen_matches = [
                job
                for job in jobs
                if PreferenceMatcher.matches(job, preference)
                and not UserNotificationRepository.already_notified(
                    user.id,
                    job.hash,
                )
            ]

            if not unseen_matches:
                continue

            # Score reflects THIS user's preferences, not a shared
            # global score - shown as the digest's Match Score.
            for job in unseen_matches:
                job.match_score = PreferenceMatcher.score(job, preference)

            # Telegram digests are capped at MAX_JOBS. Send and record
            # each batch independently so jobs beyond the first page are
            # never marked as delivered without actually being shown.
            for batch in MessageBuilder.batches(unseen_matches):
                sent = self.notifier.send_jobs(user.telegram_chat_id, batch)

                if sent:
                    for job in batch:
                        UserNotificationRepository.record(user.id, job.hash)
                    notified += len(batch)
                else:
                    failed += len(batch)

        return notified, failed
