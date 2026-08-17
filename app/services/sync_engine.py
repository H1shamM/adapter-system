import time
from collections import Counter
from typing import Awaitable, Callable, Optional

from app.adapters.factory import build_adapter
from app.config import settings
from app.monitoring import metrics
from app.storage.assets import AssetStore
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_adapter_sync(
    adapter_type: str,
    config: dict,
    on_progress: Optional[Callable[[int], Awaitable[None]]] = None,
    store: Optional[AssetStore] = None,
) -> dict:
    """Run adapter ingestion — core orchestration shared by Celery tasks and CLI.

    Drains adapter.stream() chunk by chunk instead of materializing the whole result set first --
    every adapter has a working stream() (connect() + fetch_raw()/normalize() per chunk, with
    error translation), so AuthenticationError/FetchError surface correctly here even for
    adapters whose connect() doesn't self-translate.

    Each chunk gets its own store_assets() call -- for adapters with bounded results that's one
    call, exactly like before; for real streaming adapters, Mongo writes are naturally bounded to
    page-size batches instead of one bulk_write for the whole result set. A mid-sync crash also
    keeps whatever chunks already landed, instead of losing everything.

    `store` is injectable (defaults to a real AssetStore()) so callers/tests can pass a fake
    directly instead of only being able to monkeypatch the module-level import.
    """
    start_time = time.time()

    adapter = build_adapter(adapter_type, config)
    store = store or AssetStore()

    total_inserted = total_modified = total_processed = 0
    async for chunk in adapter.stream():
        if not chunk:
            continue
        result = store.store_assets(chunk)
        total_inserted += result["nInserted"]
        total_modified += result["nModified"]
        total_processed += len(chunk)

        # Aggregate by asset_type within the chunk before incrementing -- one .inc(count) call
        # per distinct type, not one call per asset (a 500-item chunk was doing 500 label
        # lookups for what's usually 1-2 distinct asset types).
        for asset_type, count in Counter(asset.asset_type for asset in chunk).items():
            metrics.ASSET_COUNT.labels(asset_type=asset_type, customer_id=settings.customer_id).inc(
                count
            )

        if on_progress:
            await on_progress(total_processed)

    logger.info("assets_fetched", adapter_type=adapter_type, count=total_processed)

    metrics.SYNC_SUCCESS.labels(adapter_type=adapter_type, customer_id=settings.customer_id).inc()
    metrics.SYNC_DURATION.labels(
        adapter_type=adapter_type, customer_id=settings.customer_id
    ).observe(time.time() - start_time)

    return {
        "inserted": total_inserted,
        "modified": total_modified,
        "assets_processed": total_processed,
        "success": True,
    }
