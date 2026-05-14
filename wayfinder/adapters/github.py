from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from .base import NormalizedBatch
from ..models import ProductIntel, Signal


class GitHubAdapter:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    def healthcheck(self) -> tuple[bool, str]:
        return True, "GitHub public search API configured"

    def collect(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        queries = self.config.get("queries") if isinstance(self.config.get("queries"), list) else []
        per_page = int(self.config.get("per_page") or 10)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-foundry-wayfinder",
        }
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        for query in queries:
            params = urllib.parse.urlencode({"q": str(query), "sort": "updated", "order": "desc", "per_page": per_page})
            request = urllib.request.Request(f"https://api.github.com/search/repositories?{params}", headers=headers)
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for item in payload.get("items", []):
                if isinstance(item, dict):
                    item["_wayfinder_query"] = str(query)
                    records.append(item)
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        for item in raw_records:
            full_name = str(item.get("full_name") or "")
            html_url = str(item.get("html_url") or "")
            if not full_name or not html_url:
                continue
            description = str(item.get("description") or "")
            topics = item.get("topics") if isinstance(item.get("topics"), list) else []
            category = ", ".join(str(topic) for topic in topics[:8])
            stars = float(item.get("stargazers_count") or 0)
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=full_name,
                    source_url=html_url,
                    title=full_name,
                    body=description,
                    score=stars,
                    product=full_name,
                    category=category or str(item.get("_wayfinder_query") or ""),
                    raw=item,
                )
            )
            batch.products.append(
                ProductIntel(
                    product_name=full_name,
                    url=html_url,
                    category=category,
                    strengths=f"{int(stars)} GitHub stars; updated {item.get('updated_at') or 'unknown'}",
                    audience=str(item.get("_wayfinder_query") or ""),
                    raw=item,
                )
            )
        return batch
