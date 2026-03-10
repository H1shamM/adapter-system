from datetime import datetime

import psutil
from fastapi import APIRouter
from starlette import status
from starlette.responses import JSONResponse

from app.config import settings
from app.db.mongo import get_mongo_client
from app.tasks.core import app as celery_app

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness_check():
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "customer_id": settings.customer_id,
        "instance_id": settings.instance_id,
    }


@router.get("/ready")
async def readiness_check():
    checks = {}
    all_ready = True

    try:
        client = get_mongo_client()

        client.admin.command('ping', maxTimeMS=2000)

        checks["mongodb"] = {
            "status": "healthy",
            "response_time_ms": "<2000"
        }
    except Exception as e:
        checks["mongodb"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_ready = False

    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        checks["celery"] = {
            "status": "healthy" if active_workers else "unhealthy",
            "workers": len(active_workers) if active_workers else 0,
        }
    except Exception as e:
        checks["celery"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_ready = False

    response = {
        "status": "ready" if all_ready else "not ready",
        "timestamp": datetime.now().isoformat(),
        "customer_id": settings.customer_id,
        "instance_id": settings.instance_id,
        "checks": checks
    }

    status_code = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(response, status_code=status_code)


@router.get("/info")
async def instance_info():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "customer_id": settings.customer_id,
        "instance_id": settings.instance_id,
        "environment": settings.environment,

        "app_name": settings.app_name,
        "app_version": settings.app_version,

        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "disk_available_gb": round(disk.free / (1024 ** 3), 2),
        },

        "database": {
            "database_name": settings.database.mongo_db_name,
            "max_pool_size": settings.database.mongo_max_pool_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/startup")
async def startup_check():
    try:
        client = get_mongo_client()
        client.admin.command('ping', maxTimeMS=5000)

        return {
            "status": "started",
            "customer_id": settings.customer_id,
            "instance_id": settings.instance_id,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return JSONResponse(
            content={
                "status": "starting",
                "error": str(e),
                "customer_id": settings.customer_id,
                "timestamp": datetime.now().isoformat(),
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
