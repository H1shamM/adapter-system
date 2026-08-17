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
- Adapter-specific unit tests against mocked/recorded vendor responses (mocking the adapter's own
  `client.request()`/`paginated_get()` -- fast, tests business logic in isolation)
- **Mock-ENDPOINT tests (resolved 2026-08-06) -- a required second tier, not optional.** Unit tests
  that mock the adapter's own methods never exercise `AssetHttpClient`'s actual code: URL
  construction, the retry loop, the pagination strategy's real parsing logic. That's exactly where
  real bugs lived during the Auth0 build (the URL-concatenation bug, the `"a" or "b" in x`
  operator-precedence bug) -- bugs a method-mocked unit test cannot catch by construction, because
  it bypasses the code where they live. Mock-endpoint tests instead mock HTTP at the *transport*
  layer (`respx`, added to `requirements-dev.txt`), with response bodies shaped exactly like the
  vendor's real documented fields, so the adapter's real request/pagination/auth code actually runs
  against them. **This is the standard answer to "we can't sign up for every vendor we build an
  adapter for"** -- CrowdStrike's real trial needs a form + ~24hr wait + actual sensor deployment to
  get real device data (a much heavier ask than Auth0's instant dev-tenant signup or Slack's free
  workspace), so mock-endpoint tests are what verification relies on when a live account isn't
  practical. See `app/tests/adapters/test_crowdstrike_adapter_mock_endpoints.py` for the pattern.
