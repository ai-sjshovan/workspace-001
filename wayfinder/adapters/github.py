from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .base import NormalizedBatch
from ..models import ProductIntel, Signal


class GitHubCollectError(RuntimeError):
    pass


class GitHubAdapter:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config

    def healthcheck(self) -> tuple[bool, str]:
        try:
            count = len(self._query_specs())
        except ValueError as exc:
            return False, str(exc)
        auth_mode = "token" if self._token() else "anonymous"
        return count > 0, f"GitHub search configured with {count} quer{'y' if count == 1 else 'ies'} ({auth_mode})"

    def _token(self) -> str:
        return str(os.environ.get("GITHUB_TOKEN") or "").strip()

    def _timeout_seconds(self) -> float:
        value = self.config.get("timeout_seconds", 20)
        return max(float(value), 1.0)

    def _base_url(self) -> str:
        value = str(self.config.get("base_url") or "https://api.github.com/search/repositories").strip()
        return value or "https://api.github.com/search/repositories"

    def _query_specs(self) -> list[dict[str, Any]]:
        configured = self.config.get("queries")
        if not isinstance(configured, list):
            raise ValueError("github source requires a non-empty queries list")
        default_per_page = max(1, min(int(self.config.get("per_page") or 10), 100))
        default_sort = str(self.config.get("sort") or "updated").strip() or "updated"
        default_order = str(self.config.get("order") or "desc").strip() or "desc"
        specs: list[dict[str, Any]] = []
        for item in configured:
            if isinstance(item, str):
                query = item.strip()
                if query:
                    specs.append(
                        {
                            "query": query,
                            "label": query,
                            "per_page": default_per_page,
                            "sort": default_sort,
                            "order": default_order,
                        }
                    )
                continue
            if not isinstance(item, dict):
                continue
            query = str(item.get("query") or "").strip()
            if not query:
                continue
            label = str(item.get("label") or item.get("category") or query).strip() or query
            per_page_value = item.get("per_page", item.get("perPage", default_per_page))
            specs.append(
                {
                    "query": query,
                    "label": label,
                    "per_page": max(1, min(int(per_page_value or default_per_page), 100)),
                    "sort": str(item.get("sort") or default_sort).strip() or default_sort,
                    "order": str(item.get("order") or default_order).strip() or default_order,
                }
            )
        if not specs:
            raise ValueError("github source requires at least one valid query")
        return specs

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-foundry-wayfinder",
        }
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _read_payload(self, request: urllib.request.Request, spec: dict[str, Any]) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds()) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = self._format_http_error(exc.code, body)
            raise GitHubCollectError(f"GitHub API error for query '{spec['query']}': {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubCollectError(f"GitHub network error for query '{spec['query']}': {exc.reason}") from exc
        except TimeoutError as exc:
            raise GitHubCollectError(
                f"GitHub timeout for query '{spec['query']}' after {self._timeout_seconds():g}s"
            ) from exc
        except json.JSONDecodeError as exc:
            raise GitHubCollectError(f"GitHub returned invalid JSON for query '{spec['query']}'") from exc
        if not isinstance(payload, dict):
            raise GitHubCollectError(f"GitHub returned an invalid payload for query '{spec['query']}'")
        return payload

    def _format_http_error(self, status_code: int, body: str) -> str:
        detail = ""
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                detail = str(payload.get("message") or "").strip()
            elif body.strip():
                detail = body.strip()
        if status_code == 403 and "rate limit" in detail.lower():
            return f"HTTP 403 rate limit exceeded ({detail})"
        if detail:
            return f"HTTP {status_code} {detail}"
        return f"HTTP {status_code}"

    def collect(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for spec in self._query_specs():
            params = urllib.parse.urlencode(
                {
                    "q": spec["query"],
                    "sort": spec["sort"],
                    "order": spec["order"],
                    "per_page": spec["per_page"],
                }
            )
            request = urllib.request.Request(f"{self._base_url()}?{params}", headers=self._headers())
            payload = self._read_payload(request, spec)
            items = payload.get("items")
            if not isinstance(items, list):
                raise GitHubCollectError(f"GitHub payload missing repository items for query '{spec['query']}'")
            for item in items:
                if isinstance(item, dict):
                    item["_wayfinder_query"] = spec["query"]
                    item["_wayfinder_category"] = spec["label"]
                    records.append(item)
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        for item in raw_records:
            repo_name = str(item.get("name") or "").strip()
            full_name = str(item.get("full_name") or "")
            html_url = str(item.get("html_url") or "")
            if not repo_name or not full_name or not html_url:
                continue
            description = str(item.get("description") or "")
            topics = item.get("topics") if isinstance(item.get("topics"), list) else []
            category = ", ".join(str(topic) for topic in topics[:8])
            stars = float(item.get("stargazers_count") or 0)
            updated_at = str(item.get("updated_at") or "unknown")
            normalized_category = category or str(item.get("_wayfinder_category") or item.get("_wayfinder_query") or "")
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=full_name,
                    source_url=html_url,
                    title=full_name,
                    body=description,
                    score=stars,
                    product=full_name,
                    category=normalized_category,
                    raw=item,
                )
            )
            batch.products.append(
                ProductIntel(
                    product_name=full_name,
                    url=html_url,
                    category=normalized_category,
                    strengths=f"repo={repo_name}; stars={int(stars)}; updated={updated_at}",
                    audience=str(item.get("_wayfinder_category") or item.get("_wayfinder_query") or ""),
                    monetization_notes=f"GitHub repo {full_name} topics={category or 'none'}",
                    raw=item,
                )
            )
        return batch
