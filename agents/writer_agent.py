from typing import Optional

import logging
import time

from configs.settings import get_settings
from utils.llm import get_client_and_model
from utils.prompts import load_prompt, select_prompt_version
from utils.retry import run_with_retry


logger = logging.getLogger(__name__)


def build_prompt(
    template: str,
    topic: str,
    trends: str,
    brand_voice: str,
    max_sentences: int,
    feedback: Optional[str],
    existing_script: Optional[str],
) -> str:
    revision_block = ""
    if feedback or existing_script:
        revision_block = (
            "Revision notes:\n"
            f"{feedback or '- (none)'}\n\n"
            "Existing draft:\n"
            f"{existing_script or '- (none)'}\n\n"
            "If an existing draft is provided, revise it rather than starting from scratch.\n\n"
        )

    return template.format(
        topic=topic,
        brand_voice=brand_voice,
        trends=trends or "- (no research notes)",
        max_sentences=max_sentences,
        revision_block=revision_block,
    )


def run_writer(
    topic: str,
    trends: str,
    brand_voice: Optional[str] = None,
    max_sentences: Optional[int] = None,
    feedback: Optional[str] = None,
    existing_script: Optional[str] = None,
) -> dict[str, str]:
    settings = get_settings()

    voice = brand_voice or "friendly, confident, and practical"
    sentence_limit = max_sentences or settings.writer_max_sentences
    version = select_prompt_version(
        settings.writer_prompt_version,
        settings.writer_prompt_variants,
    )
    template = load_prompt(f"writer_{version}.txt")
    prompt = build_prompt(
        template,
        topic,
        trends,
        voice,
        sentence_limit,
        feedback,
        existing_script,
    )
    client, model, provider = get_client_and_model(settings.writer_model)

    def operation():
        return client.chat.completions.create(
            model=model,
            temperature=settings.writer_temperature,
            messages=[{"role": "user", "content": prompt}],
        )

    start = time.perf_counter()
    response = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
    elapsed = time.perf_counter() - start
    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "Writer completed provider=%s model=%s version=%s prompt_tokens=%s completion_tokens=%s duration=%.2fs",
            provider,
            model,
            version,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            elapsed,
        )
    else:
        logger.info(
            "Writer completed provider=%s model=%s version=%s duration=%.2fs",
            provider,
            model,
            version,
            elapsed,
        )

    return {
        "script": (response.choices[0].message.content or "").strip(),
        "prompt_version": version,
    }
