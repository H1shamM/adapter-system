# Agentic Adapter Authoring — Design

Status: proposed (Sprint 5). Originated as a system-design answer for an Orchid Security interview
(2026-08-02: "how would you design agent-driven integrations?"), then adopted as real project direction.

## The core idea

Split the system into two planes:

- **Build-time (agentic):** an agent drafts a new adapter — `connect` / `fetch_raw` / `normalize` —
  from a vendor's API docs. This is where creativity, ambiguity, and judgment live, and where an LLM
  earns its keep.
- **Run-time (deterministic):** the generated adapter is plain Python satisfying `BaseAdapter`, same as
  every hand-written adapter today (GitHub, AWS, CoinGecko, ...). No LLM call anywhere in `execute()`.

Why the split matters: a sync pulling real customer data should be fast, cheap, and fully observable —
not a probabilistic call. The agent's job ends the moment a PR is opened; production traffic never
touches an LLM.

## Why this belongs in adapter-system specifically

The architecture already assumes a fixed contract per adapter (`BaseAdapter.execute()` — Template
Method, see `adapter_system_defend_prep.md` #2) and a registry that only needs one new entry per adapter
(`ADAPTER_REGISTRY`, Factory pattern, see #3). That's exactly the shape an agent can target: a
well-defined interface to implement, not an open-ended "build me an integration" prompt.

## Pipeline

```
vendor API docs
      |
      v
[ Build-time agent ]  --drafts-->  connect() / fetch_raw() / normalize()
      |                             (implements BaseAdapter, targets ADAPTER_REGISTRY)
      v
[ Verification layer ]
  - Sprint 4.4 contract test suite (every adapter must satisfy BaseAdapter's behavioral contract)
  - Adapter-specific tests against mocked/recorded vendor responses
  - Schema completeness check: does normalize() populate every REQUIRED NormalizedAsset field
    (asset_id, customer_id, name) for realistic inputs -- gate on this specifically, not just
    "tests pass". (This is the Axonius lesson: missing id/name breaks correlation downstream --
    see axonius_stories_bank.md Story 2. Verification should catch this before it ships, not after
    a customer's asset count looks wrong.)
      |
      v
[ Human review gate ]
  - Generated adapter lands as a normal GitHub PR (docs/GITHUB_WORKFLOW.md), never auto-merged
  - A person reviews the diff exactly like a human-authored adapter PR
      |
      v
[ Merged -> deterministic runtime ]
  - Same Celery sync path as every other adapter (app/services/sync_engine.py)
  - No agent, no LLM call, anywhere in this path
```

## Drift handling (when a vendor's API changes)

If an adapter starts failing (schema drift, endpoint change, auth change), the agent may propose a fix
-- but the fix re-enters the SAME verification + human-review gate above. There is no "agent silently
patches production" path. This mirrors Story 5 (Fetch Failed debugging) -- schema drift is a known,
recurring failure mode; the fix is to make diagnosis+repair faster, not to remove the review step.

## What this is NOT

- Not an LLM call inside `fetch_raw()`/`normalize()` at sync time. Ever.
- Not auto-merge. A generated adapter has exactly the same review bar as a human-written one.
- Not a replacement for the contract test suite (4.4) -- it's a consumer of it.

## Open questions (resolve before implementing Sprint 5 stories)

1. Which model/harness authors the draft (Claude Code against the repo directly, vs. a narrower
   docs-in/code-out agent)?
2. How is "vendor API docs" supplied -- a URL to fetch, a pasted OpenAPI spec, or free text?
3. What does a failed verification loop look like -- does the agent get one automatic retry with the
   failure output before falling to human triage?

## Links

- Depends on: Sprint 4.0 (Auth0 adapter) shipping first, as the concrete comparison target and proof
  that the manual path is well understood before automating it.
- Depends on: Sprint 4.4 (adapter contract test suite) existing, since the verification layer consumes it.
- Interview material: `axonius_stories_bank.md` (system-design answer), `adapter_system_defend_prep.md`.
