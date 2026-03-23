import asyncio
import os

from celery import Celery

from app.config import settings
from app.monitoring import metrics
from app.services.sync_engine import run_adapter_sync
from app.storage.adapters import AdapterConfigStore
from app.storage.sync_history import SyncHistoryStore
from app.utils.logging import get_logger

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

app.conf.update(
    worker_concurrency=10,
    worker_prefetch_multiplier=4,

    task_acks_late=True,
    task_reject_on_worker_lost=True,

    task_soft_time_limit=3600,
    task_time_limit=4000,

    worker_max_tasks_per_child=1000,

    result_expires=3600,
)


@app.task(
    bind=True,
    serializer='json',
    max_retries=3,
    name='app.tasks.core.sync_adapter_task',  # Explicit name
    queue='sync_queue'  # Explicit queue
)
def sync_adapter_task(self, adapter_id: str, adapter_type: str, config: dict, sync_id: str):
    """Main sync task with retry logic"""
    history = SyncHistoryStore()
    logger = get_logger(__name__)

    try:
        logger.info(
            "sync_started",
            adapter_id=adapter_id,
            adapter_type=adapter_type,
            sync_id=sync_id,
            worker=self.request.hostname
        )

        result = asyncio.run(run_adapter_sync(adapter_type, config))

        history.finish_sync(
            sync_id=sync_id,
            status="SUCCESS",
            result=result,
        )
        store = AdapterConfigStore()
        store.update_after_sync(adapter_id)

        logger.info(
            "sync_completed",
            adapter_id=adapter_id,
            adapter_type=adapter_type,
            sync_id=sync_id,
            assets_processed=result.get("assets_processed", 0)
        )

        return result

    except ConnectionError as e:
        self.retry(exc=e, countdown=60)

    except Exception as e:
        history.finish_sync(
            sync_id=sync_id,
            status="FAILED",
            error=str(e),
        )

        metrics.SYNC_ERRORS.labels(
            adapter_type=adapter_type,
            customer_id=settings.customer_id
        ).inc()
        metrics.SYNC_FAILURES.labels(
            adapter_type=adapter_type,
            customer_id=settings.customer_id
        ).inc()

        logger.error(
            "sync_failed",
            adapter_id=adapter_id,
            adapter_type=adapter_type,
            sync_id=sync_id,
            error=str(e),
            exc_info=True
        )

        raise
