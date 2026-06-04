// Package graphql defines the GraphQL schema for the catalog API and resolves
// queries against the Catalog service.
package graphql

import (
	"fmt"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/model"
	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/store"
	gql "github.com/graphql-go/graphql"
)

// NewSchema builds an executable schema bound to the given Catalog.
func NewSchema(cat *store.Catalog) (gql.Schema, error) {
	textureType := gql.NewObject(gql.ObjectConfig{
		Name:        "Texture",
		Description: "A classified PBR texture map.",
		Fields: gql.Fields{
			"mapType": &gql.Field{
				Type: gql.NewNonNull(gql.String),
				Resolve: func(p gql.ResolveParams) (any, error) {
					return string(p.Source.(model.Texture).MapType), nil
				},
			},
			"url":           &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: textureField(func(t model.Texture) any { return t.URL })},
			"originalLabel": &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: textureField(func(t model.Texture) any { return t.OriginalLabel })},
		},
	})

	materialType := gql.NewObject(gql.ObjectConfig{
		Name:        "Material",
		Description: "A normalized PBR material in the catalog.",
		Fields: gql.Fields{
			"id":        &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: materialField(func(m model.Material) any { return m.ID })},
			"supplier":  &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: materialField(func(m model.Material) any { return m.Supplier })},
			"sourceUrl": &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: materialField(func(m model.Material) any { return m.SourceURL })},
			"name":      &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: materialField(func(m model.Material) any { return m.Name })},
			"slug":      &gql.Field{Type: gql.NewNonNull(gql.String), Resolve: materialField(func(m model.Material) any { return m.Slug })},
			"category": &gql.Field{Type: gql.String, Resolve: materialField(func(m model.Material) any {
				if m.Category == nil {
					return nil
				}
				return *m.Category
			})},
			"resolutionPx": &gql.Field{Type: gql.Int, Resolve: materialField(func(m model.Material) any {
				if m.ResolutionPx == nil {
					return nil
				}
				return *m.ResolutionPx
			})},
			"tags":     &gql.Field{Type: gql.NewList(gql.String), Resolve: materialField(func(m model.Material) any { return toAnySlice(m.Tags) })},
			"textures": &gql.Field{Type: gql.NewList(textureType), Resolve: materialField(func(m model.Material) any { return m.Textures })},
		},
	})

	rootQuery := gql.NewObject(gql.ObjectConfig{
		Name: "Query",
		Fields: gql.Fields{
			"materials": &gql.Field{
				Type:        gql.NewList(materialType),
				Description: "List materials, optionally filtered by category.",
				Args: gql.FieldConfigArgument{
					"category": &gql.ArgumentConfig{Type: gql.String},
					"limit":    &gql.ArgumentConfig{Type: gql.Int},
				},
				Resolve: func(p gql.ResolveParams) (any, error) {
					limit := intArg(p, "limit", 0)
					if category, ok := p.Args["category"].(string); ok && category != "" {
						ms, err := cat.MaterialsByCategory(p.Context, category, limit)
						if err != nil {
							return nil, fmt.Errorf("resolve materials by category %q: %w", category, err)
						}
						return ms, nil
					}
					ms, err := cat.ListMaterials(p.Context, limit)
					if err != nil {
						return nil, fmt.Errorf("resolve materials: %w", err)
					}
					return ms, nil
				},
			},
			"material": &gql.Field{
				Type:        materialType,
				Description: "Fetch a single material by ID.",
				Args: gql.FieldConfigArgument{
					"id": &gql.ArgumentConfig{Type: gql.NewNonNull(gql.String)},
				},
				Resolve: func(p gql.ResolveParams) (any, error) {
					id, _ := p.Args["id"].(string)
					m, err := cat.GetMaterial(p.Context, id)
					if store.IsNotFound(err) {
						return nil, nil // GraphQL null for missing entity
					}
					if err != nil {
						return nil, fmt.Errorf("resolve material %s: %w", id, err)
					}
					return m, nil
				},
			},
		},
	})

	schema, err := gql.NewSchema(gql.SchemaConfig{Query: rootQuery})
	if err != nil {
		return gql.Schema{}, fmt.Errorf("build graphql schema: %w", err)
	}
	return schema, nil
}

// helper closures keep resolver bodies tiny ----------------------------------

func materialField(get func(model.Material) any) gql.FieldResolveFn {
	return func(p gql.ResolveParams) (any, error) {
		m, ok := p.Source.(model.Material)
		if !ok {
			return nil, fmt.Errorf("expected Material source, got %T", p.Source)
		}
		return get(m), nil
	}
}

func textureField(get func(model.Texture) any) gql.FieldResolveFn {
	return func(p gql.ResolveParams) (any, error) {
		t, ok := p.Source.(model.Texture)
		if !ok {
			return nil, fmt.Errorf("expected Texture source, got %T", p.Source)
		}
		return get(t), nil
	}
}

func toAnySlice(ss []string) []any {
	out := make([]any, len(ss))
	for i, s := range ss {
		out[i] = s
	}
	return out
}

func intArg(p gql.ResolveParams, name string, def int) int {
	if v, ok := p.Args[name].(int); ok {
		return v
	}
	return def
}
