FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# Production (Railway): bind to $PORT from the platform. Local docker compose overrides
# this command with `python manage.py runserver` — see docker-compose.yml.
CMD ["sh", "-c", "exec gunicorn --chdir /app config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
