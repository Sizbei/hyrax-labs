// Package store defines the material repository interface and its
// implementations (Postgres-backed and in-memory fallback).
package store

import (
	"context"
	"errors"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// ErrNotFound is returned by Store implementations when a material does not
// exist. Callers should compare with errors.Is.
var ErrNotFound = errors.New("material not found")

// Store is the repository seam over material persistence. Both the Postgres
// repository and the in-memory fallback satisfy it, so the rest of the service
// depends only on this interface.
type Store interface {
	// FindAll returns all materials, ordered by name. limit <= 0 means "no limit".
	FindAll(ctx context.Context, limit int) ([]model.Material, error)
	// FindByID returns a single material or ErrNotFound.
	FindByID(ctx context.Context, id string) (model.Material, error)
	// SearchByCategory returns materials whose category matches exactly.
	SearchByCategory(ctx context.Context, category string, limit int) ([]model.Material, error)
	// Upsert inserts or replaces a material (and its textures) by ID.
	Upsert(ctx context.Context, m model.Material) error
	// Ping reports whether the underlying datastore is reachable.
	Ping(ctx context.Context) error
}
