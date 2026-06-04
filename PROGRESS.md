# Project Status

A representative materials-data platform monorepo demonstrating a full backend
stack. All data is synthetic; the whole platform builds and runs offline.

## Status: deployed + expanding to full skill coverage

**Live dashboard:** https://sizbei.github.io/hyrax-labs/

## In progress: full resume-skill coverage (every claimed tech as real code)

Adding genuine, working components for each resume-listed technology so the repo
demonstrates everything the resumes claim — no stubs.

- [ ] **Go** — `services/catalog-api-go`: real Go microservice (catalog API).
- [ ] **SQL / PostgreSQL** — real schema + queries wired into the Go service.
- [ ] **Redis** — real caching layer in the Go service.
- [ ] **Kafka** — real producer/consumer (event bus) in the Go service.
- [ ] **GraphQL** — real GraphQL API layer.
- [ ] **MongoDB** — real document store usage.
- [ ] **Django** — `services/analytics-py`: real Django service.
- [ ] **Kubernetes** — `infra/k8s`: valid manifests for all services.
- [ ] **C/C++** — `tools/`: real native utility.
- [ ] **Ruby** — `tools/`: real utility/script.
- [ ] **SKILLS.md** — skill → file/line evidence map.
- [ ] **Live Skills page** — rendered on the deployed dashboard site.

## Already demonstrated (verified)

- Kotlin + Java (`services/backend-jvm`, 27 tests), coroutines, structured concurrency
- Python + pydantic (`services/ingestion-pipeline`, 56 tests), 4-tool scraper adapters
- React + TS + D3 (`services/metrics-dashboard`, 27 tests), SSE real-time, static SPA
- Docker, GitHub Actions CI, end-to-end pipeline→dashboard seed flow, GitHub Pages deploy
