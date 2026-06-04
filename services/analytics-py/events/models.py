"""
Django ORM models for catalog-asset engagement analytics.

``AssetEngagement`` is the structured, queryable record of a single
engagement event (a view, download, or rating) against a catalog asset.
The high-volume *raw* append log lives separately in MongoDB
(see ``events/mongo.py``); this table holds the normalized rows that DRF
serves and aggregates.
"""
from __future__ import annotations

from django.core.validators import MinValueValidator
from django.db import models


class Metric(models.TextChoices):
    """The kinds of engagement the platform tracks per asset."""

    VIEW = "view", "View"
    DOWNLOAD = "download", "Download"
    RATING = "rating", "Rating"


class AssetEngagementQuerySet(models.QuerySet):
    """Reusable, composable query methods for engagement rows."""

    def for_metric(self, metric: str) -> "AssetEngagementQuerySet":
        return self.filter(metric=metric)

    def for_asset(self, asset_id: str) -> "AssetEngagementQuerySet":
        return self.filter(asset_id=asset_id)


class AssetEngagement(models.Model):
    """A single engagement event for a catalog asset (material/texture)."""

    asset_id = models.CharField(
        max_length=64,
        help_text="Identifier of the catalog asset, e.g. 'mat-000123'.",
    )
    metric = models.CharField(
        max_length=16,
        choices=Metric.choices,
        help_text="The type of engagement recorded.",
    )
    value = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text=(
            "Magnitude of the event. 1.0 for a view/download; a 1-5 star "
            "score for a rating."
        ),
    )
    recorded_at = models.DateTimeField(
        db_index=True,
        help_text="When the engagement occurred (UTC).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AssetEngagementQuerySet.as_manager()

    class Meta:
        db_table = "asset_engagement"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["asset_id", "metric"], name="idx_asset_metric"),
            models.Index(fields=["metric", "-recorded_at"], name="idx_metric_time"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__gte=0.0),
                name="engagement_value_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.metric}={self.value}"
