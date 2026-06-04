package cache

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
	"github.com/redis/go-redis/v9"
)

// RedisCache caches material lookups in Redis as JSON with a fixed TTL.
type RedisCache struct {
	client *redis.Client
	ttl    time.Duration
}

var _ Cache = (*RedisCache)(nil)

// NewRedisCache connects to Redis at addr and verifies connectivity. The
// returned cache must be closed by the caller via Close.
func NewRedisCache(ctx context.Context, addr string, ttl time.Duration) (*RedisCache, error) {
	client := redis.NewClient(&redis.Options{
		Addr:         addr,
		DialTimeout:  3 * time.Second,
		ReadTimeout:  2 * time.Second,
		WriteTimeout: 2 * time.Second,
	})
	if err := client.Ping(ctx).Err(); err != nil {
		_ = client.Close()
		return nil, fmt.Errorf("ping redis: %w", err)
	}
	return &RedisCache{client: client, ttl: ttl}, nil
}

// Close releases the Redis connection pool.
func (c *RedisCache) Close() error { return c.client.Close() }

// Ping verifies Redis connectivity.
func (c *RedisCache) Ping(ctx context.Context) error {
	if err := c.client.Ping(ctx).Err(); err != nil {
		return fmt.Errorf("ping redis: %w", err)
	}
	return nil
}

// GetMaterial returns the cached material, or ok=false on miss or decode error.
func (c *RedisCache) GetMaterial(ctx context.Context, id string) (model.Material, bool) {
	raw, err := c.client.Get(ctx, Key(id)).Bytes()
	if errors.Is(err, redis.Nil) || err != nil {
		return model.Material{}, false
	}
	var m model.Material
	if err := json.Unmarshal(raw, &m); err != nil {
		return model.Material{}, false
	}
	return m, true
}

// SetMaterial stores a material as JSON with the configured TTL.
func (c *RedisCache) SetMaterial(ctx context.Context, m model.Material) error {
	raw, err := json.Marshal(m)
	if err != nil {
		return fmt.Errorf("marshal material %s: %w", m.ID, err)
	}
	if err := c.client.Set(ctx, Key(m.ID), raw, c.ttl).Err(); err != nil {
		return fmt.Errorf("set material %s: %w", m.ID, err)
	}
	return nil
}
