from pydantic import BaseModel, Field

from datetime import datetime


class NormalizedAsset(BaseModel):
    """Unified asset schema — all adapters normalize vendor data into this model."""
    asset_id: str
    customer_id: str
    name: str
    asset_type: str
    status: str
    last_seen: datetime
    vendor: str
    metadata: dict = Field(default_factory=dict)


    @classmethod
    def from_raw(cls, raw: dict):
        return cls(**raw)
