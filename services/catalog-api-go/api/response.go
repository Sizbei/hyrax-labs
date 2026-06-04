package api

import (
	"encoding/json"
	"net/http"
)

// Envelope is the standard JSON response wrapper used by all REST endpoints.
type Envelope struct {
	Success bool   `json:"success"`
	Data    any    `json:"data,omitempty"`
	Error   string `json:"error,omitempty"`
	Meta    *Meta  `json:"meta,omitempty"`
}

// Meta carries list metadata such as the result count.
type Meta struct {
	Count int `json:"count"`
}

func writeJSON(w http.ResponseWriter, status int, env Envelope) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(env)
}

func writeData(w http.ResponseWriter, status int, data any, meta *Meta) {
	writeJSON(w, status, Envelope{Success: true, Data: data, Meta: meta})
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, Envelope{Success: false, Error: msg})
}
