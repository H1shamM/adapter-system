from typing import Any, Dict

from pydantic import BaseModel


class AdapterSyncRequest(BaseModel):
    config: Dict[str, Any]


class AdapterSyncResponse(BaseModel):
    task_id: str
    sync_id: str


class HealthResponse(BaseModel):
    adapter: str
    status: str
    message: str
