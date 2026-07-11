"""
Production Job Filter.
"""

from __future__ import annotations

from loguru import logger

from app.config.settings import settings
from app.models.job import Job
from app.utils.experience_classifier import ExperienceClassifier
from app.utils.scorer import JobScorer


class JobFilter:

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

        self.minimum_score = settings.filters.minimum_match_score

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

        # --------------------------------------------------
        # Experience
        # --------------------------------------------------

        experience = ExperienceClassifier.classify(
            job.title,
            job.description,
        )

        if experience > 2:
            logger.info(
                f"Rejected (experience={experience}): {job.title}"
            )
            return False

        # --------------------------------------------------
        # Score
        # --------------------------------------------------

        score = JobScorer.score(job)

        job.match_score = score

        if score < self.minimum_score:
            logger.info(
                f"Rejected (score={score}): {job.title}"
            )
            return False

        # --------------------------------------------------
        # Location
        # --------------------------------------------------

        location = job.location.lower()

        # Explicitly reject foreign-only locations.
        if any(
            word in location
            for word in self.BLOCKED_LOCATIONS
        ):
            logger.info(
                f"Rejected (location={job.location}): {job.title}"
            )
            return False

        # Accept if preferred.
        if any(
            word in location
            for word in self.ALLOWED_LOCATIONS
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