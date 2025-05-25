from pydantic import BaseModel
from typing import Optional

class NormalizedAsset(BaseModel):
    asset_id: str
    name: str
    status: str
    last_seen: str
    vendor: str
    asset_type: str
    ip_address: Optional[str] = None
    os_type: Optional[str] = None
