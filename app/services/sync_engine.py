import time

from app.adapters.factory import build_adapter
from app.config import settings
from app.monitoring import metrics
from app.storage.assets import AssetStore
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_adapter_sync(adapter_type: str, config: dict) -> dict:
    """Run adapter ingestion — core orchestration shared by Celery tasks and CLI."""
    start_time = time.time()

    adapter = build_adapter(adapter_type, config)
    assets = await adapter.execute()

    store = AssetStore()
    logger.info("assets_fetched", adapter_type=adapter_type, count=len(assets))

    result = store.store_assets(assets)

    metrics.SYNC_SUCCESS.labels(
        adapter_type=adapter_type,
        customer_id=settings.customer_id
    ).inc()
    metrics.SYNC_DURATION.labels(
        adapter_type=adapter_type,
        customer_id=settings.customer_id
    ).observe(time.time() - start_time)

    for asset in assets:
        metrics.ASSET_COUNT.labels(
            asset_type=asset.asset_type,
            customer_id=settings.customer_id
        ).inc()
    return {
        "inserted": result['nInserted'],
        "modified": result['nModified'],
        "assets_processed": len(assets),
        "success": True,
    }
