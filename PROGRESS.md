# Project Status

A representative materials-data platform monorepo. All data is synthetic; the
whole platform builds and runs offline.

## Status: ✅ complete & green

| Stage | Status |
|-------|--------|
| Three services (backend-jvm, ingestion-pipeline, metrics-dashboard) | ✅ built + tested |
| Monorepo glue (README, CI, Makefile, docker-compose) | ✅ |
| Public on GitHub, CI green on every push | ✅ |
| End-to-end demo (`make demo`, `DEMO.md`) | ✅ |
| Containerized demo (`docker compose up --build`) | ✅ |
| Multi-reviewer audit (code quality · build/CI · integrity) | ✅ signed off |

## Tests

- `backend-jvm` — 27 JUnit 5 / kotlin.test (Gradle, JDK 17)
- `ingestion-pipeline` — 52 pytest
- `metrics-dashboard` — 22 Vitest

Run everything with `make test`.

## Quality bar

The repo passed an iterative multi-agent review (code quality, buildability/CI,
and integrity) with all findings resolved:

- partner-feed ingestion is concurrent and failure-isolated via Kotlin structured
  concurrency (a single bad feed never aborts a cycle);
- resolution parsing prefers explicit pixel dimensions over shorthand;
- all claims are scoped honestly (in-process concurrency, synthetic data);
- no secrets, real vendor names, or fabricated production metrics anywhere.

See [`DEMO.md`](DEMO.md) to run it.
