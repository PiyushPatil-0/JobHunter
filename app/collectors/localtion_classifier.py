"""
Fast location classifier.
"""

from __future__ import annotations


class LocationClassifier:

    ALLOWED = {

        "india",

        "bangalore",

        "bengaluru",

        "mumbai",

        "navi mumbai",

        "thane",

        "pune",

        "remote",

        "hybrid",
    }

    @classmethod
    def accept(cls, location: str) -> bool:

        location = location.lower()

        return any(
            word in location
            for word in cls.ALLOWED
        )