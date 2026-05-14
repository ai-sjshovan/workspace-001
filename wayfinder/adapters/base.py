from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..models import Opportunity, ProductIntel, Signal


@dataclass(slots=True)
class NormalizedBatch:
    signals: list[Signal] = field(default_factory=list)
    products: list[ProductIntel] = field(default_factory=list)
    opportunities: list[Opportunity] = field(default_factory=list)


class Adapter(Protocol):
    name: str
    config: dict[str, Any]

    def healthcheck(self) -> tuple[bool, str]:
        ...

    def collect(self) -> list[dict[str, Any]]:
        ...

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        ...
