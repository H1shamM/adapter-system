---
name: add-adapter
description: Scaffolds a new adapter for the adapter-system. Creates the adapter directory, BaseAdapter implementation with connect/fetch_raw/normalize methods, config class, and registers it in the factory. Use when adding integration with a new external API/service like GitHub, AWS, Stripe, etc.
argument-hint: <adapter-name> [config-fields]
allowed-tools: Read Write Edit Glob Grep Bash(ls *) Bash(cat *)
---

# Add New Adapter

Scaffolds a complete adapter following the project's hexagonal architecture pattern.

## Arguments

- `$0` - Adapter name (e.g., "stripe", "salesforce", "shopify")
- `$1` (optional) - Config fields description (e.g., "api_key,webhook_secret")

## Steps to Execute

### 1. Validate Inputs

- Confirm adapter name is lowercase, snake_case
- Check that `app/adapters/$0/` doesn't already exist
- If it exists, ask user to confirm overwrite

### 2. Read Existing Patterns

Before creating files, READ these existing adapters to follow the same patterns:

```bash
# Read an existing simple adapter
cat app/adapters/github/adapter.py
cat app/adapters/github/config.py

# Understand the base class
cat app/adapters/base.py

# See how adapters are registered
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

Use this template (adapt based on similar adapters in the codebase):

```python
"""$0 adapter for fetching data from $0 API."""
import httpx
from typing import List, Dict, Any
from app.adapters.base import BaseAdapter
from app.models.normalized_asset import NormalizedAsset
from app.adapters.$0.config import $0Config


class $0Adapter(BaseAdapter):
    """Adapter for $0 API integration."""
    
    def __init__(self, config: $0Config):
        super().__init__(config)
        self.config: $0Config = config
        self.client: httpx.AsyncClient | None = None
    
    async def connect(self) -> None:
        """Validate credentials and test connectivity."""
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=30.0
        )
        # Test connection with a lightweight API call
        response = await self.client.get("/health")
        response.raise_for_status()
    
    async def fetch_raw(self) -> List[Dict[str, Any]]:
        """Fetch raw data from $0 API."""
        if not self.client:
            raise RuntimeError("Adapter not connected. Call connect() first.")
        
        response = await self.client.get("/api/data")
        response.raise_for_status()
        return response.json().get("items", [])
    
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[NormalizedAsset]:
        """Convert $0 vendor data to unified NormalizedAsset schema."""
        normalized = []
        for item in raw_data:
            normalized.append(NormalizedAsset(
                external_id=str(item.get("id")),
                asset_type="$0_asset",  # CHANGE THIS to actual type
                name=item.get("name", ""),
                metadata=item,
                source_adapter="$0"
            ))
        return normalized
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.aclose()
```

### 5. Generate config.py

```python
"""Configuration for $0 adapter."""
from pydantic import Field
from app.adapters.base import AdapterConfig


class $0Config(AdapterConfig):
    """Config for $0 adapter instance."""
    
    api_key: str = Field(..., description="$0 API key")
    base_url: str = Field(
        default="https://api.$0.com",
        description="$0 API base URL"
    )
    # Add additional fields based on $1 argument
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

Edit `app/adapters/registry.py` and add `"$0"` to the SUPPORTED_ADAPTERS list.

### 7b. Add entries to the contract test suite

Edit `app/tests/contract/test_adapter_contract.py` and add entries for `$0` to BOTH `MINIMAL_CONFIGS` and `SAMPLE_RAW_DATA`. The `test_minimal_configs_cover_every_registered_adapter` and `test_sample_raw_data_covers_every_registered_adapter` tests will fail otherwise. Required keys:

- `MINIMAL_CONFIGS["$0"]`: smallest dict that constructs `$0Config` (all required fields)
- `SAMPLE_RAW_DATA["$0"]`: a list of 1+ representative items in whatever shape your `fetch_raw()` returns -- `normalize()` must accept this

### 8. Create Sample Config

Create `configs/$0_sample.json`:

```json
{
  "adapter_type": "$0",
  "instance_id": "$0_default",
  "config": {
    "api_key": "REPLACE_WITH_REAL_KEY",
    "base_url": "https://api.$0.com"
  },
  "sync_interval": 3600,
  "priority": "normal",
  "enabled": true
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
|-------|----------|-------------|
| api_key | Yes | $0 API key |
| base_url | No | API base URL (default: https://api.$0.com) |

## Setup

1. Get API key from $0 dashboard
2. Add config to `configs/$0_sample.json`
3. Create adapter instance via API:

\`\`\`bash
curl -X POST http://localhost:8000/api/v1/adapters \\
  -H "Authorization: Bearer $TOKEN" \\
  -d @configs/$0_sample.json
\`\`\`

## Data Schema

The adapter normalizes $0 data into NormalizedAsset:
- external_id: $0 entity ID
- asset_type: "$0_asset"
- name: Entity display name
- metadata: Full $0 response

## Rate Limits

[Document $0's rate limits]

## Testing

\`\`\`bash
pytest app/tests/unit/adapters/test_$0_adapter.py
pytest app/tests/integration/adapters/test_$0_integration.py
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

🔧 NEXT STEPS:
1. Implement actual API calls in adapter.py (currently has placeholders)
2. Add real authentication logic in connect()
3. Map $0's data structure in normalize()
4. Run tests: pytest app/tests/unit/adapters/test_$0_adapter.py
5. Add tests with: /add-adapter-tests $0
6. Test integration: 
   - Start services: docker compose up -d
   - Create instance via API
   - Trigger sync and verify in MongoDB

📚 REFERENCES:
- Existing adapters: app/adapters/github/, app/adapters/aws/
- Base class: app/adapters/base.py
- Sync engine: app/services/sync_engine.py
```

## Important Rules

- **Always read existing adapters first** - follow the exact same pattern
- **Don't invent fields** - check what NormalizedAsset actually expects
- **Use httpx (async)** - this codebase uses async, never use requests
- **Add to BOTH factory.py AND registry.py** - both are required
- **Include type hints** - this codebase uses strict typing
- **Match code style** - check existing adapters for formatting
