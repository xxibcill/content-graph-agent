from typing import Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.content_service import run_research_only, run_workflow


app = FastAPI(
    title="Content Graph Agent API",
    version="0.1.0",
    description="HTTP interface for the content generation workflow.",
)


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1)
    niche: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1, le=10)
    research_mode: Optional[str] = Field(default=None, pattern="^(basic|react)$")


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=1)
    niche: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1, le=10)
    research_mode: Optional[str] = Field(default=None, pattern="^(basic|react)$")
    feedback: Optional[str] = None
    brand_voice: Optional[str] = None
    writer_max_sentences: Optional[int] = Field(default=None, ge=1, le=20)
    creative_max_sentences: Optional[int] = Field(default=None, ge=1, le=20)
    validation_retry_enabled: Optional[bool] = None
    validation_max_retries: Optional[int] = Field(default=None, ge=0, le=5)
    save_output: bool = False
    output_file: Optional[str] = None


class WorkflowResponse(BaseModel):
    script: str
    result: dict[str, Any]
    saved_run_id: Optional[str] = None
    saved_path: Optional[str] = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/research")
def research(request: ResearchRequest) -> dict[str, Any]:
    return run_research_only(
        topic=request.topic,
        niche=request.niche,
        limit=request.limit,
        research_mode=request.research_mode,
    )


@app.post("/generate", response_model=WorkflowResponse)
def generate(request: GenerateRequest) -> WorkflowResponse:
    payload = run_workflow(
        topic=request.topic,
        niche=request.niche,
        limit=request.limit,
        research_mode=request.research_mode,
        feedback=request.feedback,
        brand_voice=request.brand_voice,
        writer_max_sentences=request.writer_max_sentences,
        creative_max_sentences=request.creative_max_sentences,
        validation_retry_enabled=request.validation_retry_enabled,
        validation_max_retries=request.validation_max_retries,
        save_output_enabled=request.save_output,
        output_file=request.output_file,
    )
    return WorkflowResponse(**payload)
