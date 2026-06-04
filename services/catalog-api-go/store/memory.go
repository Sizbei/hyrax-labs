package store

import (
	"context"
	"sort"
	"strings"
	"sync"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// MemoryStore is an in-memory Store implementation used as a graceful-degradation
// fallback when Postgres is unreachable. It is safe for concurrent use.
type MemoryStore struct {
	mu        sync.RWMutex
	materials map[string]model.Material
}

// compile-time assertion that MemoryStore satisfies Store.
var _ Store = (*MemoryStore)(nil)

// NewMemoryStore returns an empty in-memory store.
func NewMemoryStore() *MemoryStore {
	return &MemoryStore{materials: make(map[string]model.Material)}
}

// NewSeededMemoryStore returns an in-memory store preloaded with synthetic data.
func NewSeededMemoryStore() *MemoryStore {
	s := NewMemoryStore()
	for _, m := range SeedMaterials() {
		s.materials[m.ID] = m
	}
	return s
}

// FindAll returns all materials ordered by name.
func (s *MemoryStore) FindAll(_ context.Context, limit int) ([]model.Material, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]model.Material, 0, len(s.materials))
	for _, m := range s.materials {
		out = append(out, m)
	}
	sortByName(out)
	return applyLimit(out, limit), nil
}

// FindByID returns a single material or ErrNotFound.
func (s *MemoryStore) FindByID(_ context.Context, id string) (model.Material, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	m, ok := s.materials[id]
	if !ok {
		return model.Material{}, ErrNotFound
	}
	return m, nil
}

// SearchByCategory returns materials with an exactly matching category.
func (s *MemoryStore) SearchByCategory(_ context.Context, category string, limit int) ([]model.Material, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	want := strings.ToLower(strings.TrimSpace(category))
	out := make([]model.Material, 0)
	for _, m := range s.materials {
		if m.Category != nil && strings.ToLower(*m.Category) == want {
			out = append(out, m)
		}
	}
	sortByName(out)
	return applyLimit(out, limit), nil
}

// Upsert inserts or replaces a material by ID.
func (s *MemoryStore) Upsert(_ context.Context, m model.Material) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.materials[m.ID] = m
	return nil
}

// Ping always succeeds for the in-memory store.
func (s *MemoryStore) Ping(_ context.Context) error { return nil }

func sortByName(ms []model.Material) {
	sort.Slice(ms, func(i, j int) bool {
		if ms[i].Name == ms[j].Name {
			return ms[i].ID < ms[j].ID
		}
		return ms[i].Name < ms[j].Name
	})
}

func applyLimit(ms []model.Material, limit int) []model.Material {
	if limit > 0 && len(ms) > limit {
		return ms[:limit]
	}
	return ms
}
