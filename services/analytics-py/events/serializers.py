"""DRF serializers for engagement events.

Validation and the ratings-range rule live here (fat serializer), keeping the
viewset thin.
"""
from __future__ import annotations

from rest_framework import serializers

from .models import AssetEngagement, Metric


class AssetEngagementSerializer(serializers.ModelSerializer):
    """Read/write serializer for a single engagement row."""

    class Meta:
        model = AssetEngagement
        fields = ["id", "asset_id", "metric", "value", "recorded_at", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_asset_id(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("asset_id may not be blank.")
        return value

    def validate(self, attrs: dict) -> dict:
        """Cross-field rule: ratings must fall in the 1..5 star range."""
        metric = attrs.get("metric", getattr(self.instance, "metric", None))
        value = attrs.get("value", getattr(self.instance, "value", None))
        if metric == Metric.RATING and value is not None and not (1.0 <= value <= 5.0):
            raise serializers.ValidationError(
                {"value": "Rating value must be between 1 and 5."}
            )
        return attrs


class MetricSummarySerializer(serializers.Serializer):
    """One row of the aggregate summary endpoint (read-only)."""

    metric = serializers.CharField()
    count = serializers.IntegerField()
    total_value = serializers.FloatField()
    average_value = serializers.FloatField()
    unique_assets = serializers.IntegerField()
