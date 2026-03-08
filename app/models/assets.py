from pydantic import BaseModel

from datetime import datetime


class NormalizedAsset(BaseModel):
    """Unified asset schema"""
    asset_id: str
    customer_id: str #NEW,  identifies which customer own this asset
    name: str
    asset_type: str
    status: str
    last_seen: datetime
    vendor: str
    metadata: dict = {}


    @classmethod
    def from_raw(cls, raw: dict):
        return cls(**raw)
