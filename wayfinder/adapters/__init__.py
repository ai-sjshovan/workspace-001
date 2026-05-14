from __future__ import annotations

from typing import Any

from .base import Adapter, NormalizedBatch
from .github import GitHubAdapter
from .hackernews import HackerNewsAdapter
from .static_ledger import StaticLedgerAdapter


def build_adapter(name: str, config: dict[str, Any]) -> Adapter:
    kind = str(config.get("kind") or name)
    if kind == "github":
        return GitHubAdapter(name, config)
    if kind == "hackernews":
        return HackerNewsAdapter(name, config)
    if kind == "static_ledger":
        return StaticLedgerAdapter(name, config)
    raise ValueError(f"Unsupported Wayfinder source kind: {kind}")


__all__ = ["Adapter", "NormalizedBatch", "build_adapter"]
