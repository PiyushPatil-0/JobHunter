"""
Experience classifier.
"""

from __future__ import annotations

import re


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
        "associate",
        "junior",
        "fresher",
    }

    @classmethod
    def classify(cls, title: str, description: str) -> int:

        text = f"{title} {description}".lower()

        for word in cls.ENTRY_WORDS:
            if word in text:
                return 0

        for word in cls.SENIOR_WORDS:
            if word in text:
                return 5

        matches = re.findall(
            r"(\d+)\s*\+?\s*(?:year|years|yr|yrs)",
            text,
        )

        if matches:
            return int(matches[0])

        return 1