"""
Experience classifier.
"""

from __future__ import annotations

import re

from app.utils.synonyms import normalize_phrase


class ExperienceClassifier:

    SENIOR_WORDS = {
        "senior",
        "staff",
        "principal",
        "architect",
        "lead",
        "manager",
    }

    ENTRY_WORDS = {
        "intern",
        "graduate",
        "new grad",
        "entry",
        "junior",
        "fresher",
    }

    @classmethod
    def classify(cls, title: str, description: str) -> int:

        # Word-boundary matching, not raw substring: "leadership" must
        # not trigger the "lead" -> senior rule, and "Associate
        # Director" must not trigger an "associate" -> entry rule
        # (which is why "associate" was dropped from ENTRY_WORDS below
        # - as a bare word it collides with senior-ish titles like
        # "Associate Director"/"Associate Vice President" far more
        # often than it means "entry level").
        text = normalize_phrase(f"{title} {description}")

        for word in cls.ENTRY_WORDS:
            if normalize_phrase(word) in text:
                return 0

        for word in cls.SENIOR_WORDS:
            if normalize_phrase(word) in text:
                return 5

        matches = re.findall(
            r"(\d+)\s*\+?\s*(?:year|years|yr|yrs)",
            text,
        )

        if matches:
            return int(matches[0])

        return 1
