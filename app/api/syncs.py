from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

router = APIRouter()

@router.get("/syncs/{task_id}")
async def get_sync_status(task_id: str):
    task = AsyncResult(task_id)
    if not task:
        raise HTTPException(404, detail="Task not found")
    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result if task.ready() else None,
        "ready": task.ready()
    }