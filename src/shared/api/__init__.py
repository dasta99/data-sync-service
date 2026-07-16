"""FastAPI app — mounts all routers."""

from fastapi import FastAPI

from shared.api.health import app as health_app
from shared.api.config import router as config_router
from shared.api.sync import router as sync_router

health_app.include_router(config_router, prefix="/config", tags=["config"])
health_app.include_router(sync_router, prefix="/sync", tags=["sync"])

app = health_app
