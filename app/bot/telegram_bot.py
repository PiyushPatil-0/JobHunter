"""
Telegram bot bootstrap.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from telegram.ext import Application
from telegram.ext import CommandHandler

from app.bot.commands import HELP
from app.bot.commands import DELETE_PREFERENCES
from app.bot.commands import END_SESSION
from app.bot.commands import PAUSE
from app.bot.commands import RESUME
from app.bot.commands import SCAN
from app.bot.commands import STATUS
from app.bot.handlers import BotHandlers
from app.bot.onboarding import build_onboarding_handler
from app.services.scan_service import ScanService
from app.utils.logger import logger

load_dotenv()


class TelegramBot:

    def __init__(
        self,
        scan_service: ScanService,
    ) -> None:

        token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not found."
            )

        self.application = (
            Application.builder()
            .token(token)
            .build()
        )

        handlers = BotHandlers(scan_service)

        # Onboarding conversation owns /start and /preferences.
        self.application.add_handler(
            build_onboarding_handler()
        )

        self.application.add_handler(
            CommandHandler(
                HELP,
                handlers.help,
            )
        )

        self.application.add_handler(
            CommandHandler(
                STATUS,
                handlers.status,
            )
        )

        self.application.add_handler(
            CommandHandler(
                SCAN,
                handlers.scan,
            )
        )

        self.application.add_handler(
            CommandHandler(
                PAUSE,
                handlers.pause,
            )
        )

        self.application.add_handler(
            CommandHandler(
                RESUME,
                handlers.resume,
            )
        )

        self.application.add_handler(
            CommandHandler(END_SESSION, handlers.end_session)
        )

        self.application.add_handler(
            CommandHandler(DELETE_PREFERENCES, handlers.delete_preferences)
        )

    def start(self) -> None:

        logger.success(
            "Telegram Bot Started."
        )

        self.application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
