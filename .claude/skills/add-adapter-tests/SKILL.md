---
name: add-adapter-tests
description: Generates comprehensive unit and integration tests for an existing adapter in the adapter-system. Creates test files following the project's pytest patterns with mocked HTTP calls, MongoDB fixtures, and end-to-end sync tests. Use after creating a new adapter or when test coverage is missing.
argument-hint: <adapter-name>
allowed-tools: Read Write Edit Glob Grep Bash(ls *) Bash(cat *) Bash(pytest *)
---

# Add Adapter Tests

Generates comprehensive test suite for an adapter following the project's testing patterns.

## Arguments

- `$0` - Adapter name (e.g., "stripe", "github") - must already exist in `app/adapters/`

## Steps to Execute

### 1. Verify Adapter Exists

```bash
ls app/adapters/$0/
cat app/adapters/$0/adapter.py
cat app/adapters/$0/config.py
```

If the adapter doesn't exist, tell user to create it first with `/add-adapter $0`.

### 2. Read Existing Test Patterns

Read existing tests to follow the same patterns:

```bash
# Find existing adapter tests
ls app/tests/unit/adapters/
ls app/tests/integration/adapters/

# Read example unit test
cat app/tests/unit/adapters/test_github_adapter.py

# Read example integration test
cat app/tests/integration/adapters/test_github_integration.py

# Check pytest configuration
cat pytest.ini
cat app/tests/conftest.py
```

### 3. Generate Unit Tests

Create `app/tests/unit/adapters/test_$0_adapter.py`:

```python
"""Unit tests for $0 adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.adapters.$0.adapter import $0Adapter
from app.adapters.$0.config import $0Config
from app.models.normalized_asset import NormalizedAsset


@pytest.fixture
def $0_config():
    """Provide $0 adapter config for testing."""
    return $0Config(
        adapter_type="$0",
        instance_id="test_$0",
        api_key="test_api_key",
        base_url="https://api.$0.com"
    )


@pytest.fixture
def $0_adapter($0_config):
    """Provide $0 adapter instance."""
    return $0Adapter($0_config)


@pytest.fixture
def mock_$0_response():
    """Sample $0 API response for testing."""
    return {
        "items": [
            {"id": "1", "name": "Test Item 1", "data": "value1"},
            {"id": "2", "name": "Test Item 2", "data": "value2"},
        ]
    }


class Test$0AdapterConnect:
    """Tests for $0Adapter.connect() method."""
    
    @pytest.mark.asyncio
    async def test_connect_success($0_adapter):
        """Test successful connection establishment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
            await $0_adapter.connect()
            
            assert $0_adapter.client is not None
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_invalid_credentials($0_adapter):
        """Test connection failure with invalid credentials."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=MagicMock(status_code=401)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await $0_adapter.connect()
    
    @pytest.mark.asyncio
    async def test_connect_network_error($0_adapter):
        """Test connection failure due to network issues."""
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Network error")):
            with pytest.raises(httpx.ConnectError):
                await $0_adapter.connect()


class Test$0AdapterFetchRaw:
    """Tests for $0Adapter.fetch_raw() method."""
    
    @pytest.mark.asyncio
    async def test_fetch_raw_success($0_adapter, mock_$0_response):
        """Test successful data fetching."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_$0_response
        mock_response.raise_for_status = MagicMock()
        
        await $0_adapter.connect()
        with patch.object($0_adapter.client, "get", return_value=mock_response):
            data = await $0_adapter.fetch_raw()
            
            assert len(data) == 2
            assert data[0]["id"] == "1"
            assert data[1]["name"] == "Test Item 2"
    
    @pytest.mark.asyncio
    async def test_fetch_raw_not_connected($0_adapter):
        """Test that fetch_raw raises if not connected."""
        with pytest.raises(RuntimeError, match="not connected"):
            await $0_adapter.fetch_raw()
    
    @pytest.mark.asyncio
    async def test_fetch_raw_empty_response($0_adapter):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status = MagicMock()
        
        await $0_adapter.connect()
        with patch.object($0_adapter.client, "get", return_value=mock_response):
            data = await $0_adapter.fetch_raw()
            
            assert data == []


class Test$0AdapterNormalize:
    """Tests for $0Adapter.normalize() method."""
    
    def test_normalize_success($0_adapter, mock_$0_response):
        """Test successful data normalization."""
        raw_data = mock_$0_response["items"]
        normalized = $0_adapter.normalize(raw_data)
        
        assert len(normalized) == 2
        assert all(isinstance(asset, NormalizedAsset) for asset in normalized)
        assert normalized[0].external_id == "1"
        assert normalized[0].source_adapter == "$0"
    
    def test_normalize_empty_data($0_adapter):
        """Test normalization with empty input."""
        result = $0_adapter.normalize([])
        assert result == []
    
    def test_normalize_preserves_metadata($0_adapter, mock_$0_response):
        """Test that original data is preserved in metadata."""
        raw_data = mock_$0_response["items"]
        normalized = $0_adapter.normalize(raw_data)
        
        assert normalized[0].metadata == raw_data[0]


class Test$0AdapterClose:
    """Tests for $0Adapter.close() method."""
    
    @pytest.mark.asyncio
    async def test_close_after_connect($0_adapter):
        """Test cleanup after connection."""
        with patch("httpx.AsyncClient.get", return_value=MagicMock()):
            await $0_adapter.connect()
            await $0_adapter.close()
            # Should not raise any errors
    
    @pytest.mark.asyncio
    async def test_close_without_connect($0_adapter):
        """Test that close is safe without connecting."""
        await $0_adapter.close()
        # Should not raise any errors
```

