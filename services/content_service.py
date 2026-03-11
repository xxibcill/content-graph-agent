from typing import Any, Optional

from agents.research_agent import run_research
from configs.settings import get_settings
from graph.content_graph import build_graph
from utils.persistence import save_run


def build_initial_state(
    topic: str,
    niche: Optional[str] = None,
    limit: Optional[int] = None,
    feedback: Optional[str] = None,
    brand_voice: Optional[str] = None,
    writer_max_sentences: Optional[int] = None,
    creative_max_sentences: Optional[int] = None,
    validation_retry_enabled: Optional[bool] = None,
    validation_max_retries: Optional[int] = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "topic": topic,
        "niche": niche,
        "research_limit": limit,
        "manual_feedback": feedback,
    }
    if brand_voice:
        state["brand_voice"] = brand_voice
    if writer_max_sentences is not None:
        state["writer_max_sentences"] = writer_max_sentences
    if creative_max_sentences is not None:
        state["creative_max_sentences"] = creative_max_sentences
    if validation_retry_enabled is not None:
        state["validation_retry_enabled"] = validation_retry_enabled
    if validation_max_retries is not None:
        state["validation_max_retries"] = validation_max_retries
    return state


def extract_script(result: dict[str, Any]) -> str:
    return (
        result.get("final_script")
        or result.get("validated_script")
        or result.get("draft_script")
        or ""
    )


def run_research_only(
    topic: str,
    niche: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    return run_research(topic, niche, limit)


def run_workflow(
    topic: str,
    niche: Optional[str] = None,
    limit: Optional[int] = None,
    feedback: Optional[str] = None,
    brand_voice: Optional[str] = None,
    writer_max_sentences: Optional[int] = None,
    creative_max_sentences: Optional[int] = None,
    validation_retry_enabled: Optional[bool] = None,
    validation_max_retries: Optional[int] = None,
    save_output_enabled: bool = False,
    output_file: Optional[str] = None,
) -> dict[str, Any]:
    state = build_initial_state(
        topic=topic,
        niche=niche,
        limit=limit,
        feedback=feedback,
        brand_voice=brand_voice,
        writer_max_sentences=writer_max_sentences,
        creative_max_sentences=creative_max_sentences,
        validation_retry_enabled=validation_retry_enabled,
        validation_max_retries=validation_max_retries,
    )
    result = build_graph().invoke(state)
    payload: dict[str, Any] = {
        "result": result,
        "script": extract_script(result),
    }

    if not save_output_enabled:
        return payload

    settings = get_settings()
    saved = save_run(
        settings.output_dir,
        {
            "topic": topic,
            "niche": niche,
            "result": result,
        },
        output_path=output_file,
    )
    payload["saved_run_id"] = saved["run_id"]
    payload["saved_path"] = saved["path"]
    return payload
