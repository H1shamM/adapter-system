---
name: add-adapter
description: Scaffolds a new adapter for the adapter-system. Creates the adapter directory, BaseAdapter implementation with connect/fetch_raw/normalize methods, config class, and registers it in the factory. Use when adding integration with a new external API/service like GitHub, AWS, Stripe, etc.
argument-hint: <adapter-name> [config-fields]
allowed-tools: Read Write Edit Glob Grep Bash(ls *) Bash(cat *)
---

# Add New Adapter

Scaffolds adapter structure with TODO stubs for a human to fill in -- for a fully-drafted, working
adapter built directly from a vendor's real API docs, use `build-adapter-from-docs` instead.

## Arguments

- `$0` - Adapter name (e.g., "stripe", "salesforce", "shopify")
- `$1` (optional) - Config fields description (e.g., "api_key,webhook_secret")

## Steps to Execute

### 1. Validate Inputs

- Confirm adapter name is lowercase, snake_case
- Check that `app/adapters/$0/` doesn't already exist
- If it exists, ask user to confirm overwrite

### 2. Read Existing Patterns

Before creating files, READ these existing adapters to follow the same patterns. Directory names
don't always match the registry key -- check `app/adapters/factory.py`'s `ADAPTER_REGISTRY` for
the real mapping, don't guess from the adapter name.

```bash
# Simplest real adapter -- bearer auth, one paginated endpoint
cat app/adapters/github_adapter/adapter.py

# An adapter with a genuinely new pagination shape (cursor lives in the response body)
cat app/adapters/slack/adapter.py

# An adapter with OAuth2 client-credentials auth + multi-entity fetch
cat app/adapters/crowdstrike/adapter.py
cat app/adapters/crowdstrike/config.py

# The base class every adapter implements, and the shared HTTP client
cat app/adapters/base.py
cat app/http/client.py

# The actual unified schema every adapter normalizes into
cat app/models/assets.py

# How adapters are registered
cat app/adapters/factory.py
cat app/adapters/registry.py
```

### 3. Create Adapter Directory Structure

Create these files:

```
app/adapters/$0/
├── __init__.py
├── adapter.py       # Main adapter class
├── config.py        # Pydantic config model
└── README.md        # Adapter documentation
```

### 4. Generate adapter.py

Use this template (adapt based on similar adapters in the codebase read in step 2):

```python
"""$0 adapter for fetching data from $0 API."""
from datetime import datetime
from typing import AsyncIterator, Dict, List

import httpx

from app.adapters.base import BaseAdapter
from app.adapters.errors import AuthenticationError
from app.adapters.$0.config import $0Config
from app.config import settings
from app.models.assets import NormalizedAsset


class $0Adapter(BaseAdapter):
    """Adapter for $0 API integration."""

    def __init__(self, config: $0Config):
        super().__init__(config)

    async def connect(self):
        """Test credentials/connection with one cheap real call. Uses self.client (the shared
        AssetHttpClient from BaseAdapter) -- auth is handled generically via auth_type/auth_config
        on the config, NOT a hand-rolled httpx.AsyncClient or manual Authorization header."""
        try:
            await self.client.get("/some/cheap/endpoint")
        except httpx.HTTPStatusError as err:
            if err.response.status_code in (401, 403):
                raise AuthenticationError("$0 authentication failed") from err
            raise

    async def fetch_raw(self) -> AsyncIterator[List[Dict]]:
        """Yield raw $0 data in chunks. This MUST be an async generator (`yield`, not `return`)
        -- BaseAdapter.stream() drains it page by page for production syncs, so a plain
        `return [...]` breaks the contract even though it looks like it should work. For a
        single-page/bounded result, yield once:

            data = await self.client.get("/api/data")
            yield data.json().get("items", [])

        For a genuinely paginated endpoint, use self.client.paginate_pages() (see
        app/adapters/github_adapter/adapter.py for the simple case, app/adapters/slack/adapter.py
        or app/adapters/crowdstrike/adapter.py for cursor-in-body / multi-entity cases) and yield
        each page as it's fetched -- do NOT collect all pages into one list first.

        Do NOT implement stream() yourself -- it's inherited from BaseAdapter and works
        automatically once fetch_raw() is a real generator: it just calls normalize() on each
        chunk this yields.
        """
        response = await self.client.get("/api/data")
        yield response.json().get("items", [])

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        """Convert one chunk of $0 vendor data to the unified schema. Required NormalizedAsset
        fields: asset_id, customer_id, name, asset_type, status, last_seen, vendor, metadata --
        these are the REAL field names (app/models/assets.py), not external_id/source_adapter.
        A record missing a required field should fail loudly (pydantic ValidationError), not be
        silently dropped -- add a real fallback only if the vendor's docs show the field as
        genuinely optional."""
        return [
            NormalizedAsset(
                asset_id=str(item["id"]),
                customer_id=settings.customer_id,
                name=item.get("name", ""),
                asset_type="$0_asset",  # CHANGE THIS to the actual entity type
                status="ACTIVE",  # CHANGE THIS if the vendor has a real status field
                last_seen=datetime.fromisoformat(item["updated_at"]),  # CHANGE THIS field name
                vendor="$0",
                metadata=item,
            )
            for item in raw_data
        ]
```

