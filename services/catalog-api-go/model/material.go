// Package model defines the canonical PBR-material catalog domain types.
//
// These mirror the normalized records emitted by the Python ingestion-pipeline
// service (NormalizedMaterial / PbrTexture) so the whole monorepo shares one
// contract. All data served by this API is synthetic.
package model

// MapType is a canonical PBR texture map channel. Supplier pages label these
// inconsistently (e.g. "diffuse", "base color", "col"); ingestion collapses
// those aliases onto these canonical members.
type MapType string

const (
	MapAlbedo    MapType = "albedo"
	MapNormal    MapType = "normal"
	MapRoughness MapType = "roughness"
	MapMetallic  MapType = "metallic"
	MapAO        MapType = "ao"
	MapUnknown   MapType = "unknown"
)

// Texture is a single classified PBR map belonging to a material.
type Texture struct {
	MapType       MapType `json:"map_type"`
	URL           string  `json:"url"`
	OriginalLabel string  `json:"original_label"`
}

// Material is a cleaned, catalog-ready PBR material with classified maps.
//
// ResolutionPx and Category are pointers so the JSON/SQL representation can
// distinguish "absent" from a zero value, matching the optional fields in the
// upstream normalized model.
type Material struct {
	ID           string    `json:"material_id"`
	Supplier     string    `json:"supplier"`
	SourceURL    string    `json:"source_url"`
	Name         string    `json:"name"`
	Slug         string    `json:"slug"`
	Category     *string   `json:"category,omitempty"`
	ResolutionPx *int      `json:"resolution_px,omitempty"`
	Tags         []string  `json:"tags"`
	Textures     []Texture `json:"textures"`
}

// MapTypes returns the canonical channels present on the material.
func (m Material) MapTypes() []MapType {
	out := make([]MapType, 0, len(m.Textures))
	for _, t := range m.Textures {
		out = append(out, t.MapType)
	}
	return out
}

// StrPtr is a small helper for building optional string fields in seed/test data.
func StrPtr(s string) *string { return &s }

// IntPtr is a small helper for building optional int fields in seed/test data.
func IntPtr(i int) *int { return &i }
