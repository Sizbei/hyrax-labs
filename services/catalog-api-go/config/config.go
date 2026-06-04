// Package config loads service configuration from environment variables with
// sane localhost defaults, so the binary runs anywhere with zero setup.
package config

import (
	"os"
	"strings"
	"time"
)

// Config holds all runtime configuration.
type Config struct {
	HTTPAddr     string
	PostgresDSN  string
	RedisAddr    string
	CacheTTL     time.Duration
	KafkaBrokers []string
	KafkaTopic   string
}

// Load reads configuration from the environment, applying defaults.
func Load() Config {
	return Config{
		HTTPAddr:     env("CATALOG_HTTP_ADDR", ":8080"),
		PostgresDSN:  env("CATALOG_POSTGRES_DSN", "postgres://catalog:catalog@localhost:5432/catalog?sslmode=disable"),
		RedisAddr:    env("CATALOG_REDIS_ADDR", "localhost:6379"),
		CacheTTL:     envDuration("CATALOG_CACHE_TTL", 5*time.Minute),
		KafkaBrokers: envList("CATALOG_KAFKA_BROKERS", []string{"localhost:9092"}),
		KafkaTopic:   env("CATALOG_KAFKA_TOPIC", "material.upserted"),
	}
}

func env(key, def string) string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		return v
	}
	return def
}

func envDuration(key string, def time.Duration) time.Duration {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
	}
	return def
}

func envList(key string, def []string) []string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		parts := strings.Split(v, ",")
		out := make([]string, 0, len(parts))
		for _, p := range parts {
			if t := strings.TrimSpace(p); t != "" {
				out = append(out, t)
			}
		}
		if len(out) > 0 {
			return out
		}
	}
	return def
}
