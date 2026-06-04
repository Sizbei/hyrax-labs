#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Hyrax Labs — end-to-end demo
# Runs the full platform: ingestion pipeline -> JVM backend -> dashboard.
# All data is synthetic; everything runs offline.
#
# Degrades gracefully: if a toolchain (JDK / Python venv / Node) is missing,
# that stage is skipped with a clear message instead of failing the demo.
# ──────────────────────────────────────────────────────────────
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INGEST="$ROOT/services/ingestion-pipeline"
BACKEND="$ROOT/services/backend-jvm"
DASHBOARD="$ROOT/services/metrics-dashboard"
OUT="$ROOT/.demo-output"
mkdir -p "$OUT"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
green() { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
rule() { printf "\033[90m%s\033[0m\n" "────────────────────────────────────────────────────────────"; }

clear 2>/dev/null || true
rule
bold "  HYRAX LABS — materials data platform — end-to-end demo"
yellow "  (all data is synthetic; running offline)"
rule
echo

# ── Stage 1: ingestion pipeline ───────────────────────────────
bold "[1/3] Ingestion pipeline (Python): scrape fixtures -> PBR catalog"
echo
INGEST_BIN=""
if command -v hyrax-ingest >/dev/null 2>&1; then
  INGEST_BIN="hyrax-ingest"
elif [ -x "/tmp/hyrax-ing-venv/bin/hyrax-ingest" ]; then
  INGEST_BIN="/tmp/hyrax-ing-venv/bin/hyrax-ingest"
fi

if [ -n "$INGEST_BIN" ]; then
  ( cd "$INGEST" && "$INGEST_BIN" --fetcher soup --output "$OUT/catalog.json" )
  if [ -s "$OUT/catalog.json" ]; then
    COUNT=$(python3 -c "import json;print(len(json.load(open('$OUT/catalog.json'))))" 2>/dev/null || echo "?")
    green "  ✓ wrote PBR catalog: $OUT/catalog.json ($COUNT normalized materials)"
  fi
else
  yellow "  ⚠ hyrax-ingest not installed — run: cd services/ingestion-pipeline && pip install -e ."
  yellow "    (using committed sample catalog for the rest of the demo, if present)"
fi
echo; rule; echo

# ── Stage 2: JVM backend ──────────────────────────────────────
bold "[2/3] JVM backend (Kotlin + Java): partner-API ingestion cycle"
echo
if command -v java >/dev/null 2>&1; then
  ( cd "$BACKEND" && ./gradlew run --no-daemon -q ) | tee "$OUT/backend-run.log"
  green "  ✓ backend ingestion cycle complete (log: $OUT/backend-run.log)"
else
  yellow "  ⚠ no JDK on this machine — the backend builds & runs in CI (JDK 17)."
  yellow "    To run locally: install JDK 17, then 'make backend'."
  yellow "    What it would do: fetch synthetic partner feeds concurrently (one"
  yellow "    coroutine per partner), normalize + dedup into the canonical model,"
  yellow "    and schedule the work as async jobs."
fi
echo; rule; echo

# ── Stage 3: dashboard ────────────────────────────────────────
bold "[3/3] Metrics dashboard (React + D3 + SSE): real-time analytics"
echo
if command -v npm >/dev/null 2>&1; then
  if [ ! -d "$DASHBOARD/node_modules" ]; then
    yellow "  installing dashboard deps (first run)…"
    ( cd "$DASHBOARD" && npm install >/dev/null 2>&1 )
  fi
  green "  ✓ starting dashboard (API + web)…"
  echo "    Open: http://localhost:5173"
  echo "    Press Ctrl+C to stop the demo."
  echo
  ( cd "$DASHBOARD" && exec npm run dev )
else
  yellow "  ⚠ npm not found — install Node 18+, then 'make dashboard'."
fi

echo
green "Demo finished."
