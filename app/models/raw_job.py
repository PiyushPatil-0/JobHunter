"""
Represents a job exactly as received from a source.

No validation.
No normalization.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class RawJob:

    title: str

    company: str

    location: str

    experience: str

    source: str

    url: str

    description: str = ""

    employment_type: str = ""

    posted_at: str = ""