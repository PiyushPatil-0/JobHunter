"""
Collector scheduling groups.

Every collector is registered under one of these groups so the
scheduler can run each tier on its own interval. ATS collectors are
polled via clean JSON APIs and post/update jobs frequently, so they
run often. Consumer job boards are heavier (often scraped, rate
limited) and change less predictably, so they run less often.

Adding a new collector never requires touching the Job Engine -
just register it under the group that matches its update cadence.
"""

from __future__ import annotations


class CollectorGroup:

    ATS = "ats"

    JOB_BOARDS = "job_boards"
