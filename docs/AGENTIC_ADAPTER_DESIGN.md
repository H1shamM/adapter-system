# Agentic Adapter Authoring — Design

Status: prototyped (Sprint 5), scaling design in progress. Originated as a system-design answer for an
Orchid Security interview (2026-08-02: "how would you design agent-driven integrations?"), adopted as
real project direction, proven against a real build (Slack, 2026-08-05), now being designed for scale.

## The goal, stated plainly

Get to a workflow where giving a vendor name (or its docs) is enough to get a working, verified,
deployed adapter — and where a broken adapter gets diagnosed and fixed the same way — at a scale
(target: ~100 adapters, with ongoing maintenance) where this is no longer humans hand-writing and
hand-debugging each integration one at a time. The entities that matter most for the intended customer
base: **devices, users, and roles/permissions** — identity/asset-correlation data, not arbitrary API
ingestion in general.

## The core idea

Split the system into two planes:

- **Build-time (agentic):** an agent drafts a new adapter — `connect` / `fetch_raw` / `normalize` —
  from a vendor's API docs, or fixes an existing one that broke. This is where creativity, ambiguity,
  and judgment live, and where an LLM earns its keep.
- **Run-time (deterministic):** the generated adapter is plain Python satisfying `BaseAdapter`, same as
  every hand-written adapter today (GitHub, AWS, Auth0, Slack, ...). No LLM call anywhere in `execute()`.

Why the split matters: a sync pulling real customer data should be fast, cheap, and fully observable —
not a probabilistic call. The agent's job ends the moment a PR is opened; production traffic never
touches an LLM.

## Why this belongs in adapter-system specifically

