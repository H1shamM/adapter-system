from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.tasks import process_adapter

app = FastAPI()


class AdapterRequest(BaseModel):
    adapter_type: str
    config: dict  # Now takes full config (API keys, etc.)


@app.post("/sync")
def trigger_sync(request: AdapterRequest):
    """Generic sync endpoint"""
    if request.adapter_type not in ["github"]:  # Add new adapters here
        raise HTTPException(status_code=400, detail="Invalid adapter type")

    task = process_adapter.delay(request.adapter_type, request.config)
    return {
        "status": "queued",
        "task_id": task.id,
        "adapter": request.adapter_type
    }
