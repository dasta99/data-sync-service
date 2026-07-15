"""Sync control API — cancel, status, running tasks."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from extract.loop import cancel_table, get_cancelled_tables, get_running_tables
from extract.status import StatusWriter
from shared.connections import PooledDatabaseFactory
from shared.config import ConfigLoader
from shared.mode import get_mode

router = APIRouter()
_loader = ConfigLoader()
_factory = PooledDatabaseFactory()


def _get_db():
    config = _loader.get_destination(get_mode())
    return _factory.get_or_create(f"dest_{get_mode()}", config, pool_size=5)


class CancelResponse(BaseModel):
    table: str
    status: str


@router.post("/{table_name}/cancel", response_model=CancelResponse)
def cancel_sync(table_name: str):
    """Cancel a running sync for the given table."""
    cancelled = cancel_table(table_name)
    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' is not currently running")
    return CancelResponse(table=table_name, status="cancel_requested")


@router.get("/running")
def running_tables():
    """List all currently running sync tasks."""
    return {"running": get_running_tables(), "total": len(get_running_tables())}


@router.get("/cancelled")
def cancelled_tables():
    """List all tables with pending cancellation."""
    return {"cancelled": list(get_cancelled_tables()), "total": len(get_cancelled_tables())}
