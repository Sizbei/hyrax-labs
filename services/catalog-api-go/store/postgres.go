package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
	"github.com/jackc/pgx/v5/stdlib" // register the "pgx" database/sql driver
)

// blank import side effect: ensure the pgx stdlib driver is linked even if the
// symbol is otherwise unused.
var _ = stdlib.GetDefaultDriver

// PostgresStore is a Store backed by PostgreSQL via database/sql + pgx.
type PostgresStore struct {
	db *sql.DB
}

// compile-time assertion that PostgresStore satisfies Store.
var _ Store = (*PostgresStore)(nil)

// NewPostgresStore opens a connection pool using the pgx stdlib driver and
// verifies connectivity. The caller owns Close via the returned *sql.DB.
func NewPostgresStore(ctx context.Context, dsn string) (*PostgresStore, error) {
	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return nil, fmt.Errorf("open postgres: %w", err)
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("ping postgres: %w", err)
	}
	return &PostgresStore{db: db}, nil
}

// DB exposes the underlying pool so main can manage its lifecycle.
func (s *PostgresStore) DB() *sql.DB { return s.db }

// Ping verifies datastore connectivity.
func (s *PostgresStore) Ping(ctx context.Context) error {
	if err := s.db.PingContext(ctx); err != nil {
		return fmt.Errorf("ping postgres: %w", err)
	}
	return nil
}

const baseSelect = `
SELECT id, supplier, source_url, name, slug, category, resolution_px, tags
FROM materials`

// FindAll returns all materials ordered by name.
func (s *PostgresStore) FindAll(ctx context.Context, limit int) ([]model.Material, error) {
	query := baseSelect + ` ORDER BY name ASC`
	args := []any{}
	if limit > 0 {
		query += ` LIMIT $1`
		args = append(args, limit)
	}
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query materials: %w", err)
	}
	defer rows.Close()
	return s.scanMaterials(ctx, rows)
}

// FindByID returns a single material or ErrNotFound.
func (s *PostgresStore) FindByID(ctx context.Context, id string) (model.Material, error) {
	row := s.db.QueryRowContext(ctx, baseSelect+` WHERE id = $1`, id)
	m, err := scanMaterialRow(row)
	if errors.Is(err, sql.ErrNoRows) {
		return model.Material{}, ErrNotFound
	}
	if err != nil {
		return model.Material{}, fmt.Errorf("scan material %s: %w", id, err)
	}
	textures, err := s.loadTextures(ctx, id)
	if err != nil {
		return model.Material{}, err
	}
	m.Textures = textures
	return m, nil
}

// SearchByCategory returns materials with an exactly matching (case-insensitive) category.
func (s *PostgresStore) SearchByCategory(ctx context.Context, category string, limit int) ([]model.Material, error) {
	query := baseSelect + ` WHERE lower(category) = lower($1) ORDER BY name ASC`
	args := []any{category}
	if limit > 0 {
		query += ` LIMIT $2`
		args = append(args, limit)
	}
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query materials by category: %w", err)
	}
	defer rows.Close()
	return s.scanMaterials(ctx, rows)
}