### 5. Generate config.py

Auth is NOT a new field -- it flows through the generic `auth_type`/`auth_config` mechanism every
adapter inherits from `AdapterConfig`/`HttpClientConfig` (see `app/http/client.py`'s
`_setup_auth()` for the supported `auth_type` values: `bearer`, `api_key`, `aws_sigv4`,
`oauth2_client_credentials`). Only add fields here for things that are genuinely vendor-specific
(e.g. Auth0's `domain`, CrowdStrike's `device_filter`) -- see `app/adapters/auth0/config.py` and
`app/adapters/crowdstrike/config.py` for real examples, including the docstring convention of
showing an example instantiation.

```python
"""Configuration for $0 adapter."""
from app.adapters.base import AdapterConfig


class $0Config(AdapterConfig):
    """$0 API configuration.

    Auth flows through the generic auth_type/auth_config mechanism (see app/http/client.py),
    same as every other adapter -- it is NOT a field on this class.

    Expected instantiation:
        $0Config(
            name="$0",
            base_url="https://api.$0.com",
            auth_type="bearer",  # or api_key / oauth2_client_credentials -- check $0's real docs
            auth_config={"token": "VAR:$0_API_TOKEN"},
        )
    """

    # Add fields here ONLY for things that are genuinely $0-specific, not auth.
    # e.g.: some_filter: Optional[str] = None
```

### 6. Register in factory.py

Edit `app/adapters/factory.py` and add:

```python
from app.adapters.$0.adapter import $0Adapter
from app.adapters.$0.config import $0Config

ADAPTER_REGISTRY = {
    # ... existing adapters
    "$0": ($0Adapter, $0Config),
}
```

### 7. Register in registry.py

Edit `app/adapters/registry.py` and add `"$0"` to the `SUPPORTED_ADAPTERS` set.

### 7b. Add entries to the contract test suite

Edit `app/tests/contract/test_adapter_contract.py` and add entries for `$0` to BOTH
`MINIMAL_CONFIGS` and `SAMPLE_RAW_DATA`. The `test_minimal_configs_cover_every_registered_adapter`
and `test_sample_raw_data_covers_every_registered_adapter` tests will fail otherwise. Required
keys:

- `MINIMAL_CONFIGS["$0"]`: smallest dict that constructs `$0Config` -- `name`, `base_url`,
  `auth_type`, `auth_config` (matching whatever auth_type $0 actually uses) plus any
  `$0`-specific fields, following the `"auth0"` or `"slack"` entries already in that dict as the
  real pattern (not a nested `{"config": {...}}` wrapper -- these are flat kwargs to `$0Config`)
- `SAMPLE_RAW_DATA["$0"]`: a list of 1+ representative raw dict items, shaped exactly like what
  one `fetch_raw()` chunk yields -- `normalize()` must accept this directly

