"""
Builds the live search scope (keywords + locations) for consumer
job board collectors, from the union of every active user's
preferences - filtered to users who actually enabled that specific
source during onboarding.

This is what makes LinkedIn/Naukri search for what users actually
asked for, instead of a frozen YAML list. With no matching user
preferences, the collector has no search request and does not run.
"""

from __future__ import annotations

from app.database.preference_repository import PreferenceRepository


def build_search_scope(
    source_key: str,
) -> tuple[list[str], list[str]]:

    keywords: set[str] = set()
    locations: set[str] = set()

    for preference in PreferenceRepository.list_all_active():

        if source_key not in preference.enabled_sources:
            continue

        if preference.preferred_role.strip():
            keywords.add(preference.preferred_role.strip())

        keywords.update(
            skill.strip()
            for skill in preference.skills
            if skill.strip()
        )

        locations.update(
            location.strip()
            for location in preference.locations
            if location.strip()
        )

    return sorted(keywords), sorted(locations)
