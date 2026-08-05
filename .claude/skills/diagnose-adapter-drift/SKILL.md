# Diagnose Adapter Drift

Investigates a failing adapter (recurring "Fetch Failed" status, a sync error, or a report that an
integration "just stopped working"), determines whether it's actually vendor-side drift or something
else entirely, and — only if it genuinely is drift — proposes a minimal fix that re-enters the SAME
verification + human-review gate as `build-adapter-from-docs`. This is Sprint 5.5 in
`docs/AGENTIC_ADAPTER_DESIGN.md`: **there is no "agent silently patches production" path, ever.**

The real-world analog this codifies: Story 5 in `axonius_stories_bank.md` ("Fetch Failed" debugging) —
root causes ran the full range (expired auth, vendor API down, unparseable responses, vendor schema
changes), and the actual skill was isolating WHICH layer broke before touching anything. This skill
exists to do that isolation systematically, not to jump straight to "the API must have changed."

## Arguments

- `adapter` — adapter type (e.g. "auth0", "slack")
- `evidence` (optional) — the actual error/exception seen, or a description of the symptom. If not
  given, look for recent failed syncs first (see step 1).

## Steps to Execute

### 1. Get real evidence before theorizing

If `evidence` wasn't given, look for it:
```python
# via SyncHistoryStore -- recent failures for this adapter, with error field populated
```
If there's no evidence at all (no error message, no failed sync record, just "it seems off"), **say so
and stop** — don't invent a plausible-sounding root cause without something real to point at.

### 2. Isolate the layer BEFORE assuming it's drift — this is the step most likely to get skipped

Read the actual error and classify it, same as Story 5's real triage:
- **Connection-layer** (timeout, DNS, connection refused) — likely vendor outage or network issue,
  not drift. Report this and stop; there's no code fix for a vendor being down.
- **Auth-layer** (401/403, or a vendor-specific "invalid_auth"-shaped body per that adapter's own
  `connect()` logic) — likely expired/revoked credentials, not drift. Report this and stop; rotating
  a secret isn't a code change.
- **Rate-limit** (429, or the vendor's documented rate-limit error shape) — not drift; check whether
  the adapter already backs off correctly (see `app/http/client.py` retry logic) and whether the
  volume genuinely exceeds the vendor's limit.
- **Parse/schema layer** (KeyError, ValidationError from `NormalizedAsset`, unexpected response
  shape) — THIS is the one that's actually drift. Proceed to step 3 only for this case.

If it's not schema/parse-layer, your job is done: report which layer broke and why it's not a code
problem, the same way Story 1's lesson was "recognizing the constraint was external, not mine to fix."

### 3. Confirm it's really drift, not a pre-existing bug

Check: did this adapter's tests already cover the field/shape that's now failing? If a test used
placeholder/simplified mock data that never matched the vendor's real shape, this might be a
pre-existing gap in test coverage, not something that changed on the vendor's side. Say which one it
looks like.

### 4. Fetch CURRENT vendor docs and diff against what the code assumes

Re-fetch the same docs URL(s) used when the adapter was originally built (check the adapter's
`README.md` if one exists, e.g. `app/adapters/<adapter>/README.md`). Compare current documented
field names / endpoint paths / response shape against what `fetch_raw()`/`normalize()` currently
expect. State exactly what changed — field renamed, endpoint moved, a field that was always-present
is now optional, etc.

### 5. Propose the MINIMAL fix

Patch only what actually drifted. Do not rewrite the adapter. If a field was renamed, update the one
reference; if a new required field appeared, add a defensive `.get()` with a fallback (per the Story 2
lesson — don't silently drop records with a missing required field, fail loudly if there's truly no
reasonable fallback).

### 6. Re-run verification — same as build-adapter-from-docs, same retry limit

```bash
black app/adapters/<adapter>/ app/tests/adapters/test_<adapter>_adapter*.py
isort app/adapters/<adapter>/ app/tests/adapters/test_<adapter>_adapter*.py
flake8 app/adapters/<adapter>/ app/tests/adapters/test_<adapter>_adapter*.py
pytest app/tests/adapters/test_<adapter>_adapter*.py app/tests/contract/test_adapter_contract.py -v
pytest app/tests/ -q
```
If existing tests (either tier -- unit or mock-endpoint) still pass with OLD data that no longer
reflects the vendor's real shape, update the mock data too — a green suite testing the wrong shape
is worse than a red one. If the drift is in the response shape itself, update the mock-endpoint
tier's `respx` responses specifically -- that's the tier that's supposed to catch exactly this.

One retry on verification failure, same as `build-adapter-from-docs`. If it still fails, stop and
report for human triage — do not loop.

### 7. Hand off — never auto-commit, never auto-merge, never auto-deploy

Report: which layer broke (step 2), whether it was really drift (step 3-4), the minimal fix (step 5),
and verification results (step 6). Branch/commit/PR only after a human says to proceed, exactly like
`build-adapter-from-docs` and every other change in this repo (`docs/GITHUB_WORKFLOW.md`).

## What this skill is NOT

- Not a monitoring/alerting system — it's invoked reactively (a human noticed a failure and asked),
  not a background process watching for failures itself.
- Not a way to skip the connection/auth/rate-limit triage in step 2 — most "it's broken" reports are
  NOT drift, and saying so is a valid, complete answer.
- Not autonomous past verification — step 7 is a hard stop, always, same as `build-adapter-from-docs`.
