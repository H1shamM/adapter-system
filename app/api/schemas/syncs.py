from typing import Any, Optional

from pydantic import BaseModel


class SyncStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    result: Optional[Any] = None
    error: Optional[Any] = None
