"""
Fast title classifier.

Runs before Job objects are created.
"""

from __future__ import annotations


class TitleClassifier:

    ALLOWED = {

        "software engineer",
        "backend",
        "backend engineer",
        "backend developer",
        "java",
        "java developer",
        "java engineer",
        "spring",
        "platform engineer",
        "distributed systems",
        "api",
        "microservices",
        "cloud engineer",
        "site reliability",
        "devops",
        "systems engineer",
        "full stack",
        "fullstack",
    }

    BLOCKED = {

        "sales",
        "marketing",
        "finance",
        "account executive",
        "customer success",
        "recruiter",
        "human resources",
        "hr",
        "legal",
        "support",
        "talent",
        "operations",
        "business development",
        "product marketing",
    }

    @classmethod
    def accept(cls, title: str) -> bool:

        title = title.lower()

        for word in cls.BLOCKED:
            if word in title:
                return False

        return any(word in title for word in cls.ALLOWED)