"""
Production Job Scorer.
"""

from __future__ import annotations
from app.utils.logger import logger

from app.models.job import Job


class JobScorer:
    WEIGHTS = {
        "java": 60,
        "spring boot": 50,
        "spring": 30,
        "backend": 50,
        "api": 30,
        "software engineer": 30,
        "engineer": 15,
        "developer": 15,
        "microservices": 30,
        "distributed": 20,
        "kafka": 20,
        "redis": 15,
        "docker": 15,
        "rest": 15,
        "sql": 10,
    }

    LOCATION_WEIGHT = 30

    REMOTE_WEIGHT = 25

    @classmethod
    def score(cls, job: Job) -> int:

        score = 0

        text = (
            f"{job.title} "
            f"{getattr(job, 'description', '')}"
        ).lower()

        for keyword, weight in cls.WEIGHTS.items():

            if keyword in text:

                score += weight

        location = job.location.lower()

        if "remote" in location:

            score += cls.REMOTE_WEIGHT

        preferred = (
            "mumbai",
            "navi mumbai",
            "thane",
            "pune",
            "bangalore",
            "india",
        )

        for city in preferred:

            if city in location:

                score += cls.LOCATION_WEIGHT

                break

        logger.info(
            f"{job.title} | Score = {score}"
        )

        return score