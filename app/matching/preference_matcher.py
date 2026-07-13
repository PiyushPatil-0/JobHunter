"""
Match a collected job against a single user's preferences.

This is the *only* relevance gate in the pipeline - the global
JobFilter deliberately no longer rejects on skills, experience, or
employment type, since those are inherently personal, not shared
across every user. See app.filters.job_filter for why.
"""

from __future__ import annotations

from app.models.job import Job
from app.models.preference import UserPreference
from app.utils.experience_classifier import ExperienceClassifier
from app.utils.experience_ranges import EXPERIENCE_RANGES

SKILL_WEIGHT = 20
LOCATION_WEIGHT = 30


class PreferenceMatcher:

    @classmethod
    def matches(cls, job: Job, preference: UserPreference) -> bool:

        if not cls._source_ok(job, preference):
            return False

        if not cls._employment_type_ok(job, preference):
            return False

        if not cls._experience_ok(job, preference):
            return False

        # A user who left both skills and locations empty hasn't
        # given us anything to score against - don't reject every
        # job just because of that.
        if not preference.skills and not preference.locations:
            return True

        return cls.score(job, preference) >= preference.minimum_match_score

    @staticmethod
    def _source_ok(job: Job, preference: UserPreference) -> bool:

        if not preference.enabled_sources:
            return True

        enabled = {
            source.strip().lower()
            for source in preference.enabled_sources
        }

        return job.source.value.lower() in enabled

    @staticmethod
    def _employment_type_ok(job: Job, preference: UserPreference) -> bool:

        if not preference.employment_types:
            return True

        return job.employment_type.value in preference.employment_types

    @staticmethod
    def _experience_ok(job: Job, preference: UserPreference) -> bool:

        bucket = EXPERIENCE_RANGES.get(preference.experience_level)

        if bucket is None:
            return True

        job_years = ExperienceClassifier.classify(
            job.title,
            job.description,
        )

        minimum, maximum = bucket

        return minimum <= job_years <= maximum

    @staticmethod
    def score(job: Job, preference: UserPreference) -> int:
        """
        This user's relevance score for this job - also used as the
        ⭐ Match Score shown in their Telegram digest, so it reflects
        what actually matters to them, not a shared global score.
        """

        score = 0

        text = f"{job.title} {job.description}".lower()

        for skill in preference.skills:

            if skill.strip().lower() in text:
                score += SKILL_WEIGHT

        location = job.location.lower()

        if preference.locations and any(
            loc.strip().lower() in location
            for loc in preference.locations
        ):
            score += LOCATION_WEIGHT

        return score
