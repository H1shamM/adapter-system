from datetime import datetime, timedelta
from uuid import uuid4

from app.storage.adapters import AdapterConfigStore
from app.storage.sync_history import SyncHistoryStore
from app.tasks.core import app, sync_adapter_task
from app.utils.logging import get_logger

logger = get_logger(__name__)


@app.task(name='check_due_adapters')
def check_and_queue_due_adapters():
    logger.info(
        "scheduler_checking_due_adapters"
    )
    store = AdapterConfigStore()
    due_adapters = store.get_due_adapters()

    if not due_adapters:
        logger.info("scheduler_no_due_adapters")
        return {"queued": 0, "total_due": 0}

    history = SyncHistoryStore()
    queued = 0

    for adapter in due_adapters:
        adapter_id = adapter["adapter_id"]
        adapter_type = adapter["adapter_type"]
        sync_id = str(uuid4())

        try:

            task = sync_adapter_task.delay(
                adapter_id,
                adapter_type,
                adapter,
                sync_id
            )

            history.start_sync(sync_id=sync_id, adapter=adapter_id)

            queued += 1

            logger.info(
                "scheduler_queued_sync",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                sync_interval=adapter.get('sync_interval'),
                priority=adapter.get('priority'),
                task_id=task.id,
                sync_id=sync_id
            )
        except Exception as e:
            logger.error(
                "scheduler_queue_failed",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                error=str(e),
                exc_info=True
            )

    logger.info(
        "scheduler_completed",
        total_due=len(due_adapters),
        queued=queued
    )

    return {
        "queued": queued,
        "total_due": len(due_adapters),
        "timestamp": datetime.now().isoformat(),
    }


app.conf.beat_schedule = {
    'check-due-adapters-every-5-min': {
        'task': 'check_due_adapters',
        'schedule': timedelta(minutes=5),
        'options': {
            'expires': 300
        },
    }
}

app.conf.timezone = 'UTC'
