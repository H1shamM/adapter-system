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


def _single_chunk_stream(chunk):
    """Build a stream() replacement that yields exactly one chunk."""

    async def _stream():
        yield chunk

    return MagicMock(side_effect=_stream)


@pytest.fixture
def patched_engine(mocker, fake_asset):
    """Patch external collaborators of run_adapter_sync and yield handles."""
    fake_adapter = MagicMock()
    fake_adapter.stream = _single_chunk_stream([fake_asset])
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


async def test_run_adapter_sync_calls_stream_and_store(patched_engine):
    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    patched_engine["adapter"].stream.assert_called_once()
    patched_engine["store"].store_assets.assert_called_once()


async def test_run_adapter_sync_uses_injected_store_over_default(mocker, fake_asset):
    """store is injectable -- callers/tests can pass a fake directly instead of only being able
    to monkeypatch the module-level AssetStore import."""
    fake_adapter = MagicMock()
    fake_adapter.stream = _single_chunk_stream([fake_asset])
    mocker.patch("app.services.sync_engine.build_adapter", return_value=fake_adapter)

    default_store_cls = mocker.patch("app.services.sync_engine.AssetStore")
    mocker.patch("app.services.sync_engine.metrics")

    injected_store = MagicMock()
    injected_store.store_assets.return_value = {"nInserted": 1, "nModified": 0}

    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"}, store=injected_store)

    injected_store.store_assets.assert_called_once()
    default_store_cls.assert_not_called()


async def test_run_adapter_sync_increments_metrics(patched_engine):
    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    metrics = patched_engine["metrics"]
    metrics.SYNC_SUCCESS.labels.assert_called_once()
    metrics.SYNC_DURATION.labels.assert_called_once()
    # one ASSET_COUNT increment per asset returned (1 in this fixture)
    assert metrics.ASSET_COUNT.labels.call_count == 1


async def test_run_adapter_sync_aggregates_metrics_by_asset_type_per_chunk(
    patched_engine, fake_asset
):
    """A chunk with multiple assets of the same type should increment ASSET_COUNT once with the
    aggregate count, not once per asset -- the actual performance fix (a 500-item chunk shouldn't
    do 500 separate label lookups)."""
    other_asset = fake_asset.model_copy(update={"asset_id": "x2", "asset_type": "s3"})
    patched_engine["adapter"].stream = _single_chunk_stream([fake_asset, fake_asset, other_asset])

    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    metrics = patched_engine["metrics"]
    # 2 distinct asset_types in the chunk (ec2 x2, s3 x1) -- 2 labels() calls, not 3 -- and the
    # ec2 increment carries count=2 in one call, not two separate count=1 increments.
    assert metrics.ASSET_COUNT.labels.call_count == 2
    inc_counts = sorted(
        call.args[0] for call in metrics.ASSET_COUNT.labels.return_value.inc.call_args_list
    )
    assert inc_counts == [1, 2]


async def test_run_adapter_sync_with_zero_assets(patched_engine):
    """A chunk that comes back empty is skipped entirely -- no store_assets call (pymongo's
    bulk_write raises on an empty operations list), no ASSET_COUNT increment."""
    patched_engine["adapter"].stream = _single_chunk_stream([])

    from app.services.sync_engine import run_adapter_sync

    result = await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    assert result == {
        "inserted": 0,
        "modified": 0,
        "assets_processed": 0,
        "success": True,
    }
    patched_engine["store"].store_assets.assert_not_called()
    patched_engine["metrics"].ASSET_COUNT.labels.assert_not_called()


async def test_run_adapter_sync_stores_and_aggregates_per_chunk(patched_engine, fake_asset):
    """Multiple chunks each get their own store_assets() call, and counts aggregate across all
    of them -- the actual behavior change that makes chunked/streaming adapters bound their Mongo
    writes to page-size batches instead of one bulk_write for the whole result set."""

    async def multi_chunk_stream():
        yield [fake_asset]
        yield [fake_asset, fake_asset]

    patched_engine["adapter"].stream = MagicMock(side_effect=multi_chunk_stream)
    patched_engine["store"].store_assets.side_effect = [
        {"nInserted": 1, "nModified": 0},
        {"nInserted": 1, "nModified": 1},
    ]

    from app.services.sync_engine import run_adapter_sync

    result = await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    assert patched_engine["store"].store_assets.call_count == 2
    assert result == {
        "inserted": 2,
        "modified": 1,
        "assets_processed": 3,
        "success": True,
    }


async def test_run_adapter_sync_calls_on_progress_with_cumulative_count(patched_engine, fake_asset):
    async def multi_chunk_stream():
        yield [fake_asset]
        yield [fake_asset, fake_asset]

    patched_engine["adapter"].stream = MagicMock(side_effect=multi_chunk_stream)
    patched_engine["store"].store_assets.side_effect = [
        {"nInserted": 1, "nModified": 0},
        {"nInserted": 2, "nModified": 0},
    ]

    on_progress = AsyncMock()

    from app.services.sync_engine import run_adapter_sync

    await run_adapter_sync(
        "github", {"name": "n", "base_url": "https://x"}, on_progress=on_progress
    )

    assert on_progress.await_args_list == [((1,),), ((3,),)]


async def test_run_adapter_sync_propagates_adapter_errors(patched_engine):
    """If stream() raises, the error bubbles up to the caller."""

    async def failing_stream():
        raise RuntimeError("boom")
        yield []  # pragma: no cover -- unreachable, keeps this an async generator function

    patched_engine["adapter"].stream = MagicMock(side_effect=failing_stream)

    from app.services.sync_engine import run_adapter_sync

    with pytest.raises(RuntimeError, match="boom"):
        await run_adapter_sync("github", {"name": "n", "base_url": "https://x"})

    patched_engine["store"].store_assets.assert_not_called()
