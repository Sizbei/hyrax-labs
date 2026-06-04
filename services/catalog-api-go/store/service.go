package store

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/cache"
	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/events"
	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// Catalog is the application service: it composes a Store with a read-through
// cache and an event Publisher. REST and GraphQL both depend on this, not on
// the individual seams.
type Catalog struct {
	store     Store
	cache     cache.Cache
	publisher events.Publisher
	log       *slog.Logger
}

// NewCatalog wires a Catalog from its collaborators. Any of cache/publisher may
// be the no-op implementation for graceful degradation.
func NewCatalog(s Store, c cache.Cache, p events.Publisher, log *slog.Logger) *Catalog {
	return &Catalog{store: s, cache: c, publisher: p, log: log}
}

// ListMaterials returns all materials (optionally limited).
func (cat *Catalog) ListMaterials(ctx context.Context, limit int) ([]model.Material, error) {
	return cat.store.FindAll(ctx, limit)
}

// MaterialsByCategory returns materials in a category.
func (cat *Catalog) MaterialsByCategory(ctx context.Context, category string, limit int) ([]model.Material, error) {
	return cat.store.SearchByCategory(ctx, category, limit)
}

// GetMaterial resolves a material, trying the cache first and falling back to
// the store, then populating the cache on a hit.
func (cat *Catalog) GetMaterial(ctx context.Context, id string) (model.Material, error) {
	if m, ok := cat.cache.GetMaterial(ctx, id); ok {
		return m, nil
	}
	m, err := cat.store.FindByID(ctx, id)
	if err != nil {
		return model.Material{}, err
	}
	if err := cat.cache.SetMaterial(ctx, m); err != nil {
		// Cache population is best-effort; log and continue.
		cat.log.Warn("cache set failed", "material_id", id, "error", err)
	}
	return m, nil
}

// UpsertMaterial writes a material, refreshes its cache entry, and publishes a
// material.upserted event. Cache/event failures are logged, not fatal.
func (cat *Catalog) UpsertMaterial(ctx context.Context, m model.Material) error {
	if err := cat.store.Upsert(ctx, m); err != nil {
		return fmt.Errorf("upsert: %w", err)
	}
	if err := cat.cache.SetMaterial(ctx, m); err != nil {
		cat.log.Warn("cache set after upsert failed", "material_id", m.ID, "error", err)
	}
	if err := cat.publisher.PublishUpserted(ctx, m); err != nil {
		cat.log.Warn("publish upserted event failed", "material_id", m.ID, "error", err)
	}
	return nil
}

// IsNotFound reports whether err means the material was absent.
func IsNotFound(err error) bool { return errors.Is(err, ErrNotFound) }
