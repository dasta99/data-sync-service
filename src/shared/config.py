"""YAML config loader — reads config.yaml and resolves env variables."""

import os
import pathlib
from typing import Any, Dict

import yaml

_CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent / "config.yaml"


class ConfigLoader:
    """Loads database configs from YAML, resolves ${ENV_VAR} references."""

    def __init__(self, yaml_path: str = None):
        self._path = str(yaml_path or _CONFIG_PATH)
        self._data = None

    def _load(self) -> dict:
        if self._data is None:
            with open(self._path, "r") as f:
                self._data = yaml.safe_load(f)
        return self._data

    def _resolve(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            inner = value[2:-1]
            if ":" in inner:
                var_name, default = inner.split(":", 1)
                return os.getenv(var_name, default)
            return os.getenv(inner, "")
        return value

    def get_sources(self) -> Dict[str, dict]:
        return self._resolve(self._load().get("sources", {}))

    def get_destination(self, mode: str = "prod") -> dict:
        dests = self._load().get("destination", {})
        return self._resolve(dests.get(mode, dests.get("prod", {})))

    def get_source(self, name: str) -> dict:
        sources = self.get_sources()
        if name not in sources:
            raise ValueError(f"Unknown source: {name}")
        return sources[name]
