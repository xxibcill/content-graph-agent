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
    script: str,
    brand_voice: str,
    max_sentences: int,
    guidelines: str,
) -> str:
    return template.format(
        script=script,
        brand_voice=brand_voice,
        max_sentences=max_sentences,
        guidelines=guidelines,
    )


def run_creative(
    script: str,
    brand_voice: Optional[str] = None,
    max_sentences: Optional[int] = None,
    guidelines: Optional[str] = None,
) -> dict[str, str]:
    settings = get_settings()

    voice = brand_voice or "friendly, confident, and practical"
    sentence_limit = max_sentences or settings.creative_max_sentences
    active_guidelines = guidelines or settings.creative_guidelines
    version = select_prompt_version(
        settings.creative_prompt_version,
        settings.creative_prompt_variants,
    )
    template = load_prompt(f"creative_{version}.txt")
    prompt = build_prompt(template, script, voice, sentence_limit, active_guidelines)

    client, model, provider = get_client_and_model(settings.creative_model)

    def operation():
        return client.chat.completions.create(
            model=model,
            temperature=settings.creative_temperature,
            messages=[{"role": "user", "content": prompt}],
        )

    start = time.perf_counter()
    response = run_with_retry(operation, retries=2, base_delay=0.5, logger=logger)
    elapsed = time.perf_counter() - start
    usage = getattr(response, "usage", None)
    if usage:
        logger.info(
            "Creative completed provider=%s model=%s version=%s prompt_tokens=%s completion_tokens=%s duration=%.2fs",
            provider,
            model,
            version,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            elapsed,
        )
    else:
        logger.info(
            "Creative completed provider=%s model=%s version=%s duration=%.2fs",
            provider,
            model,
            version,
            elapsed,
        )

    return {
        "script": (response.choices[0].message.content or "").strip(),
        "prompt_version": version,
    }