### 4. Generate Integration Tests

Create `app/tests/integration/adapters/test_$0_integration.py`:

```python
"""Integration tests for $0 adapter (requires real services)."""
import pytest
from app.adapters.$0.adapter import $0Adapter
from app.adapters.$0.config import $0Config
from app.adapters.factory import build_adapter
from app.services.sync_engine import run_adapter_sync


@pytest.mark.integration
class Test$0AdapterIntegration:
    """Integration tests requiring MongoDB + real API."""
    
    @pytest.fixture
    def $0_config(self):
        """Real config for integration testing - uses test API key."""
        return $0Config(
            adapter_type="$0",
            instance_id="integration_test_$0",
            api_key="TEST_API_KEY_FROM_ENV",  # Set via .env.test
            base_url="https://api.$0.com"
        )
    
    @pytest.mark.asyncio
    async def test_factory_builds_$0_adapter(self, $0_config):
        """Test that factory correctly builds $0 adapter."""
        adapter = build_adapter("$0", $0_config.dict())
        assert isinstance(adapter, $0Adapter)
    
    @pytest.mark.asyncio
    async def test_full_sync_flow(self, $0_config, mongodb_client):
        """Test complete sync: connect → fetch → normalize → store."""
        adapter = $0Adapter($0_config)
        
        # Run full sync
        result = await run_adapter_sync(
            adapter_type="$0",
            instance_id=$0_config.instance_id,
            config=$0_config.dict()
        )
        
        # Verify sync succeeded
        assert result["status"] == "success"
        assert result["assets_synced"] > 0
        
        # Verify data in MongoDB
        assets = await mongodb_client.assets.find(
            {"source_adapter": "$0"}
        ).to_list(length=100)
        assert len(assets) > 0
    
    @pytest.mark.asyncio
    async def test_sync_history_recorded(self, $0_config, mongodb_client):
        """Test that sync history is recorded in MongoDB."""
        await run_adapter_sync(
            adapter_type="$0",
            instance_id=$0_config.instance_id,
            config=$0_config.dict()
        )
        
        history = await mongodb_client.sync_history.find_one(
            {"adapter_type": "$0"},
            sort=[("started_at", -1)]
        )
        assert history is not None
        assert history["status"] == "success"
```

### 5. Run Tests to Verify

```bash
# Run unit tests for the new adapter
pytest app/tests/unit/adapters/test_$0_adapter.py -v

# Check coverage
pytest app/tests/unit/adapters/test_$0_adapter.py --cov=app.adapters.$0
```

### 6. Report Results

Show user:

```
✅ Created tests for $0 adapter:
   - app/tests/unit/adapters/test_$0_adapter.py (X tests)
   - app/tests/integration/adapters/test_$0_integration.py (Y tests)

📊 Test Categories Covered:
   ✓ connect() - success, auth failure, network error
   ✓ fetch_raw() - success, not connected, empty response
   ✓ normalize() - success, empty data, metadata preservation
   ✓ close() - cleanup after connect, safe without connect
   ✓ Integration - factory, full sync flow, history recording

🚀 NEXT STEPS:
1. Update test data in mock_$0_response fixture to match real API
2. Set TEST_API_KEY in .env.test for integration tests
3. Run: pytest app/tests/unit/adapters/test_$0_adapter.py
4. Run: pytest app/tests/integration/adapters/test_$0_integration.py -m integration
5. Verify coverage: pytest --cov=app.adapters.$0 --cov-report=html
```

## Important Rules

- **Match existing test style** - read other adapter tests first
- **Use pytest-asyncio** - this codebase uses async tests
- **Mock external HTTP calls** - never make real API calls in unit tests
- **Use `@pytest.mark.integration`** - for tests requiring real services
- **Use existing fixtures** - check conftest.py for shared fixtures
- **Aim for >80% coverage** - this is the project standard
