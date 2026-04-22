# PubPlus Backend Local Setup

## Quick start

1. Copy `.env.example` to `.env`.
2. Fill all placeholder values in `.env`.
3. Start the backend:
   - Docker: `docker compose up --build`
   - Local Python: `pip install -r requirements.txt && python manage.py runserver`

The backend reads configuration from environment variables (with `.env` support for local development). If required values are missing, startup fails with an explicit error.
