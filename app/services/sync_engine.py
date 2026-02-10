import json
import time

from app.adapters.factory import build_adapter
from app.monitoring import metrics
from app.storage.assets import AssetStore


def run_adapter_sync(adapter_type: str, config: dict):
    """"
    Run adapter ingestion synchronously.
    This is the core orchestration logic shared by Celery and CLI.
    """
    start_time = time.time()

    adapter = build_adapter(adapter_type, config)
    assets = adapter.execute()

    store = AssetStore()
    print(f"DEBUG assets len {len(assets)}")

    result = store.store_assets(assets)

    metrics.SYNC_SUCCESS.labels(adapter_type=adapter_type).inc()
    metrics.SYNC_DURATION.labels(adapter_type=adapter_type).set(time.time() - start_time)

    for asset in assets:
        metrics.ASSET_COUNT.labels(asset_type=asset.asset_type).inc()
    return {
        "inserted": result['nInserted'],
        "modified": result['nModified'],
        "success": True,
    }
