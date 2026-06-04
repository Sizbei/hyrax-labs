"""
Django settings for the Hyrax analytics service.

Configuration is environment-driven with sensible local defaults so the
service runs with zero external dependencies: SQLite for the Django ORM and
a graceful Mongo fallback (see ``events/mongo.py``).
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --- Core ----------------------------------------------------------------

# Synthetic portfolio project: the default key is fine for local/dev/CI use.
# Override with DJANGO_SECRET_KEY in any real deployment.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-key-not-for-production-synthetic-data-only",
)

DEBUG = _env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "analytics.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "analytics.wsgi.application"

# --- Database (SQLite by default; zero external services) ----------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- MongoDB (high-volume raw event log; degrades gracefully) ------------

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "hyrax_analytics")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "raw_events")
# Connection timeout (ms) before we fall back to the in-memory store.
MONGO_TIMEOUT_MS = int(os.environ.get("MONGO_TIMEOUT_MS", "500"))
# Force the mongomock backend (used by the test suite and offline demos).
MONGO_USE_MOCK = _env_bool("MONGO_USE_MOCK", False)

# --- DRF -----------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# --- i18n / static -------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "events": {"handlers": ["console"], "level": "INFO"},
    },
}
