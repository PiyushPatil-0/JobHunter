"""
Match a collected job against a single user's preferences.

This is the *only* relevance gate in the pipeline - the global
JobFilter deliberately no longer rejects on skills, experience, or
employment type, since those are inherently personal, not shared
across every user. See app.filters.job_filter for why.
"""

from __future__ import annotations

import re

from app.models.job import Job
from app.models.preference import UserPreference
from app.utils.experience_classifier import ExperienceClassifier
from app.utils.experience_ranges import EXPERIENCE_RANGES

SKILL_WEIGHT = 20
LOCATION_WEIGHT = 30
GENERIC_ROLE_WORDS = {"developer", "engineer", "manager", "specialist", "analyst"}
LOCATION_ALIASES = {
    "bangalore": {"bangalore", "bengaluru"},
    "bengaluru": {"bangalore", "bengaluru"},
    "gurgaon": {"gurgaon", "gurugram"},
    "gurugram": {"gurgaon", "gurugram"},
}


class PreferenceMatcher:

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @classmethod
    def matches(cls, job: Job, preference: UserPreference) -> bool:

        if not cls._source_ok(job, preference):
            return False

        if not cls._employment_type_ok(job, preference):
            return False

        if not cls._experience_ok(job, preference):
            return False

        if not cls._role_ok(job, preference):
            return False

        if not cls._skills_ok(job, preference):
            return False

        return cls._location_ok(job, preference)

    @staticmethod
    def _role_ok(job: Job, preference: UserPreference) -> bool:
        """Require the requested role when the user supplied one."""
        role = preference.preferred_role.strip()
        if not role:
            return True

        title = PreferenceMatcher._normalise(job.title)
        normalised_role = PreferenceMatcher._normalise(role)
        if normalised_role in title:
            return True

        role_terms = [
            PreferenceMatcher._normalise(term)
            for term in role.split()
            if PreferenceMatcher._normalise(term) not in GENERIC_ROLE_WORDS
            and len(PreferenceMatcher._normalise(term)) >= 3
        ]
        return bool(role_terms) and any(term in title for term in role_terms)

    @staticmethod
    def _skills_ok(job: Job, preference: UserPreference) -> bool:
        """A job must mention at least one requested skill, if any."""
        requested_skills = [
            PreferenceMatcher._normalise(skill.strip())
            for skill in preference.skills
            if skill.strip()
        ]
        if not requested_skills:
            return True

        text = PreferenceMatcher._normalise(f"{job.title} {job.description}")
        return any(skill in text for skill in requested_skills)

    @staticmethod
    def _location_ok(job: Job, preference: UserPreference) -> bool:
        """Require one of the user's requested locations, if any."""
        requested_locations = [
            location.strip().lower()
            for location in preference.locations
            if location.strip()
        ]
        if not requested_locations:
            return True

        job_location = job.location.lower()
        for location in requested_locations:
            aliases = LOCATION_ALIASES.get(location, {location})
            if any(alias in job_location for alias in aliases):
                return True
        return False

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

        allowed_types = {
            employment_type.strip().lower()
            for employment_type in preference.employment_types
            if employment_type.strip()
        }
        return job.employment_type.value.lower() in allowed_types

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

    @classmethod
    def score(cls, job: Job, preference: UserPreference) -> int:
        """
        This user's relevance score for this job - also used as the
        ⭐ Match Score shown in their Telegram digest, so it reflects
        what actually matters to them, not a shared global score.
        """

        score = 0

        text = cls._normalise(f"{job.title} {job.description}")

        if preference.skills and cls._skills_ok(job, preference):
            score += SKILL_WEIGHT * sum(
                cls._normalise(skill.strip()) in text
                for skill in preference.skills
                if skill.strip()
            )

        if preference.locations and cls._location_ok(job, preference):
            score += LOCATION_WEIGHT

        return score
