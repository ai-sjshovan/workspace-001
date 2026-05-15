from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


SourceStatus = Literal["enabled", "dry-run-only", "needs-review", "disabled"]


@dataclass(slots=True)
class SourceRiskReview:
    credentials: str = "none"
    terms: str = "review-required"
    rate_limits: str = "unknown"
    scraping: str = "none"
    pii_user_generated_content: str = "none"
    hosted_dependencies: str = "none"


@dataclass(slots=True)
class SourceReviewPolicy:
    status: SourceStatus = "needs-review"
    notes: str = ""
    risk: SourceRiskReview = field(default_factory=SourceRiskReview)


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
    source: str = ""
    category: str = ""
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


DEFAULT_SCORING_WEIGHTS = {
    "pain": 0.35,
    "freshness": 0.15,
    "recurrence": 0.20,
    "source_quality": 0.15,
    "build_fit": 0.15,
}

LEGACY_SCORING_WEIGHT_ALIASES = {
    "pain": ("evidence_count_weight",),
    "freshness": (),
    "recurrence": ("monetization_signal_weight",),
    "source_quality": (),
    "build_fit": (),
}


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def scoring_weights(config: dict[str, Any] | None = None) -> dict[str, float]:
    section = config.get("scoring") if isinstance(config, dict) else {}
    resolved: dict[str, float] = {}
    for key, default in DEFAULT_SCORING_WEIGHTS.items():
        value = default
        if isinstance(section, dict):
            if f"{key}_weight" in section:
                value = section.get(f"{key}_weight", default)
            else:
                for legacy_key in LEGACY_SCORING_WEIGHT_ALIASES.get(key, ()):
                    if legacy_key in section:
                        value = section.get(legacy_key, default)
                        break
        try:
            resolved[key] = max(float(value), 0.0)
        except (TypeError, ValueError):
            resolved[key] = default
    total = sum(resolved.values())
    if total <= 0:
        return DEFAULT_SCORING_WEIGHTS.copy()
    return {key: value / total for key, value in resolved.items()}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _keyword_hits(text: str, words: tuple[str, ...]) -> int:
    haystack = text.lower()
    return sum(1 for word in words if word in haystack)


def _pain_input(opportunity: Opportunity) -> float:
    text = " ".join(
        [
            opportunity.title,
            opportunity.problem,
            opportunity.what_users_want_better,
            opportunity.iteration_angle,
            str(opportunity.raw.get("verdict") or ""),
        ]
    )
    pain_terms = (
        "pain",
        "problem",
        "need",
        "friction",
        "manual",
        "slow",
        "delay",
        "urgent",
        "bottleneck",
        "blocked",
        "better",
        "faster",
    )
    soft_terms = ("inspect", "research", "review", "idea", "candidate")
    score = 0.25 + min(opportunity.evidence_count, 5) * 0.08
    score += _keyword_hits(text, pain_terms) * 0.06
    score -= _keyword_hits(text, soft_terms) * 0.03
    return _clamp(score)


def _freshness_input(opportunity: Opportunity, reference_time: datetime | None = None) -> float:
    try:
        collected_at = parse_timestamp(opportunity.collected_at)
    except ValueError:
        return 0.5
    baseline = reference_time or collected_at
    age_days = max((baseline - collected_at).total_seconds() / 86400.0, 0.0)
    return _clamp(1.0 - min(age_days, 180.0) / 180.0, 0.2, 1.0)


def _source_quality_input(opportunity: Opportunity) -> float:
    raw = opportunity.raw
    license_value = str(raw.get("license") or "").lower()
    useful_outputs = raw.get("useful_outputs") if isinstance(raw.get("useful_outputs"), list) else []
    safety_risks = raw.get("safety_risks") if isinstance(raw.get("safety_risks"), list) else []
    score = 0.35
    if license_value in {"mit", "apache-2.0", "apache", "bsd-3-clause", "bsd", "mpl-2.0"}:
        score += 0.25
    if str(raw.get("url") or "").startswith("https://github.com/"):
        score += 0.1
    score += min(len(useful_outputs), 4) * 0.08
    score -= min(len(safety_risks), 4) * 0.05
    if "high-leverage" in str(raw.get("verdict") or "").lower():
        score += 0.08
    return _clamp(score)


def _build_fit_input(opportunity: Opportunity) -> float:
    raw = opportunity.raw
    complexity = (opportunity.build_difficulty or str(raw.get("install_complexity") or "")).lower()
    reuse_code = str(raw.get("can_reuse_code") or "").lower()
    reuse_ideas = str(raw.get("can_reuse_ideas") or "").lower()

    score = 0.3
    score += {
        "low": 0.35,
        "medium": 0.2,
        "high": 0.05,
        "unknown": 0.1,
    }.get(complexity, 0.1)
    score += {
        "high": 0.22,
        "partial": 0.16,
        "inspect-first": 0.1,
        "low": 0.04,
        "unlikely": 0.0,
    }.get(reuse_code, 0.05)
    score += {
        "high": 0.18,
        "medium": 0.1,
        "low": 0.03,
    }.get(reuse_ideas, 0.04)
    return _clamp(score)


def _recurrence_input(opportunity: Opportunity) -> float:
    useful_outputs = opportunity.raw.get("useful_outputs") if isinstance(opportunity.raw.get("useful_outputs"), list) else []
    text = " ".join(
        [
            opportunity.problem,
            opportunity.what_users_want_better,
            opportunity.iteration_angle,
            opportunity.target_user,
            str(opportunity.raw.get("verdict") or ""),
            " ".join(str(item) for item in useful_outputs),
        ]
    )
    recurrence_terms = (
        "daily",
        "weekly",
        "recurring",
        "repeat",
        "workflow",
        "teams",
        "operators",
        "monitor",
        "reporting",
        "alerts",
    )
    soft_terms = ("prototype", "one-off", "idea", "candidate")
    score = 0.2 + min(opportunity.evidence_count, 5) * 0.11
    score += _keyword_hits(text, recurrence_terms) * 0.05
    if opportunity.target_user.strip():
        score += 0.05
    score -= _keyword_hits(text, soft_terms) * 0.03
    return _clamp(score)


def score_opportunity(
    opportunity: Opportunity,
    weights: dict[str, float],
    *,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    inputs = {
        "pain": round(_pain_input(opportunity), 4),
        "freshness": round(_freshness_input(opportunity, reference_time=reference_time), 4),
        "recurrence": round(_recurrence_input(opportunity), 4),
        "source_quality": round(_source_quality_input(opportunity), 4),
        "build_fit": round(_build_fit_input(opportunity), 4),
    }
    contributions = {
        key: round(inputs[key] * weights.get(key, 0.0) * 100.0, 2)
        for key in DEFAULT_SCORING_WEIGHTS
    }
    total = round(sum(contributions.values()), 2)
    return {
        "score": total,
        "components": contributions,
        "inputs": inputs,
        "weights": {key: round(weights.get(key, 0.0), 4) for key in DEFAULT_SCORING_WEIGHTS},
    }


def opportunity_from_row_data(row: dict[str, Any], raw: dict[str, Any]) -> Opportunity:
    fields = set(Opportunity.__dataclass_fields__)
    data = {
        key: value
        for key, value in row.items()
        if key in fields and key != "raw"
    }
    data["raw"] = raw
    return Opportunity(**data)