The architecture already assumes a fixed contract per adapter (`BaseAdapter.execute()` — Template
Method, see `adapter_system_defend_prep.md` #2) and a registry that only needs one new entry per adapter
(`ADAPTER_REGISTRY`, Factory pattern, see #3). That's exactly the shape an agent can target: a
well-defined interface to implement, not an open-ended "build me an integration" prompt.

## The closed loop (build AND maintain, not just build)

```
NEW VENDOR (name or docs)
      |
      v
[ BUILD ] -- drafts adapter, entity-focused: devices, users, roles/permissions
  (.claude/skills/build-adapter-from-docs/)
      |
      v
[ VERIFICATION layer ] -- automated tests (below) + human-in-loop review
      |
      v  (human approves)
[ DEPLOYED ] -- live, used by customers, deterministic runtime only
      |
      v  (breaks in production -- see Trigger model below)
[ DIAGNOSE ] -- isolates the real cause; does NOT assume drift
  (.claude/skills/diagnose-adapter-drift/)
      |
      v  (hands off, not just a report)
[ BUILD ] -- fixes/adjusts the EXISTING adapter (not a rewrite)
      |
      v
[ VERIFICATION layer ] -- same gate, again, no shortcuts for "it's just a fix"
      |
      v  (human approves)
[ DEPLOYED ] -- fixed, back in production
```

The human gate sits specifically at **verification/deployment** — diagnose and the fix itself can run
without a human in the loop moment-to-moment, but nothing ships without passing back through the same
reviewed gate. This was true for the original build path and stays true for the repair path; there is
no "it's just a small fix" exception.

### Verification layer, concretely

- Sprint 4.4 contract test suite (every adapter must satisfy `BaseAdapter`'s behavioral contract)
- Adapter-specific unit tests against mocked/recorded vendor responses
- Schema completeness check: does `normalize()` populate every REQUIRED `NormalizedAsset` field
  (`asset_id`, `customer_id`, `name`) for realistic inputs — gate on this specifically, not just
  "tests pass". (The Axonius lesson: missing id/name breaks correlation downstream — see
  `axonius_stories_bank.md` Story 2. Verification should catch this before it ships, not after a
  customer's device/user count looks wrong.)
- `black` / `isort` / `flake8` + full regression suite (see both skills for the exact commands)

### Human review gate

Generated (or fixed) adapter lands as a normal GitHub PR (`docs/GITHUB_WORKFLOW.md`), never
auto-merged. A person reviews the diff exactly like a human-authored adapter PR.

## Trigger model (resolved 2026-08-05) — how DIAGNOSE actually gets invoked

Two real paths, not one:

1. **Automated, health-metric-driven.** The system already tracks per-adapter Prometheus metrics
   (`SYNC_SUCCESS`, `SYNC_FAILURES`, `SYNC_ERRORS`, `SYNC_DURATION`, `ASSET_COUNT` — see
   `app/monitoring/metrics.py`), and Sprint 3.5 in `docs/PROGRESS.md` already plans alert rules for
   failure rate. When failure/error rate crosses a threshold for a given adapter, that's the automated
   trigger into DIAGNOSE — this is the majority case at scale (a human can't watch 100 adapters).
2. **Human-reported.** A customer reports an issue with fetched assets (data looks wrong, incomplete,
   or stale) even though the sync technically "succeeded" — exactly the Story 2 failure mode, where
   health metrics alone don't catch it because nothing errored, the data was just silently wrong. In
   this case a human explicitly triggers DIAGNOSE with the report as the starting evidence.

**Open implementation question (not yet resolved):** path 1 requires something that actually watches
metrics/alerts and invokes DIAGNOSE without a human typing a command — a Celery beat job polling
`sync_history` for repeated failures, or a Prometheus Alertmanager webhook, are the two obvious
candidates. Either way, this is a background-orchestration problem, not something a Skill (which runs
inline, in a live conversation) solves alone — Skills are the right *procedure* for BUILD and DIAGNOSE
themselves; something else needs to *call* them automatically for path 1. Resolve this before treating
Sprint 5.5 (drift handling) as fully done at scale.

## What this is NOT

- Not an LLM call inside `fetch_raw()`/`normalize()` at sync time. Ever.
- Not auto-merge, ever, for either a new adapter or a fix to an existing one.
- Not a replacement for the contract test suite (4.4) -- it's a consumer of it.
- Not (yet) a fully autonomous background watcher -- the automated trigger path above is designed but
  not implemented; today both skills are invoked by a human asking.

## Decisions (resolved 2026-08-05)

1. **Harness**: Claude Code, working directly against the repo, human-in-the-loop for the final gate --
   same shape as the Auth0 build (Sprint 4.0). Not a narrower docs-in/code-out agent; the repo's own
   conventions (`BaseAdapter` contract, existing adapters as examples, `CLAUDE.md`) are part of what
   makes the draft good.
2. **Vendor docs input**: primarily a URL for the agent to fetch directly. If it can't find or access
   usable docs there, fall back to a pasted spec/free-text description rather than guessing -- don't
   draft against docs never actually read. (Validated: this is exactly how the Slack adapter was built.)
3. **Failed verification**: one automatic retry, with the failure output (test failures, schema gaps)
   fed back so the agent can self-correct once. Second failure -> stop, hand off to human triage. No
   infinite retry loop, no silent failure. Same rule applies to DIAGNOSE's fix attempts.
4. **Trigger model**: hybrid -- automated (health-metric threshold) for the majority case at scale,
   human-reported for silent-failure cases metrics can't see (see Trigger model section above).

## Proof it works, not just documented

Validated 2026-08-05 by actually using `build-adapter-from-docs` (not hand-holding like Auth0) to draft
the Slack adapter (`app/adapters/slack/`) from real Slack API documentation — including extending the
shared `AssetHttpClient` with a new `cursor_body` pagination strategy Slack genuinely required, and
handling a real vendor quirk (Slack returns HTTP 200 even on auth failure). Passed the full verification
layer: lint, unit tests, contract test suite, full regression (129 passing). See PR #21 / issue #20.
`diagnose-adapter-drift` exists but hasn't diagnosed a real failure yet -- no live drift scenario so far.

## Links

- Skills: `.claude/skills/build-adapter-from-docs/SKILL.md`, `.claude/skills/diagnose-adapter-drift/SKILL.md`
- Depends on: Sprint 4.0 (Auth0 adapter, issue #17) shipping first as the manual-build comparison point
- Depends on: Sprint 4.4 (adapter contract test suite) existing, since the verification layer consumes it
- Depends on: Sprint 3.5 (Prometheus alert rules, not yet built) for the automated trigger path
- Interview material: `axonius_stories_bank.md` Story 7 (design walkthrough) and Story 8 (the real Auth0
  build), `adapter_system_defend_prep.md`
