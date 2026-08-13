# JobHunter AI

Telegram job alerts matched to each user's role, skills, location,
experience, employment type, and selected job sources.

## Run locally

1. In `.env` set `TELEGRAM_BOT_TOKEN`.
2. Review `config/settings.yaml` for retention and ATS sources.
3. Start the bot and scheduler together:

   ```powershell
   .\.venv\Scripts\python.exe run_bot.py
   ```

Use `/start` in Telegram to create preferences. `/end_session` pauses
notifications; `/delete_preferences` removes saved preferences and delivery
history.
