from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from kombu.exceptions import OperationalError

from app.adapters.errors import AuthenticationError
from app.adapters.factory import build_adapter
from app.adapters.registry import SUPPORTED_ADAPTERS
from app.adapters.schemas import ADAPTER_SCHEMAS
from app.api.deps import get_adapter_config_store, get_sync_history_store
from app.api.registry import ADAPTER_CONFIGS
from app.api.schemas.adapters import AdapterSyncResponse, HealthResponse
from app.auth.dependencies import get_current_user
from app.storage.adapters import AdapterConfigStore
from app.storage.sync_history import SyncHistoryStore
from app.tasks.core import sync_adapter_task
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/adapters/{adapter_id}/sync",
    response_model=AdapterSyncResponse,
)
async def trigger_sync(
        adapter_id: str,
        history: SyncHistoryStore = Depends(get_sync_history_store),
        store: AdapterConfigStore = Depends(get_adapter_config_store),
        current_user=Depends(get_current_user)
):
    config = store.get(adapter_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter instance '{adapter_id}' not found"
        )

    adapter_type = config.get("adapter_type")
    if adapter_type not in SUPPORTED_ADAPTERS:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter type '{adapter_type}' not supported"
        )

    sync_id = str(uuid4())
    try:
        logger.info(
            "Queuing adapter sync task",
            adapter_id=adapter_id,
            adapter_type=adapter_type,
            sync_id=sync_id
        )
        task = sync_adapter_task.delay(adapter_id, adapter_type, config, sync_id)
        history.start_sync(
            sync_id=sync_id,
            adapter=adapter_id,
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
async def list_adapters(
        adapter_type: str = None,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    if adapter_type:
        instances = store.get_by_type(adapter_type)
    else:
        instances = store.list_all()

    return {
        "total": len(instances),
        "instances": instances,
        "supported_types": list(SUPPORTED_ADAPTERS)
    }


@router.post("/adapters")
async def upsert_adapter(
        payload: dict,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    adapter_type = payload.get("adapter_type") or payload.get("name")

    if not adapter_type:
        raise HTTPException(400, "Missing adapter type")

    if adapter_type not in SUPPORTED_ADAPTERS:
        raise HTTPException(400, f"Unknown adapter type: {adapter_type}")

    adapter_id = payload.get("adapter_id")
    if not adapter_id:
        from uuid import uuid4
        adapter_id = f"{adapter_type}_{uuid4().hex[:8]}"

    schema = ADAPTER_CONFIGS.get(adapter_type)
    user_config = schema(**payload)
    config_dict = user_config.dict(exclude_unset=True)

    store.upsert(
        adapter_id=adapter_id,
        adapter_type=adapter_type,
        config=config_dict
    )

    if config_dict.get("enabled", True):
        sync_interval = config_dict.get("sync_interval", 3600)
        store.set_next_sync(adapter_id, sync_interval)
    return {
        "status": "saved",
        "adapter_id": adapter_id,
        "adapter_type": adapter_type,
    }


@router.get("/adapters/{adapter_id}")
async def get_adapter(
        adapter_id: str,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    config = store.get(adapter_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter instance {adapter_id} not found",
        )

    return {
        "adapter_id": adapter_id,
        "adapter_type": config.get("adapter_type"),
        "enabled": config.get("enabled", True),
        "config": config,
    }


@router.get("/adapters/{name}/schema")
async def get_adapter_schema(name: str):
    return ADAPTER_SCHEMAS.get(name, {})


@router.post("/adapters/{adapter_id}/health")
async def health_check(
        adapter_id: str,
        store: AdapterConfigStore = Depends(get_adapter_config_store)
):
    config = store.get(adapter_id)

    if not config:
        return HealthResponse(
            adapter=adapter_id,
            status="UNKNOWN",
            message=f"Adapter {adapter_id} not configured"
        )
    if not config.get("enabled", True):
        return HealthResponse(
            adapter=adapter_id,
            status="DISABLED",
            message=f"Adapter {adapter_id} disabled"
        )

    adapter_type = config.get("adapter_type")
    try:
        adapter = build_adapter(adapter_type, config)
        await adapter.connect()

        return HealthResponse(
            adapter=adapter_id,
            status="HEALTHY",
            message=f"Adapter {adapter_id} healthy"
        )

    except AuthenticationError as e:
        return HealthResponse(
            adapter=adapter_id,
            status="UNHEALTHY",
            message=f"Adapter {adapter_id} unhealthy: {str(e)}"
        )
    except Exception as e:
        return HealthResponse(
            adapter=adapter_id,
            status="UNHEALTHY",
            message=f"Adapter {adapter_id} failed: {str(e)}"
        )
