from fastapi import APIRouter ,Query

from app.api.errors import NotFoundException
from app.storage.assets import AssetStore

router = APIRouter()
store = AssetStore()

@router.get('/assets')
async def list_assets(
        page: int = Query(1, ge= 1),
        limit: int = Query(50, le=100),
        type: str =None,
        status: str =None
):
    query = {}
    if type: query["type"] = type
    if status: query["status"] = status

    skip = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "results": store.find_assets(query, skip , limit)
    }

@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    asset = store.get_asset(asset_id)
    if not asset:
        raise NotFoundException(f"Asset {asset_id} not found")
    return asset
