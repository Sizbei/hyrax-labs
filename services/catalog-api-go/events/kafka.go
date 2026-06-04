package events

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
	"github.com/segmentio/kafka-go"
)

// KafkaPublisher publishes material change events to a Kafka topic.
type KafkaPublisher struct {
	writer *kafka.Writer
}

var _ Publisher = (*KafkaPublisher)(nil)

// NewKafkaPublisher constructs a publisher writing to the given brokers/topic.
// It does not dial eagerly; kafka-go connects lazily on first write. To verify
// reachability up front, call Ping.
func NewKafkaPublisher(brokers []string, topic string) *KafkaPublisher {
	w := &kafka.Writer{
		Addr:         kafka.TCP(brokers...),
		Topic:        topic,
		Balancer:     &kafka.Hash{}, // partition by key (material ID) for ordering
		RequiredAcks: kafka.RequireOne,
		WriteTimeout: 3 * time.Second,
		BatchTimeout: 50 * time.Millisecond,
	}
	return &KafkaPublisher{writer: w}
}

// Ping verifies that at least one broker is reachable by opening a control conn.
func Ping(ctx context.Context, brokers []string) error {
	if len(brokers) == 0 {
		return fmt.Errorf("no kafka brokers configured")
	}
	d := &kafka.Dialer{Timeout: 3 * time.Second}
	conn, err := d.DialContext(ctx, "tcp", brokers[0])
	if err != nil {
		return fmt.Errorf("dial kafka %s: %w", brokers[0], err)
	}
	defer conn.Close()
	if _, err := conn.Brokers(); err != nil {
		return fmt.Errorf("read kafka brokers: %w", err)
	}
	return nil
}

// PublishUpserted publishes a material.upserted event keyed by material ID.
func (p *KafkaPublisher) PublishUpserted(ctx context.Context, m model.Material) error {
	evt := MaterialUpserted{
		Type:       "material.upserted",
		MaterialID: m.ID,
		Material:   m,
		OccurredAt: time.Now().UTC(),
	}
	value, err := json.Marshal(evt)
	if err != nil {
		return fmt.Errorf("marshal event for %s: %w", m.ID, err)
	}
	msg := kafka.Message{Key: []byte(m.ID), Value: value, Time: evt.OccurredAt}
	if err := p.writer.WriteMessages(ctx, msg); err != nil {
		return fmt.Errorf("write kafka message for %s: %w", m.ID, err)
	}
	return nil
}

// Close flushes and closes the writer.
func (p *KafkaPublisher) Close() error {
	if err := p.writer.Close(); err != nil {
		return fmt.Errorf("close kafka writer: %w", err)
	}
	return nil
}

// Handler processes a decoded material event.
type Handler func(ctx context.Context, evt MaterialUpserted) error

// Consumer reads material.upserted events from Kafka. It is an example of the
// consumer side of the event flow; main does not start it by default.
type Consumer struct {
	reader *kafka.Reader
	log    *slog.Logger
}

// NewConsumer builds a consumer for the given brokers/topic/group.
func NewConsumer(brokers []string, topic, group string, log *slog.Logger) *Consumer {
	r := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        brokers,
		Topic:          topic,
		GroupID:        group,
		MinBytes:       1,
		MaxBytes:       10e6,
		CommitInterval: time.Second,
	})
	return &Consumer{reader: r, log: log}
}

// Run consumes messages until ctx is cancelled, invoking handler per event.
// Decode failures are logged and skipped so one bad message never stalls the
// stream. Returns ctx.Err() on cancellation.
func (c *Consumer) Run(ctx context.Context, handler Handler) error {
	for {
		msg, err := c.reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			return fmt.Errorf("read kafka message: %w", err)
		}
		var evt MaterialUpserted
		if err := json.Unmarshal(msg.Value, &evt); err != nil {
			c.log.Warn("skipping undecodable event", "error", err, "offset", msg.Offset)
			continue
		}
		if err := handler(ctx, evt); err != nil {
			c.log.Error("event handler failed", "error", err, "material_id", evt.MaterialID)
		}
	}
}

// Close closes the reader.
func (c *Consumer) Close() error {
	if err := c.reader.Close(); err != nil {
		return fmt.Errorf("close kafka reader: %w", err)
	}
	return nil
}
