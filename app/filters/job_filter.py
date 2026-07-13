"""
Production Job Filter.

This is deliberately thin. It only enforces things that are true
for *every* user regardless of what they're looking for: a company
blacklist, and the geographic scope this service operates in.

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

    # Broad, hardcoded net of major Indian tech hubs - always
    # accepted regardless of config, since this app fundamentally
    # targets Indian/remote roles. job_preferences.locations
    # (config) is unioned on top of this at construction time.
    # This is a geographic *service scope* decision (which regions
    # we operate in at all), not a personal preference - personal
    # location preference is handled separately per user by
    # PreferenceMatcher.
    ALLOWED_LOCATIONS = {
        "india",
        "remote",
        "hybrid",
        "distributed",
        "bangalore",
        "bengaluru",
        "mumbai",
        "navi mumbai",
        "thane",
        "pune",
        "hyderabad",
        "gurugram",
        "noida",
        "delhi",
        "chennai",
    }

    BLOCKED_LOCATIONS = {
        "tokyo",
        "paris",
        "dublin",
        "mexico",
        "sydney",
        "toronto",
        "boston",
        "new york",
        "san francisco",
        "chicago",
        "seoul",
        "tel aviv",
        "singapore",
    }

    def __init__(self) -> None:

        self.excluded_companies = {
            company.lower()
            for company in settings.companies.exclude
        }

        self.allowed_locations = self.ALLOWED_LOCATIONS | {
            location.lower()
            for location in settings.job_preferences.locations
        }

    def accept(self, job: Job) -> bool:

        # --------------------------------------------------
        # Company blacklist
        # --------------------------------------------------

        if job.company.lower() in self.excluded_companies:
            logger.info(f"Rejected (company): {job.title}")
            return False

        # --------------------------------------------------
        # Location - operational service scope, not personal
        # preference.
        # --------------------------------------------------

        location = job.location.lower()

        if any(
            word in location
            for word in self.BLOCKED_LOCATIONS
        ):
            logger.info(
                f"Rejected (location={job.location}): {job.title}"
            )
            return False

        if any(
            word in location
            for word in self.allowed_locations
        ):
            return True

        # Unknown locations such as:
        # Hybrid
        # Distributed
        # N/A
        # In Office
        # are accepted in V1.
        if location in {
            "",
            "n/a",
            "hybrid",
            "distributed",
            "in-office",
            "in office",
        }:
            return True

        logger.info(
            f"Rejected (location={job.location}): {job.title}"
        )

        return False
