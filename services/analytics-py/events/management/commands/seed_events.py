"""
Seed synthetic engagement events into BOTH the Django ORM and the Mongo log.

Deterministic by default (fixed seed) so the catalog numbers are reproducible.

    python manage.py seed_events --count 500
    python manage.py seed_events --count 500 --clear --seed 1729
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from events import mongo
from events.models import AssetEngagement
from events.seeding import DEFAULT_SEED, generate_events


class Command(BaseCommand):
    help = "Seed deterministic synthetic engagement events (ORM + MongoDB)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--count",
            type=int,
            default=500,
            help="Number of synthetic events to generate (default: 500).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=DEFAULT_SEED,
            help=f"RNG seed for reproducibility (default: {DEFAULT_SEED}).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing rows/documents before seeding.",
        )

    def handle(self, *args, **options) -> None:
        count: int = options["count"]
        seed: int = options["seed"]

        if options["clear"]:
            deleted, _ = AssetEngagement.objects.all().delete()
            mongo.clear()
            self.stdout.write(f"Cleared {deleted} ORM rows and the Mongo log.")

        events = list(generate_events(count, seed=seed))

        # ORM bulk insert.
        AssetEngagement.objects.bulk_create(
            [AssetEngagement(**e) for e in events], batch_size=500
        )

        # Mongo raw log (datetimes serialized to ISO strings for portability).
        mongo.insert_many(
            [
                {
                    "asset_id": e["asset_id"],
                    "metric": e["metric"],
                    "value": e["value"],
                    "recorded_at": e["recorded_at"].isoformat(),
                }
                for e in events
            ]
        )

        backend = mongo.active_backend()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {count} events into ORM and Mongo "
                f"(backend={backend}, seed={seed})."
            )
        )
