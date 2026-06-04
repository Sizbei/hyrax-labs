# backend-jvm — Supplier Material Ingestion Service

A small JVM backend microservice that ingests **supplier material** records from
third-party partner APIs, normalizes them into a canonical model, deduplicates
across partners, and runs the work as **asynchronous, scheduled jobs**. The
ingestion stage models a distributed pipeline: each partner feed is processed
concurrently as an independent, individually-tracked, failure-isolated job
(here via Kotlin coroutines and structured concurrency).

It is written in a mix of **Kotlin** (service logic, domain models, scheduler,
partner-client interfaces) and **Java** (a legacy-style partner client, a DTO,
and a string utility) to demonstrate clean Kotlin/Java interop.

> **All data in this project is SYNTHETIC.** There are no real partner names, no
> real API endpoints, and no API keys. The partner clients return hard-coded
> sample records so the service builds and runs with zero external dependencies.

## What it does

1. **Fetch** — each configured partner exposes a `PartnerApiClient`. The pipeline
   fetches each partner's records concurrently (one coroutine per partner, on the
   I/O dispatcher).
2. **Normalize** — `MaterialNormalizer` parses messy partner quantity strings,
   converts every quantity to kilograms, resolves free-form category labels to a
   canonical enum, and derives a deterministic `canonicalKey`.
3. **Deduplicate** — `Deduplicator` collapses the same physical material reported
   by multiple partners using the canonical key.
4. **Schedule** — `JobScheduler` runs ingestion cycles on a fixed interval using
   Kotlin coroutines and structured concurrency. Each per-partner ingestion is a
   tracked `ProcessingJob` in a coroutine-`Mutex`-guarded `JobQueue`, so a single
   failing partner feed is isolated and never aborts the rest of the cycle.

## Architecture

```
src/main/kotlin/com/hyraxlabs/ingest/
├── App.kt                       # demo entry point — wires everything, runs cycles
├── domain/                      # immutable models (Kotlin data classes) + enums
│   ├── Enums.kt                 # MaterialUnit, MaterialCategory, JobStatus
│   ├── Material.kt              # normalized canonical material
│   ├── SupplierRecord.kt        # raw partner record
│   └── ProcessingJob.kt         # async job with lifecycle transitions
├── partner/
│   ├── PartnerApiClient.kt      # Kotlin interface + PartnerApiException
│   ├── SampleAlphaPartnerClient.kt   # Kotlin partner implementation
│   └── PartnerRegistry.kt       # immutable registry of clients
├── pipeline/
│   ├── MaterialNormalizer.kt    # raw record -> canonical Material
│   └── Deduplicator.kt          # cross-partner dedup
└── scheduler/
    ├── JobQueue.kt              # coroutine-safe in-memory job store
    ├── IngestionPipeline.kt     # concurrent fetch + normalize + dedup per cycle
    └── JobScheduler.kt          # interval-based coroutine scheduler

src/main/java/com/hyraxlabs/ingest/partner/
├── PartnerApiClient ...         # (interface lives in Kotlin)
├── BetaFeedItem.java            # legacy-style immutable Java DTO
├── LegacyBetaPartnerClient.java # Java class implementing the Kotlin interface
└── QuantityStrings.java         # Java utility consumed by the Kotlin normalizer
```

**Interop highlights**
- `LegacyBetaPartnerClient` (Java) implements the Kotlin `PartnerApiClient`
  interface, exposes the Kotlin `val source` via `getSource()`, and constructs the
  Kotlin `SupplierRecord` data class through its generated Java constructor.
- The Kotlin `MaterialNormalizer` calls the Java `QuantityStrings.clean(...)`.

## Requirements

- **JDK 17** (the build pins a Java 17 toolchain for both Kotlin and Java).
- No global Gradle install needed — use the committed wrapper.

## Build / Run / Test

```bash
# Build everything (compiles Kotlin + Java, runs tests, assembles jar)
./gradlew build

# Run the demo ingestion cycles (logs normalized materials + job summary)
./gradlew run

# Run only the unit tests
./gradlew test
```

## Gradle wrapper

The full wrapper is committed: `gradlew`, `gradlew.bat`,
`gradle/wrapper/gradle-wrapper.properties` (pinned to **Gradle 8.7**), and
`gradle/wrapper/gradle-wrapper.jar` (the official Gradle 8.7 wrapper jar). A clean
checkout can build immediately with `./gradlew build` — the wrapper downloads the
Gradle 8.7 distribution on first run.

If for any reason the `gradle-wrapper.jar` is missing or corrupted in your
checkout, regenerate it once with a system Gradle:

```bash
gradle wrapper --gradle-version 8.7
```

## Tech stack

- Kotlin 1.9.24 (JVM)
- kotlinx-coroutines-core 1.8.1 (async scheduling / structured concurrency)
- slf4j-api + slf4j-simple 2.0.13 (logging)
- JUnit 5 + kotlin.test + kotlinx-coroutines-test (unit tests)

## Tests

The suite (`src/test/kotlin/...`) covers the normalizer (unit conversion, bad-row
handling, canonical keys), the deduplicator, both partner clients and the Java
util, the partner registry, the coroutine-safe `JobQueue` (including concurrent
enqueues), the full `IngestionPipeline` (cross-partner dedup + failure isolation),
and the `JobScheduler` (one-shot and interval-driven runs via the coroutine-test
virtual clock).
```bash
./gradlew test
```
