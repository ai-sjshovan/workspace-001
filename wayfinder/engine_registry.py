from __future__ import annotations

from importlib import import_module
from typing import Any

from .config import engine_configs
from .models import EngineDefinition


def inspect_engine(engine: EngineDefinition) -> dict[str, Any]:
    if not engine.module:
        return {
            "name": engine.name,
            "module": "",
            "object": engine.object_name,
            "importable": False,
            "sensors_only": engine.sensors_only,
            "notes": engine.notes,
            "error": "missing module path",
        }
    try:
        module = import_module(engine.module)
    except Exception as exc:  # noqa: BLE001
        return {
            "name": engine.name,
            "module": engine.module,
            "object": engine.object_name,
            "importable": False,
            "sensors_only": engine.sensors_only,
            "notes": engine.notes,
            "error": str(exc),
        }
    if engine.object_name:
        try:
            getattr(module, engine.object_name)
        except AttributeError as exc:
            return {
                "name": engine.name,
                "module": engine.module,
                "object": engine.object_name,
                "importable": False,
                "sensors_only": engine.sensors_only,
                "notes": engine.notes,
                "error": str(exc),
            }
    return {
        "name": engine.name,
        "module": engine.module,
        "object": engine.object_name,
        "importable": True,
        "sensors_only": engine.sensors_only,
        "notes": engine.notes,
        "error": "",
    }


def registry_snapshot(config: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for engine in engine_configs(config).values():
        snapshot.append(inspect_engine(engine))
    return sorted(snapshot, key=lambda item: item["name"])
