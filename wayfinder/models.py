from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Signal:
    source: str
    source_id: str
    source_url: str
    title: str
    body: str = ""
    author: str = ""
    score: float = 0
    product: str = ""
    category: str = ""
    pain_type: str = ""
    feature_request: str = ""
    monetization_signal: str = ""
    collected_at: str = field(default_factory=utc_now)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProductIntel:
    product_name: str
    url: str = ""
    category: str = ""
    pricing_model: str = ""
    strengths: str = ""
    complaints: str = ""
    feature_gaps: str = ""
    audience: str = ""
    monetization_notes: str = ""
    collected_at: str = field(default_factory=utc_now)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Opportunity:
    title: str
    target_user: str = ""
    problem: str = ""
    evidence_count: int = 0
    competing_products: str = ""
    what_products_do_right: str = ""
    what_users_want_better: str = ""
    build_difficulty: str = ""
    replication_time_estimate: str = ""
    iteration_angle: str = ""
    monetization_strategy: str = ""
    foundry_task_suggestions: str = ""
    collected_at: str = field(default_factory=utc_now)
    raw: dict[str, Any] = field(default_factory=dict)
