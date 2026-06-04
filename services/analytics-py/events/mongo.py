"""
MongoDB-backed raw event log with graceful degradation.

This module owns the *high-volume append store*: every engagement event is
written here as a raw document, separate from the normalized Django ORM table.
It exposes a tiny repository interface (``insert_event``, ``count``,
``top_assets``) backed by ``pymongo``.

Degradation strategy (so the app always runs with zero external services):

1. ``MONGO_USE_MOCK=1`` (or the test suite)  -> use an in-process ``mongomock``
   client. Full aggregation-pipeline support, no server required.
2. A real ``MONGO_URI`` that is reachable     -> use the real pymongo client.
3. A real URI that is *unreachable*           -> log a warning and transparently
   fall back to a ``mongomock`` client so reads/writes still succeed in-memory.

The chosen backend is memoized per-process. Call ``reset_client()`` to force
re-selection (used in tests).
"""
from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger("events")

# Module-level memoized handles.
_collection: Any | None = None
_backend: str | None = None


def _build_mock_collection() -> Any:
    """Return a mongomock-backed collection (in-memory, pipeline-capable)."""
    import mongomock

    client = mongomock.MongoClient()
    return client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION]


def _build_real_collection() -> tuple[Any, str]:
    """
    Try to connect to a real MongoDB. On any connection failure, fall back to
    mongomock so callers never see an exception just because Mongo is down.

    Returns the collection and a backend label ("pymongo" or "mongomock").
    """
    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError

        client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=settings.MONGO_TIMEOUT_MS,
        )
        # Force server selection now so we discover unreachability eagerly.
        client.admin.command("ping")
        collection = client[settings.MONGO_DB_NAME][settings.MONGO_COLLECTION]
        return collection, "pymongo"
    except Exception as exc:  # pragma: no cover - exercised only when Mongo down
        # PyMongoError or import-time issues both land here.
        logger.warning(
            "MongoDB unreachable (%s); falling back to in-memory mongomock store.",
            exc.__class__.__name__,
        )
        return _build_mock_collection(), "mongomock"


def get_collection() -> Any:
    """Return the active raw-events collection, selecting a backend lazily."""
    global _collection, _backend
    if _collection is not None:
        return _collection

    if settings.MONGO_USE_MOCK:
        _collection = _build_mock_collection()
        _backend = "mongomock"
        logger.info("Mongo backend: mongomock (forced via MONGO_USE_MOCK).")
    else:
        _collection, _backend = _build_real_collection()
        logger.info("Mongo backend: %s.", _backend)

    _ensure_indexes(_collection)
    return _collection


def active_backend() -> str | None:
    """Return the label of the currently selected backend, if any."""
    return _backend


def _ensure_indexes(collection: Any) -> None:
    """Index the fields used by reads. Safe/idempotent on both backends."""
    try:
        collection.create_index("asset_id")
        collection.create_index("recorded_at")
    except Exception:  # pragma: no cover - defensive
        logger.debug("Skipping index creation on raw-events collection.")


def reset_client() -> None:
    """Drop the memoized handle so the next call re-selects a backend."""
    global _collection, _backend
    _collection = None
    _backend = None


# --- Repository operations ------------------------------------------------


def insert_event(event: dict[str, Any]) -> str:
    """Append one raw engagement document. Returns the inserted _id as a str."""
    result = get_collection().insert_one(dict(event))
    return str(result.inserted_id)


def insert_many(events: list[dict[str, Any]]) -> int:
    """Bulk-append raw documents. Returns the number inserted."""
    if not events:
        return 0
    result = get_collection().insert_many([dict(e) for e in events])
    return len(result.inserted_ids)


def count(metric: str | None = None) -> int:
    """Count raw events, optionally filtered by metric."""
    query = {"metric": metric} if metric else {}
    return get_collection().count_documents(query)


def top_assets(limit: int = 5) -> list[dict[str, Any]]:
    """
    Aggregate the raw log to find the most-engaged assets.

    Real aggregation pipeline: group by asset_id, count events, sort desc.
    """
    pipeline = [
        {"$group": {"_id": "$asset_id", "event_count": {"$sum": 1}}},
        {"$sort": {"event_count": -1, "_id": 1}},
        {"$limit": int(limit)},
        {"$project": {"_id": 0, "asset_id": "$_id", "event_count": 1}},
    ]
    return list(get_collection().aggregate(pipeline))


def clear() -> None:
    """Remove all raw events (used by seeding/tests)."""
    get_collection().delete_many({})
