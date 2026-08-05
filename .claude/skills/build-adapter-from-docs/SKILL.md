# Build Adapter From Docs

Drafts a COMPLETE, WORKING adapter (real `connect`/`fetch_raw`/`normalize` logic, not placeholder
stubs) from a vendor's real API documentation, then runs it through the verification layer before
handing it off for human review. This is the Sprint 5 "agentic adapter authoring" capability
(`docs/AGENTIC_ADAPTER_DESIGN.md`) — the build-time half of the design. Runtime stays fully
deterministic; nothing here runs at sync time.

Unlike `add-adapter` (which scaffolds structure with TODO stubs for a human to fill in), this skill
is expected to produce adapter code that actually works, because a human isn't filling in the logic
afterward — verification has to catch what a human review would otherwise catch first.

**Precedents to pattern-match against**: `app/adapters/auth0/` (built by a human, hand-guided,
2026-08-04) and `app/adapters/slack/` (drafted by an agent with real autonomy, 2026-08-05, following
this exact process for the first time). Read both before drafting a new one — they show what "real,
defensible decisions" looks like versus "TODO, fill this in."

## Arguments

- `vendor` — adapter name, lowercase snake_case (e.g. "stripe", "linear")
- `docs_url` — a URL to the vendor's API reference for the resource(s) being ingested
- `resources` (optional) — which resource(s) to fetch (e.g. "charges, customers"). If omitted, infer
  the most obviously "asset-like" resource(s) from the docs.

## Steps to Execute

### 1. Read the docs — don't guess

Fetch `docs_url`. If it 404s, redirects somewhere unhelpful, or the content doesn't actually describe
request/response shapes, **stop and ask for a better URL or a pasted spec** — per
`AGENTIC_ADAPTER_DESIGN.md`'s resolved decision #2, don't draft against docs you never actually read.

Extract, concretely:
- Auth mechanism (bearer token? API key header? OAuth2 client-credentials? something else?)
- Pagination shape (cursor in a header? cursor in the response body? page number? offset? none?)
- The exact field names in a representative response object
- Rate limit signaling (headers? error codes?)
- Any vendor quirk that breaks a framework assumption (e.g. Slack returning HTTP 200 with
  `{"ok": false}` on auth failure instead of a real 401 — read the actual documented error shapes,
  not just the happy path)

### 2. Read the existing framework and adapters first

```bash
cat app/adapters/base.py           # BaseAdapter contract, error translation
cat app/http/client.py             # existing auth_type / pagination strategies
cat app/adapters/auth0/adapter.py  # example: new auth strategy was needed
cat app/adapters/slack/adapter.py  # example: new pagination strategy was needed
```

### 3. Decide: does this vendor fit existing strategies, or does the framework need extending?

For BOTH auth and pagination, check whether an existing `auth_type` / pagination strategy in
`app/http/client.py` already fits. If yes, use it — do not special-case anything in the adapter that
the shared client already handles generically.

If NO existing strategy fits (a genuinely new auth or pagination shape), **extend the shared
framework** (`AssetHttpClient._setup_auth` / `_get_next_page_params`), the same way Auth0 added
`oauth2_client_credentials` and Slack added `cursor_body`. Do not work around the gap inside the
adapter itself — a real "why extend the shared abstraction instead of special-casing" decision is
exactly the kind of thing this needs to produce, not avoid.

### 4. Draft the adapter — real logic, not TODOs

Create `app/adapters/<vendor>/{__init__.py,config.py,adapter.py}`:
- `<Vendor>Config(AdapterConfig)` — only add fields for things that are genuinely vendor-specific
  (not auth, which flows through `auth_type`/`auth_config` generically)
- `connect()` — one cheap real call that proves auth actually works; translate the vendor's actual
  documented failure shape into `AuthenticationError` (check status code AND body, per step 1)
