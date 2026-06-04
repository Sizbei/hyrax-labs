"""ASGI entrypoint for the analytics service."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "analytics.settings")

application = get_asgi_application()
