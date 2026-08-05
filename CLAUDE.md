# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A pluggable data ingestion platform using hexagonal (Ports & Adapters) architecture. External APIs (GitHub, AWS, CoinGecko, etc.) are abstracted behind a common adapter interface, normalized into a unified `NormalizedAsset` schema, and stored in MongoDB. Sync tasks run asynchronously via Celery with RabbitMQ. Supports multi-instance adapters with horizontal scaling (4 workers x 10 concurrency = 40 simultaneous syncs).

## Commands

### Backend
```bash
pip install -r requirements.txt          # Install Python deps
uvicorn app.api.main:app --port 8000     # Run API server
celery -A app.tasks.core worker -Q sync_queue  # Run Celery worker
celery -A app.tasks.core beat            # Run beat scheduler
python runner.py --adapter <type> --config <path>  # CLI sync (no Celery)
pytest                                   # Run all tests
pytest app/tests/unit/                   # Unit tests only
pytest app/tests/integration/            # Integration tests (needs MongoDB/RabbitMQ)
```

### Frontend (ui/)
```bash
cd ui && npm install    # Install deps
npm run dev             # Vite dev server (port 5173)
npm run build           # TypeScript check + production build
npm run lint            # ESLint
```

### Docker
```bash
docker compose up --build                                    # Production (API + worker + beat + MongoDB + RabbitMQ)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up  # Dev with hot reload
docker compose -f docker-compose.yml -f docker-compose.scaling-test.yml up  # 4-worker scaling test
```

### Scaling Test
```bash
python scripts/setup_scaling_test.py     # Create 40 test adapter instances
python scripts/trigger_all_syncs.py      # Trigger all instances
python scripts/monitor_scaling.py        # Real-time monitoring
```

## Architecture

**Core data flow:** API request --> Celery task --> `run_adapter_sync()` --> `build_adapter()` --> adapter.`execute()` (connect --> fetch_raw --> normalize) --> MongoDB storage

**Key abstractions:**
- `BaseAdapter` (`app/adapters/base.py`): ABC with three methods: `connect()`, `fetch_raw()`, `normalize()`. The `execute()` template method chains them.
- `AdapterConfig` extends `HttpClientConfig` (Pydantic) -- each adapter type can define its own config subclass (e.g., `GitHubConfig`, `AWSConfig`).
- `ADAPTER_REGISTRY` in `app/adapters/factory.py`: maps type strings to `(AdapterClass, ConfigClass)` tuples. `build_adapter()` instantiates from this registry.
- `NormalizedAsset` (`app/models/assets.py`): unified schema all adapters normalize into.
- `AssetHttpClient` (`app/http/client.py`): shared async httpx client with auth, pagination, and retry.

**Adding a new adapter:** Create a directory under `app/adapters/`, implement `BaseAdapter` subclass, optionally create a config subclass, register in `ADAPTER_REGISTRY` and `SUPPORTED_ADAPTERS`.

**Storage layer** (`app/storage/`): MongoDB DAOs -- `AdapterConfigStore`, `AssetStore`, `SyncHistoryStore`. Adapter configs are keyed by `adapter_id` (supports multiple instances of the same adapter type).

**API layer** (`app/api/`): FastAPI routes under `/adapters`, `/assets`, `/syncs`, `/health`, `/auth`. JWT auth via `app/auth/`. Prometheus metrics at `/metrics`. All prefixed with `/api/v1`.

**Task layer** (`app/tasks/`): Celery app in `core.py`, beat scheduler in `scheduler.py`. Tasks routed to `sync_queue`.

**Frontend** (`ui/src/`): React + TypeScript + Vite. Tabbed dashboard (Overview, Adapters, Assets, Sync History). API client in `ui/src/api/`, components in `ui/src/components/`, hooks in `ui/src/hooks/`.

## Configuration

- Environment variables defined in `.env` / `.env.prod`, loaded via Pydantic `BaseSettings` in `app/config/settings.py`.
- Adapter instance configs stored in MongoDB (keyed by `adapter_id`).
- `pytest.ini`: `asyncio_mode = auto`, test discovery in `app/tests`.
- `pyproject.toml`: black, isort, mypy, coverage config (`line-length = 100`).
- `.flake8`: `max-line-length = 100`, ignores E203/W503 for black compatibility.
- Default login: `admin` / `admin123` (hardcoded demo user in `app/auth/router.py`).

## Professional Engineering Workflow

This repo follows a documented sprint-based engineering process. Read these before non-trivial work:

- `docs/PROFESSIONAL_WORKFLOW.md` -- sprint cycle, architecture discipline, quality gates
- `docs/GITHUB_WORKFLOW.md` -- branching, PR mechanics, `gh` commands
- `docs/PROGRESS.md` -- 4-week sprint roadmap, current focus
- `docs/USER_STORY_TEMPLATE.md` -- structure for new feature issues
- `docs/BUG_REPORT_TEMPLATE.md` -- structure for bug issues

**CI/CD**: GitHub Actions in `.github/workflows/` runs `tests.yml` (pytest + coverage) and `lint.yml` (black, isort, flake8, mypy) on every PR.

**Before pushing**:

```bash
# Backend
black app/ scripts/ runner.py
isort app/ scripts/ runner.py
flake8 app/ scripts/ runner.py
pytest

# Frontend
cd ui && npm run lint && npm run build
```

### Available skills

Use these skills instead of writing scaffolding by hand:

- `add-adapter` -- scaffolds a new adapter (BaseAdapter + config + factory + registry entries) with TODO stubs for a human to fill in. See `.claude/skills/add-adapter/SKILL.md`.
- `add-adapter-tests` -- generates unit + integration tests for an existing adapter. See `.claude/skills/add-adapter-tests/SKILL.md`.
- `build-adapter-from-docs` -- drafts a COMPLETE, working adapter from a vendor's real API docs (real logic, not stubs), then runs it through lint/tests before handing off for human review. The Sprint 5 agentic-authoring capability (`docs/AGENTIC_ADAPTER_DESIGN.md`). See `.claude/skills/build-adapter-from-docs/SKILL.md`.
- `diagnose-adapter-drift` -- investigates a failing adapter, isolates connection/auth/rate-limit/schema layers BEFORE assuming vendor drift, and only if it's genuinely schema drift proposes a minimal fix through the same verification + human-review gate. Never auto-patches production. See `.claude/skills/diagnose-adapter-drift/SKILL.md`.

Personal-account skills (also available):

- `orqestra-create-user-story` -- structured INVEST story for a GitHub issue
- `orqestra-create-bug` -- structured bug report
- `github-pr-workflow` -- end-to-end PR + post-merge issue housekeeping
