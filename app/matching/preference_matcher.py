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
from app.utils.synonyms import expand
from app.utils.synonyms import fuzzy_match
from app.utils.synonyms import normalize_phrase

SKILL_WEIGHT = 20
LOCATION_WEIGHT = 30
GENERIC_ROLE_WORDS = {"developer", "engineer", "manager", "specialist", "analyst"}


class PreferenceMatcher:
    """
    Matching is phrase-based, not raw substring: text is tokenised on
    non-alphanumeric boundaries and every term is checked with word
    boundaries so "java" never matches inside "javascript", and every
    term is expanded through app.utils.synonyms so equivalent spellings
    ("bangalore"/"bengaluru", ".net"/"dotnet", "bcom"/"bachelor of
    commerce", ...) are treated as the same thing. A fuzzy fallback
    catches spelling variants that aren't in the synonym list at all
    yet (typos like "Bengalooru").
    """

    @staticmethod
    def _norm_word(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    def _contains_any(haystack: str, phrases: set[str]) -> bool:
        return any(phrase in haystack for phrase in phrases if phrase)

    @staticmethod
    def _term_matches(haystack: str, term: str) -> bool:
        """
        True if `term` (or a known synonym of it) appears in
        `haystack`. Falls back to a conservative fuzzy match for
        spelling variants that aren't in any synonym group yet.
        """
        if PreferenceMatcher._contains_any(haystack, expand(term)):
            return True
        return fuzzy_match(haystack, term)

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

        title = normalize_phrase(job.title)

        # Try the role as a whole phrase first (and any synonyms of
        # that whole phrase, e.g. "sde" for "software development
        # engineer").
        if PreferenceMatcher._term_matches(title, role):
            return True

        # Fall back to individual significant words, synonym- and
        # fuzzy-matched too, so "java developer" still matches "Java
        # Backend Developer" or "Java Backend Engineer" even though
        # the full phrases differ. Generic words like
        # "developer"/"engineer" are skipped since they'd match almost
        # any title.
        role_terms = [
            term
            for term in role.split()
            if PreferenceMatcher._norm_word(term) not in GENERIC_ROLE_WORDS
            and len(PreferenceMatcher._norm_word(term)) >= 3
        ]
        return bool(role_terms) and any(
            PreferenceMatcher._term_matches(title, term) for term in role_terms
        )

    @staticmethod
    def _skills_ok(job: Job, preference: UserPreference) -> bool:
        """A job must mention at least one requested skill, if any."""
        requested_skills = [skill.strip() for skill in preference.skills if skill.strip()]
        if not requested_skills:
            return True

        text = normalize_phrase(f"{job.title} {job.description}")
        return any(
            PreferenceMatcher._term_matches(text, skill) for skill in requested_skills
        )

    @staticmethod
    def _location_ok(job: Job, preference: UserPreference) -> bool:
        """Require one of the user's requested locations, if any."""
        requested_locations = [
            location.strip() for location in preference.locations if location.strip()
        ]
        if not requested_locations:
            return True

        job_location = normalize_phrase(job.location)
        return any(
            PreferenceMatcher._term_matches(job_location, location)
            for location in requested_locations
        )

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

        text = normalize_phrase(f"{job.title} {job.description}")

        if preference.skills and cls._skills_ok(job, preference):
            score += SKILL_WEIGHT * sum(
                cls._term_matches(text, skill.strip())
                for skill in preference.skills
                if skill.strip()
            )

        if preference.locations and cls._location_ok(job, preference):
            score += LOCATION_WEIGHT

        return score
