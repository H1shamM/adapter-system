from typing import List

from pydantic import BaseModel


class AssetResponse(BaseModel):
    id: str
    type: str
    status: str
    data: dict


class AssetListResponse(BaseModel):
    page: int
    limit: int
    total: int
    results: List[AssetResponse]