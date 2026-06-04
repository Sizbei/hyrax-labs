# Hyrax Labs — materials data platform
# Convenience targets for building, running, testing, and demoing all services.
# All data is synthetic; everything runs offline.

ROOT        := $(shell pwd)
BACKEND     := services/backend-jvm
INGEST      := services/ingestion-pipeline
DASHBOARD   := services/metrics-dashboard
DEMO_OUT    := .demo-output

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo "Hyrax Labs — make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Build ─────────────────────────────────────────────────────
.PHONY: build
build: build-backend build-ingest build-dashboard ## Build all services

.PHONY: build-backend
build-backend: ## Build the JVM backend (requires JDK 17)
	cd $(BACKEND) && ./gradlew build --no-daemon

.PHONY: build-ingest
build-ingest: ## Install the Python ingestion pipeline (editable)
	cd $(INGEST) && pip install -e ".[dev]"

.PHONY: build-dashboard
build-dashboard: ## Install + build the dashboard
	cd $(DASHBOARD) && npm install && npm run build

# ── Run ───────────────────────────────────────────────────────
.PHONY: backend
backend: ## Run a JVM backend demo ingestion cycle (requires JDK 17)
	cd $(BACKEND) && ./gradlew run --no-daemon -q

.PHONY: ingest
ingest: ## Run the ingestion pipeline over fixtures -> catalog.json
	cd $(INGEST) && hyrax-ingest --fetcher soup --output catalog.json

.PHONY: dashboard
dashboard: ## Start the dashboard (API + web) at http://localhost:5173
	cd $(DASHBOARD) && npm run dev

.PHONY: seed-dashboard
seed-dashboard: ## Generate the dashboard asset seed from the ingestion pipeline
	cd $(INGEST) && hyrax-ingest --fetcher soup --output catalog.json \
		--asset-seed ../metrics-dashboard/public/assets-seed.json

.PHONY: dashboard-static
dashboard-static: seed-dashboard ## Build + preview the static (serverless) dashboard
	cd $(DASHBOARD) && VITE_STATIC=1 npm run build && npm run preview

# ── Test ──────────────────────────────────────────────────────
.PHONY: test
test: test-backend test-ingest test-dashboard ## Run all test suites

.PHONY: test-backend
test-backend: ## Test the JVM backend (requires JDK 17)
	cd $(BACKEND) && ./gradlew test --no-daemon

.PHONY: test-ingest
test-ingest: ## Test the ingestion pipeline
	cd $(INGEST) && pytest

.PHONY: test-dashboard
test-dashboard: ## Test the dashboard
	cd $(DASHBOARD) && npm test

# ── Demo ──────────────────────────────────────────────────────
.PHONY: demo
demo: ## Run the full end-to-end demo (ingestion -> backend -> dashboard)
	@bash scripts/demo.sh

# ── Clean ─────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove build artifacts and generated catalogs
	rm -rf $(DEMO_OUT)
	rm -f $(INGEST)/catalog.json $(INGEST)/catalog.jsonl
	cd $(DASHBOARD) && rm -rf dist
	cd $(BACKEND) && rm -rf build .gradle