- Schema completeness check: does `normalize()` populate every REQUIRED `NormalizedAsset` field
  (`asset_id`, `customer_id`, `name`) for realistic inputs — gate on this specifically, not just
  "tests pass". (The Axonius lesson: missing id/name breaks correlation downstream — see
  `axonius_stories_bank.md` Story 2. Verification should catch this before it ships, not after a
  customer's device/user count looks wrong.)
- `black` / `isort` / `flake8` + full regression suite (see both skills for the exact commands)

**Honesty boundary, still true even with mock-endpoint tests**: this proves the adapter handles
realistic-*shaped* data correctly. It does not prove the vendor's real API actually returns that
shape -- only a live account (like Auth0's) closes that gap. Say both things if asked, not just the
reassuring half.

### Human review gate

Generated (or fixed) adapter lands as a normal GitHub PR (`docs/GITHUB_WORKFLOW.md`), never
auto-merged. A person reviews the diff exactly like a human-authored adapter PR.

## Trigger model (resolved 2026-08-05; Path 1 detection built 2026-08-17) — how DIAGNOSE actually gets invoked

Two real paths, not one:

1. **Automated, health-metric-driven.** Built via a Celery beat watcher, not Prometheus/Alertmanager
   (that stack -- Sprint 3.1/3.5 -- doesn't exist in this repo at all; building it first would have
   been unrelated scope creep). `check_repeatedly_failing_adapters` (`app/tasks/scheduler.py`, every
   15 min) polls `sync_history` via `SyncHistoryStore.last_n_statuses()` for each enabled adapter
   instance; when the last `FAILURE_STREAK_THRESHOLD` (3) finished syncs were all `FAILED`, it opens
   a labeled (`adapter-drift`) GitHub issue via `GitHubIssueClient`
   (`app/integrations/github.py`) with the failing sync_ids/timestamps/errors attached, deduped
   against any already-open issue for that adapter. This is the majority-case detection mechanism at
   scale (a human can't watch 100 adapters) -- **but detection and invocation are two different
   things, see below.**
2. **Human-reported.** A customer reports an issue with fetched assets (data looks wrong, incomplete,
   or stale) even though the sync technically "succeeded" — exactly the Story 2 failure mode, where
   health metrics alone don't catch it because nothing errored, the data was just silently wrong. In
   this case a human explicitly triggers DIAGNOSE with the report as the starting evidence.

**What's still not automated**: the opened issue is not yet wired to actually invoke
`diagnose-adapter-drift`. Closing that requires registering a `RemoteTrigger` webhook routine
subscribed to that issue label -- a real, deliberately deferred step (see Execution model below and
the backlog in `docs/PROGRESS.md`). Until then, path 1 automates *detection and evidence-gathering*;
a human still reads the issue and runs the skill (or triggers it manually) -- one real step closer to
the full loop, not the full loop itself.

## Execution model: Skill vs. Agent (resolved 2026-08-05)

**Skill = the reusable procedure. Agent = who runs the procedure when no human is present to invoke
it.** These aren't competing choices — they answer different questions.

- **Human-initiated BUILD** ("go build a Stripe adapter") and **human-reported DIAGNOSE** (a customer
  flagged an issue) both already have a human present and driving. A **Skill** is correct here — it
  runs inline in that person's session, they watch each decision happen, same shape as the Slack build.
- **The automated trigger path (Trigger model, path 1)** has no human present by construction — a
  metric crossed a threshold, nobody typed anything. A Skill can't fire itself; it only runs inside an
  active conversation. This needs an **Agent** (Claude Code's Agent tool: a separate instance, its own
  context, can run in the background, reports back when something needs review) that the watcher
  launches, and that agent *invokes* `diagnose-adapter-drift` — and, if a fix is needed,
  `build-adapter-from-docs`'s repair path — on its own.
- **Building at scale** ("draft adapters for these 10 vendors") is the same shape as the automated
  path even though a human initiated it: instead of 10 sequential live sessions, it becomes 10
  parallel background Agent runs, each invoking `build-adapter-from-docs` once.

**What does NOT change based on this split**: the human-review gate. A background Agent invoking these
skills stops at exactly the same place a human invoking them inline would — verification passes, a PR
is opened, and a person approves before anything merges or deploys. Moving from Skill-invoked-by-human
to Agent-invoked-by-watcher changes *who dials the phone*, never *who's allowed to hang up the call*.

## What this is NOT

- Not an LLM call inside `fetch_raw()`/`normalize()` at sync time. Ever.
- Not auto-merge, ever, for either a new adapter or a fix to an existing one.
- Not a replacement for the contract test suite (4.4) -- it's a consumer of it.
- Not (yet) a fully autonomous background watcher -- detection (the drift watcher, above) is real and
  running, but it stops at opening a GitHub issue; nothing yet fires `diagnose-adapter-drift`
  automatically off that issue (needs the deferred `RemoteTrigger` registration). Today, both skills
  are still invoked by a human asking, though for path 1 that human now starts from a pre-gathered
  issue instead of digging through `sync_history` themselves.

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
5. **Execution model**: Skills for anything human-initiated (inline, watched); a background Agent for
   anything triggered without a human present (the automated diagnose path, and at-scale parallel
   builds) -- and that Agent invokes the same Skills rather than duplicating their logic. The
   human-review gate is identical either way (see Execution model section above).

## Proof it works, not just documented

Validated 2026-08-05 by actually using `build-adapter-from-docs` (not hand-holding like Auth0) to draft
the Slack adapter (`app/adapters/slack/`) from real Slack API documentation — including extending the
shared `AssetHttpClient` with a new `cursor_body` pagination strategy Slack genuinely required, and
handling a real vendor quirk (Slack returns HTTP 200 even on auth failure). Passed the full verification
layer: lint, unit tests, contract test suite, full regression (129 passing). See PR #22 (adapter) /
PR #23 (skills) / issue #20.
`diagnose-adapter-drift` exists but hasn't diagnosed a real failure yet -- no live drift scenario so far.

## Links

- Skills: `.claude/skills/build-adapter-from-docs/SKILL.md`, `.claude/skills/diagnose-adapter-drift/SKILL.md`
- Depends on: Sprint 4.0 (Auth0 adapter, issue #17) shipping first as the manual-build comparison point
- Depends on: Sprint 4.4 (adapter contract test suite) existing, since the verification layer consumes it
- Depends on: Sprint 3.5 (Prometheus alert rules, not yet built) for the automated trigger path
- Interview material: `axonius_stories_bank.md` Story 7 (design walkthrough) and Story 8 (the real Auth0
  build), `adapter_system_defend_prep.md`
