-- Schema for the catalog-api-go service.
--
-- Mirrors the normalized PBR-material catalog produced by the ingestion
-- pipeline: a material has scalar attributes plus a set of classified PBR
-- texture maps (1:N). All data is synthetic.

CREATE TABLE IF NOT EXISTS materials (
    id            TEXT        PRIMARY KEY,            -- stable content hash, e.g. mat_oak_planks_01
    supplier      TEXT        NOT NULL,
    source_url    TEXT        NOT NULL,
    name          TEXT        NOT NULL,
    slug          TEXT        NOT NULL,
    category      TEXT,                                -- nullable: not every supplier labels category
    resolution_px INTEGER,                             -- nullable: square pixel resolution (e.g. 4096)
    tags          TEXT[]      NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Speeds up SearchByCategory (exact, case-insensitive lookups go through lower()).
CREATE INDEX IF NOT EXISTS idx_materials_category ON materials (category);
CREATE INDEX IF NOT EXISTS idx_materials_slug     ON materials (slug);

CREATE TABLE IF NOT EXISTS textures (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    material_id    TEXT NOT NULL REFERENCES materials (id) ON DELETE CASCADE,
    map_type       TEXT NOT NULL,                      -- albedo|normal|roughness|metallic|ao|unknown
    url            TEXT NOT NULL,
    original_label TEXT NOT NULL,
    UNIQUE (material_id, map_type, url)
);

-- All texture rows for a material are fetched together, so index the FK.
CREATE INDEX IF NOT EXISTS idx_textures_material_id ON textures (material_id);
