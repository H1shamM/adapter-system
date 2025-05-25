from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.adapters import router as adapters_router
from app.api.syncs import router as syncs_router

app = FastAPI()
metrics_app = make_asgi_app()

app.include_router(adapters_router, prefix="/api/v1")
app.include_router(syncs_router, prefix="/api/v1")

app.mount("/metrics", metrics_app)

@app.get('/')
async  def root():
    return  {"message": "Adapter System API"}