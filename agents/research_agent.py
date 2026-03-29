from typing import Any, Optional

import logging
import time
import re

import requests

from configs.settings import get_settings
from utils.cache import make_cache_key, read_cache, write_cache
from utils.llm import get_client_and_model
from utils.retry import run_with_retry


logger = logging.getLogger(__name__)


def build_query(topic: str, niche: Optional[str]) -> str:
    base = f"Trending topics and recent facts about {topic}"
    if niche:
        return f"{base} in {niche}"
    return base


def normalize_research_mode(mode: Optional[str]) -> str:
    if (mode or "").strip().lower() == "react":
        return "react"
    return "basic"


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


def _search_with_provider(
    query: str,
    provider: str,
    limit: int,
    tavily_api_key: Optional[str],
    serper_api_key: Optional[str],
) -> dict[str, Any]:
    start = time.perf_counter()
    if provider == "serper":
        if not serper_api_key:
            raise RuntimeError("SERPER_API_KEY is required for Serper research provider.")

        def operation():
            return _serper_search(query, serper_api_key, limit)

        raw = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
        bullets, sources = _normalize_serper(raw, limit)
    else:
        if not tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY is required for Tavily research provider.")

        def operation():
            return _tavily_search(query, tavily_api_key, limit)

        raw = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
        bullets, sources = _normalize_tavily(raw, limit)

    elapsed = time.perf_counter() - start
    logger.info(
        "Research search completed provider=%s query=%s results=%s duration=%.2fs",
        provider,
        query,
        len(bullets),
        elapsed,
    )
    return {
        "bullets": bullets,
        "sources": sources,
        "raw": raw,
    }


def build_react_prompt(
    topic: str,
    niche: Optional[str],
    result_limit: int,
    scratchpad: str,
) -> str:
    audience = niche or "general audience"
    return (
        "You are a research agent using the ReAct pattern for short-form content planning.\n"
        "Your job is to decide whether you need another web search or if you already have enough evidence.\n\n"
        f"Topic: {topic}\n"
        f"Audience/Niche: {audience}\n"
        f"Need at most {result_limit} final bullets.\n\n"
        "Available action:\n"
        "- search: run one web search query.\n\n"
        "Reply using exactly one of these formats:\n"
        "THOUGHT: <brief reasoning>\n"
        "ACTION: search\n"
        "ACTION_INPUT: <single search query>\n\n"
        "OR\n\n"
        "THOUGHT: <brief reasoning>\n"
        "FINAL:\n"
        "- bullet 1\n"
        "- bullet 2\n\n"
        "Keep bullets concrete and directly useful for a writer.\n"
        "Do not mention the format rules in your answer.\n\n"
        f"Scratchpad:\n{scratchpad or '- No observations yet.'}"
    )


def parse_react_response(text: str) -> dict[str, str]:
    lines = text.splitlines()
    action = ""
    action_input = ""
    final_lines: list[str] = []
    final_mode = False

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        upper = line.upper()
        if upper.startswith("ACTION:"):
            action = line.split(":", 1)[1].strip().lower()
            continue
        if upper.startswith("ACTION_INPUT:"):
            action_input = line.split(":", 1)[1].strip()
            continue
        if upper.startswith("FINAL:"):
            final_mode = True
            inline_value = line.split(":", 1)[1].strip()
            if inline_value:
                final_lines.append(inline_value)
            final_lines.extend(lines[index + 1 :])
            break

    final_text = "\n".join(final_lines).strip()
    if final_mode or final_text:
        return {"type": "final", "content": final_text}
    if action == "search" and action_input:
        return {"type": "action", "action": action, "action_input": action_input}
    return {"type": "invalid", "content": text.strip()}


def extract_final_bullets(text: str, limit: int) -> list[str]:
    bullets: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s*", "", line)
        if line:
            bullets.append(line)
        if len(bullets) >= limit:
            break
    if bullets:
        return bullets
    stripped = text.strip()
    return [stripped] if stripped else []


def summarize_observation(query: str, bullets: list[str], sources: list[str]) -> str:
    lines = [f"Search query: {query}"]
    if not bullets:
        lines.append("Observation: no useful results returned.")
    else:
        lines.append("Observation:")
        for bullet in bullets:
            lines.append(f"- {bullet}")
    if sources:
        lines.append("Sources:")
        for source in sources:
            lines.append(f"- {source}")
    return "\n".join(lines)


