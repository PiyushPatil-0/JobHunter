"""
Telegram onboarding conversation flow.

Users never edit YAML files to configure preferences - this flow
collects them and stores them in SQLite via PreferenceRepository.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import filters

from app.bot.commands import CANCEL
from app.bot.commands import PREFERENCES
from app.bot.commands import START
from app.config.settings import settings
from app.database.preference_repository import PreferenceRepository
from app.database.user_repository import UserRepository
from app.models.preference import UserPreference
from app.utils.logger import logger

(
    ROLE,
    SKILLS,
    LOCATIONS,
    EXPERIENCE,
    EMPLOYMENT_TYPE,
    SOURCES,
    CONFIRM,
) = range(7)

EXPERIENCE_OPTIONS = [
    "Fresher",
    "0-1 years",
    "1-3 years",
    "3-5 years",
    "5+ years",
]

EMPLOYMENT_TYPE_OPTIONS = [
    "Full Time",
    "Internship",
    "Contract",
    "Part Time",
]

SOURCE_OPTIONS = [
    "greenhouse",
    "lever",
    "workday",
    "smartrecruiters",
    "ashby",
    "linkedin",
    "naukri",
]

DONE = "__done__"


def _available_source_options() -> list[str]:
    """Only show job sources that this deployment actually runs."""
    return [
        source
        for source in SOURCE_OPTIONS
        if getattr(settings.sources, source).enabled
    ]



def _toggle_keyboard(
    options: list[str],
    selected: set[str],
    prefix: str,
) -> InlineKeyboardMarkup:
    """
    Build an inline keyboard where each option can be toggled on/off,
    with a trailing Done button to advance the flow.
    """

    rows = [
        [
            InlineKeyboardButton(
                f"{'✅' if option in selected else '▫️'} {option}",
                callback_data=f"{prefix}:{option}",
            )
        ]
        for option in options
    ]

    rows.append(
        [InlineKeyboardButton("➡️ Done", callback_data=f"{prefix}:{DONE}")]
    )

    return InlineKeyboardMarkup(rows)


class OnboardingFlow:

    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        chat = update.effective_chat
        user = update.effective_user

        UserRepository.get_or_create(
            chat_id=str(chat.id),
            username=user.username if user else None,
        )

        context.user_data.clear()

        await update.message.reply_text(
            "👋 Welcome to JobHunter AI!\n\n"
            "Let's set up your job preferences.\n\n"
            "What role are you looking for? "
            "(e.g. Backend Developer)",
            reply_markup=ReplyKeyboardRemove(),
        )

        return ROLE

    async def role(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        context.user_data["preferred_role"] = update.message.text.strip()

        await update.message.reply_text(
            "Great. What skills should I match on?\n"
            "Send them comma-separated "
            "(e.g. Java, Spring Boot, Kafka)."
        )

        return SKILLS

    async def skills(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        skills = [
            skill.strip()
            for skill in update.message.text.split(",")
            if skill.strip()
        ]

        context.user_data["skills"] = skills

        await update.message.reply_text(
            "Which locations are you interested in?\n"
            "Send them comma-separated "
            "(e.g. Mumbai, Remote)."
        )

        return LOCATIONS

    async def locations(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        locations = [
            location.strip()
            for location in update.message.text.split(",")
            if location.strip()
        ]

        context.user_data["locations"] = locations

        await update.message.reply_text(
            "What's your experience level?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            option,
                            callback_data=f"exp:{option}",
                        )
                    ]
                    for option in EXPERIENCE_OPTIONS
                ]
            ),
        )

        return EXPERIENCE

    async def experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        query = update.callback_query
        await query.answer()

        _, value = query.data.split(":", 1)

        context.user_data["experience_level"] = value
        context.user_data["employment_types"] = set()

        await query.edit_message_text(
            f"Experience level: {value} ✅\n\n"
            "Which employment types are you open to?\n"
            "Tap to select, then tap Done.",
        )

        await query.message.reply_text(
            "Employment types:",
            reply_markup=_toggle_keyboard(
                EMPLOYMENT_TYPE_OPTIONS,
                context.user_data["employment_types"],
                "emp",
            ),
        )

        return EMPLOYMENT_TYPE

    async def employment_type(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        query = update.callback_query
        await query.answer()

        _, value = query.data.split(":", 1)

        selected: set = context.user_data.setdefault(
            "employment_types", set()
        )

        if value == DONE:

            if not selected:
                await query.answer(
                    "Pick at least one option first.",
                    show_alert=True,
                )
                return EMPLOYMENT_TYPE

            context.user_data["enabled_sources"] = set()

            await query.edit_message_text(
                f"Employment types: {', '.join(sorted(selected))} ✅\n\n"
                "Which job sources should I search?\n"
                "Tap to select, then tap Done.",
            )

            await query.message.reply_text(
                "Sources:",
                reply_markup=_toggle_keyboard(
                    _available_source_options(),
                    context.user_data["enabled_sources"],
                    "src",
                ),
            )

            return SOURCES

        if value in selected:
            selected.remove(value)
        else:
            selected.add(value)

        await query.edit_message_reply_markup(
            reply_markup=_toggle_keyboard(
                EMPLOYMENT_TYPE_OPTIONS, selected, "emp"
            )
        )

        return EMPLOYMENT_TYPE

    async def sources(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        query = update.callback_query
        await query.answer()

        _, value = query.data.split(":", 1)

        selected: set = context.user_data.setdefault(
            "enabled_sources", set()
        )

        if value == DONE:

            if not selected:
                await query.answer(
                    "Pick at least one source first.",
                    show_alert=True,
                )
                return SOURCES

            return await self._show_summary(update, context)

        if value in selected:
            selected.remove(value)
        else:
            selected.add(value)

        await query.edit_message_reply_markup(
            reply_markup=_toggle_keyboard(
                _available_source_options(), selected, "src"
            )
        )

        return SOURCES

    async def _show_summary(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        query = update.callback_query
        data = context.user_data

        summary = (
            "📋 <b>Please confirm your preferences</b>\n\n"
            f"Role: {data.get('preferred_role')}\n"
            f"Skills: {', '.join(data.get('skills', []))}\n"
            f"Locations: {', '.join(data.get('locations', []))}\n"
            f"Experience: {data.get('experience_level')}\n"
            f"Employment types: "
            f"{', '.join(sorted(data.get('employment_types', [])))}\n"
            f"Sources: "
            f"{', '.join(sorted(data.get('enabled_sources', [])))}\n"
        )

        await query.edit_message_text(summary, parse_mode="HTML")

        await query.message.reply_text(
            "Save these preferences?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Save",
                            callback_data="confirm:save",
                        ),
                        InlineKeyboardButton(
                            "🔁 Restart",
                            callback_data="confirm:restart",
                        ),
                    ]
                ]
            ),
        )

        return CONFIRM

    async def confirm(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        query = update.callback_query
        await query.answer()

        _, action = query.data.split(":", 1)

        if action == "restart":
            context.user_data.clear()
            await query.edit_message_text(
                "Let's start over. What role are you looking for?"
            )
            return ROLE

        chat = update.effective_chat
        tg_user = update.effective_user

        user = UserRepository.get_or_create(
            chat_id=str(chat.id),
            username=tg_user.username if tg_user else None,
        )

        data = context.user_data

        preference = UserPreference(
            user_id=user.id,
            preferred_role=data.get("preferred_role", ""),
            skills=data.get("skills", []),
            locations=data.get("locations", []),
            experience_level=data.get("experience_level", ""),
            employment_types=sorted(data.get("employment_types", [])),
            enabled_sources=sorted(data.get("enabled_sources", [])),
        )

        PreferenceRepository.upsert(preference)

        UserRepository.mark_onboarding_completed(user.id)

        context.user_data.clear()

        await query.edit_message_text(
            "✅ Preferences saved! You're all set.\n\n"
            "I'll notify you here whenever a matching job shows up.\n"
            "Use /preferences to update these anytime, "
            "or /help for other commands."
        )

        logger.success(
            "Onboarding completed."
        )

        return ConversationHandler.END

    async def cancel(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> int:

        context.user_data.clear()

        await update.message.reply_text(
            "Onboarding cancelled. Send /start to try again."
        )

        return ConversationHandler.END


def build_onboarding_handler() -> ConversationHandler:

    flow = OnboardingFlow()

    return ConversationHandler(
        entry_points=[
            CommandHandler(START, flow.start),
            CommandHandler(PREFERENCES, flow.start),
        ],
        states={
            ROLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, flow.role
                )
            ],
            SKILLS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, flow.skills
                )
            ],
            LOCATIONS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, flow.locations
                )
            ],
            EXPERIENCE: [
                CallbackQueryHandler(flow.experience, pattern=r"^exp:")
            ],
            EMPLOYMENT_TYPE: [
                CallbackQueryHandler(flow.employment_type, pattern=r"^emp:")
            ],
            SOURCES: [
                CallbackQueryHandler(flow.sources, pattern=r"^src:")
            ],
            CONFIRM: [
                CallbackQueryHandler(flow.confirm, pattern=r"^confirm:")
            ],
        },
        fallbacks=[CommandHandler(CANCEL, flow.cancel)],
        name="onboarding",
        persistent=False,
    )
