# JobHunter AI

Telegram job alerts matched to each user's role, skills, location,
experience, employment type, and selected job sources.

## Run locally

1. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`.
2. Review `config/settings.yaml` for retention and ATS sources.
3. Start the bot and scheduler together:

   ```powershell
   .\.venv\Scripts\python.exe run_bot.py
   ```

Use `/start` in Telegram to create preferences. `/end_session` pauses
notifications; `/delete_preferences` removes saved preferences and delivery
history.

## Docker deployment

Build and run with persistent volumes for the SQLite database and logs:

```powershell
docker build -t jobhunter-ai .
docker run --env-file .env -v ${PWD}/data:/app/data -v ${PWD}/logs:/app/logs jobhunter-ai
```

Do not commit `.env`; use a secret manager or deployment environment variables
in production. The application applies safe additive SQLite migrations at
startup and automatically removes jobs older than `job_retention_days`.
