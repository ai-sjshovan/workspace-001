from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class EngineProbe:
    title: str
    source: str
    detail: str = ""


class EngineSensor(Protocol):
    name: str

    def collect(self) -> list[EngineProbe]:
        ...
