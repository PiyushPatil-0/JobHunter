"""
Utility functions for generating deterministic job hashes.
"""

from __future__ import annotations

import hashlib

from app.models.job import Job


def generate_job_hash(job: Job) -> str:
    """
    Generate a deterministic SHA-256 hash for a job.
    """

    raw = "|".join(
        (
            job.source.value.lower().strip(),
            job.company.lower().strip(),
            job.title.lower().strip(),
            job.location.lower().strip(),
            job.url.lower().strip(),
        )
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def assign_job_hash(job: Job) -> Job:
    """
    Generate and assign the hash to the Job instance.
    """

    job.hash = generate_job_hash(job)
    return job