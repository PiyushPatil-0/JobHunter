"""
Builds the live search scope (keywords + locations) for consumer
job board collectors, from the union of every active user's
preferences - filtered to users who actually enabled that specific
source during onboarding - plus an optional static baseline from
config.

This is what makes LinkedIn/Naukri search for what users actually
asked for, instead of a frozen YAML list. Config keywords/locations
become a floor that's always included (so a fresh install with zero
onboarded users still searches for something), not the ceiling.
"""

from __future__ import annotations

from app.database.preference_repository import PreferenceRepository


def build_search_scope(
    source_key: str,
    baseline_keywords: list[str] | None = None,
    baseline_locations: list[str] | None = None,
) -> tuple[list[str], list[str]]:

    keywords: set[str] = {
        keyword.strip()
        for keyword in (baseline_keywords or [])
        if keyword.strip()
    }

    locations: set[str] = {
        location.strip()
        for location in (baseline_locations or [])
        if location.strip()
    }

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
