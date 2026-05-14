from __future__ import annotations

import html
import json
import pathlib
import re
import socket
import urllib.parse
import urllib.error
import urllib.request
from typing import Any

from .base import NormalizedBatch
from ..models import Signal


class HackerNewsCollectError(RuntimeError):
    pass


class HackerNewsAdapter:
    _DEFAULT_BASE_URL = "https://hn.algolia.com/api/v1/search"
    _ALLOWED_HOSTS = {"hn.algolia.com"}

    def __init__(self, name: str, config: dict[str, Any] | Any) -> None:
        self.name = name
        self.config = config if isinstance(config, dict) else {}

    def healthcheck(self) -> tuple[bool, str]:
        try:
            specs = self._query_specs()
            fixture_path = self._fixture_path()
            if fixture_path is not None:
                self._fixture_hits_by_query()
            else:
                self._base_url()
                self._timeout_seconds()
        except ValueError as exc:
            return False, str(exc)
        count = len(specs)
        if fixture_path is not None:
            return count > 0, (
                f"HN deterministic fixture configured with {count} quer{'y' if count == 1 else 'ies'} "
                f"via {fixture_path}"
            )
        return count > 0, f"HN Algolia API configured with {count} quer{'y' if count == 1 else 'ies'} via {self._base_url()}"

    def _timeout_seconds(self) -> float:
        value = self.config.get("timeout_seconds", 15)
        try:
            return max(float(value), 1.0)
        except (TypeError, ValueError):
            raise ValueError("hackernews source timeout_seconds must be a positive number") from None

    def _base_url(self) -> str:
        value = str(self.config.get("base_url") or self._DEFAULT_BASE_URL).strip() or self._DEFAULT_BASE_URL
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme != "https" or parsed.netloc not in self._ALLOWED_HOSTS:
            raise ValueError("hackernews source requires the official https://hn.algolia.com search endpoint")
        if not parsed.path.rstrip("/").endswith("/api/v1/search"):
            raise ValueError("hackernews source must use the /api/v1/search public search path")
        return value

    def _fixture_path(self) -> pathlib.Path | None:
        value = self.config.get("fixture_path")
        if not value:
            return None
        path = pathlib.Path(str(value))
        config_dir = self.config.get("_config_dir")
        if path.is_absolute() or not config_dir:
            resolved = path
        else:
            resolved = (pathlib.Path(str(config_dir)) / path).resolve()
        if not resolved.exists():
            raise ValueError(f"hackernews fixture_path does not exist: {resolved}")
        return resolved

    def _query_specs(self) -> list[dict[str, Any]]:
        configured = self.config.get("queries")
        if not isinstance(configured, list):
            raise ValueError("hackernews source requires a non-empty queries list")
        default_hits = self._hits_per_page(self.config.get("hits_per_query"), 10)
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
                    "hits_per_page": self._hits_per_page(hits_value, default_hits),
                }
            )
        if not specs:
            raise ValueError("hackernews source requires at least one valid query")
        return specs

    def _hits_per_page(self, value: Any, default: int) -> int:
        try:
            return max(1, min(int(value or default), 100))
        except (TypeError, ValueError):
            return default

    def _read_payload(self, request: urllib.request.Request, spec: dict[str, Any]) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds()) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()
            detail = body[:180] if body else ""
            suffix = f" ({detail})" if detail else ""
            raise HackerNewsCollectError(f"HTTP {exc.code} for query '{spec['query']}'{suffix}") from exc
        except urllib.error.URLError as exc:
            raise HackerNewsCollectError(f"network error for query '{spec['query']}': {exc.reason}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise HackerNewsCollectError(f"timeout for query '{spec['query']}' after {self._timeout_seconds():g}s") from exc
        except OSError as exc:
            raise HackerNewsCollectError(f"I/O error for query '{spec['query']}': {exc.strerror or str(exc)}") from exc
        except json.JSONDecodeError as exc:
            raise HackerNewsCollectError(f"invalid JSON for query '{spec['query']}'") from exc
        if not isinstance(payload, dict):
            raise HackerNewsCollectError(f"invalid payload for query '{spec['query']}': expected JSON object")
        return payload

    def _fixture_hits_by_query(self) -> dict[str, list[dict[str, Any]]]:
        fixture_path = self._fixture_path()
        if fixture_path is None:
            return {}
        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"hackernews fixture_path could not be read: {exc.strerror or str(exc)}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"hackernews fixture_path is not valid JSON: {fixture_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("hackernews fixture_path must contain a JSON object") from None
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("hackernews fixture_path must contain a results list") from None
        hits_by_query: dict[str, list[dict[str, Any]]] = {}
        for item in results:
            if not isinstance(item, dict):
                continue
            query = str(item.get("query") or "").strip()
            hits = item.get("hits")
            if not query or not isinstance(hits, list):
                continue
            hits_by_query[query] = [hit for hit in hits if isinstance(hit, dict)]
        if not hits_by_query:
            raise ValueError("hackernews fixture_path must contain at least one query with hit dictionaries")
        return hits_by_query

    def _clean_text(self, value: Any) -> str:
        text = html.unescape(str(value or ""))
        text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(text.split())

    def _pick_text(self, records: list[dict[str, Any]], *keys: str) -> str:
        values = {
            self._clean_text(record.get(key) or "")
            for record in records
            for key in keys
        }
        values.discard("")
        return min(values, key=lambda value: (-len(value), value)) if values else ""

    def _pick_url(self, records: list[dict[str, Any]], key: str) -> str:
        values = {str(record.get(key) or "").strip() for record in records}
        values.discard("")
        return min(values, key=lambda value: (-len(value), value)) if values else ""

    def _pick_category(self, records: list[dict[str, Any]]) -> str:
        values = {str(record.get("_wayfinder_category") or record.get("_wayfinder_query") or "").strip() for record in records}
        values.discard("")
        return min(values) if values else ""

    def _pick_score(self, records: list[dict[str, Any]]) -> float:
        scores: list[float] = []
        for record in records:
            try:
                scores.append(float(record.get("points") or 0))
            except (TypeError, ValueError):
                scores.append(0.0)
        return max(scores, default=0.0)

    def _unique_parts(self, *parts: str) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for part in parts:
            if part and part not in seen:
                seen.add(part)
                unique.append(part)
        return unique

    def _canonical_signal_payload(self, records: list[dict[str, Any]]) -> Signal | None:
        object_id = str(records[0].get("objectID") or "")
        title = self._pick_text(records, "title", "story_title")
        if not object_id or not title:
            return None
        article_url = self._pick_url(records, "url")
        hn_url = f"https://news.ycombinator.com/item?id={object_id}"
        author = self._pick_text(records, "author")
        body = "\n".join(
            self._unique_parts(
                self._pick_text(records, "story_text"),
                self._pick_text(records, "comment_text"),
                article_url,
                hn_url,
            )
        )
        canonical_raw = dict(
            min(
                records,
                key=lambda record: (
                    str(record.get("created_at") or ""),
                    str(record.get("_wayfinder_category") or ""),
                    str(record.get("_wayfinder_query") or ""),
                ),
            )
        )
        canonical_raw["_wayfinder_category"] = self._pick_category(records)
        canonical_raw["url"] = article_url
        canonical_raw["author"] = author
        canonical_raw["points"] = self._pick_score(records)
        if canonical_raw.get("title") or canonical_raw.get("story_title"):
            canonical_raw["title"] = title
        return Signal(
            source=self.name,
            source_id=object_id,
            source_url=article_url or hn_url,
            title=title,
            body=body,
            author=author,
            score=self._pick_score(records),
            category=canonical_raw["_wayfinder_category"],
            raw=canonical_raw,
        )

    def collect(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        fixture_hits = self._fixture_hits_by_query()
        for spec in self._query_specs():
            hits: list[dict[str, Any]]
            if fixture_hits:
                hits = fixture_hits.get(spec["query"], [])
                if not hits:
                    raise HackerNewsCollectError(f"fixture payload missing hits for query '{spec['query']}'")
            else:
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
                payload = self._read_payload(request, spec)
                hits = payload.get("hits")
                if not isinstance(hits, list):
                    raise HackerNewsCollectError(f"invalid payload for query '{spec['query']}': missing hits list")
            for hit in hits:
                if isinstance(hit, dict):
                    records.append(
                        {
                            **hit,
                            "_wayfinder_query": spec["query"],
                            "_wayfinder_category": spec["label"],
                            "_wayfinder_tags": spec["tags"],
                        }
                    )
        records.sort(
            key=lambda item: (
                str(item.get("objectID") or ""),
                str(item.get("_wayfinder_category") or ""),
                str(item.get("created_at") or ""),
            )
        )
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        records_by_id: dict[str, list[dict[str, Any]]] = {}
        for item in raw_records:
            object_id = str(item.get("objectID") or "")
            if not object_id:
                continue
            records_by_id.setdefault(object_id, []).append(item)
        for object_id in sorted(records_by_id):
            signal = self._canonical_signal_payload(records_by_id[object_id])
            if signal is not None:
                batch.signals.append(signal)
        return batch
