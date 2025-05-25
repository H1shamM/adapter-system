import time

from celery import Celery
from app.adapters.factory import get_adapter
from app.monitoring import metrics
from app.storage.assets import AssetStore

app = Celery(
    'core',
    broker='amqp://guest:guest@localhost:5672//',
    backend='rpc://',
    # Add these critical configurations
    result_extended=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],  # Ignore other content
    worker_send_task_events=True,
    task_send_sent_event=True,
    imports=['app.tasks.core']  # Explicitly import task module
)

# Add task routing configuration
app.conf.task_routes = {
    'app.tasks.core.sync_adapter_task': {'queue': 'sync_queue'}
}

@app.task(
    bind=True,
    serializer='json',
    max_retries=3,
    name='app.tasks.core.sync_adapter_task',  # Explicit name
    queue='sync_queue'  # Explicit queue
)
def sync_adapter_task(self, adapter_type: str, config: dict):
    """Main sync task with retry logic"""
    start_time = time.time()
    try:
        adapter = get_adapter(adapter_type, config)
        assets = adapter.execute()

        store = AssetStore()
        result = store.store_assets(assets)

        metrics.SYNC_SUCCESS.labels(adapter_type=adapter_type).inc()
        metrics.SYNC_DURATION.labels(adapter_type=adapter_type).set(time.time() - start_time)

        for asset in assets:
            metrics.ASSET_COUNT.labels(asset_type=asset.type).inc()

        return {
            "inserted": result.upserted_count,
            "modified": result.modified_count,
            "success": True
        }

    except Exception as e:
        metrics.SYNC_ERRORS.labels(adapter_type=adapter_type).inc()
        raise
    except ConnectionError as e:
        self.retry(exc=e, countdown=60)
