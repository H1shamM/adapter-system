from fastapi import APIRouter, Query, Depends

from app.api.errors import NotFoundException
from app.api.deps import get_asset_store
from app.api.schemas.assets import AssetListResponse, AssetResponse
from app.storage.assets import AssetStore

router = APIRouter()


@router.get('/assets')
async def list_assets(
        page: int = Query(1, ge=1),
        limit: int = Query(50, le=100),
        asset_type: str | None = None,
        status: str | None = None,
        store: AssetStore = Depends(get_asset_store),
):
    query = {}
    if asset_type:
        query["type"] = asset_type
    if status:
        query["status"] = status

    skip = (page - 1) * limit

    results = store.find_assets(query, skip, limit)
    assets = [store._normalize_asset(res) for res in results]

    total = store.count_assets(query)

    return AssetListResponse(
        results=assets,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
        asset_id: str,
        store: AssetStore = Depends(get_asset_store),
):
    asset = store.get_asset(asset_id)
    if not asset:
        raise NotFoundException(f"Asset {asset_id} not found")
    asset = store._normalize_asset(asset)
    return AssetResponse(
        id=asset_id,
        data=asset,
        status='200',
        type="ASSET"
    )
