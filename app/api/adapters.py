from fastapi import APIRouter
from app.tasks.core import sync_adapter_task

router =  APIRouter()

@router.post("/adapters/{adapter_type}/sync")
async def trigger_sync(adapter_type: str, config:dict):
    task = sync_adapter_task.delay(adapter_type, config)
    return {"task_id": task.id}

@router.get("/adapters")
async def list_adapters():
    return  {
        "available" : ["github" , "aws", "mock"],
        "active" : ["github", "mock"]
    }

