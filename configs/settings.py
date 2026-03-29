from dataclasses import dataclass
import os
from typing import Optional


def _default_model(provider: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "openrouter": "openrouter/auto",
        "groq": "llama-3.1-8b-instant",
        "deepseek": "deepseek-chat",
    }
    return defaults.get(provider, "gpt-4o-mini")


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    tavily_api_key: Optional[str]
    serper_api_key: Optional[str]
    research_provider: str
    research_mode: str
    research_agent_model: str
    research_agent_temperature: float
    react_max_steps: int
    cache_dir: str
    cache_ttl_seconds: int
    default_limit: int
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    openrouter_api_key: Optional[str]
    openrouter_base_url: str
    groq_api_key: Optional[str]
    groq_base_url: str
    deepseek_api_key: Optional[str]
    deepseek_base_url: str
    writer_model: str
    writer_temperature: float
    writer_max_sentences: int
    writer_prompt_version: str
    writer_prompt_variants: list[str]
    validation_model: str
    validation_temperature: float
    validation_max_sentences: int
    validation_blocklist: list[str]
    validation_guidelines: str
    validation_retry_enabled: bool
    validation_max_retries: int
    creative_model: str
    creative_temperature: float
    creative_max_sentences: int
    creative_guidelines: str
    creative_prompt_version: str
    creative_prompt_variants: list[str]
    output_dir: str


def get_settings() -> Settings:
    provider = os.getenv("RESEARCH_PROVIDER", "tavily").strip().lower()
    if provider not in {"tavily", "serper"}:
        provider = "tavily"

    research_mode = os.getenv("RESEARCH_MODE", "basic").strip().lower()
    if research_mode not in {"basic", "react"}:
        research_mode = "basic"

    llm_provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if llm_provider not in {"openai", "openrouter", "groq", "deepseek"}:
        llm_provider = "openai"

    default_model = (
        os.getenv("LLM_MODEL")
        or os.getenv("OPENAI_MODEL")
        or _default_model(llm_provider)
    )

    return Settings(
        llm_provider=llm_provider,
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        serper_api_key=os.getenv("SERPER_API_KEY"),
        research_provider=provider,
        research_mode=research_mode,
        research_agent_model=os.getenv("RESEARCH_AGENT_MODEL", default_model),
        research_agent_temperature=float(os.getenv("RESEARCH_AGENT_TEMPERATURE", "0.1")),
        react_max_steps=int(os.getenv("REACT_MAX_STEPS", "3")),
        cache_dir=os.getenv("RESEARCH_CACHE_DIR", ".cache/research"),
        cache_ttl_seconds=int(os.getenv("RESEARCH_CACHE_TTL_SECONDS", "86400")),
        default_limit=int(os.getenv("RESEARCH_RESULT_LIMIT", "5")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        writer_model=os.getenv("WRITER_MODEL", default_model),
        writer_temperature=float(os.getenv("WRITER_TEMPERATURE", "0.7")),
        writer_max_sentences=int(os.getenv("WRITER_MAX_SENTENCES", "5")),
        writer_prompt_version=os.getenv("WRITER_PROMPT_VERSION", "v1"),
        writer_prompt_variants=[
            item.strip()
            for item in os.getenv("WRITER_PROMPT_VARIANTS", "").split(",")
            if item.strip()
        ],
        validation_model=os.getenv("VALIDATION_MODEL", default_model),
        validation_temperature=float(os.getenv("VALIDATION_TEMPERATURE", "0.2")),
        validation_max_sentences=int(os.getenv("VALIDATION_MAX_SENTENCES", "5")),
        validation_blocklist=[
            item.strip()
            for item in os.getenv("VALIDATION_BLOCKLIST", "").split(",")
            if item.strip()
        ],
        validation_guidelines=os.getenv(
            "VALIDATION_GUIDELINES",
            "No profanity, avoid hypey claims, keep it clear and practical.",
        ),
        validation_retry_enabled=os.getenv("VALIDATION_RETRY_ENABLED", "false").lower()
        in {"1", "true", "yes"},
        validation_max_retries=int(os.getenv("VALIDATION_MAX_RETRIES", "1")),
        creative_model=os.getenv("CREATIVE_MODEL", default_model),
        creative_temperature=float(os.getenv("CREATIVE_TEMPERATURE", "0.8")),
        creative_max_sentences=int(os.getenv("CREATIVE_MAX_SENTENCES", "5")),
        creative_guidelines=os.getenv(
            "CREATIVE_GUIDELINES",
            "Add a strong hook and story flow while keeping it authentic.",
        ),
        creative_prompt_version=os.getenv("CREATIVE_PROMPT_VERSION", "v1"),
        creative_prompt_variants=[
            item.strip()
            for item in os.getenv("CREATIVE_PROMPT_VARIANTS", "").split(",")
            if item.strip()
        ],
        output_dir=os.getenv("OUTPUT_DIR", "outputs"),
    )
