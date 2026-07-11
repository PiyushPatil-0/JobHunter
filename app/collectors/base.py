"""
Base collector interface.

Every job source must inherit from this class.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from app.models.job import Job


class BaseCollector(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Collector name."""

    @abstractmethod
    def collect(self) -> list[Job]:
        """
        Collect jobs.

        Returns
        -------
        list[Job]
        """