from __future__ import annotations

from .base import EngineProbe


class ExamplePainEngineSensor:
    name = "example-pain-engine"

    def collect(self) -> list[EngineProbe]:
        return []