// Upsert inserts or replaces a material and its textures inside a transaction.
func (s *PostgresStore) Upsert(ctx context.Context, m model.Material) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer func() { _ = tx.Rollback() }() // no-op after commit

	const upsertMaterial = `
INSERT INTO materials (id, supplier, source_url, name, slug, category, resolution_px, tags, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now())
ON CONFLICT (id) DO UPDATE SET
    supplier      = EXCLUDED.supplier,
    source_url    = EXCLUDED.source_url,
    name          = EXCLUDED.name,
    slug          = EXCLUDED.slug,
    category      = EXCLUDED.category,
    resolution_px = EXCLUDED.resolution_px,
    tags          = EXCLUDED.tags,
    updated_at    = now()`

	tags := m.Tags
	if tags == nil {
		tags = []string{}
	}
	if _, err := tx.ExecContext(ctx, upsertMaterial,
		m.ID, m.Supplier, m.SourceURL, m.Name, m.Slug,
		nullStr(m.Category), nullInt(m.ResolutionPx), tags,
	); err != nil {
		return fmt.Errorf("upsert material %s: %w", m.ID, err)
	}

	// Replace texture set: delete then re-insert keeps the 1:N consistent.
	if _, err := tx.ExecContext(ctx, `DELETE FROM textures WHERE material_id = $1`, m.ID); err != nil {
		return fmt.Errorf("clear textures for %s: %w", m.ID, err)
	}
	const insertTexture = `
INSERT INTO textures (material_id, map_type, url, original_label)
VALUES ($1, $2, $3, $4)`
	for _, t := range m.Textures {
		if _, err := tx.ExecContext(ctx, insertTexture, m.ID, string(t.MapType), t.URL, t.OriginalLabel); err != nil {
			return fmt.Errorf("insert texture for %s: %w", m.ID, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit upsert %s: %w", m.ID, err)
	}
	return nil
}

// scanMaterials scans a result set of material rows and bulk-loads textures.
func (s *PostgresStore) scanMaterials(ctx context.Context, rows *sql.Rows) ([]model.Material, error) {
	var out []model.Material
	ids := make([]string, 0)
	for rows.Next() {
		m, err := scanMaterialRow(rows)
		if err != nil {
			return nil, fmt.Errorf("scan material: %w", err)
		}
		out = append(out, m)
		ids = append(ids, m.ID)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate materials: %w", err)
	}
	if len(out) == 0 {
		return out, nil
	}
	byID, err := s.loadTexturesForMany(ctx, ids)
	if err != nil {
		return nil, err
	}
	for i := range out {
		out[i].Textures = byID[out[i].ID]
	}
	return out, nil
}

// loadTextures loads all textures for a single material.
func (s *PostgresStore) loadTextures(ctx context.Context, materialID string) ([]model.Texture, error) {
	byID, err := s.loadTexturesForMany(ctx, []string{materialID})
	if err != nil {
		return nil, err
	}
	return byID[materialID], nil
}

// loadTexturesForMany fetches textures for a set of materials in one query.
func (s *PostgresStore) loadTexturesForMany(ctx context.Context, ids []string) (map[string][]model.Texture, error) {
	result := make(map[string][]model.Texture, len(ids))
	if len(ids) == 0 {
		return result, nil
	}
	const q = `
SELECT material_id, map_type, url, original_label
FROM textures
WHERE material_id = ANY($1)
ORDER BY material_id, map_type`
	rows, err := s.db.QueryContext(ctx, q, ids)
	if err != nil {
		return nil, fmt.Errorf("query textures: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var matID, mapType, url, label string
		if err := rows.Scan(&matID, &mapType, &url, &label); err != nil {
			return nil, fmt.Errorf("scan texture: %w", err)
		}
		result[matID] = append(result[matID], model.Texture{
			MapType:       model.MapType(mapType),
			URL:           url,
			OriginalLabel: label,
		})
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate textures: %w", err)
	}
	return result, nil
}

// rowScanner abstracts *sql.Row and *sql.Rows for shared scan logic.
type rowScanner interface {
	Scan(dest ...any) error
}

func scanMaterialRow(r rowScanner) (model.Material, error) {
	var (
		m        model.Material
		category sql.NullString
		resPx    sql.NullInt64
		tags     []string
	)
	if err := r.Scan(&m.ID, &m.Supplier, &m.SourceURL, &m.Name, &m.Slug, &category, &resPx, &tags); err != nil {
		return model.Material{}, err
	}
	if category.Valid {
		c := category.String
		m.Category = &c
	}
	if resPx.Valid {
		v := int(resPx.Int64)
		m.ResolutionPx = &v
	}
	m.Tags = tags
	return m, nil
}

func nullStr(s *string) sql.NullString {
	if s == nil {
		return sql.NullString{}
	}
	return sql.NullString{String: *s, Valid: true}
}

func nullInt(i *int) sql.NullInt64 {
	if i == nil {
		return sql.NullInt64{}
	}
	return sql.NullInt64{Int64: int64(*i), Valid: true}
}

// SchemaStatements splits the embedded schema into executable statements.
// Useful for applying db/schema.sql programmatically in integration tests.
func SchemaStatements(schema string) []string {
	parts := strings.Split(schema, ";")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if strings.TrimSpace(p) != "" {
			out = append(out, strings.TrimSpace(p))
		}
	}
	return out
}
