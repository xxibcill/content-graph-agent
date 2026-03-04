from typing import TypedDict


class ContentState(TypedDict, total=False):
    topic: str
    niche: str
    research_limit: int
    trends: str
    research_sources: list[str]
    research_query: str
    research_provider: str
    brand_voice: str
    writer_max_sentences: int
    writer_prompt_version: str
    draft_script: str
    validated_script: str
    validation_status: str
    validation_notes: str
    validation_feedback: str
    validation_retry_enabled: bool
    validation_retry_count: int
    validation_max_retries: int
    creative_max_sentences: int
    creative_prompt_version: str
    final_script: str
    manual_feedback: str
