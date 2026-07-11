from dataclasses import dataclass


@dataclass(slots=True)
class ProcessResult:
    inserted: bool
    duplicate: bool
    job_id: int | None = None