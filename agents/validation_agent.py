import logging
import re
import time
from typing import Optional

from configs.settings import get_settings
from utils.llm import get_client_and_model
from utils.retry import run_with_retry


logger = logging.getLogger(__name__)


def count_sentences(text: str) -> int:
    if not text:
        return 0
    chunks = re.split(r"[.!?]+", text)
    return len([chunk for chunk in chunks if chunk.strip()])


def find_blocklist_hits(text: str, blocklist: list[str]) -> list[str]:
    if not blocklist or not text:
        return []
    lowered = text.lower()
    hits = []
    for item in blocklist:
        if item.lower() in lowered:
            hits.append(item)
    return hits


def build_prompt(
    script: str,
    brand_voice: str,
    guidelines: str,
    max_sentences: int,
    issues_text: str,
) -> str:

    return (
        "You are a brand voice editor for short-form video scripts.\n\n"
        f"Brand voice: {brand_voice}\n"
        f"Guidelines: {guidelines}\n"
        f"Max sentences: {max_sentences}\n\n"
        f"Detected issues:\n{issues_text}\n\n"
        "Task: If the script fully complies, respond with exactly 'OK'. "
        "Otherwise, return a revised script only (no preface), fixing issues and "
        "keeping the core meaning.\n\n"
        f"Script:\n{script}"
    )


def detect_issues(
    script: str,
    max_sentences: int,
    blocklist: list[str],
) -> tuple[list[str], int]:
    issues = []
    sentence_count = count_sentences(script)
    if sentence_count > max_sentences:
        issues.append(
            f"Too long: {sentence_count} sentences (max {max_sentences})."
        )
    blocklist_hits = find_blocklist_hits(script, blocklist)
    if blocklist_hits:
        issues.append(f"Blocked terms found: {', '.join(blocklist_hits)}")
    return issues, sentence_count


def run_validation(
    script: str,
    brand_voice: Optional[str] = None,
    max_sentences: Optional[int] = None,
    blocklist: Optional[list[str]] = None,
    guidelines: Optional[str] = None,
) -> dict[str, str]:
    settings = get_settings()

    voice = brand_voice or "friendly, confident, and practical"
    sentence_limit = max_sentences or settings.validation_max_sentences
    active_blocklist = blocklist if blocklist is not None else settings.validation_blocklist
    active_guidelines = guidelines or settings.validation_guidelines

    issues, sentence_count = detect_issues(script, sentence_limit, active_blocklist)
    issues_text = "\n".join(f"- {item}" for item in issues) or "- None detected"
    prompt = build_prompt(
        script,
        voice,
        active_guidelines,
        sentence_limit,
        issues_text,
    )

    client, model, provider = get_client_and_model(settings.validation_model)

    def operation():
        return client.chat.completions.create(
            model=model,
            temperature=settings.validation_temperature,
            messages=[{"role": "user", "content": prompt}],
        )

    start = time.perf_counter()
    response = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
    elapsed = time.perf_counter() - start
    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "Validation completed provider=%s model=%s prompt_tokens=%s completion_tokens=%s duration=%.2fs",
            provider,
            model,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            elapsed,
        )
    else:
        logger.info(
            "Validation completed provider=%s model=%s duration=%.2fs",
            provider,
            model,
            elapsed,
        )

    output = (response.choices[0].message.content or "").strip()
    status = "ok"
    validated_script = script.strip()
    if output.upper() != "OK" or issues:
        status = "rewrite"
        if output.upper() != "OK":
            validated_script = output

    feedback = issues_text
    if status == "rewrite" and issues_text == "- None detected":
        feedback = "Rewrite to better align with the brand voice and guidelines."

    return {
        "validated_script": validated_script,
        "validation_status": status,
        "validation_notes": "ok" if status == "ok" else "rewrite",
        "validation_feedback": feedback,
    }
