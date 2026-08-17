---
name: add-adapter-tests
description: Generates unit and contract-suite test coverage for an existing adapter in the adapter-system. Creates test files following the project's real pytest patterns (mocking adapter.client, not raw httpx) plus the respx mock-endpoint tier. Use after creating a new adapter or when test coverage is missing.
argument-hint: <adapter-name>
allowed-tools: Read Write Edit Glob Grep Bash(ls *) Bash(cat *) Bash(pytest *)
---

# Add Adapter Tests

Generates test coverage for an adapter following the project's real testing patterns -- read the
actual test files in step 2 before writing anything; this doc summarizes them but the files are
the source of truth.

## Arguments

- `$0` - Adapter name (e.g., "stripe", "slack") - must already exist in `app/adapters/`

## Steps to Execute

### 1. Verify Adapter Exists

```bash
ls app/adapters/$0/
cat app/adapters/$0/adapter.py
cat app/adapters/$0/config.py
```

If the adapter doesn't exist, tell the user to create it first with `/add-adapter $0` or
`build-adapter-from-docs`.

### 2. Read Existing Test Patterns

Tests for adapters live flat under `app/tests/adapters/` -- there is no `unit/adapters/` or
`integration/adapters/` split for adapter-level tests.

```bash
ls app/tests/adapters/

# Read a clean, current example (connect/fetch_raw/normalize, no pagination)
cat app/tests/adapters/test_slack_adapter.py

# Read one with OAuth2 + pagination
cat app/tests/adapters/test_auth0_adapter.py

# Read the respx mock-endpoint tier -- exercises the REAL AssetHttpClient code (retry, URL
# construction, pagination) against realistic response bodies, not the adapter's own mocked
# methods. Standard practice when there's no live vendor account to test against for real
# (see docs/AGENTIC_ADAPTER_DESIGN.md).
cat app/tests/adapters/test_crowdstrike_adapter_mock_endpoints.py

# The generic cross-adapter contract suite -- every adapter needs entries here too
cat app/tests/contract/test_adapter_contract.py

# Check pytest configuration -- asyncio_mode = auto means test functions are just
# `async def test_...`, no @pytest.mark.asyncio decorator needed anywhere
cat pytest.ini
```

### 3. Generate Unit Tests

