# Bug Report Template

Use this template when filing a bug as a GitHub issue.

For automated bug creation, use the `orqestra-create-bug` skill -- it produces a more thorough structured report with severity assessment and linked fix sub-tasks. This template is the manual / lightweight version.

---

## How to use

1. Open a new GitHub issue.
2. Paste the structure below.
3. Fill in each section. Reproduction steps are mandatory -- a bug without repro is a question.
4. Add labels: `bug`, severity (`sev-1`, `sev-2`, `sev-3`), area (`adapter`, `api`, `frontend`, `infra`).

---

## Template

```markdown
## Summary

[One sentence: what's broken and where.]

## Severity

- [ ] **sev-1** -- production down, data loss, security exposure
- [ ] **sev-2** -- core feature broken, no workaround
- [ ] **sev-3** -- minor / cosmetic / has a workaround

## Environment

- Branch / commit: [SHA]
- Deployment: [docker compose prod / dev / scaling-test / local]
- Adapter (if applicable): [github / aws / coingecko / ...]
- Browser (if frontend): [Chrome 120 / Firefox 122 / ...]
- OS: [Windows 11 / macOS 14 / Ubuntu 22.04]

## Steps to Reproduce

1. [Exact step]
2. [Exact step]
3. [Exact step]

## Expected Result

[What should happen.]

## Actual Result

[What happens instead. Include error messages, stack traces, screenshots.]

## Affected Components

[Which files / modules / endpoints are involved? Cite `app/...` paths.]

- `app/services/sync_engine.py`
- `app/storage/sync_history.py`
- ...

## Suspected Root Cause (optional)

[If you have a hypothesis, share it. Don't speculate -- mark as guess.]

## Fix Sub-Tasks

- [ ] Reproduce locally
- [ ] Add a failing test that captures the bug
- [ ] Implement fix
- [ ] Confirm test passes
- [ ] Manual verification in [environment]
- [ ] Update docs / changelog if user-facing

## Workaround

[Anything users can do until this is fixed. "None" is a valid answer.]

## Logs / Artifacts

```
[Paste relevant logs. Trim to the failure window. Redact secrets.]
```

## Links

- Related: #
- PR: #
```

---

## Example (filled in)

```markdown
## Summary

CoinGecko adapter sync fails with HTTP 429 after ~12 minutes when running the
4-worker scaling test, leaving sync_history entries in `STARTED` state.

## Severity

- [x] **sev-2** -- core feature broken, no workaround

## Environment

- Branch / commit: main @ c1ef0c8
- Deployment: docker compose -f docker-compose.yml -f docker-compose.scaling-test.yml up
- Adapter: coingecko
- OS: Windows 11

## Steps to Reproduce

1. Start scaling-test compose stack
2. `python scripts/setup_scaling_test.py`
3. `python scripts/trigger_all_syncs.py` (triggers 40 instances)
4. Wait ~12 minutes
5. Check Sync History tab in dashboard

## Expected Result

All coingecko instances complete successfully or fail with a clean error +
`sync_history.status = "FAILED"`.

## Actual Result

~6 of 8 coingecko instances stay in `status="STARTED"` indefinitely.
Worker logs show `httpx.HTTPStatusError: 429 Too Many Requests`.
The exception escapes the task without updating sync_history.

## Affected Components

- `app/adapters/coingecko/adapter.py` (no retry on 429)
- `app/services/sync_engine.py` (exception handling around `adapter.execute()`)
- `app/storage/sync_history.py` (status not updated on uncaught exception)

## Suspected Root Cause (guess)

The sync_engine's try/except wraps `adapter.execute()` but only catches
`Exception`, not `BaseException`. CoinGecko's free tier rate-limits at
~30 req/min, and 8 instances burning through pages exceeds that.

## Fix Sub-Tasks

- [x] Reproduce locally with scaling-test
- [ ] Add failing integration test (`test_sync_records_failure_on_429`)
- [ ] Add retry-with-backoff for 429 in `AssetHttpClient`
- [ ] Ensure `sync_history.status = "FAILED"` on uncaught exceptions
- [ ] Verify in scaling-test that all instances reach a terminal state

## Workaround

Reduce coingecko instances to 1 in `setup_scaling_test.py`.

## Logs

```
[2026-05-07 14:32:11,427] ERROR celery.worker: ...
httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.coingecko.com/api/v3/coins/markets'
```

## Links

- Related: #N (sync history reliability)
```

---

## See also

- `docs/USER_STORY_TEMPLATE.md` -- for new features
- `docs/PROFESSIONAL_WORKFLOW.md` -- sprint flow context
- `orqestra-create-bug` skill -- automated alternative