def dedupe_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items


def _run_react_research(
    topic: str,
    niche: Optional[str],
    result_limit: int,
) -> dict[str, Any]:
    settings = get_settings()
    client, model, provider = get_client_and_model(settings.research_agent_model)
    scratchpad = ""
    trace: list[dict[str, Any]] = []

    for step in range(1, settings.react_max_steps + 1):
        prompt = build_react_prompt(topic, niche, result_limit, scratchpad)

        def operation():
            return client.chat.completions.create(
                model=model,
                temperature=settings.research_agent_temperature,
                messages=[{"role": "user", "content": prompt}],
            )

        response = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
        content = (response.choices[0].message.content or "").strip()
        decision = parse_react_response(content)

        if decision["type"] == "final":
            final_bullets = extract_final_bullets(decision.get("content", ""), result_limit)
            if not final_bullets:
                final_bullets = dedupe_items(
                    [
                        bullet
                        for step_result in trace
                        for bullet in step_result.get("bullets", [])
                    ]
                )[:result_limit]
            return {
                "provider": settings.research_provider,
                "query": build_query(topic, niche),
                "bullets": final_bullets,
                "sources": dedupe_items(
                    [
                        source
                        for step_result in trace
                        for source in step_result.get("sources", [])
                    ]
                ),
                "raw": trace,
                "mode": "react",
                "iterations": step,
                "tool_queries": [step_result["query"] for step_result in trace],
            }

        if decision["type"] != "action" or decision.get("action") != "search":
            logger.warning("Invalid ReAct response received: %s", content)
            break

        search_result = _search_with_provider(
            decision["action_input"],
            settings.research_provider,
            result_limit,
            settings.tavily_api_key,
            settings.serper_api_key,
        )
        trace.append(
            {
                "step": step,
                "query": decision["action_input"],
                "bullets": search_result["bullets"],
                "sources": search_result["sources"],
                "raw": search_result["raw"],
            }
        )
        scratchpad = "\n\n".join(
            summarize_observation(
                step_result["query"],
                step_result["bullets"],
                step_result["sources"],
            )
            for step_result in trace
        )

    fallback_bullets = dedupe_items(
        [
            bullet
            for step_result in trace
            for bullet in step_result.get("bullets", [])
        ]
    )[:result_limit]
    return {
        "provider": settings.research_provider,
        "query": build_query(topic, niche),
        "bullets": fallback_bullets,
        "sources": dedupe_items(
            [
                source
                for step_result in trace
                for source in step_result.get("sources", [])
            ]
        ),
        "raw": trace,
        "mode": "react",
        "iterations": len(trace),
        "tool_queries": [step_result["query"] for step_result in trace],
    }


def run_research(
    topic: str,
    niche: Optional[str] = None,
    limit: Optional[int] = None,
    mode: Optional[str] = None,
) -> dict[str, Any]:
    settings = get_settings()
    result_limit = limit or settings.default_limit
    query = build_query(topic, niche)
    research_mode = normalize_research_mode(mode or settings.research_mode)

    cache_key = make_cache_key(
        "research",
        research_mode,
        settings.research_provider,
        topic,
        niche,
        str(result_limit),
    )
    cached = read_cache(settings.cache_dir, cache_key, settings.cache_ttl_seconds)
    if cached:
        logger.info("Research cache hit provider=%s topic=%s", settings.research_provider, topic)
        return cached

    if research_mode == "react":
        result = _run_react_research(topic, niche, result_limit)
    else:
        search_result = _search_with_provider(
            query,
            settings.research_provider,
            result_limit,
            settings.tavily_api_key,
            settings.serper_api_key,
        )
        result = {
            "provider": settings.research_provider,
            "query": query,
            "bullets": search_result["bullets"],
            "sources": search_result["sources"],
            "raw": search_result["raw"],
            "mode": "basic",
            "iterations": 1,
            "tool_queries": [query],
        }
    write_cache(settings.cache_dir, cache_key, result)
    return result


def format_bullets(bullets: list[str]) -> str:
    return "\n".join(f"- {item}" for item in bullets)
