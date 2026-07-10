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

from sync.database.mode import set_mode, get_mode
from sync.container import get_dest_db, ensure_schema, seed_config
from sync.engine import run_sync_loop

load_dotenv()

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

    dest_db = get_dest_db()
    ensure_schema(dest_db)
    seed_config(dest_db)

    port = int(os.getenv("HEALTH_PORT", "8090"))
    from sync.api import app
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    health_server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.create_task(health_server.serve())
    loop.run_until_complete(run_sync_loop(dest_db, shutdown_event))


if __name__ == "__main__":
    main()
