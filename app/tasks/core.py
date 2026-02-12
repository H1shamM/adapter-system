import asyncio
import os

from celery import Celery

from app.monitoring import metrics
from app.services.sync_engine import run_adapter_sync
from app.storage.sync_history import SyncHistoryStore

broker = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

app = Celery(
    'core',
    broker=broker,
    backend=backend,
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
def sync_adapter_task(self, adapter_type: str, config: dict, sync_id: str):
    """Main sync task with retry logic"""
    history = SyncHistoryStore()

    try:

        result = asyncio.run(run_adapter_sync(adapter_type, config))

        history.finish_sync(
            sync_id=sync_id,
            status="SUCCESS",
            result=result,
        )
        return result

    except ConnectionError as e:
        self.retry(exc=e, countdown=60)

    except Exception as e:
        history.finish_sync(
            sync_id= sync_id,
            status="FAILED",
            error=str(e),
        )

        metrics.SYNC_ERRORS.labels(adapter_type=adapter_type).inc()
        raise
