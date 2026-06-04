# Hyrax Labs Monorepo — Autonomous Build Progress

Operating mode: AUTONOMOUS (user removed from planning loop, 2026-06-04 overnight).
Goal: a polished, public, demoable monorepo backing the Hyrax Labs resume bullets.
Integrity rule: synthetic/sample data only; no real proprietary code, vendor names, or credentials.

## Stages

- [x] **S1 — Monorepo glue**: root README + architecture diagram, .gitignore, LICENSE, CI (JVM+Py+Node), docker-compose, Makefile. DONE.
- [x] **S2 — Git + GitHub**: git init, create public repo Sizbei/hyrax-labs, push. DONE → https://github.com/Sizbei/hyrax-labs
- [x] **S3 — Review loop #1**: 3 parallel reviewers ran. Verdicts: code SHIP, CI WILL-PASS (confirmed green), integrity FIX-BEFORE-PUBLISH (DEMO.md). Fixes applied (round 1):
      - backend: supervisorScope + broaden catch (rethrow CancellationException) for true failure isolation + new test.
      - python: parse_resolution mixed-token bug fixed (explicit dims win over k-shorthand) + hoisted alias constant + 3 new tests (52 total).
      - dashboard: removed dead sourceRef. lint/build/test green.
      - docs: softened "distributed pipeline" framing. Added DEMO.md + 3 Dockerfiles + .dockerignores; fixed compose port 8787→4000.
      RE-REVIEW pending (round 2).
- [x] **S4 — Demo layer**: `make demo` + scripts/demo.sh + DEMO.md with real captured output. DONE.
- [x] **S5 — CI green**: round-1 push CI passed all 3 jobs (JVM on real JDK17). Re-verify after fix push.
- [x] **S6 — Round-2 review**: code SHIP (all 4 fixes verified, no regressions), integrity caught 1 remaining unqualified "distributed pipeline" in root README table → fixed both root + backend README wording. Re-review pending (round 3).

## Service status (pre-existing, verified)
- backend-jvm: Kotlin+Java, Gradle 8.7 wrapper (real jar), 26 tests. NOT locally built (no JDK) — CI builds it.
- ingestion-pipeline: Python, 49 tests pass, CLI runs over fixtures.
- metrics-dashboard: Vite+React+TS+D3, Express SSE, 22 tests, build green.

## Log
- (start) services built by 3 parallel subagents; monorepo glue next.
