package graphql

import (
	"encoding/json"
	"net/http"

	gql "github.com/graphql-go/graphql"
)

// request is the standard GraphQL-over-HTTP POST body.
type request struct {
	Query         string         `json:"query"`
	OperationName string         `json:"operationName"`
	Variables     map[string]any `json:"variables"`
}

// NewHandler returns an http.Handler serving GraphQL POST requests against the
// schema. It executes with the request's context so resolvers can be cancelled.
func NewHandler(schema gql.Schema) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, `{"errors":[{"message":"method not allowed"}]}`, http.StatusMethodNotAllowed)
			return
		}
		var req request
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, `{"errors":[{"message":"invalid request body"}]}`, http.StatusBadRequest)
			return
		}
		result := gql.Do(gql.Params{
			Schema:         schema,
			RequestString:  req.Query,
			VariableValues: req.Variables,
			OperationName:  req.OperationName,
			Context:        r.Context(),
		})
		w.Header().Set("Content-Type", "application/json")
		// GraphQL returns 200 even with field errors; encode the result as-is.
		_ = json.NewEncoder(w).Encode(result)
	})
}
