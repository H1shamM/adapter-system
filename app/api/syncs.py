from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from app.api.deps import get_sync_history_store
from app.api.errors import NotFoundException
from app.api.schemas.syncs import SyncStatusResponse
from app.auth.dependencies import get_current_user
from app.storage.sync_history import SyncHistoryStore
from app.tasks.core import app as celery_app
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/syncs/history")
async def list_syncs(
    adapter: str | None = None,
    limit: int = 100,
    store: SyncHistoryStore = Depends(get_sync_history_store),
    current_user=Depends(get_current_user),
):
    return store.list(adapter=adapter, limit=limit)


@router.get("/syncs/summary")
async def get_sync_summary(
    store: SyncHistoryStore = Depends(get_sync_history_store),
):
    docs = store.list(limit=500)
    summary = {}

    for doc in docs:
        adapter = doc["adapter"]

        if adapter not in summary:
            summary[adapter] = {
                "last_status": doc["status"],
                "last_run": doc["finished_at"],
                "last_duration_ms": doc["duration_ms"],
                "total_runs": 0,
                "failures": 0,
            }
        summary[adapter]["total_runs"] += 1

        if doc["status"] == "FAILED":
            summary[adapter]["failures"] += 1

    for adapter in summary:
        total = summary[adapter]["total_runs"]
        failures = summary[adapter]["failures"]

        summary[adapter]["success_rate"] = (
            round((total - failures) / total * 100, 2) if total else 0
        )

    return summary


@router.get("/syncs/stats")
async def get_sync_stats(
    store: SyncHistoryStore = Depends(get_sync_history_store),
    current_user=Depends(get_current_user),
):
    """Real-time stats from Celery workers and sync history."""
    active_tasks = 0
    reserved_tasks = 0
    workers = {}

    try:
        inspect = celery_app.control.inspect(timeout=2.0)
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}

        for worker_name, tasks in active.items():
            count = len(tasks)
            active_tasks += count
            workers[worker_name] = {"active": count, "reserved": 0}

        for worker_name, tasks in reserved.items():
            count = len(tasks)
            reserved_tasks += count
            if worker_name in workers:
                workers[worker_name]["reserved"] = count
            else:
                workers[worker_name] = {"active": 0, "reserved": count}

    except Exception as e:
        logger.warning("celery_inspect_failed", error=str(e))

    return {
        "active_tasks": active_tasks,
        "queue_depth": reserved_tasks,
        "worker_count": len(workers),
        "workers": workers,
    }


@router.get("/syncs/{sync_id}")
async def get_sync_history(sync_id: str, store: SyncHistoryStore = Depends(get_sync_history_store)):
    sync = store.get(sync_id)
    if not sync:
        raise NotFoundException(f"Sync {sync_id} not found")
    return sync


@router.get("/syncs/{task_id}/status", response_model=SyncStatusResponse)
async def get_sync_status(task_id: str):
    task = AsyncResult(task_id)

    if task.state == "PENDING":
        return SyncStatusResponse(
            task_id=task_id,
            status="PENDING",
            ready=False,
        )

    if task.state == "FAILURE":
        return SyncStatusResponse(
            task_id=task_id,
            status="FAILURE",
            ready=False,
        )

    if task.state == "SUCCESS":
        return SyncStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            ready=True,
            result=task.result,
        )

    return SyncStatusResponse(
        task_id=task_id,
        status=task.state,
        ready=False,
    )
