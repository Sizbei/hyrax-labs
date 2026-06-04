# analytics-py — Django + DRF + MongoDB engagement analytics service
# Runs with zero external services by default: SQLite for the ORM and an
# in-memory Mongo fallback (MONGO_USE_MOCK=1) when no real Mongo is configured.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=analytics.settings \
    MONGO_USE_MOCK=1

WORKDIR /app

COPY pyproject.toml ./
COPY manage.py ./
COPY analytics ./analytics
COPY events ./events
COPY README.md ./

RUN pip install --no-cache-dir -e .

# Apply migrations, seed deterministic synthetic data, then serve.
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_events --count 500 --clear && python manage.py runserver 0.0.0.0:8000"]
