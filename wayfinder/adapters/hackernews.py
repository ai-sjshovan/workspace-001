from __future__ import annotations

import json
import urllib.parse
import urllib.error
import urllib.request
from typing import Any

from .base import NormalizedBatch
from ..models import Signal


class HackerNewsCollectError(RuntimeError):
    pass


class HackerNewsAdapter:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    def healthcheck(self) -> tuple[bool, str]:
        try:
            count = len(self._query_specs())
        except ValueError as exc:
            return False, str(exc)
        return count > 0, f"HN Algolia API configured with {count} quer{'y' if count == 1 else 'ies'}"

    def _timeout_seconds(self) -> float:
        value = self.config.get("timeout_seconds", 15)
        return max(float(value), 1.0)

    def _base_url(self) -> str:
        value = str(self.config.get("base_url") or "https://hn.algolia.com/api/v1/search").strip()
        return value or "https://hn.algolia.com/api/v1/search"

    def _query_specs(self) -> list[dict[str, Any]]:
        configured = self.config.get("queries")
        if not isinstance(configured, list):
            raise ValueError("hackernews source requires a non-empty queries list")
        default_hits = int(self.config.get("hits_per_query") or 10)
        default_tags = str(self.config.get("default_tags") or "story").strip() or "story"
        specs: list[dict[str, Any]] = []
        for item in configured:
            if isinstance(item, str):
                query = item.strip()
                if query:
                    specs.append(
                        {
                            "query": query,
                            "label": query,
                            "tags": default_tags,
                            "hits_per_page": default_hits,
                        }
                    )
                continue
            if not isinstance(item, dict):
                continue
            query = str(item.get("query") or "").strip()
            if not query:
                continue
            label = str(item.get("label") or item.get("category") or query).strip() or query
            tags = str(item.get("tags") or default_tags).strip() or default_tags
            hits_value = item.get("hits_per_page", item.get("hitsPerPage", item.get("hits_per_query", default_hits)))
            specs.append(
                {
                    "query": query,
                    "label": label,
                    "tags": tags,
                    "hits_per_page": int(hits_value or default_hits),
                }
            )
        if not specs:
            raise ValueError("hackernews source requires at least one valid query")
        return specs

    def collect(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for spec in self._query_specs():
            params = urllib.parse.urlencode(
                {
                    "query": spec["query"],
                    "tags": spec["tags"],
                    "hitsPerPage": spec["hits_per_page"],
                }
            )
            url = f"{self._base_url()}?{params}"
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "wayfinder/0 hn-ingest"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_seconds()) as response:
                    data = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                raise HackerNewsCollectError(f"HTTP {exc.code} for query '{spec['query']}'") from exc
            except urllib.error.URLError as exc:
                raise HackerNewsCollectError(f"network error for query '{spec['query']}': {exc.reason}") from exc
            except TimeoutError as exc:
                raise HackerNewsCollectError(f"timeout for query '{spec['query']}' after {self._timeout_seconds():g}s") from exc
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as exc:
                raise HackerNewsCollectError(f"invalid JSON for query '{spec['query']}'") from exc
            hits = payload.get("hits")
            if not isinstance(hits, list):
                raise HackerNewsCollectError(f"invalid payload for query '{spec['query']}': missing hits list")
            for hit in hits:
                if isinstance(hit, dict):
                    hit["_wayfinder_query"] = spec["query"]
                    hit["_wayfinder_category"] = spec["label"]
                    hit["_wayfinder_tags"] = spec["tags"]
                    records.append(hit)
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        seen_ids: set[str] = set()
        for item in raw_records:
            object_id = str(item.get("objectID") or "")
            title = str(item.get("title") or item.get("story_title") or "").strip()
            if not object_id or not title:
                continue
            if object_id in seen_ids:
                continue
            seen_ids.add(object_id)
            hn_url = f"https://news.ycombinator.com/item?id={object_id}"
            article_url = str(item.get("url") or "").strip()
            body_parts = [
                str(item.get("story_text") or "").strip(),
                str(item.get("comment_text") or "").strip(),
                article_url,
                hn_url,
            ]
            body = "\n".join(part for part in body_parts if part)
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=object_id,
                    source_url=article_url or hn_url,
                    title=title,
                    body=body,
                    author=str(item.get("author") or ""),
                    score=float(item.get("points") or 0),
                    category=str(item.get("_wayfinder_category") or item.get("_wayfinder_query") or ""),
                    raw=item,
                )
            )
        return batch
