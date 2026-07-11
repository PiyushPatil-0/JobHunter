from dataclasses import dataclass


@dataclass(slots=True)
class EngineResult:
    scanned: int = 0
    duplicates: int = 0
    inserted: int = 0
    filtered: int = 0
    notified: int = 0
    failed: int = 0