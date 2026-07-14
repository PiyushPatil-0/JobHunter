"""
Telegram notification service.
"""

from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

from app.models.job import Job
from app.notifications.message_builder import MessageBuilder
from app.utils.logger import logger

load_dotenv()


class TelegramNotifier:

    def __init__(self) -> None:

        self.token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found.")

        # Optional. Reserved for future admin/status alerts -
        # per-user job notifications always target the user's own
        # telegram_chat_id instead.
        self.admin_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        self.base_url = (
            f"https://api.telegram.org/bot{self.token}"
        )

    def send_message(self, chat_id: str, message: str) -> bool:

        try:

            response = httpx.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )

            response.raise_for_status()

            result = response.json()

            if result.get("ok"):

                logger.success(
                    "Telegram notification sent."
                )

                return True

            logger.error(result)

            return False

        except Exception:

            logger.exception(
                "Telegram notification failed."
            )

            return False

    def send_jobs(
        self,
        chat_id: str,
        jobs: list[Job],
    ) -> bool:
        """
        Send a single digest of jobs to one specific chat.
        """

        if not jobs:

            logger.info(
                "No jobs to notify."
            )

            return True

        message = MessageBuilder.build(jobs)

        return self.send_message(chat_id, message)
