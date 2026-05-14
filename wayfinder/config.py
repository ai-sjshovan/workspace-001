from __future__ import annotations

import pathlib
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "wayfinder.yaml"


def _config_dir(config: dict[str, Any]) -> pathlib.Path:
    value = config.get("_config_dir")
    return pathlib.Path(str(value)) if value else ROOT


def _resolve_path(config: dict[str, Any], value: Any, fallback: pathlib.Path) -> pathlib.Path:
    if not value:
        return fallback
    path = pathlib.Path(str(value))
    return path if path.is_absolute() else (_config_dir(config) / path).resolve()


def load_config(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    config_path = pathlib.Path(path) if path else DEFAULT_CONFIG
    if not config_path.exists():
        raise FileNotFoundError(f"Wayfinder config not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"_config_dir": str(config_path.resolve().parent)}
    data["_config_dir"] = str(config_path.resolve().parent)
    return data


def wayfinder_section(config: dict[str, Any]) -> dict[str, Any]:
    value = config.get("wayfinder")
    return value if isinstance(value, dict) else {}


def storage_path(config: dict[str, Any]) -> pathlib.Path:
    value = wayfinder_section(config).get("storage_path")
    return _resolve_path(config, value, ROOT / ".ai-state" / "wayfinder" / "wayfinder.db")


def audit_log_path(config: dict[str, Any]) -> pathlib.Path:
    value = wayfinder_section(config).get("audit_log")
    return _resolve_path(config, value, ROOT / "logs" / "wayfinder-audit.log")


def source_configs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = config.get("sources")
    if not isinstance(sources, dict):
        return {}
    config_dir = str(_config_dir(config))
    resolved: dict[str, dict[str, Any]] = {}
    for name, value in sources.items():
        if isinstance(value, dict):
            resolved[str(name)] = {**value, "_config_dir": config_dir}
    return resolved