### 8. Create Sample Config

Create `configs/$0_sample.json`, matching the flat shape every other `configs/*_sample.json`
uses (see `configs/auth0_sample.json`, `configs/slack_sample.json`) -- NOT a
`{"adapter_type": ..., "instance_id": ..., "config": {...}}` wrapper:

```json
{
  "name": "$0",
  "enabled": true,
  "sync_interval": 3600,
  "priority": "medium",
  "asset_types": ["$0_asset"],
  "base_url": "https://api.$0.com",
  "auth_type": "bearer",
  "auth_config": {
    "token": "VAR:$0_API_TOKEN"
  }
}
```

### 9. Generate README.md

Create `app/adapters/$0/README.md`:

```markdown
# $0 Adapter

## Overview
Integration with $0 API for [purpose].

## Configuration

| Field | Required | Description |
|-------|----------|--------------|
| auth_config.token | Yes | $0 API token (see auth_type in config.py) |
| base_url | No | API base URL (default: https://api.$0.com) |

## Setup

1. Get an API token from the $0 dashboard
2. Set the `$0_API_TOKEN` environment variable
3. Create an adapter instance via the API using `configs/$0_sample.json` as a starting point

## Data Schema

The adapter normalizes $0 data into `NormalizedAsset`:
- `asset_id`: $0 entity ID
- `asset_type`: "$0_asset"
- `name`: entity display name
- `vendor`: "$0"
- `metadata`: full $0 response for this item

## Rate Limits

[Document $0's rate limits]

## Testing

\`\`\`bash
pytest app/tests/adapters/test_$0_adapter.py
pytest app/tests/contract/test_adapter_contract.py -k $0
\`\`\`
```

### 10. Remind User of Next Steps

After creating all files, tell the user:

```
✅ Created $0 adapter:
   - app/adapters/$0/adapter.py
   - app/adapters/$0/config.py
   - app/adapters/$0/README.md
   - configs/$0_sample.json
   - Registered in factory.py and registry.py
   - Added $0 entries to app/tests/contract/test_adapter_contract.py

🔧 NEXT STEPS:
1. Implement the real API calls in fetch_raw() (currently has a placeholder single endpoint)
2. Confirm the real auth_type against $0's actual docs (bearer / api_key / oauth2_client_credentials)
3. Map $0's real field names in normalize() -- the placeholder guesses at field names
4. Run tests: pytest app/tests/adapters/test_$0_adapter.py app/tests/contract/ -k $0
5. Add full test coverage with: /add-adapter-tests $0
6. Test integration:
   - Start services: docker compose up -d
   - Create instance via API
   - Trigger sync and verify in MongoDB

📚 REFERENCES:
- Existing adapters: app/adapters/github_adapter/, app/adapters/slack/, app/adapters/crowdstrike/
- Base class: app/adapters/base.py
- Sync engine: app/services/sync_engine.py
```

## Important Rules

- **Always read existing adapters first** - follow the exact same pattern, don't invent a new one
- **`fetch_raw()` MUST be an async generator** (`yield`, not `return`) -- BaseAdapter.stream()
  drains it per chunk; a coroutine returning `List[Dict]` breaks the contract
- **Never implement `stream()`** - it's universal on BaseAdapter, inherited automatically
- **Use `self.client` (BaseAdapter's shared `AssetHttpClient`)** - never construct your own
  `httpx.AsyncClient` or manage auth headers by hand; auth flows through `auth_type`/`auth_config`
- **Don't invent `NormalizedAsset` fields** - the real ones are `asset_id`, `customer_id`, `name`,
  `asset_type`, `status`, `last_seen`, `vendor`, `metadata` (`app/models/assets.py`)
- **Add to BOTH factory.py AND registry.py** - both are required
- **Add to BOTH `MINIMAL_CONFIGS` AND `SAMPLE_RAW_DATA`** in the contract test suite
- **Include type hints** - this codebase uses strict typing
- **Match code style** - check existing adapters for formatting