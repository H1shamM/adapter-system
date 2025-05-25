from pydantic import BaseModel

from datetime import datetime


class NormalizedAsset(BaseModel):
    """Unified asset schema"""
    asset_id: str
    name: str
    asset_type: str
    status: str
    last_seen: datetime
    vendor: str
    metadata: dict = {}

    @classmethod
    def from_raw(cls, raw: dict):
        """Optional factory method for adapters"""
        return cls(**raw)