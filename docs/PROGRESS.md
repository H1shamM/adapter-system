# Progress & Roadmap

Tracks what's shipped, what's in flight, and the upcoming sprint plan.

Last updated: 2026-08-02

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
| # | Story | Size | Status |
|---|-------|------|--------|
| 4.0 | Auth0 adapter (users + roles, via the Management API) -- real multi-endpoint complexity: OAuth2 client-credentials auth (Machine-to-Machine app), page-based pagination, per-endpoint rate limits, roles-per-role batch-fetch-and-invert vs. per-user N+1 tradeoff | L | done (#18) |
| 4.1 | Stripe adapter (charges + customers) | M | open |
| 4.2 | Slack adapter (channels + messages) | M | done (#22) -- drafted by build-adapter-from-docs, not hand-guided |
| 4.3 | Linear adapter (issues + projects) | M | open |
| 4.4 | Adapter contract test suite -- shared tests every adapter must pass | S | done |
| 4.5 | Documentation: "How to add a new adapter in 30 minutes" with screencast/walkthrough | S | open |
| 4.6 | **NEXT UP** -- CrowdStrike Falcon adapter (devices + users + roles/permissions). Chosen because Axonius's own real CrowdStrike Falcon adapter fetches exactly these entities (confirmed via docs.axonius.com) -- directly ties to Hisham's real Axonius background. Run via the `build-adapter-from-docs` skill in a FRESH session (skills created mid-session aren't invokable in the session that created them -- discovery happens at session start; this was confirmed the hard way in the session that researched this entry). Docs: auth `https://developer.crowdstrike.com/api-reference/collections/oauth2/`, devices `https://developer.crowdstrike.com/api-reference/collections/hosts/`, users/roles/permissions `https://developer.crowdstrike.com/api-reference/collections/user-management/`. Real wrinkles already researched (RESEARCH ONLY -- no code written, nothing in `app/http/client.py` changed; the skill should make these decisions itself, same as it did for Auth0/Slack): (1) CrowdStrike's OAuth2 token request is form-encoded (`application/x-www-form-urlencoded`) with only `client_id`/`client_secret` -- no `grant_type`/`audience`, unlike Auth0's JSON+grant_type+audience shape; `_setup_auth`'s `oauth2_client_credentials` branch and `ensure_token()` currently hardcode Auth0's exact shape and will need generalizing (e.g. resolve only whichever of audience/grant_type are actually present in `auth_config`, and support a `token_body_format` flag for form vs JSON). (2) CrowdStrike's pagination cursor lives in `meta.pagination.offset` in the response body -- same *shape* as Slack's `cursor_body` (cursor in the body, not a header or client-computed number) but a different field path and request-param name (`offset`, not `cursor`); `_get_next_page_params`'s `cursor_body` branch currently hardcodes Slack's exact path and will need a configurable field-path/param-name instead. (3) CrowdStrike returns normal HTTP status codes for auth failures (401/403) -- unlike Slack's always-200-with-`ok:false` quirk, so `connect()` can use the standard `httpx.HTTPStatusError` pattern same as Auth0/GitHub. (4) Devices come back fully hydrated from one endpoint (`GET /devices/combined/devices/v1`, offset-paginated, `resources` key), so no separate query-then-hydrate step is needed for the device entity. | L | not started |

### Sprint 5 -- Agentic Adapter Authoring

Goal: Build the build-time/run-time agent design (drafted for an Orchid Security system-design interview,
2026-08-02) for real -- an agent that drafts new adapters from vendor API docs, with a verification gate
before anything ships. Depended on 4.0 (Auth0, not Okta -- pivoted early, no company email available for
an Okta dev org) shipping first as the concrete comparison target.

| # | Story | Size | Status |
|---|-------|------|--------|
| 5.1 | Build-time agent: given a vendor's API docs, draft a `connect`/`fetch_raw`/`normalize` adapter skeleton against `BaseAdapter` | L | prototyped -- `build-adapter-from-docs` skill, proven against Slack 2026-08-05 |
| 5.2 | Verification layer: generated adapter must pass the Sprint 4.4 contract test suite + mocked-data tests before it's eligible to ship | M | prototyped -- Slack run passed lint + contract + unit + full regression, one retry allowed on failure |
| 5.3 | Human-review gate: generated adapter sits in a draft/PR state, never auto-merged, until a person approves | S | prototyped -- skill hard-stops before commit/PR by design, not yet exercised as a repeated habit across many runs |
| 5.4 | Runtime stays deterministic: confirm/document that the agent runs ONLY at authoring time -- no LLM call anywhere in the `execute()` hot path | S | true by construction -- generated adapters are plain code satisfying `BaseAdapter`, same as hand-written ones |
| 5.5 | Drift handling: if a vendor's API changes and an adapter starts failing, the agent proposes a fix, but re-enters the same verification gate (5.2/5.3), not an auto-deploy | M | prototyped -- `diagnose-adapter-drift` skill; not yet run against a real drift scenario (no live failure to diagnose yet) |

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

---

## Process

- New stories enter the backlog first. Promote to a numbered sprint slot during sprint planning.
- One story per GitHub issue. Use `docs/USER_STORY_TEMPLATE.md`.
- Status field on the table reflects branch state, not issue state.
- At sprint end, mark shipped items as ✅ and roll unfinished work into the next sprint.
