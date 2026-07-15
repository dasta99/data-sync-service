"""Transform handler registry — discovers and manages handlers."""

import importlib
import logging
import pathlib
from typing import Dict, List, Optional

import yaml

from transform.base import TransformHandler

logger = logging.getLogger("transform.registry")

_registry: Dict[str, TransformHandler] = {}
_configs: Dict[str, dict] = {}


def register(name: str, handler: TransformHandler, config: Optional[dict] = None):
    """Register a handler manually."""
    _registry[name] = handler
    if config:
        _configs[name] = config
    logger.info(f"Registered transform handler: {name}")


def get_handler(name: str) -> Optional[TransformHandler]:
    """Get a registered handler by name."""
    return _registry.get(name)


def get_all_handlers() -> Dict[str, TransformHandler]:
    """Get all registered handlers."""
    return dict(_registry)


def get_handler_config(name: str) -> dict:
    """Get config for a registered handler."""
    return _configs.get(name, {})


def discover_handlers(base_dir: str = None):
    """Auto-discover handlers from transform/*/config.yaml.

    Each domain folder should have:
    - config.yaml with name, depends_on, outputs
    - handler.py with a Handler class implementing TransformHandler
    """
    if base_dir is None:
        base_dir = str(pathlib.Path(__file__).parent)

    base_path = pathlib.Path(base_dir)

    for domain_dir in sorted(base_path.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name.startswith("_"):
            continue

        config_path = domain_dir / "config.yaml"
        if not config_path.exists():
            continue

        try:
            config = yaml.safe_load(config_path.read_text())
            handler_name = config.get("name", domain_dir.name)

            # Import handler module
            module_path = f"transform.{domain_dir.name}.handler"
            module = importlib.import_module(module_path)

            # Expect a Handler class in handler.py
            handler_cls = getattr(module, "Handler")
            handler_instance = handler_cls()

            register(handler_name, handler_instance, config)
            logger.info(f"Discovered transform handler: {handler_name} from {domain_dir.name}/")

        except Exception as e:
            logger.error(f"Failed to load handler from {domain_dir.name}/: {e}")


def get_dependency_map() -> Dict[str, List[str]]:
    """Return {handler_name: [dep_tables]} for all registered handlers."""
    return {name: h.depends_on for name, h in _registry.items()}
