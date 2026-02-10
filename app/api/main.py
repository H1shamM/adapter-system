import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from prometheus_client import make_asgi_app
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.adapters import router as adapters_router
from app.api.syncs import router as syncs_router
from app.api.assets import router as assets_router

app = FastAPI(
    title="Adapter System API",
    version="1.0.0",
)

logger = logging.getLogger(__name__)


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

app.include_router(adapters_router, prefix="/api/v1")
app.include_router(syncs_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")

app.mount("/metrics", metrics_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def root():
    return {"message": "Adapter System API"}
