# Progress & Roadmap

Tracks what's shipped, what's in flight, and the upcoming sprint plan.

Last updated: 2026-08-06

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
- Auth0 (users + roles) -- hand-built, real OAuth2 client-credentials, real-tenant verified
- Slack (channels + messages) -- first agent-drafted adapter, `cursor_body` pagination added
- CrowdStrike Falcon (devices + users + roles) -- agent-drafted in a fresh session, proved the
  packaged skill works standalone

**Agentic adapter authoring** (Sprint 5, `docs/AGENTIC_ADAPTER_DESIGN.md`)
- Two Claude Code Skills: `build-adapter-from-docs` (draft + verify), `diagnose-adapter-drift`
  (investigate a failure, fix only if it's genuine drift)
- Two-tier verification: unit tests (business logic) + `respx` mock-endpoint tests (real
  request/pagination/auth code against realistic vendor-shaped data)
- Full closed build-verify-deploy-diagnose-fix-reverify-deploy loop designed, including a resolved
  Skill-vs-Agent execution-model decision

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
- Claude skills: `add-adapter`, `add-adapter-tests`, `build-adapter-from-docs`, `diagnose-adapter-drift`

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
| # | Story | Size | Status |
|---|-------|------|--------|
| 4.0 | Auth0 adapter (users + roles, via the Management API) -- real multi-endpoint complexity: OAuth2 client-credentials auth (Machine-to-Machine app), page-based pagination, per-endpoint rate limits, roles-per-role batch-fetch-and-invert vs. per-user N+1 tradeoff | L | done (#18) |
| 4.1 | Stripe adapter (charges + customers) | M | open |
| 4.2 | Slack adapter (channels + messages) | M | done (#22) -- drafted by build-adapter-from-docs, not hand-guided |
| 4.3 | Linear adapter (issues + projects) | M | open |
| 4.4 | Adapter contract test suite -- shared tests every adapter must pass | S | done |
| 4.5 | Documentation: "How to add a new adapter in 30 minutes" with screencast/walkthrough | S | open |
| 4.6 | CrowdStrike Falcon adapter (devices + users + roles/permissions) -- same entities Axonius's own real Falcon adapter fetches. Built via `build-adapter-from-docs` in a fresh session (the first real proof the packaged skill works outside the session that created it -- confirmed skills created mid-session aren't invokable in that same session, discovery happens at start). Research predictions from this entry's original draft held up closely: form-encoded token request confirmed exactly, `meta.pagination.offset` cursor-body shape confirmed exactly, real 401/403 auth-failure codes confirmed. `oauth2_client_credentials` and `cursor_body` both generalized further to fit (bundled with this adapter, same as Auth0/Slack). Users' role-per-user N+1 confirmed unavoidable (no batch-roles endpoint). | L | done (#25/#26) |

### Sprint 5 -- Agentic Adapter Authoring

Goal: Build the build-time/run-time agent design (drafted for an Orchid Security system-design interview,
2026-08-02) for real -- an agent that drafts new adapters from vendor API docs, with a verification gate
before anything ships. Depended on 4.0 (Auth0, not Okta -- pivoted early, no company email available for
an Okta dev org) shipping first as the concrete comparison target.

| # | Story | Size | Status |
|---|-------|------|--------|
| 5.1 | Build-time agent: given a vendor's API docs, draft a `connect`/`fetch_raw`/`normalize` adapter skeleton against `BaseAdapter` | L | prototyped -- `build-adapter-from-docs` skill, proven against Slack 2026-08-05 |
| 5.2 | Verification layer: generated adapter must pass the Sprint 4.4 contract test suite + mocked-data tests before it's eligible to ship | M | strengthened -- added a required second tier (`respx` mock-endpoint tests, #27/#28) that exercises `AssetHttpClient`'s REAL request/pagination/auth code against realistic vendor-shaped responses, not just the adapter's own mocked methods. This is the standard answer to "we can't sign up for every vendor" (CrowdStrike's real trial needs a form + ~24hr wait + real sensor deployment, unlike Auth0's instant signup). Explicit honesty boundary documented: proves realistic-shaped data is handled correctly, not that the vendor's real API returns that shape. |
| 5.3 | Human-review gate: generated adapter sits in a draft/PR state, never auto-merged, until a person approves | S | prototyped -- skill hard-stops before commit/PR by design, not yet exercised as a repeated habit across many runs |
| 5.4 | Runtime stays deterministic: confirm/document that the agent runs ONLY at authoring time -- no LLM call anywhere in the `execute()` hot path | S | true by construction -- generated adapters are plain code satisfying `BaseAdapter`, same as hand-written ones |
| 5.5 | Drift handling: if a vendor's API changes and an adapter starts failing, the agent proposes a fix, but re-enters the same verification gate (5.2/5.3), not an auto-deploy | M | prototyped -- `diagnose-adapter-drift` skill; not yet run against a real drift scenario (no live failure to diagnose yet) |
| 5.6 | Automated trigger path: detect a repeatedly-failing adapter without a human watching, and get evidence in front of whoever/whatever runs DIAGNOSE next | M | detection built (#34) -- Celery beat watcher (`check_repeatedly_failing_adapters`, `app/tasks/scheduler.py`, 15-min interval) polls `sync_history` per adapter instance via the new `SyncHistoryStore.last_n_statuses()`, opens a labeled GitHub issue with evidence via the new `GitHubIssueClient` (`app/integrations/github.py`) when the last 3 finished syncs all failed, deduped against any already-open issue. Chose Celery-beat-poll over Prometheus/Alertmanager since that stack (Sprint 3.1/3.5) doesn't exist in this repo at all -- building it first would've been unrelated scope creep. **Invocation is still deferred**: the issue doesn't yet fire `diagnose-adapter-drift` itself, a human (or a manual run) still has to act on it -- see backlog. |

Known gap in the prototype: Slack was verified only through the verification layer (lint/contract/unit
tests), not a live API call -- there's no test workspace/bot token. Auth0 (4.0) is still the only adapter
verified against a REAL live vendor. Story 8 in `axonius_stories_bank.md` and the skill's own docs are
honest about this distinction.

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
- `sync_engine.run_adapter_sync`: extract a unified reporter (metrics + progress + logging) instead of the current mix of hardcoded module-level globals (`metrics`, `logger`) plus a separately-injected `on_progress` callback -- noted during the universal-adapter-streaming review (feature/universal-adapter-streaming) as an inconsistent extension pattern, deferred as a bigger change (touches `sync_engine.py`, `tasks/core.py`'s callback wiring, and test fixtures)
- `sync_adapter_task` (`app/tasks/core.py`): distinguish fetch-side failures (`AuthenticationError`/`FetchError` from `adapter.stream()`) from store-side failures (Mongo/`AssetStore.store_assets()`) -- currently both land in one blanket `except Exception`, but they likely warrant different retry/alerting treatment; related to the Sprint 2.1 idempotent-syncs backlog item above
- Rate-limit-aware backpressure: `AssetHttpClient` already tracks `X-RateLimit-Remaining` per adapter (`RATE_LIMIT_GAUGE`) but nothing throttles on it -- adaptive concurrency (e.g. shrinking `gather_bounded`'s limit as remaining quota drops) would be a real improvement for high-volume adapters like CrowdStrike, noted during that adapter's build but out of scope there
- `add-adapter` skill (`.claude/skills/add-adapter/SKILL.md`) was severely out of date, predating the current codebase -- wrong adapter directory path (`app/adapters/github/`, actual is `github_adapter/`), wrong `NormalizedAsset` field names (`external_id`/`source_adapter` vs. the real `asset_id`/`customer_id`/`vendor`/etc.), manages its own `httpx.AsyncClient` instead of `BaseAdapter`'s shared `AssetHttpClient`, wrong sample-config shape, and generated `fetch_raw()` as a plain `return` instead of the now-required async generator. Found while auditing CLAUDE.md compliance during feature/universal-adapter-streaming (2026-08-17) -- fixed in #33
- Register a `RemoteTrigger` webhook routine subscribed to the `adapter-drift`-labeled issues the new drift watcher opens (#34, Sprint 5.6), so `diagnose-adapter-drift` actually runs off that issue with zero human involvement -- closes the automated trigger path for real. Deliberately deferred from #34: registering a persistent cloud routine against this repo is a real external effect, wants its own explicit go-ahead rather than being bundled into the detection PR
- Prometheus + Alertmanager + Grafana (Sprint 3.1/3.5) -- still entirely unbuilt (confirmed while researching #34: no `infra/` dir, no compose service, no scrape config exist anywhere in the repo). The drift watcher (#34) uses a Celery-beat-poll instead precisely to avoid needing this stack as a prerequisite; building it properly remains a separate, real piece of work if/when richer alerting (queue depth, latency percentiles, etc.) is actually needed beyond what `sync_history` polling can answer

---

## Process

- New stories enter the backlog first. Promote to a numbered sprint slot during sprint planning.
- One story per GitHub issue. Use `docs/USER_STORY_TEMPLATE.md`.
- Status field on the table reflects branch state, not issue state.
- At sprint end, mark shipped items as ✅ and roll unfinished work into the next sprint.
