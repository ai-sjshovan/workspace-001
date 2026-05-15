from __future__ import annotations

import json
import os
import pathlib
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .base import NormalizedBatch
from ..models import Opportunity, ProductIntel, Signal


class GitHubCollectError(RuntimeError):
    pass


class GitHubAdapter:
    _DEFAULT_BASE_URL = "https://api.github.com/search/repositories"
    _ALLOWED_HOSTS = {"api.github.com"}

    def __init__(self, name: str, config: dict[str, Any] | Any) -> None:
        self.name = name
        self.config = config if isinstance(config, dict) else {}

    def healthcheck(self) -> tuple[bool, str]:
        try:
            specs = self._query_specs()
            fixture_path = self._fixture_path()
            if fixture_path is not None:
                items_by_query = self._fixture_items_by_query()
                missing = [spec["query"] for spec in specs if spec["query"] not in items_by_query]
                if missing:
                    missing_text = ", ".join(sorted(missing))
                    raise ValueError(f"github fixture_path is missing items for configured queries: {missing_text}")
            else:
                self._base_url()
                self._timeout_seconds()
                auth_mode = self._auth_mode()
        except ValueError as exc:
            return False, str(exc)
        count = len(specs)
        if fixture_path is not None:
            return count > 0, (
                f"GitHub deterministic fixture configured with {count} quer{'y' if count == 1 else 'ies'} "
                f"via {fixture_path}"
            )
        return count > 0, (
            f"GitHub public search configured with {count} quer{'y' if count == 1 else 'ies'} "
            f"via {self._base_url()} ({auth_mode})"
        )

    def _timeout_seconds(self) -> float:
        value = self.config.get("timeout_seconds", 20)
        try:
            return max(float(value), 1.0)
        except (TypeError, ValueError):
            raise ValueError("github source timeout_seconds must be a positive number") from None

    def _per_page(self, value: Any, default: int) -> int:
        try:
            return max(1, min(int(value or default), 100))
        except (TypeError, ValueError):
            raise ValueError("github source per_page must be an integer between 1 and 100") from None

    def _token(self) -> str:
        direct = str(self.config.get("token") or "").strip()
        if direct:
            return direct
        env_name = str(self.config.get("token_env") or "GITHUB_TOKEN").strip()
        if not env_name:
            return ""
        return str(os.environ.get(env_name) or "").strip()

    def _auth_mode(self) -> str:
        return "token optional" if self._token() else "anonymous fallback"

    def _base_url(self) -> str:
        value = str(self.config.get("base_url") or self._DEFAULT_BASE_URL).strip() or self._DEFAULT_BASE_URL
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme != "https" or parsed.netloc not in self._ALLOWED_HOSTS:
            raise ValueError("github source requires the official https://api.github.com repository search endpoint")
        if not parsed.path.rstrip("/").endswith("/search/repositories"):
            raise ValueError("github source must use the /search/repositories public search path")
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
            raise ValueError(f"github fixture_path does not exist: {resolved}")
        return resolved

    def _query_specs(self) -> list[dict[str, Any]]:
        configured = self.config.get("queries")
        if not isinstance(configured, list):
            raise ValueError("github source requires a non-empty queries list")
        default_per_page = self._per_page(self.config.get("per_page"), 10)
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
                    "per_page": self._per_page(per_page_value, default_per_page),
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
            message = self._format_http_error(exc.code, body, exc.headers)
            raise GitHubCollectError(f"GitHub API error for query '{spec['query']}': {message}") from exc
        except urllib.error.URLError as exc:
            raise GitHubCollectError(f"GitHub network error for query '{spec['query']}': {exc.reason}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise GitHubCollectError(
                f"GitHub timeout for query '{spec['query']}' after {self._timeout_seconds():g}s"
            ) from exc
        except OSError as exc:
            raise GitHubCollectError(f"GitHub I/O error for query '{spec['query']}': {exc.strerror or str(exc)}") from exc
        except json.JSONDecodeError as exc:
            raise GitHubCollectError(f"GitHub returned invalid JSON for query '{spec['query']}'") from exc
        if not isinstance(payload, dict):
            raise GitHubCollectError(f"GitHub returned an invalid payload for query '{spec['query']}'")
        return payload

    def _fixture_items_by_query(self) -> dict[str, list[dict[str, Any]]]:
        fixture_path = self._fixture_path()
        if fixture_path is None:
            return {}
        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"github fixture_path could not be read: {exc.strerror or str(exc)}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"github fixture_path is not valid JSON: {fixture_path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("github fixture_path must contain a JSON object") from None
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError("github fixture_path must contain a results list") from None
        items_by_query: dict[str, list[dict[str, Any]]] = {}
        for item in results:
            if not isinstance(item, dict):
                continue
            query = str(item.get("query") or "").strip()
            results_items = item.get("items")
            if not query or not isinstance(results_items, list):
                continue
            items_by_query[query] = [record for record in results_items if isinstance(record, dict)]
        if not items_by_query:
            raise ValueError("github fixture_path must contain at least one query with item dictionaries")
        return items_by_query

    def _rate_limit_suffix(self, headers: Any) -> str:
        if headers is None:
            return ""
        remaining = str(headers.get("X-RateLimit-Remaining") or "").strip()
        reset_raw = str(headers.get("X-RateLimit-Reset") or "").strip()
        if remaining != "0" and not reset_raw:
            return ""
        if reset_raw:
            try:
                reset_at = datetime.fromtimestamp(int(reset_raw), tz=timezone.utc).isoformat().replace("+00:00", "Z")
            except ValueError:
                reset_at = reset_raw
            return f"; rate limit resets at {reset_at}"
        return "; rate limit exhausted"

    def _format_http_error(self, status_code: int, body: str, headers: Any = None) -> str:
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
        if status_code in {403, 429} and "rate limit" in detail.lower():
            return f"HTTP {status_code} rate limit exceeded ({detail}){self._rate_limit_suffix(headers)}"
        if detail:
            return f"HTTP {status_code} {detail}"
        return f"HTTP {status_code}"

    def _collapse_text(self, value: Any) -> str:
        return " ".join(str(value or "").strip().split())

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        seen: set[str] = set()
        values: list[str] = []
        for item in value:
            text = self._collapse_text(item)
            lowered = text.lower()
            if not text or lowered in seen:
                continue
            seen.add(lowered)
            values.append(text)
        return values

    def _repo_key(self, value: Any) -> str:
        return self._collapse_text(value).lower()

    def _star_count(self, value: Any) -> float | None:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return None

    def _merge_record(self, existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = {**existing, **incoming}
        merged["_wayfinder_queries"] = self._string_list(
            [*self._string_list(existing.get("_wayfinder_queries")), *self._string_list(incoming.get("_wayfinder_queries"))]
        )
        merged["_wayfinder_categories"] = self._string_list(
            [
                *self._string_list(existing.get("_wayfinder_categories")),
                *self._string_list(incoming.get("_wayfinder_categories")),
            ]
        )
        merged["_wayfinder_query"] = ", ".join(merged["_wayfinder_queries"])
        merged["_wayfinder_category"] = ", ".join(merged["_wayfinder_categories"])
        merged["topics"] = self._string_list([*self._string_list(existing.get("topics")), *self._string_list(incoming.get("topics"))])

        existing_description = self._collapse_text(existing.get("description"))
        incoming_description = self._collapse_text(incoming.get("description"))
        if len(existing_description) > len(incoming_description):
            merged["description"] = existing.get("description")

        existing_updated = self._collapse_text(existing.get("updated_at"))
        incoming_updated = self._collapse_text(incoming.get("updated_at"))
        if existing_updated > incoming_updated:
            merged["updated_at"] = existing.get("updated_at")

        try:
            merged["stargazers_count"] = max(int(existing.get("stargazers_count") or 0), int(incoming.get("stargazers_count") or 0))
        except (TypeError, ValueError):
            merged["stargazers_count"] = incoming.get("stargazers_count") or existing.get("stargazers_count") or 0

        return merged

    def collect(self) -> list[dict[str, Any]]:
        records_by_repo: dict[str, dict[str, Any]] = {}
        fixture_items = self._fixture_items_by_query()
        for spec in self._query_specs():
            items: list[dict[str, Any]]
            if fixture_items:
                items = fixture_items.get(spec["query"], [])
                if not items:
                    raise GitHubCollectError(f"fixture payload missing items for query '{spec['query']}'")
            else:
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
                    items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                full_name = self._collapse_text(item.get("full_name"))
                if not full_name:
                    continue
                repo_key = self._repo_key(full_name)
                if not repo_key:
                    continue
                normalized = {
                    **item,
                    "_wayfinder_query": spec["query"],
                    "_wayfinder_category": spec["label"],
                    "_wayfinder_queries": [spec["query"]],
                    "_wayfinder_categories": [spec["label"]],
                }
                existing = records_by_repo.get(repo_key)
                records_by_repo[repo_key] = self._merge_record(existing, normalized) if existing else normalized
        records = list(records_by_repo.values())
        records.sort(
            key=lambda item: (
                str(item.get("full_name") or ""),
                str(item.get("updated_at") or ""),
            )
        )
        return records

    def normalize(self, raw_records: list[dict[str, Any]]) -> NormalizedBatch:
        batch = NormalizedBatch()
        seen_ids: set[str] = set()
        for item in raw_records:
            if not isinstance(item, dict):
                continue
            repo_name = str(item.get("name") or "").strip()
            full_name = str(item.get("full_name") or "").strip()
            html_url = str(item.get("html_url") or "").strip()
            if not repo_name or not full_name or not html_url:
                continue
            repo_key = self._repo_key(full_name)
            if not repo_key or repo_key in seen_ids:
                continue
            stars = self._star_count(item.get("stargazers_count"))
            if stars is None:
                continue
            seen_ids.add(repo_key)
            description = self._collapse_text(item.get("description"))
            topics = self._string_list(item.get("topics"))
            category = ", ".join(topics[:8])
            updated_at = str(item.get("updated_at") or "unknown")
            matched_categories = self._string_list(item.get("_wayfinder_categories"))
            matched_queries = self._string_list(item.get("_wayfinder_queries"))
            normalized_category = category or ", ".join(matched_categories or matched_queries)
            language = self._collapse_text(item.get("language"))
            homepage = self._collapse_text(item.get("homepage"))
            license_name = self._collapse_text((item.get("license") or {}).get("spdx_id") if isinstance(item.get("license"), dict) else "")
            query_context = ", ".join(matched_queries)
            repo_facts = [
                f"stars={int(stars)}",
                f"updated={updated_at}",
                f"language={language or 'unknown'}",
                f"license={license_name or 'unknown'}",
            ]
            if topics:
                repo_facts.append(f"topics={', '.join(topics[:8])}")
            if homepage:
                repo_facts.append(f"homepage={homepage}")
            signal_body = "; ".join(part for part in [description, ", ".join(repo_facts), query_context] if part)
            batch.signals.append(
                Signal(
                    source=self.name,
                    source_id=full_name,
                    source_url=html_url,
                    title=full_name,
                    body=signal_body,
                    score=stars,
                    product=full_name,
                    category=normalized_category,
                    feature_request=query_context,
                    monetization_signal=license_name,
                    raw=item,
                )
            )
            batch.products.append(
                ProductIntel(
                    product_name=full_name,
                    url=html_url,
                    category=normalized_category,
                    strengths="; ".join(["repo=" + repo_name, *repo_facts]),
                    feature_gaps=f"Matched GitHub queries: {query_context}" if query_context else "",
                    audience=", ".join(matched_categories or matched_queries),
                    monetization_notes=f"GitHub repo {full_name} topics={category or 'none'}",
                    raw=item,
                )
            )
            batch.opportunities.append(
                Opportunity(
                    title=f"Inspect {full_name} for leverage",
                    source=self.name,
                    category=normalized_category,
                    target_user="Wayfinder operator",
                    problem=description or f"Need better tooling in {normalized_category or 'open-source workflows'}.",
                    evidence_count=max(1, len(matched_queries)),
                    competing_products=full_name,
                    what_products_do_right=f"Repository shows traction with {int(stars)} stars and {language or 'unknown'} implementation.",
                    what_users_want_better=f"Matched public GitHub demand: {query_context}" if query_context else "",
                    build_difficulty="inspect-first",
                    replication_time_estimate="inspect before estimating",
                    iteration_angle=f"Reuse repository patterns, docs, or architecture from {full_name} where safe.",
                    monetization_strategy="open-source leverage or competitor/tool intelligence for future product bets",
                    foundry_task_suggestions=f"Review {full_name} for reusable patterns and market adjacency signals.",
                    raw=item,
                )
            )
        return batch
