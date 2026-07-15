"""Config CRUD API — manage sync_config via REST."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.interfaces import Database
from shared.connections import PooledDatabaseFactory
from shared.config import ConfigLoader
from shared.repositories import TableConfigRepository
from shared.mode import get_mode

router = APIRouter()
_loader = ConfigLoader()
_factory = PooledDatabaseFactory()


def _get_db() -> Database:
    config = _loader.get_destination(get_mode())
    return _factory.get_or_create(f"dest_{get_mode()}", config, pool_size=5)


def _get_repo() -> TableConfigRepository:
    return TableConfigRepository(_get_db())


# ─── Pydantic Models ─────────────────────────────────────────


class SyncConfigCreate(BaseModel):
    table_name: str
    source_name: str
    source_table: str
    dest_table: str
    enabled: bool = True
    poll_interval: int = Field(default=30, ge=1)
    batch_size: int = Field(default=500, ge=1)
    watermark_column: str = "updated_at"
    primary_key: str = "id"
    columns: List[str] = Field(default_factory=list)
    filters: List[str] = Field(default_factory=list)
    timezone_offset: int = 0
    no_data_threshold: int = Field(default=2, ge=0)
    backoff_multiplier: int = Field(default=2, ge=1)
    max_poll_interval: int = Field(default=600, ge=1)


class SyncConfigUpdate(BaseModel):
    source_name: Optional[str] = None
    source_table: Optional[str] = None
    dest_table: Optional[str] = None
    enabled: Optional[bool] = None
    poll_interval: Optional[int] = Field(default=None, ge=1)
    batch_size: Optional[int] = Field(default=None, ge=1)
    watermark_column: Optional[str] = None
    primary_key: Optional[str] = None
    columns: Optional[List[str]] = None
    filters: Optional[List[str]] = None
    timezone_offset: Optional[int] = None
    no_data_threshold: Optional[int] = Field(default=None, ge=0)
    backoff_multiplier: Optional[int] = Field(default=None, ge=1)
    max_poll_interval: Optional[int] = Field(default=None, ge=1)


# ─── Routes ──────────────────────────────────────────────────


@router.get("")
def list_configs(enabled_only: bool = True):
    """List all table configs. Use ?enabled_only=false to include disabled."""
    try:
        repo = _get_repo()
        tables = repo.get_enabled_tables() if enabled_only else repo.get_all_tables()
        return {"tables": tables, "total": len(tables)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{table_name}")
def get_config(table_name: str):
    """Get a single table config."""
    try:
        repo = _get_repo()
        config = repo.get_table_config(table_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201)
def create_config(body: SyncConfigCreate):
    """Create a new table sync config."""
    try:
        repo = _get_repo()
        existing = repo.get_table_config(body.table_name)
        if existing:
            raise HTTPException(status_code=409, detail=f"Table '{body.table_name}' already exists")
        config = repo.create(body.model_dump())
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{table_name}")
def update_config(table_name: str, body: SyncConfigUpdate):
    """Update an existing table config (partial update)."""
    try:
        repo = _get_repo()
        existing = repo.get_table_config(table_name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        fields = {k: v for k, v in body.model_dump().items() if v is not None}
        config = repo.update(table_name, fields)
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{table_name}")
def delete_config(table_name: str):
    """Delete a table sync config."""
    try:
        repo = _get_repo()
        deleted = repo.delete(table_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        return {"deleted": table_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
