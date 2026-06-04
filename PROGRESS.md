# Hyrax Labs Monorepo — Autonomous Build Progress

Operating mode: AUTONOMOUS (user removed from planning loop, 2026-06-04 overnight).
Goal: a polished, public, demoable monorepo backing the Hyrax Labs resume bullets.
Integrity rule: synthetic/sample data only; no real proprietary code, vendor names, or credentials.

## Stages

- [ ] **S1 — Monorepo glue**: root README + architecture diagram, .gitignore, LICENSE, CI (JVM+Py+Node), docker-compose, Makefile.
- [ ] **S2 — Git + GitHub**: git init, create public repo Sizbei/hyrax-labs, push.
- [ ] **S3 — Review loop #1**: 3 parallel reviewers (code quality / build+CI / resume-integrity) → fix → re-review until sign-off.
- [ ] **S4 — Demo layer**: one-command end-to-end demo (ingestion → backend → dashboard), captured output/screenshots.
- [ ] **S5 — CI green**: confirm GitHub Actions pass; harden + polish.
- [ ] **S6 — Final sign-off**: final review, demo instructions, DEMO.md.

## Service status (pre-existing, verified)
- backend-jvm: Kotlin+Java, Gradle 8.7 wrapper (real jar), 26 tests. NOT locally built (no JDK) — CI builds it.
- ingestion-pipeline: Python, 49 tests pass, CLI runs over fixtures.
- metrics-dashboard: Vite+React+TS+D3, Express SSE, 22 tests, build green.

## Log
- (start) services built by 3 parallel subagents; monorepo glue next.
