# Progress & Roadmap

Tracks what's shipped, what's in flight, and the upcoming sprint plan.

Last updated: 2026-05-07

---

## Current State (Shipped)

**Architecture & Core**
- Hexagonal adapter architecture (`BaseAdapter` + factory + registry)
- Unified `NormalizedAsset` schema
- Multi-instance adapters (multiple instances per type, keyed by `adapter_id`)
- Sync engine with `connect --> fetch_raw --> normalize` template

**Adapters**
- GitHub
- AWS
- CoinGecko
- JSONPlaceholder
- RandomUser
- PerfTest (synthetic load)
- MockAdapter (testing)

**Infrastructure**
- FastAPI with JWT auth (access + refresh)
- Celery + RabbitMQ task queue
- MongoDB storage (assets, configs, sync_history)
- Docker Compose: prod, dev (hot reload), scaling-test (4 workers x 10 concurrency)
- Beat scheduler for periodic syncs
- Prometheus metrics at `/metrics`
- Health probes (`/live`, `/ready`, `/info`) -- Kubernetes-ready
- slowapi rate limiting

**Frontend**
- React 19 + TypeScript + Vite dashboard
- Tabbed UI: Overview, Adapters, Assets, Sync History
- Live sync monitor with worker visualization
- JWT auto-refresh

**Tooling**
- pytest (unit + integration split)
- Scaling test scripts (`setup_scaling_test.py`, `trigger_all_syncs.py`, `monitor_scaling.py`)
- Claude skills: `add-adapter`, `add-adapter-tests`

---

## Roadmap (4-Week Sprint Plan)

The roadmap is grouped into four sprints, each ~2 weeks of focused work. Sprints are aligned with the README's "Production Considerations" section and the gaps surfaced during the workflow audit.

### Sprint 1 -- Engineering Foundation (current)

Goal: Lock in the professional workflow before adding more features.

| # | Story | Size | Status |
|---|-------|------|--------|
| 1.1 | Set up GitHub Actions CI (tests + lint) | M | in-progress (this PR) |
| 1.2 | Add `requirements-dev.txt` and `pyproject.toml` quality config | S | in-progress (this PR) |
| 1.3 | Fix UTF-16 encoding of `requirements.txt` (suspected pip install issue) | XS | open |
| 1.4 | Increase test coverage to 70%+ on `app/services/` and `app/storage/` | M | done |
| 1.5 | Add contract tests for `BaseAdapter` (every adapter must satisfy the interface) | S | done |
| 1.6 | Document the workflow in `docs/PROFESSIONAL_WORKFLOW.md` and `docs/GITHUB_WORKFLOW.md` | S | done (this PR) |

### Sprint 2 -- Production Hardening

Goal: Address the items called out in README's "Production Considerations".

| # | Story | Size |
|---|-------|------|
| 2.1 | Idempotent syncs -- prevent duplicate processing on worker restart | M |
| 2.2 | Dead-letter queue -- handle permanently failing tasks | M |
| 2.3 | Graceful shutdown -- Celery workers drain before container stop | S |
| 2.4 | MongoDB authentication + TLS enabled by default in compose | S |
| 2.5 | Per-tenant rate limiting (extend slowapi by `customer_id`) | M |
| 2.6 | Secret loading from external source (env var indirection / file mount) | M |

### Sprint 3 -- Observability & Operations

Goal: Make production failures debuggable.

| # | Story | Size |
|---|-------|------|
| 3.1 | Grafana dashboard JSON committed in `infra/grafana/` | M |
| 3.2 | Structured logging end-to-end (`structlog` is already a dep -- wire it in) | S |
| 3.3 | Sync correlation IDs surfaced in API responses + logs | S |
| 3.4 | Per-adapter SLO metrics (success rate, p95 duration) | M |
| 3.5 | Alert rules (Prometheus) for adapter failure rate + queue depth | S |

### Sprint 4 -- Adapter Expansion

Goal: Demonstrate the "add a new integration in 3 methods" claim.

| # | Story | Size |
|---|-------|------|
| 4.1 | Stripe adapter (charges + customers) | M |
| 4.2 | Slack adapter (channels + messages) | M |
| 4.3 | Linear adapter (issues + projects) | M |
| 4.4 | Adapter contract test suite -- shared tests every adapter must pass | S |
| 4.5 | Documentation: "How to add a new adapter in 30 minutes" with screencast/walkthrough | S |

---

## Backlog (Unplanned)

Things noted but not yet sprinted:

- Replace hardcoded `admin/admin123` demo user with a real user store
- Multi-tenant data isolation (per-customer asset partitioning)
- Webhook adapter support (push, not pull)
- Bulk asset export endpoint (NDJSON / Parquet)
- Adapter-level circuit breaker (stop calling a failing API for N minutes)
- Frontend: dark mode, accessibility audit
- Frontend: drag-and-drop adapter config builder
- E2E test suite (Playwright) for the dashboard

---

## Process

- New stories enter the backlog first. Promote to a numbered sprint slot during sprint planning.
- One story per GitHub issue. Use `docs/USER_STORY_TEMPLATE.md`.
- Status field on the table reflects branch state, not issue state.
- At sprint end, mark shipped items as ✅ and roll unfinished work into the next sprint.
