// Package api exposes the REST surface of the catalog service over chi.
package api

import (
	"net/http"
	"strconv"

	"github.com/Sizbei/hyrax-labs/services/catalog-api-go/store"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// Health reports the readiness of the service's backing components.
type Health struct {
	Status   string            `json:"status"`
	Backends map[string]string `json:"backends"`
}

// HealthChecker reports backend health for /healthz.
type HealthChecker func() Health

// NewRouter builds the REST router. graphqlHandler is mounted at POST /graphql.
func NewRouter(cat *store.Catalog, graphqlHandler http.Handler, health HealthChecker) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)

	h := &handlers{cat: cat, health: health}

	r.Get("/healthz", h.healthz)
	r.Route("/materials", func(r chi.Router) {
		r.Get("/", h.listMaterials)
		r.Get("/{id}", h.getMaterial)
	})
	r.Method(http.MethodPost, "/graphql", graphqlHandler)

	return r
}

type handlers struct {
	cat    *store.Catalog
	health HealthChecker
}

func (h *handlers) healthz(w http.ResponseWriter, r *http.Request) {
	hc := h.health()
	status := http.StatusOK
	if hc.Status != "ok" {
		status = http.StatusServiceUnavailable
	}
	writeData(w, status, hc, nil)
}

func (h *handlers) listMaterials(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r.URL.Query().Get("limit"))
	category := r.URL.Query().Get("category")

	var (
		materials = []any{}
		err       error
	)
	if category != "" {
		ms, e := h.cat.MaterialsByCategory(r.Context(), category, limit)
		err = e
		materials = boxMaterials(ms)
	} else {
		ms, e := h.cat.ListMaterials(r.Context(), limit)
		err = e
		materials = boxMaterials(ms)
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list materials")
		return
	}
	writeData(w, http.StatusOK, materials, &Meta{Count: len(materials)})
}

func (h *handlers) getMaterial(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if id == "" {
		writeError(w, http.StatusBadRequest, "material id is required")
		return
	}
	m, err := h.cat.GetMaterial(r.Context(), id)
	if store.IsNotFound(err) {
		writeError(w, http.StatusNotFound, "material not found")
		return
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to fetch material")
		return
	}
	writeData(w, http.StatusOK, m, nil)
}

func parseLimit(raw string) int {
	if raw == "" {
		return 0
	}
	n, err := strconv.Atoi(raw)
	if err != nil || n < 0 {
		return 0
	}
	return n
}

// boxMaterials converts a typed slice to []any so an empty result serializes as
// [] rather than null.
func boxMaterials[T any](items []T) []any {
	out := make([]any, len(items))
	for i, it := range items {
		out[i] = it
	}
	return out
}
