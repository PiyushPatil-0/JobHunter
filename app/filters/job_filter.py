"""
Production Job Filter.

This is deliberately thin. It only enforces things that are true
for *every* user regardless of what they're looking for: a company
blacklist.

Anything about whether a specific job is relevant to a specific
person - skills, experience level, employment type - belongs to
that person's own preferences and is decided by
app.matching.PreferenceMatcher, not here. An earlier version of
this filter also hard-rejected on experience and on a software-
engineering-specific keyword score; that meant a job outside that
one persona (e.g. an MBA/marketing role) was discarded before any
user's own preferences ever got a chance to match it, no matter who
had onboarded. Global relevance gates don't work once more than one
kind of user exists.
"""

from __future__ import annotations

from loguru import logger

from app.config.settings import settings
from app.models.job import Job


class JobFilter:

    def __init__(self) -> None:

        self.excluded_companies = {
            company.lower()
            for company in settings.companies.exclude
        }

    def accept(self, job: Job) -> bool:

        # --------------------------------------------------
        # Company blacklist
        # --------------------------------------------------

        if job.company.lower() in self.excluded_companies:
            logger.info(f"Rejected (company): {job.title}")
            return False

        # Location and every other relevance criterion are evaluated
        # against each recipient's saved preferences in
        # PreferenceMatcher. A shared allow/block list would discard
        # valid jobs before the requesting user can be considered.
        return True
