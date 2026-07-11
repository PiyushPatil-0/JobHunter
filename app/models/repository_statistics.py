from dataclasses import dataclass


@dataclass(slots=True)
class RepositoryStatistics:
    total_jobs: int
    notified_jobs: int
    pending_jobs: int