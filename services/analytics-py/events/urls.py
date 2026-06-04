"""URL routing for the events app, mounted under ``/api/`` by the project."""
from rest_framework.routers import DefaultRouter

from .views import AnalyticsSummaryViewSet, AssetEngagementViewSet

router = DefaultRouter()
router.register(r"events", AssetEngagementViewSet, basename="engagement")
router.register(r"analytics/summary", AnalyticsSummaryViewSet, basename="summary")

urlpatterns = router.urls
