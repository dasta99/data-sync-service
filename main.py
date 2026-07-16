"""Entry point — signal handling, CLI args, launch."""

import os
import sys
import signal
import asyncio
import logging
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn
from dotenv import load_dotenv

from shared.mode import set_mode, get_mode
from shared.connections import PooledDatabaseFactory
from shared.config import ConfigLoader
from shared.repositories import SchemaManager, TableConfigRepository
from extract.loop import run_sync_loop
from transform.orchestrator import TransformOrchestrator

# Don't load .env.local on host — it has Docker container names
# Only load .env (production creds) and rely on config.yaml defaults for --local
load_dotenv(override=False, dotenv_path=".env" if os.path.exists(".env") else None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
logger = logging.getLogger("sync.main")

shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    logger.info("Shutdown signal received")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    parser = argparse.ArgumentParser(description="Data sync service")
    parser.add_argument("--local", action="store_true", help="Use local Docker MySQL")
    args = parser.parse_args()

    set_mode("local" if args.local else "prod")
    logger.info(f"Starting data-sync-service [{'LOCAL' if get_mode() == 'local' else 'PRODUCTION'}]")

    # Initialize destination DB
    loader = ConfigLoader()
    factory = PooledDatabaseFactory()
    config = loader.get_destination(get_mode())
    dest_db = factory.get_or_create(f"dest_{get_mode()}", config, pool_size=5)
    if get_mode() == "local":
        logger.info(f"  dest: {config['host']}:{config['port']}/{config['database']}")

    # Ensure schema and seed config
    SchemaManager(dest_db).ensure_tables()
    default_source = "local" if get_mode() == "local" else "mytdp_remote"
    TableConfigRepository(dest_db).seed_initial_config(default_source=default_source)

    # Initialize transform orchestrator (with source DB factory for transform queries)
    def source_db_factory(name: str):
        source_config = loader.get_source(name)
        if get_mode() == "local":
            logger.info(f"  source '{name}': {source_config['host']}:{source_config['port']}/{source_config['database']}")
        return factory.get_or_create(f"source_{name}", source_config, pool_size=3)

    orchestrator = TransformOrchestrator(dest_db, source_db_factory=source_db_factory, default_source=default_source)
    orchestrator.initialize()

    # Health API server
    port = int(os.getenv("HEALTH_PORT", "8090"))
    from shared.api import app
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    health_server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.create_task(health_server.serve())
    loop.run_until_complete(
        run_sync_loop(dest_db, shutdown_event, on_sync_complete=orchestrator.notify)
    )


if __name__ == "__main__":
    main()
