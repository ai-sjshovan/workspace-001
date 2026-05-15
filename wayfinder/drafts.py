from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _value(row: Mapping[str, Any], key: str) -> Any:
    return row.get(key)


def draft_title(row: Mapping[str, Any]) -> str:
    category = str(_value(row, "category") or "").replace("-", " ").strip()
    if category:
        return f"{_value(row, 'title')} for {category}"
    return str(_value(row, "title") or "")


def draft_goal(row: Mapping[str, Any]) -> str:
    parts = [str(_value(row, "problem") or "").strip(), str(_value(row, "iteration_angle") or "").strip()]
    return " ".join(part for part in parts if part) or (
        f"Review {_value(row, 'title')} and decide whether it merits a follow-on Foundry task."
    )


def draft_acceptance_criteria(row: Mapping[str, Any]) -> list[str]:
    criteria = [
        (
            f"Review the opportunity context for `{_value(row, 'title')}` and capture the concrete reuse angle for "
            f"`{_value(row, 'target_user') or 'the operator'}`."
        ),
        "Use the existing evidence, competition, and user-want signals to decide whether this should become a follow-on Foundry task.",
    ]
    if _value(row, "foundry_task_suggestions"):
        criteria.append(
            f"Translate the existing suggestion into an operator-ready next step: {_value(row, 'foundry_task_suggestions')}."
        )
    else:
        criteria.append(
            "Produce a specific next step that can be reviewed by Hermes or pasted into Linear without further rewriting."
        )
    return criteria


def draft_validation(row: Mapping[str, Any]) -> list[str]:
    return [
        f"Confirm the draft references the source opportunity score (`{_value(row, 'opportunity_score')}`) and the relevant evidence fields.",
        "Confirm the draft is specific enough for Hermes review or direct paste into Linear.",
    ]


def draft_scope_boundaries(row: Mapping[str, Any]) -> list[str]:
    boundaries = [
        "Do not auto-stage follow-on tasks.",
        "Do not call LLMs.",
        "Do not create Linear issues directly from this command.",
    ]
    if _value(row, "source"):
        boundaries.append(
            f"Do not broaden this draft beyond the `{_value(row, 'source')}` source material without explicit operator review."
        )
    return boundaries


def draft_delivery_expectation() -> list[str]:
    return [
        "Keep the output Markdown-only and operator-editable.",
        "Hand the draft to Hermes for review or paste it into Linear manually when ready.",
    ]


def format_task_draft(row: Mapping[str, Any], index: int) -> str:
    metadata = [
        f"source={_value(row, 'source') or 'unknown'}",
        f"category={_value(row, 'category') or 'uncategorized'}",
        f"score={_value(row, 'opportunity_score')}",
    ]
    lines = [
        f"## Task Draft {index}: {draft_title(row)}",
        "",
        f"Metadata: {' | '.join(metadata)}",
        "",
        "### Goal",
        draft_goal(row),
        "",
        "### Acceptance Criteria",
    ]
    lines.extend(f"- {item}" for item in draft_acceptance_criteria(row))
    lines.extend(
        [
            "",
            "### Validation",
        ]
    )
    lines.extend(f"- {item}" for item in draft_validation(row))
    lines.extend(
        [
            "",
            "### Scope Boundaries",
        ]
    )
    lines.extend(f"- {item}" for item in draft_scope_boundaries(row))
    lines.extend(
        [
            "",
            "### Delivery Expectation",
        ]
    )
    lines.extend(f"- {item}" for item in draft_delivery_expectation())
    return "\n".join(lines)
