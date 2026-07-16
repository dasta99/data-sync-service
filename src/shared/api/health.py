"""Health check endpoints using FastAPI dependency injection."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from shared.interfaces import Database
from shared.connections import PooledDatabaseFactory
from shared.config import ConfigLoader
from shared.repositories import TableConfigRepository
from shared.mode import get_mode
from extract.status import StatusWriter
from extract.history import HistoryLogger

app = FastAPI(title="Data Sync Service")

_loader = ConfigLoader()
_factory = PooledDatabaseFactory()


def _get_db() -> Database:
    config = _loader.get_destination(get_mode())
    return _factory.get_or_create(f"dest_{get_mode()}", config, pool_size=5)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    try:
        db = _get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return {"database": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"database": "unreachable", "error": str(e)})


@app.get("/health/sync")
def sync_health():
    try:
        db = _get_db()
        writer = StatusWriter(db)
        rows = writer.get_all_status()
        unhealthy = [r for r in rows if r.get("consecutive_errors", 0) >= 3 or r.get("status") == "error"]
        return {
            "total_tables": len(rows),
            "healthy": len(rows) - len(unhealthy),
            "unhealthy": len(unhealthy),
            "overall": "ok" if not unhealthy else "degraded",
            "tables": rows,
        }
    except Exception as e:
        return JSONResponse(status_code=503, content={"error": str(e)})


@app.get("/health/history/{table_name}")
def sync_history(table_name: str):
    try:
        db = _get_db()
        logger = HistoryLogger(db)
        runs = logger.get_history(table_name)
        return {"table": table_name, "runs": runs, "total": len(runs)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
