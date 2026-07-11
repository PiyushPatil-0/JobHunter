"""
Build Telegram digest messages.
"""

from __future__ import annotations

from app.models.job import Job


class MessageBuilder:

    MAX_JOBS = 10

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
            jobs[: cls.MAX_JOBS],
            start=1,
        ):

            lines.append(
                f"""
<b>{index}. {job.title}</b>

🏢 {job.company}

📍 {job.location}

⭐ Match Score: {int(job.match_score)}

<a href="{job.url}">Apply Here</a>

────────────────────
"""
            )

        if len(jobs) > cls.MAX_JOBS:

            lines.append(
                f"\n...and {len(jobs)-cls.MAX_JOBS} more jobs."
            )

        return "\n".join(lines)