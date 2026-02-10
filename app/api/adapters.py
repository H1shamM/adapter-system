import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from kombu.exceptions import OperationalError

from app.adapters.base import AdapterConfig
from app.adapters.errors import AuthenticationError
from app.adapters.factory import build_adapter
from app.adapters.registry import SUPPORTED_ADAPTERS
from app.adapters.schemas import ADAPTER_SCHEMAS
from app.api.deps import get_adapter_config_store, get_sync_history_store
from app.api.registry import ADAPTER_CONFIGS
from app.api.schemas.adapters import AdapterSyncResponse, HealthResponse
from app.storage.adapters import AdapterConfigStore
from app.storage.sync_history import SyncHistoryStore
from app.tasks.core import sync_adapter_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/adapters/{adapter_type}/sync",
    response_model=AdapterSyncResponse,
)
async def trigger_sync(
        adapter_type: str,
        history: SyncHistoryStore = Depends(get_sync_history_store),
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    adapter_type = adapter_type.lower()
    if adapter_type not in SUPPORTED_ADAPTERS:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter  {adapter_type} not supported"
        )
    config = store.get(adapter_type)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter  {adapter_type} not Configured"
        )
    sync_id = str(uuid4())
    try:
        logger.info("Queuing adapter sync task", extra={"adapter_type": adapter_type, "config": config})
        task = sync_adapter_task.delay(adapter_type, config, sync_id)
        history.start_sync(
            sync_id=sync_id,
            adapter=adapter_type,
        )

    except OperationalError:
        logger.error("Failed to queue adapter sync task", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Task queue unavailable"
        )
    return AdapterSyncResponse(
        task_id=task.id,
        sync_id=sync_id,
    )


@router.get("/adapters")
async def list_adapters():
    return {
        "available": list(SUPPORTED_ADAPTERS),
        "active": list(SUPPORTED_ADAPTERS)
    }


@router.post("/adapters")
async def upsert_adapter(
        payload: dict,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    adapter_name = payload.get("name")
    if adapter_name not in SUPPORTED_ADAPTERS:
        raise HTTPException(400, "Unknown adapter")

    schema = ADAPTER_CONFIGS.get(adapter_name)
    user_config = schema(**payload)

    store.upsert(name=adapter_name, config=user_config.dict(exclude_unset=True))
    return {"status": "saved"}


@router.get("/adapters/{name}")
async def get_adapter(
        name: str,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    config = store.get(name)
    return {
        "name": name,
        "enabled": bool(config),
        "config": config or {},
    }

@router.get("/adapters/{name}/schema")
async def get_adapter_schema(name: str):
    return ADAPTER_SCHEMAS.get(name, {})

@router.post("/adapters/{adapter_name}/health")
async def health_check(
        adapter_name: str,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    config = store.get(adapter_name)

    if not config:
        return HealthResponse(
            adapter=adapter_name,
            status="UNKNOWN",
            message=f"Adapter {adapter_name} not configured"

        )
    if not config.get("enabled", True):
        return HealthResponse(
            adapter=adapter_name,
            status="DISABLED",
            message=f"Adapter {adapter_name} disabled"
        )

    try:
        adapter = build_adapter(adapter_name, config)
        adapter.connect()

        return HealthResponse(
            adapter=adapter_name,
            status="HEALTHY",
            message=f"Adapter {adapter_name} healthy"
        )

    except AuthenticationError as e:
        return HealthResponse(
            adapter=adapter_name,
            status="UNHEALTHY",
            message=f"Adapter {adapter_name} unhealthy {str(e)}"
        )
    except Exception as e:
        return HealthResponse(
            adapter=adapter_name,
            status="UNHEALTHY",
            message=f"Adapter {adapter_name} Failed {str(e)}"
        )
