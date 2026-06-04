// Package cache provides a read-through cache for material lookups.
package cache

import (
	"context"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// Cache is the seam over material caching. The no-op implementation lets the
// service run without Redis; the Redis implementation backs production use.
type Cache interface {
	// GetMaterial returns the cached material and true, or ok=false on miss.
	GetMaterial(ctx context.Context, id string) (model.Material, bool)
	// SetMaterial stores a material with the configured TTL.
	SetMaterial(ctx context.Context, m model.Material) error
	// Ping reports whether the cache backend is reachable.
	Ping(ctx context.Context) error
}

// Key returns the canonical cache key for a material by ID. It is deterministic
// and namespaced so multiple services can share a Redis instance safely.
func Key(id string) string {
	return "catalog:material:" + id
}
