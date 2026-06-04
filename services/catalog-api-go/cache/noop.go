package cache

import (
	"context"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// NoopCache is a Cache that never stores anything. It is used as a graceful
// fallback when Redis is unreachable, and in tests.
type NoopCache struct{}

var _ Cache = NoopCache{}

// NewNoopCache returns a cache that always misses.
func NewNoopCache() NoopCache { return NoopCache{} }

// GetMaterial always reports a miss.
func (NoopCache) GetMaterial(context.Context, string) (model.Material, bool) {
	return model.Material{}, false
}

// SetMaterial discards the value.
func (NoopCache) SetMaterial(context.Context, model.Material) error { return nil }

// Ping always succeeds.
func (NoopCache) Ping(context.Context) error { return nil }
