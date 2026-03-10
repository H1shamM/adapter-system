from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from app.api.adapters import router as adapters_router
from app.api.assets import router as assets_router
from app.api.health import router as health_router
from app.api.syncs import router as syncs_router
from app.auth.router import router as auth_router
from app.config.settings import settings
from app.db.mongo import close_mongo_client
from app.utils.logging import get_logger, setup_logging

# setup structured logging
setup_logging()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.api.api_debug,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        enviorment=settings.environment,
        customer_id=settings.customer_id,
        instance_id=settings.instance_id
    )
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.app_name} v{settings.app_version}")
    close_mongo_client()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc):
    logger.error(f"HTTP exception occurred: {exc.detail} - Path: {request.base_url}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body.decode() if isinstance(exc.body, (bytes, bytearray)) else exc.body,
        })


metrics_app = make_asgi_app()

app.include_router(adapters_router, prefix="/api/v1", )
app.include_router(syncs_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

app.mount("/metrics", metrics_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def root():
    return {
        "message": f"{settings.app_name} API",
        "version": settings.app_version,
        "environment": settings.environment,
        "customer_id": settings.customer_id,
        "instance_id": settings.instance_id,
        "health_checks": {
            "liveness": "health/live",
            "readiness": "health/ready",
            "info": "health/info",
            "startup": "health/startup",
        },
        "documentation": "/docs",
    }

@app.get('/debug/dev')
async def debug_dev():
    import os
    return {
        "customer_id_from_settings": settings.customer_id,
        "customer_id_from_env": os.getenv("CUSTOMER_ID"),
        "mongo_url_from_settings": settings.database.mongo_url,
        "mongo_url_from_env": os.getenv("MONGO_URL"),
        "all_env_vars": {k: v for k, v in os.environ.items() if k.startswith(('CUSTOMER', 'MONGO', 'API', 'ADAPTER'))}
    }
