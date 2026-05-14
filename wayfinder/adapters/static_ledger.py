from __future__ import annotations

import pathlib
from typing import Any

import yaml

from .base import NormalizedBatch
from ..models import Opportunity, ProductIntel, Signal


class StaticLedgerAdapter:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    def _path(self) -> pathlib.Path:
        value = self.config.get("path")
        if not value:
            raise FileNotFoundError("static ledger source requires path")
        path = pathlib.Path(str(value))
        config_dir = self.config.get("_config_dir")
        if path.is_absolute() or not config_dir:
            return path
        return (pathlib.Path(str(config_dir)) / path).resolve()

    def healthcheck(self) -> tuple[bool, str]:
        path = self._path()
        return path.exists(), str(path)

    def collect(self) -> list[dict[str, Any]]:
        path = self._path()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        repos = data.get("repos")
        return [item for item in repos if isinstance(item, dict)] if isinstance(repos, list) else []

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        for item in raw_records:
            name = str(item.get("name") or "").strip()
            url = str(item.get("url") or "").strip()
            if not name:
                continue
            useful_outputs = item.get("useful_outputs") if isinstance(item.get("useful_outputs"), list) else []
            risks = item.get("safety_risks") if isinstance(item.get("safety_risks"), list) else []
            body = "; ".join(str(output) for output in useful_outputs)
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=name,
                    source_url=url,
                    title=f"OSS leverage candidate: {name}",
                    body=body or str(item.get("verdict") or ""),
                    product=name,
                    category=str(item.get("category") or ""),
                    feature_request=str(item.get("verdict") or ""),
                    monetization_signal=str(item.get("api_keys_required") or ""),
                    raw=item,
                )
            )
            batch.products.append(
                ProductIntel(
                    product_name=name,
                    url=url,
                    category=str(item.get("category") or ""),
                    strengths=body,
                    complaints="; ".join(str(risk) for risk in risks),
                    feature_gaps=str(item.get("verdict") or ""),
                    audience="Wayfinder source adapter research",
                    monetization_notes=str(item.get("api_keys_required") or ""),
                    raw=item,
                )
            )
            batch.opportunities.append(
                Opportunity(
                    title=f"Leverage {name}",
                    target_user="Codex Foundry operator",
                    problem=f"Need {item.get('category') or 'research'} capability without rebuilding from scratch.",
                    evidence_count=1,
                    competing_products=name,
                    what_products_do_right=body,
                    what_users_want_better=str(item.get("verdict") or ""),
                    build_difficulty=str(item.get("install_complexity") or "unknown"),
                    replication_time_estimate="inspect before estimating",
                    iteration_angle=f"Review and adapt {name} patterns into Wayfinder adapters.",
                    monetization_strategy="internal leverage first; no subscription dependency by default",
                    foundry_task_suggestions=f"Research: safety review {name}; Adapter: evaluate {name} output model",
                    raw=item,
                )
            )
        return batch
