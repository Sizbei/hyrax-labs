# Hyrax Labs — Kubernetes Reference Deployment

This directory holds a **reference** Kubernetes deployment for the Hyrax Labs
materials platform. It is meant to demonstrate the full topology and is not wired
to a live image registry — see [Images](#images) below.

Everything lives in the `hyrax-labs` namespace and is tied together with
[Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/).

## Topology

```
                         ┌──────────────────────────────┐
                         │        ingestion-pipeline      │
                         │        (CronJob, every 6h)     │
                         │  scrapes → normalizes → dedups │
                         └───────┬───────────────┬────────┘
                                 │ publish        │ write raw docs
                                 ▼                ▼
                            ┌────────┐       ┌─────────┐
                            │ kafka  │       │ mongodb │
                            └───┬────┘       └────┬────┘
                consume events  │                 │
                                ▼                 │
   ┌──────────────┐      ┌──────────────┐         │
   │ catalog-api  │◄────►│  backend-jvm │         │
   │   -go :8080  │      │    :8081     │         │
   │ REST+GraphQL │      └──────┬───────┘         │
   └──────┬───────┘             │                 │
          │      ┌──────────────┴───┐             │
          ▼      ▼                  ▼             ▼
       ┌──────────┐            ┌──────────┐  ┌──────────────┐
       │ postgres │◄───────────│  redis   │  │ analytics-py │
       │  :5432   │            │  :6379   │  │ (Django:8000)│
       └──────────┘            └──────────┘  └──────────────┘
              ▲                                      ▲
              │                                      │
       ┌──────┴──────────────────────────────────────┐
       │           metrics-dashboard                   │
       │   web :5173  +  api :4000  (two containers)   │
       └───────────────────────────────────────────────┘
```

### Application services

| Service             | Kind        | Ports          | Health endpoint | Image (placeholder)                          |
| ------------------- | ----------- | -------------- | --------------- | -------------------------------------------- |
| `backend-jvm`       | Deployment  | 8081           | `/healthz`      | `ghcr.io/sizbei/hyrax-backend-jvm`           |
| `catalog-api-go`    | Deployment  | 8080 (REST+GQL)| `/healthz`      | `ghcr.io/sizbei/hyrax-catalog-api-go`        |
| `analytics-py`      | Deployment  | 8000 (Django)  | `/api/health`   | `ghcr.io/sizbei/hyrax-analytics-py`          |
| `metrics-dashboard` | Deployment  | 5173 web, 4000 api | `/api/health` | `ghcr.io/sizbei/hyrax-metrics-dashboard-*`  |
| `ingestion-pipeline`| CronJob     | —              | —               | `ghcr.io/sizbei/hyrax-ingestion-pipeline`    |

### Backing services

| Service    | Kind         | Port  | Probe                       |
| ---------- | ------------ | ----- | --------------------------- |
| `postgres` | StatefulSet  | 5432  | `pg_isready`                |
| `redis`    | StatefulSet  | 6379  | `redis-cli ping`            |
| `mongodb`  | StatefulSet  | 27017 | `db.adminCommand('ping')`   |
| `kafka`    | Deployment   | 9092/9093 | TCP socket (KRaft mode) |

Backing stores are `StatefulSet`s with a headless `Service` (`clusterIP: None`)
so each pod has stable DNS; Kafka is a single-broker `Deployment` (KRaft, no
ZooKeeper) which is fine for a dev/reference cluster.

## Configuration & secrets

- **`config.yaml`** — a `ConfigMap` (`hyrax-config`) holding non-secret config:
  service hostnames, ports, topic names, log level. Services reach each other via
  in-cluster DNS (`postgres`, `redis`, `kafka`, `mongodb`, etc.).
- **`secret.yaml`** — a `Secret` (`hyrax-secrets`) with **synthetic placeholder**
  values. Every entry is base64 of an obviously-dummy string (e.g.
  `"hyrax-dev-pg-pw"`). **In a real deployment these come from a secret manager**
  (External Secrets Operator / Vault / cloud secret manager) and the file would
  not be committed.

## Apply

```bash
# Render only (review what Kustomize produces — no cluster required):
kubectl kustomize infra/k8s/

# Apply everything to a cluster:
kubectl apply -k infra/k8s/

# Watch it come up:
kubectl -n hyrax-labs get pods,svc,statefulset,cronjob

# Tear down:
kubectl delete -k infra/k8s/
```

## Images

The image references (`ghcr.io/sizbei/hyrax-*:latest`) are **placeholders**. This
public portfolio repo's CI does not build or push container images, so pods will
not become `Running` against a real cluster without first building and pushing
those images (or retagging the manifests to images you control). The manifests
themselves are complete and valid — this is a **reference deployment** showing the
intended topology, wiring, probes, and resource policy.

## Validation

Validated with PyYAML (kubeconform/kubectl/yamllint were unavailable in the
authoring environment):

- All 13 files parse as valid YAML.
- Every object uses a current `apiVersion` (`v1`, `apps/v1`, `batch/v1`).
- Every `Deployment`/`StatefulSet` `selector.matchLabels` matches its pod-template
  labels.
- Every `Service` selector resolves to exactly one workload.

If you have the tools locally, you can additionally run:

```bash
kubeconform -strict -summary infra/k8s/*.yaml
kubectl apply --dry-run=client -k infra/k8s/
yamllint infra/k8s/
```
