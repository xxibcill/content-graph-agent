from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.research_agent import format_bullets, run_research
from agents.writer_agent import run_writer
from agents.validation_agent import run_validation
from agents.creative_agent import run_creative
from graph.state import ContentState

from configs.settings import get_settings


def research_node(state: ContentState) -> dict[str, Any]:
    topic = state.get("topic")
    if not topic:
        raise ValueError("ContentState.topic is required")

    niche = state.get("niche")
    limit = state.get("research_limit")
    result = run_research(topic, niche, limit)

    return {
        "trends": format_bullets(result.get("bullets", [])),
        "research_sources": result.get("sources", []),
        "research_query": result.get("query", ""),
        "research_provider": result.get("provider", ""),
    }


def writer_node(state: ContentState) -> dict[str, Any]:
    topic = state.get("topic")
    if not topic:
        raise ValueError("ContentState.topic is required")

    trends = state.get("trends", "")
    brand_voice = state.get("brand_voice")
    max_sentences = state.get("writer_max_sentences")
    feedback_parts = []
    validation_feedback = state.get("validation_feedback")
    if validation_feedback:
        feedback_parts.append(f"Validation feedback:\n{validation_feedback}")
    manual_feedback = state.get("manual_feedback")
    if manual_feedback:
        feedback_parts.append(f"Manual feedback:\n{manual_feedback}")
    feedback = "\n\n".join(feedback_parts) if feedback_parts else None
    existing_script = state.get("validated_script") or state.get("draft_script")
    result = run_writer(
        topic,
        trends,
        brand_voice,
        max_sentences,
        feedback,
        existing_script,
    )
    return {
        "draft_script": result["script"],
        "writer_prompt_version": result["prompt_version"],
    }


def validation_node(state: ContentState) -> dict[str, Any]:
    script = state.get("draft_script")
    if not script:
        raise ValueError("ContentState.draft_script is required")

    brand_voice = state.get("brand_voice")
    max_sentences = state.get("writer_max_sentences")
    settings = get_settings()
    retry_enabled = state.get("validation_retry_enabled", settings.validation_retry_enabled)
    max_retries = state.get("validation_max_retries", settings.validation_max_retries)
    retry_count = state.get("validation_retry_count", 0)

    result = run_validation(script, brand_voice, max_sentences)
    if result.get("validation_status") == "rewrite" and retry_enabled:
        retry_count += 1

    return {
        **result,
        "validation_retry_enabled": retry_enabled,
        "validation_max_retries": max_retries,
        "validation_retry_count": retry_count,
    }


def creative_node(state: ContentState) -> dict[str, Any]:
    script = state.get("validated_script") or state.get("draft_script")
    if not script:
        raise ValueError("ContentState.validated_script or draft_script is required")

    brand_voice = state.get("brand_voice")
    max_sentences = state.get("creative_max_sentences") or state.get("writer_max_sentences")
    result = run_creative(script, brand_voice, max_sentences)
    return {
        "final_script": result["script"],
        "creative_prompt_version": result["prompt_version"],
    }


def build_graph():
    graph = StateGraph(ContentState)
    graph.add_node("research", research_node)
    graph.add_node("writer", writer_node)
    graph.add_node("validate", validation_node)
    graph.add_node("creative", creative_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", "writer")
    graph.add_edge("writer", "validate")
    graph.add_conditional_edges(
        "validate",
        _route_after_validation,
        {
            "writer": "writer",
            "creative": "creative",
        },
    )
    graph.add_edge("creative", END)
    return graph.compile()


def _route_after_validation(state: ContentState) -> str:
    status = state.get("validation_status")
    retry_enabled = state.get("validation_retry_enabled", False)
    retry_count = state.get("validation_retry_count", 0)
    max_retries = state.get("validation_max_retries", 0)
    if status == "rewrite" and retry_enabled and retry_count <= max_retries:
        return "writer"
    return "creative"
