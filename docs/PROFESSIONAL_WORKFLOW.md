# Professional Engineering Workflow

This document describes the engineering practices used to develop and maintain the adapter-system. It applies to all backend (FastAPI / Celery / MongoDB) and frontend (React / Vite) work in this repo.

The intent is consistency, not bureaucracy: every change is tracked from issue --> branch --> PR --> CI --> merge, with quality gates that scale with risk.

---

## 1. Sprint Workflow

We organize work in **2-week sprints**. Each sprint has 3-6 user stories pulled from `docs/PROGRESS.md`.

### Sprint cycle

1. **Plan** -- Pick stories from `docs/PROGRESS.md`. Convert each into a GitHub issue using the `USER_STORY_TEMPLATE.md` format.
2. **Implement** -- One branch per issue. Small, focused PRs.
3. **Review** -- Self-review then PR. CI must pass before merge.
4. **Ship** -- Merge to `main`. Update `docs/PROGRESS.md` with what shipped.
5. **Retro** -- At sprint end, note what worked / what to change in the next sprint.

### Story sizing

- **XS** (~1 hour) -- Tiny config change, single-file fix
- **S** (~half day) -- One adapter feature, one new endpoint, one UI component
- **M** (1-2 days) -- New adapter, multi-component feature, schema migration
- **L** (3-5 days) -- Cross-cutting infra change (e.g., new task queue strategy, auth overhaul)

If a story is **L**, split it before starting.

---

## 2. Architecture Discipline

The adapter-system is a **hexagonal (Ports & Adapters)** architecture. Every change must respect the layering:

```
API / CLI / Beat scheduler   <- entry points
        |
   Sync engine (services/)   <- orchestration
        |
   Adapter Factory           <- builds adapters from registry
        |
   BaseAdapter subclasses    <- connect / fetch_raw / normalize
        |
   Storage DAOs              <- MongoDB access only here
```

### Rules

- **Don't bypass the adapter contract.** All external API calls happen inside an adapter. The sync engine never calls `httpx` directly.
- **Don't bypass the storage layer.** API routes never touch MongoDB collections directly -- always go through `AdapterConfigStore` / `AssetStore` / `SyncHistoryStore`.
- **Configs are Pydantic.** All adapter config classes extend `AdapterConfig`. No raw dicts in business logic.
- **Tasks stay thin.** Celery task functions in `app/tasks/` should be small wrappers that delegate to `app/services/sync_engine.py`.
- **Frontend uses the typed API client.** Components import from `ui/src/api/`, never `fetch` raw URLs.

If a change requires breaking these rules, it deserves an architectural discussion in the issue *before* coding.

See `CLAUDE.md` for the canonical reference of abstractions and `design.md` for the high-level diagram.

---

## 3. Adding a New Adapter

This is the most common kind of change. Use the existing skills:

```

/add-adapter <name>                          # Scaffolds the adapter directory + factory registration (TODO stubs)
/add-adapter-tests <name>                    # Generates unit + integration tests
/build-adapter-from-docs <name> <docs_url>   # Drafts a COMPLETE working adapter from real vendor docs
/diagnose-adapter-drift <name>               # Investigates a failing adapter, fixes ONLY if it's real drift
```

The skills enforce the right patterns (async httpx client, NormalizedAsset output, factory registration). Read `.claude/skills/add-adapter/SKILL.md`, `.claude/skills/add-adapter-tests/SKILL.md`, `.claude/skills/build-adapter-from-docs/SKILL.md`, and `.claude/skills/diagnose-adapter-drift/SKILL.md` for the full procedures.

### Adapter PR checklist

- [ ] `connect()`, `fetch_raw()`, `normalize()` implemented
- [ ] Config class extends `AdapterConfig`
- [ ] Registered in `app/adapters/factory.py` AND `app/adapters/registry.py`
- [ ] Unit tests with mocked HTTP
- [ ] Integration test that runs end-to-end against a real (or recorded) response
- [ ] Sample config in `configs/<adapter>_sample.json`
- [ ] README in `app/adapters/<adapter>/README.md`

---

## 4. Quality Gates

Every PR must pass these gates before merge.

### Backend

| Gate            | Tool          | Required |
|-----------------|---------------|----------|
| Format          | `black`       | yes      |
| Imports         | `isort`       | yes      |
| Lint            | `flake8`      | yes      |
| Type check      | `mypy`        | best-effort initially (continue-on-error in CI) |
| Unit tests      | `pytest app/tests/unit/`         | yes |
| Integration     | `pytest app/tests/integration/`  | yes (when MongoDB/RabbitMQ available) |
| Coverage        | `pytest --cov=app`                | report only initially; target 70%+ |

### Frontend

| Gate            | Tool          | Required |
|-----------------|---------------|----------|
| Type check      | `tsc --noEmit` (via `npm run build`) | yes |
| Lint            | `npm run lint`                       | yes |
| Build           | `npm run build`                      | yes |

### Run locally before pushing

```bash
# Backend
black app/
isort app/
flake8 app/
pytest

# Frontend
cd ui
npm run lint
npm run build
```

CI runs the same checks (see `.github/workflows/`). If CI fails, fix the underlying issue -- don't disable hooks or skip tests.

---

## 5. Issue --> PR --> Merge Flow

Detailed git mechanics live in `docs/GITHUB_WORKFLOW.md`. The shape:

1. **Issue first.** No code without an issue. Use templates:
   - User story --> `docs/USER_STORY_TEMPLATE.md`
   - Bug --> `docs/BUG_REPORT_TEMPLATE.md`
2. **Branch from `main`** with a descriptive prefix (`feature/`, `bugfix/`, `hotfix/`, `refactor/`).
3. **Small PRs.** < 400 lines diff is the target. If it's bigger, split it.
4. **Self-review** before requesting review. Read your own diff.
5. **CI green** -- never merge red.
6. **Squash merge** to `main` with a clean conventional-commit message.
7. **Close the issue** automatically via `Closes #N` in the PR body.

---

## 6. Skills Available in This Repo

| Skill | Purpose |
|-------|---------|
| `add-adapter` | Scaffold a new adapter (directory, BaseAdapter subclass, config, registry entries) with TODO stubs |
| `add-adapter-tests` | Generate unit + integration tests for an existing adapter |
| `build-adapter-from-docs` | Draft a complete, working adapter from real vendor API docs, verify, hand off for review |
| `diagnose-adapter-drift` | Investigate a failing adapter, isolate the real cause, fix ONLY if it's genuine schema drift, through the same verification gate |

Personal-account skills used when relevant:

| Skill | Purpose |
|-------|---------|
| `orqestra-create-user-story` | Build a structured INVEST user story (acceptance criteria, BE/FE/QA sub-tasks) |
| `orqestra-create-bug` | Create a structured bug report (repro, expected/actual, severity, fix sub-tasks) |
| `github-pr-workflow` | End-to-end GitHub PR + post-merge issue housekeeping |

Use the skills. They enforce the patterns documented above so you don't have to remember them.

---

## 7. References

- `CLAUDE.md` -- canonical architecture reference
- `README.md` -- public-facing project description
- `DEMO.md` -- 5-minute demo script
- `docs/PROGRESS.md` -- current sprint roadmap
- `docs/GITHUB_WORKFLOW.md` -- git/PR mechanics
- `design.md` -- high-level system diagram
