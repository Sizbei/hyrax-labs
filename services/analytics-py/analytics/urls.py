"""Root URL configuration for the analytics service."""
from django.http import JsonResponse
from django.urls import include, path


def healthcheck(_request) -> JsonResponse:
    """Liveness probe used by Docker / orchestrators."""
    return JsonResponse({"status": "ok", "service": "hyrax-analytics"})


urlpatterns = [
    path("healthz", healthcheck, name="healthz"),
    path("api/", include("events.urls")),
]
