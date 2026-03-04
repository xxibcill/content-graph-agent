from typing import Any, Optional

import logging
import time

import requests

from configs.settings import get_settings
from utils.cache import make_cache_key, read_cache, write_cache
from utils.retry import run_with_retry


logger = logging.getLogger(__name__)


def build_query(topic: str, niche: Optional[str]) -> str:
    base = f"Trending topics and recent facts about {topic}"
    if niche:
        return f"{base} in {niche}"
    return base


def _tavily_search(query: str, api_key: str, limit: int) -> dict[str, Any]:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": limit,
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _serper_search(query: str, api_key: str, limit: int) -> dict[str, Any]:
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": limit}
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def _normalize_tavily(data: dict[str, Any], limit: int) -> tuple[list[str], list[str]]:
    bullets: list[str] = []
    sources: list[str] = []
    for item in data.get("results", []):
        title = (item.get("title") or "").strip()
        snippet = (item.get("content") or "").strip()
        url = (item.get("url") or "").strip()
        if not title and not snippet:
            continue
        if title and snippet:
            bullets.append(f"{title}: {snippet}")
        else:
            bullets.append(title or snippet)
        if url:
            sources.append(url)
        if len(bullets) >= limit:
            break
    return bullets, sources


def _normalize_serper(data: dict[str, Any], limit: int) -> tuple[list[str], list[str]]:
    bullets: list[str] = []
    sources: list[str] = []
    for item in data.get("organic", []):
        title = (item.get("title") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        link = (item.get("link") or "").strip()
        if not title and not snippet:
            continue
        if title and snippet:
            bullets.append(f"{title}: {snippet}")
        else:
            bullets.append(title or snippet)
        if link:
            sources.append(link)
        if len(bullets) >= limit:
            break
    return bullets, sources


def run_research(topic: str, niche: Optional[str] = None, limit: Optional[int] = None) -> dict[str, Any]:
    settings = get_settings()
    result_limit = limit or settings.default_limit
    query = build_query(topic, niche)

    cache_key = make_cache_key(
        "research",
        settings.research_provider,
        topic,
        niche,
        str(result_limit),
    )
    cached = read_cache(settings.cache_dir, cache_key, settings.cache_ttl_seconds)
    if cached:
        logger.info("Research cache hit provider=%s topic=%s", settings.research_provider, topic)
        return cached

    start = time.perf_counter()
    if settings.research_provider == "serper":
        api_key = settings.serper_api_key
        if not api_key:
            raise RuntimeError("SERPER_API_KEY is required for Serper research provider.")

        def operation():
            return _serper_search(query, api_key, result_limit)

        raw = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
        bullets, sources = _normalize_serper(raw, result_limit)
    else:
        api_key = settings.tavily_api_key
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is required for Tavily research provider.")

        def operation():
            return _tavily_search(query, api_key, result_limit)

        raw = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
        bullets, sources = _normalize_tavily(raw, result_limit)

    elapsed = time.perf_counter() - start
    logger.info(
        "Research completed provider=%s topic=%s results=%s duration=%.2fs",
        settings.research_provider,
        topic,
        len(bullets),
        elapsed,
    )

    result = {
        "provider": settings.research_provider,
        "query": query,
        "bullets": bullets,
        "sources": sources,
        "raw": raw,
    }
    write_cache(settings.cache_dir, cache_key, result)
    return result


def format_bullets(bullets: list[str]) -> str:
    return "\n".join(f"- {item}" for item in bullets)
