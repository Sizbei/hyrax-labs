package store

import "github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"

// SeedMaterials returns ~12 synthetic PBR materials used to seed the in-memory
// fallback store (and the demo data set). All values are invented; the URLs
// point at a non-routable example host and reference no real assets.
func SeedMaterials() []model.Material {
	tex := func(t model.MapType, slug, label string) model.Texture {
		return model.Texture{
			MapType:       t,
			URL:           "https://assets.example.invalid/pbr/" + slug + "/" + string(t) + ".png",
			OriginalLabel: label,
		}
	}
	full := func(slug string) []model.Texture {
		return []model.Texture{
			tex(model.MapAlbedo, slug, "BaseColor"),
			tex(model.MapNormal, slug, "Normal"),
			tex(model.MapRoughness, slug, "Roughness"),
			tex(model.MapMetallic, slug, "Metalness"),
			tex(model.MapAO, slug, "AO"),
		}
	}

	return []model.Material{
		{ID: "mat_brick_red_01", Supplier: "TextureForge", SourceURL: "https://textureforge.example.invalid/brick-red", Name: "Red Clay Brick", Slug: "red-clay-brick", Category: model.StrPtr("masonry"), ResolutionPx: model.IntPtr(4096), Tags: []string{"wall", "outdoor"}, Textures: full("red-clay-brick")},
		{ID: "mat_oak_planks_01", Supplier: "TextureForge", SourceURL: "https://textureforge.example.invalid/oak-planks", Name: "Oak Floor Planks", Slug: "oak-floor-planks", Category: model.StrPtr("wood"), ResolutionPx: model.IntPtr(2048), Tags: []string{"floor", "interior"}, Textures: full("oak-floor-planks")},
		{ID: "mat_marble_white_01", Supplier: "PixelQuarry", SourceURL: "https://pixelquarry.example.invalid/white-marble", Name: "White Carrara Marble", Slug: "white-carrara-marble", Category: model.StrPtr("stone"), ResolutionPx: model.IntPtr(8192), Tags: []string{"polished"}, Textures: full("white-carrara-marble")},
		{ID: "mat_rust_metal_01", Supplier: "PixelQuarry", SourceURL: "https://pixelquarry.example.invalid/rusted-iron", Name: "Rusted Iron Plate", Slug: "rusted-iron-plate", Category: model.StrPtr("metal"), ResolutionPx: model.IntPtr(4096), Tags: []string{"weathered", "industrial"}, Textures: full("rusted-iron-plate")},
		{ID: "mat_concrete_01", Supplier: "SurfaceLab", SourceURL: "https://surfacelab.example.invalid/concrete", Name: "Polished Concrete", Slug: "polished-concrete", Category: model.StrPtr("concrete"), ResolutionPx: model.IntPtr(2048), Tags: []string{"floor"}, Textures: full("polished-concrete")},
		{ID: "mat_fabric_denim_01", Supplier: "SurfaceLab", SourceURL: "https://surfacelab.example.invalid/denim", Name: "Blue Denim Weave", Slug: "blue-denim-weave", Category: model.StrPtr("fabric"), ResolutionPx: model.IntPtr(2048), Tags: []string{"cloth"}, Textures: []model.Texture{tex(model.MapAlbedo, "blue-denim-weave", "Diffuse"), tex(model.MapNormal, "blue-denim-weave", "Normal"), tex(model.MapRoughness, "blue-denim-weave", "Rough")}},
		{ID: "mat_grass_01", Supplier: "NatureScan", SourceURL: "https://naturescan.example.invalid/grass", Name: "Wild Meadow Grass", Slug: "wild-meadow-grass", Category: model.StrPtr("ground"), ResolutionPx: model.IntPtr(4096), Tags: []string{"outdoor", "terrain"}, Textures: full("wild-meadow-grass")},
		{ID: "mat_sand_dune_01", Supplier: "NatureScan", SourceURL: "https://naturescan.example.invalid/sand", Name: "Desert Dune Sand", Slug: "desert-dune-sand", Category: model.StrPtr("ground"), ResolutionPx: model.IntPtr(4096), Tags: []string{"outdoor", "terrain"}, Textures: full("desert-dune-sand")},
		{ID: "mat_leather_01", Supplier: "TextureForge", SourceURL: "https://textureforge.example.invalid/leather", Name: "Brown Worn Leather", Slug: "brown-worn-leather", Category: model.StrPtr("fabric"), ResolutionPx: model.IntPtr(2048), Tags: []string{"upholstery"}, Textures: full("brown-worn-leather")},
		{ID: "mat_tiles_hex_01", Supplier: "PixelQuarry", SourceURL: "https://pixelquarry.example.invalid/hex-tiles", Name: "Hexagonal Ceramic Tiles", Slug: "hexagonal-ceramic-tiles", Category: model.StrPtr("ceramic"), ResolutionPx: model.IntPtr(4096), Tags: []string{"floor", "interior"}, Textures: full("hexagonal-ceramic-tiles")},
		{ID: "mat_gold_brushed_01", Supplier: "SurfaceLab", SourceURL: "https://surfacelab.example.invalid/brushed-gold", Name: "Brushed Gold", Slug: "brushed-gold", Category: model.StrPtr("metal"), ResolutionPx: model.IntPtr(2048), Tags: []string{"polished"}, Textures: full("brushed-gold")},
		{ID: "mat_snow_fresh_01", Supplier: "NatureScan", SourceURL: "https://naturescan.example.invalid/snow", Name: "Fresh Powder Snow", Slug: "fresh-powder-snow", Category: model.StrPtr("ground"), ResolutionPx: model.IntPtr(4096), Tags: []string{"outdoor", "winter"}, Textures: full("fresh-powder-snow")},
	}
}
