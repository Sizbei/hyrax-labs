// Package events publishes and consumes material change events over Kafka.
package events

import (
	"context"
	"time"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
)

// TopicMaterialUpserted is the Kafka topic for material write events.
const TopicMaterialUpserted = "material.upserted"

// MaterialUpserted is the event payload published when a material is written.
type MaterialUpserted struct {
	Type       string         `json:"type"` // always "material.upserted"
	MaterialID string         `json:"material_id"`
	Material   model.Material `json:"material"`
	OccurredAt time.Time      `json:"occurred_at"`
}

// Publisher publishes material change events. The no-op implementation lets the
// service run without Kafka.
type Publisher interface {
	// PublishUpserted publishes a material.upserted event keyed by material ID.
	PublishUpserted(ctx context.Context, m model.Material) error
	// Close releases any underlying resources.
	Close() error
}

// NoopPublisher discards all events. Used as a graceful fallback and in tests.
type NoopPublisher struct{}

var _ Publisher = NoopPublisher{}

// NewNoopPublisher returns a publisher that discards events.
func NewNoopPublisher() NoopPublisher { return NoopPublisher{} }

// PublishUpserted discards the event.
func (NoopPublisher) PublishUpserted(context.Context, model.Material) error { return nil }

// Close is a no-op.
func (NoopPublisher) Close() error { return nil }