- `fetch_raw()` — implement the real fetch, including any multi-resource batching decision (does
  fetching resource B require resource A first? is there a batch endpoint or is per-item N+1
  unavoidable given the vendor's actual API shape — state which, and why)
- `normalize()` — map to `NormalizedAsset`, with fallbacks for any field the docs show as optional
  or vendor-configurable; required fields (`asset_id`, `customer_id`, `name`, `last_seen`) must
  either have a real fallback or the record should fail loudly (per Story 2 — no silent drops)

### 5. Register + sample config

- Add to `ADAPTER_REGISTRY` in `app/adapters/factory.py` AND `SUPPORTED_ADAPTERS` in
  `app/adapters/registry.py`
- Add `configs/<vendor>_sample.json`, secrets via `VAR:` indirection, never real values

### 6. Write tests — TWO tiers, not one

- **Unit tier** (`app/tests/adapters/test_<vendor>_adapter.py`): mocks the adapter's own
  `client.request()`/`paginated_get()`. Fast, tests business logic in isolation -- connect
  success/failure, fetch_raw's actual batching/pagination behavior (assert call counts where
  that's the point, like Auth0's and Slack's N+1-avoidance assertions), normalize on both a rich
  and a deliberately sparse input.
- **Mock-endpoint tier** (`app/tests/adapters/test_<vendor>_adapter_mock_endpoints.py`) --
  REQUIRED, not optional, when there's no live vendor account (the normal case: most vendors
  aren't as easy to sign up for as Auth0/Slack were -- see CrowdStrike, which needs a form + ~24hr
  wait + real sensor deployment just to get device data). Uses `respx` to mock HTTP at the
  transport layer, with response bodies shaped exactly like the vendor's documented fields, so
  `AssetHttpClient`'s REAL request/pagination/auth code actually runs -- not just the adapter's
  business logic. This is the tier that would have caught the Auth0 URL-concatenation bug even
  without a live tenant. Pattern: `app/tests/adapters/test_crowdstrike_adapter_mock_endpoints.py`.
- Add `<vendor>` entries to `MINIMAL_CONFIGS` and `SAMPLE_RAW_DATA` in
  `app/tests/contract/test_adapter_contract.py`

### 7. Run the verification layer

```bash
black app/adapters/<vendor>/ app/tests/adapters/test_<vendor>_adapter*.py
isort app/adapters/<vendor>/ app/tests/adapters/test_<vendor>_adapter*.py
flake8 app/adapters/<vendor>/ app/tests/adapters/test_<vendor>_adapter*.py
pytest app/tests/adapters/test_<vendor>_adapter*.py app/tests/contract/test_adapter_contract.py -v
pytest app/tests/ -q   # full regression -- confirm nothing else broke
```

Report both what mock-endpoint tests proved (realistic-shaped data is handled correctly) and what
they didn't (whether the vendor's real API actually returns that shape) -- don't blur the two.

### 8. One retry on failure, then stop

Per `AGENTIC_ADAPTER_DESIGN.md` decision #3: if verification fails, read the actual failure output,
fix it, and run step 7 again — **once**. If it still fails after that one retry, STOP. Do not keep
looping. Report exactly what's failing and why, for a human to triage.

### 9. Hand off for human review — never commit or open a PR automatically

Per the design doc: a generated adapter gets exactly the same review bar as a human-written one.
Report what was built, the real decisions made (auth/pagination strategy chosen or added and why,
any N+1-vs-batch tradeoff, any vendor quirk that broke a framework assumption), and verification
results. Branch/commit/PR only happen after a human says to proceed — same as `docs/GITHUB_WORKFLOW.md`
for every other change in this repo.

## What this skill is NOT

- Not a way to skip reading the docs — step 1 is not optional.
- Not a way to skip understanding the existing framework — step 2/3 exist specifically so this
  doesn't reinvent an auth or pagination strategy that already exists.
- Not autonomous past verification — step 9 is a hard stop, always.
