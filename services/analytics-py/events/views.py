"""DRF viewsets for engagement events and the aggregate summary endpoint."""
from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from . import mongo, services
from .models import AssetEngagement
from .serializers import AssetEngagementSerializer, MetricSummarySerializer


class AssetEngagementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List, retrieve and create engagement events.

    Creating a row through the API also mirrors the event into the MongoDB raw
    append log, keeping both stores consistent. Supports ``?metric=`` and
    ``?asset_id=`` filtering plus DRF page-number pagination.
    """

    serializer_class = AssetEngagementSerializer

    def get_queryset(self):
        qs = AssetEngagement.objects.all()
        metric = self.request.query_params.get("metric")
        asset_id = self.request.query_params.get("asset_id")
        if metric:
            qs = qs.for_metric(metric)
        if asset_id:
            qs = qs.for_asset(asset_id)
        return qs

    def perform_create(self, serializer: AssetEngagementSerializer) -> None:
        instance = serializer.save()
        # Mirror into the high-volume raw log. Degrades gracefully if Mongo is
        # down (the mongo module falls back to an in-memory store).
        mongo.insert_event(
            {
                "asset_id": instance.asset_id,
                "metric": instance.metric,
                "value": instance.value,
                "recorded_at": instance.recorded_at.isoformat(),
            }
        )


class AnalyticsSummaryViewSet(viewsets.ViewSet):
    """Read-only aggregate analytics across all engagement events."""

    def list(self, request: Request) -> Response:
        try:
            top_n = max(1, min(50, int(request.query_params.get("top_n", "5"))))
        except (TypeError, ValueError):
            top_n = 5

        payload = services.summary_payload(top_n=top_n)
        metric_rows = MetricSummarySerializer(payload["per_metric"], many=True).data
        return Response(
            {
                "per_metric": metric_rows,
                "top_assets": payload["top_assets"],
                "raw_event_count": payload["raw_event_count"],
                "mongo_backend": payload["mongo_backend"],
            }
        )
