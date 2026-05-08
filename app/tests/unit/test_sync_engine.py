"""Unit tests for run_adapter_sync (app/services/sync_engine.py).

Mocks build_adapter, AssetStore, and the prometheus metric labels so the
test stays fast and doesn't require any external service.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.assets import NormalizedAsset


@pytest.fixture
def fake_asset():
    return NormalizedAsset(
        asset_id="x1",
        customer_id="acme",
        name="thing",
        asset_type="ec2",
        status="RUNNING",
        last_seen=datetime(2024, 1, 1),
        vendor="AWS",
        metadata={},
    )


@pytest.fixture
def patched_engine(mocker, fake_asset):
    """Patch external collaborators of run_adapter_sync and yield handles."""
    fake_adapter = MagicMock()
    fake_adapter.execute = AsyncMock(return_value=[fake_asset])
    mocker.patch("app.services.sync_engine.build_adapter", return_value=fake_adapter)

    fake_store = MagicMock()
    fake_store.store_assets.return_value = {"nInserted": 1, "nModified": 0}
    mocker.patch("app.services.sync_engine.AssetStore", return_value=fake_store)

    # Replace the metric label objects so .inc() / .observe() don't actually
    # mutate the registry. We don't care about call shapes here, just that
    # the function runs to completion without exploding.
    metrics = mocker.patch("app.services.sync_engine.metrics")
    metrics.SYNC_SUCCESS.labels.return_value = MagicMock()
    metrics.SYNC_DURATION.labels.return_value = MagicMock()
    metrics.ASSET_COUNT.labels.return_value = MagicMock()

    return {"adapter": fake_adapter, "store": fake_store, "metrics": metrics}


async def test_run_adapter_sync_returns_summary(patched_engine):
    from app.services.sync_engine import run_adapter_sync

    result = await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    assert result == {
        "inserted": 1,
        "modified": 0,
        "assets_processed": 1,
        "success": True,
    }


async def test_run_adapter_sync_calls_execute_and_store(patched_engine):
    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    patched_engine["adapter"].execute.assert_awaited_once()
    patched_engine["store"].store_assets.assert_called_once()


async def test_run_adapter_sync_increments_metrics(patched_engine):
    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    metrics = patched_engine["metrics"]
    metrics.SYNC_SUCCESS.labels.assert_called_once()
    metrics.SYNC_DURATION.labels.assert_called_once()
    # one ASSET_COUNT increment per asset returned (1 in this fixture)
    assert metrics.ASSET_COUNT.labels.call_count == 1


async def test_run_adapter_sync_with_zero_assets(patched_engine):
    """Empty asset list still completes; ASSET_COUNT not incremented."""
    patched_engine["adapter"].execute.return_value = []
    patched_engine["store"].store_assets.return_value = {"nInserted": 0, "nModified": 0}

    from app.services.sync_engine import run_adapter_sync

    result = await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    assert result["assets_processed"] == 0
    assert result["success"] is True
    patched_engine["metrics"].ASSET_COUNT.labels.assert_not_called()


async def test_run_adapter_sync_propagates_adapter_errors(patched_engine):
    """If the adapter's execute() raises, the error bubbles up to the caller."""
    patched_engine["adapter"].execute.side_effect = RuntimeError("boom")

    from app.services.sync_engine import run_adapter_sync

    with pytest.raises(RuntimeError, match="boom"):
        await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    patched_engine["store"].store_assets.assert_not_called()
