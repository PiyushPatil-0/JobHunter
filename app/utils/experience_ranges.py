"""
Shared experience-bucket definitions.

Used by both the global JobFilter (config-driven cutoff) and the
per-user PreferenceMatcher (per-user cutoff), so a bucket like
"Fresher" or "1-3 years" means the same thing everywhere.
"""

from __future__ import annotations

EXPERIENCE_RANGES: dict[str, tuple[int, int]] = {
    "Fresher": (0, 0),
    "0-1 years": (0, 1),
    "1-3 years": (1, 3),
    "3-5 years": (3, 5),
    "5+ years": (5, 99),
}
