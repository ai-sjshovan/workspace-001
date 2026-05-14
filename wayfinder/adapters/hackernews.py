from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Any

from .base import NormalizedBatch
from ..models import Signal


class HackerNewsAdapter:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    def healthcheck(self) -> tuple[bool, str]:
        return True, "HN Algolia API configured"

    def collect(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        queries = self.config.get("queries") if isinstance(self.config.get("queries"), list) else []
        hits_per_query = int(self.config.get("hits_per_query") or 10)
        for query in queries:
            params = urllib.parse.urlencode({"query": str(query), "tags": "story", "hitsPerPage": hits_per_query})
            url = f"https://hn.algolia.com/api/v1/search?{params}"
            with urllib.request.urlopen(url, timeout=15) as response:
                data = response.read().decode("utf-8")
            import json

            payload = json.loads(data)
            for hit in payload.get("hits", []):
                if isinstance(hit, dict):
                    hit["_wayfinder_query"] = str(query)
                    records.append(hit)
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        for item in raw_records:
            object_id = str(item.get("objectID") or "")
            title = str(item.get("title") or item.get("story_title") or "").strip()
            if not object_id or not title:
                continue
            hn_url = f"https://news.ycombinator.com/item?id={object_id}"
            body = str(item.get("comment_text") or item.get("story_text") or item.get("url") or "")
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=object_id,
                    source_url=hn_url,
                    title=title,
                    body=body,
                    author=str(item.get("author") or ""),
                    score=float(item.get("points") or 0),
                    category=str(item.get("_wayfinder_query") or ""),
                    raw=item,
                )
            )
        return batch
