"""FastAPI app — mounts all routers."""

from fastapi import FastAPI

from sync.api.health import app as health_app
from sync.api.config import router as config_router

health_app.include_router(config_router, prefix="/config", tags=["config"])

app = health_app
