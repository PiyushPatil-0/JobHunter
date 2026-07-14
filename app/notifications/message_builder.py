"""
Build Telegram digest messages.
"""

from __future__ import annotations

from datetime import datetime
from html import escape

from app.models.job import Job


class MessageBuilder:

    MAX_JOBS = 10
    MAX_MESSAGE_LENGTH = 4096

    @classmethod
    def batches(cls, jobs: list[Job]) -> list[list[Job]]:
        """Split jobs into Telegram-safe digest batches."""
        batches: list[list[Job]] = []
        current: list[Job] = []

        for job in jobs:
            candidate = current + [job]
            if current and (
                len(candidate) > cls.MAX_JOBS
                or len(cls.build(candidate)) > cls.MAX_MESSAGE_LENGTH
            ):
                batches.append(current)
                current = [job]
            else:
                current = candidate

        if current:
            batches.append(current)

        return batches

    @staticmethod
    def _escaped(value: str, limit: int) -> str:
        """Bound untrusted fields before HTML escaping for Telegram."""
        suffix = "..." if len(value) > limit else ""
        return escape(value[:limit]) + suffix

    @staticmethod
    def _relative_age(timestamp: datetime) -> str:
        seconds = max(0, int((datetime.utcnow() - timestamp).total_seconds()))
        if seconds < 60:
            return "just now"
        if seconds < 3_600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86_400:
            hours = seconds // 3_600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = seconds // 86_400
        return f"{days} day{'s' if days != 1 else ''} ago"

    @classmethod
    def build(cls, jobs: list[Job]) -> str:

        if not jobs:
            return "No matching jobs found."

        lines: list[str] = []

        lines.append(
            f"🚀 <b>JobHunter AI</b>\n"
        )

        lines.append(
            f"Found <b>{len(jobs)}</b> matching jobs.\n"
        )

        for index, job in enumerate(
            jobs,
            start=1,
        ):
            timestamp = job.posted_at or job.collected_at
            age_label = "Posted" if job.posted_at else "Discovered"

            lines.append(
                f"""
<b>{index}. {cls._escaped(job.title, 160)}</b>

🏢 {cls._escaped(job.company, 80)}

📍 {cls._escaped(job.location, 80)}

🕒 {age_label}: {cls._relative_age(timestamp)}

⭐ Match Score: {int(job.match_score)}

<a href="{cls._escaped(job.url, 240)}">Apply Here</a>

────────────────────
"""
            )

        return "\n".join(lines)