Create `app/tests/adapters/test_$0_adapter.py`. Mock `adapter.client` (BaseAdapter's shared
`AssetHttpClient`) -- never patch raw `httpx.AsyncClient`, and never assume `adapter.client` is
`None` before `connect()` (it's constructed in `BaseAdapter.__init__`, always present).
`fetch_raw()` is an async generator -- consume it with `[page async for page in adapter.fetch_raw()]`,
never `await adapter.fetch_raw()` directly (that raises, it's not a coroutine).

```python
"""Unit tests for $0 adapter."""
from unittest.mock import AsyncMock

import httpx
import pytest

from app.adapters.$0.adapter import $0Adapter
from app.adapters.$0.config import $0Config
from app.adapters.errors import AuthenticationError
from app.models.assets import NormalizedAsset


@pytest.fixture
def $0_config():
    return $0Config(
        name="$0",
        base_url="https://api.$0.com",
        auth_type="bearer",  # match whatever auth_type $0Config actually uses
        auth_config={"token": "test-token"},
    )


# --- connect() ---
async def test_$0_connect_success(mocker, $0_config):
    adapter = $0Adapter($0_config)
    mocker.patch.object(adapter.client, "get", new=AsyncMock(return_value=None))
    await adapter.connect()


async def test_$0_connect_auth_failure(mocker, $0_config):
    adapter = $0Adapter($0_config)
    fake_response = httpx.Response(401, request=httpx.Request("GET", "https://x"))
    mocker.patch.object(
        adapter.client,
        "get",
        new=AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401", request=fake_response.request, response=fake_response
            )
        ),
    )
    with pytest.raises(AuthenticationError):
        await adapter.connect()


# --- fetch_raw() ---
async def test_$0_fetch_raw_yields_chunk(mocker, $0_config):
    adapter = $0Adapter($0_config)

    def fake_response():
        class FakeResponse:
            def json(self):
                return {"items": [{"id": "1", "name": "Test Item 1"}]}

        return FakeResponse()

    mocker.patch.object(adapter.client, "get", new=AsyncMock(return_value=fake_response()))

    pages = [page async for page in adapter.fetch_raw()]

    assert len(pages) >= 1
    assert pages[0][0]["id"] == "1"


# --- normalize() ---
def test_$0_normalize_rich_item($0_config):
    adapter = $0Adapter($0_config)
    raw = [{"id": "1", "name": "Test Item 1", "updated_at": "2026-08-04T08:59:03.789Z"}]

    assets = adapter.normalize(raw)

    assert len(assets) == 1
    assert isinstance(assets[0], NormalizedAsset)
    assert assets[0].asset_id == "1"
    assert assets[0].vendor == "$0"


def test_$0_normalize_empty_input($0_config):
    adapter = $0Adapter($0_config)
    assert adapter.normalize([]) == []
```

### 4. Generate the respx mock-endpoint tier (when no live vendor account exists)

If there's no real test account/token to verify against (the common case), add a second test file
exercising `AssetHttpClient`'s REAL request/pagination/auth code via `respx` (mocks httpx at the
transport layer, not `adapter.client`'s methods) -- model it directly on
`app/tests/adapters/test_crowdstrike_adapter_mock_endpoints.py`. This is the standard
verification-layer tier per `docs/AGENTIC_ADAPTER_DESIGN.md` -- it catches real bugs (URL
construction, pagination cursor parsing, auth request shape) that mocking `adapter.client`
directly cannot, by construction.

### 5. Add entries to the contract test suite

If `/add-adapter` didn't already do this, add `$0` entries to both `MINIMAL_CONFIGS` and
`SAMPLE_RAW_DATA` in `app/tests/contract/test_adapter_contract.py` (see step 7b in that skill).

### 6. Run Tests to Verify

```bash
pytest app/tests/adapters/test_$0_adapter.py -v
pytest app/tests/contract/test_adapter_contract.py -k $0 -v
```

### 7. Report Results

Show user:

```
✅ Created tests for $0 adapter:
   - app/tests/adapters/test_$0_adapter.py
   - app/tests/adapters/test_$0_adapter_mock_endpoints.py (if no live account)
   - $0 entries added to app/tests/contract/test_adapter_contract.py

📊 Coverage:
   ✓ connect() - success, auth failure
   ✓ fetch_raw() - yields at least one chunk with real fields
   ✓ normalize() - rich item, empty input
   ✓ Contract suite - construction, normalize round-trip, execute() round-trip

🚀 NEXT STEPS:
1. Fill in real $0 field names in the fake response fixtures (currently placeholders)
2. If $0 paginates, add a multi-page test asserting fetch_raw() yields multiple chunks
   (see test_crowdstrike_adapter_mock_endpoints.py's test_crowdstrike_stream_yields_multiple_chunks
   for the pattern)
3. Run: pytest app/tests/adapters/test_$0_adapter.py app/tests/contract/ -k $0 -v
```

## Important Rules

- **Match existing test style** - read `test_slack_adapter.py`/`test_auth0_adapter.py` first,
  don't invent a new structure
- **No `@pytest.mark.asyncio`** - `pytest.ini` sets `asyncio_mode = auto`, plain `async def test_...`
  is enough
- **Mock `adapter.client`'s methods** (`get`/`request`/`paginated_get`/`paginate_pages`) -
  never patch raw `httpx.AsyncClient`, and never assume `adapter.client` can be `None`
- **`fetch_raw()` is an async generator** - consume with `[page async for page in adapter.fetch_raw()]`,
  never `await adapter.fetch_raw()`
- **Use the real `NormalizedAsset` fields** - `asset_id`, `customer_id`, `name`, `asset_type`,
  `status`, `last_seen`, `vendor`, `metadata` (`app/models/assets.py`)
- **Add the respx mock-endpoint tier when there's no live account** - standard practice, not
  optional, per `docs/AGENTIC_ADAPTER_DESIGN.md`
- **Always add contract suite entries** - `MINIMAL_CONFIGS` and `SAMPLE_RAW_DATA` in
  `app/tests/contract/test_adapter_contract.py`