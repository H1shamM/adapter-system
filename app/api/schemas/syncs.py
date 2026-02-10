from pydantic import BaseModel
from typing import Optional, Any

class SyncStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    result: Optional[Any] = None
    error: Optional[Any] = None