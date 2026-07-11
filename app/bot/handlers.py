"""
Telegram command handlers.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.services.scan_service import ScanService


class BotHandlers:

    def __init__(self, scan_service: ScanService):

        self.scan_service = scan_service

    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "👋 Welcome to JobHunter AI!\n\n"
            "Use /help to see available commands."
        )

    async def help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "/scan - Scan jobs now\n"
            "/status - Current status\n"
            "/pause - Pause notifications\n"
            "/resume - Resume notifications"
        )

    async def status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "✅ JobHunter AI is running."
        )

    async def scan(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "🔍 Starting scan..."
        )

        result = self.scan_service.run_scan()

        if result is None:

            await update.message.reply_text(
                "⚠️ Scan already running."
            )

            return

        await update.message.reply_text(
            f"""
✅ Scan Completed

Scanned: {result.scanned}
Inserted: {result.inserted}
Filtered: {result.filtered}
Duplicates: {result.duplicates}
Notified: {result.notified}
"""
        )

    async def pause(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "⏸ Notifications paused.\n"
            "(Implementation in next step)"
        )

    async def resume(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "▶ Notifications resumed.\n"
            "(Implementation in next step)"
        )