"""
Telegram command handlers.
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.database.preference_repository import PreferenceRepository
from app.database.user_repository import UserRepository
from app.services.scan_service import ScanService


class BotHandlers:

    def __init__(self, scan_service: ScanService):

        self.scan_service = scan_service

    # /start is handled by the onboarding ConversationHandler
    # (app.bot.onboarding) instead of a plain handler here.

    async def help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        await update.message.reply_text(
            "/start - Create or replace job preferences\n"
            "/preferences - Update job preferences\n"
            "/cancel - Cancel preference setup\n"
            "/scan - Scan jobs now\n"
            "/status - Check service status\n"
            "/pause - Pause notifications\n"
            "/resume - Resume notifications\n"
            "/end_session - End notification session\n"
            "/delete_preferences - Permanently delete saved preferences"
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

        user = UserRepository.get_by_chat_id(str(update.effective_chat.id))
        if user is None:
            await update.message.reply_text("Use /start before pausing notifications.")
            return

        UserRepository.set_active(user.id, False)
        await update.message.reply_text("⏸ Notifications paused.")

    async def resume(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):

        user = UserRepository.get_by_chat_id(str(update.effective_chat.id))
        if user is None:
            await update.message.reply_text("Use /start before resuming notifications.")
            return

        UserRepository.set_active(user.id, True)
        await update.message.reply_text("▶ Notifications resumed.")

    async def end_session(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        """Alias for pausing a user's notification session."""
        await self.pause(update, context)

    async def delete_preferences(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ):
        user = UserRepository.get_by_chat_id(str(update.effective_chat.id))
        if user is None or user.id is None:
            await update.message.reply_text("No saved preferences were found.")
            return

        PreferenceRepository.delete_by_user_id(user.id)
        UserRepository.reset_onboarding(user.id)
        await update.message.reply_text(
            "🗑 Saved preferences and notification history deleted. "
            "Send /start whenever you want to set up a new search."
        )
