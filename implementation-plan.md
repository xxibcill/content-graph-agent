# AI Agent Workflow for Personal Branding - Implementation Plan

This plan is based on `research.md` and structured as an incremental, agile delivery. Each phase ships an MVP and includes TODOs to track progress.

## Phase 0 - Foundations (MVP: runnable skeleton)
Goal: repo scaffolding, configs, and an end-to-end LangGraph skeleton with stub agents.

TODO:
- Define project structure (`agents/`, `graph/`, `configs/`, `scripts/`).
- Add env/config handling for API keys and model selection.
- Implement ContentState schema (TypedDict or dataclass).
- Create stub agents that return placeholder data.
- Build LangGraph pipeline: START -> Research -> Write -> Validate -> Creative -> END.
- Add a CLI entrypoint to run with a topic and print output.

## Phase 1 - Research Agent (MVP: trend data collection)
Goal: collect real trend inputs from minimal sources.

TODO:
- Choose data source (Serper/Tavily or Google Trends via pytrends).
- Implement search tool wrapper with API key.
- Add query templates based on brand niche and topic.
- Normalize output into concise bullet list (3-5 items).
- Add basic caching (in-memory or file-based) for daily reuse.

## Phase 2 - Writer Agent (MVP: draft script)
Goal: generate a short-form script from research output.

TODO:
- Define prompt template (hook + 3-5 beats + CTA).
- Implement OpenAI call with model/temperature controls.
- Add length guardrails (sentence count or word limit).
- Store `draft_script` in state.

## Phase 3 - Validation Agent (MVP: brand voice compliance)
Goal: enforce tone and style guidelines.

TODO:
- Define brand voice config (tone, forbidden terms, style rules).
- LLM-as-judge prompt to return "OK" or a corrected script.
- Add deterministic checks (emoji count, profanity list).
- Store `validated_script` in state.

## Phase 4 - Creative Agent (MVP: hook + story polish)
Goal: increase engagement with a stronger hook and narrative flow.

TODO:
- Prompt for hook rewrite and narrative framing.
- Enforce maximum sentence count.
- Preserve core meaning while enhancing engagement.
- Store `final_script` in state.

## Phase 5 - Orchestration and Reliability (MVP: stable workflow)
Goal: production-ready reliability for a single user.

TODO:
- Add retry logic for API calls.
- Add optional loop: if validation fails, rewrite once.
- Add logging per node (timing, token usage, errors).
- Add trace hooks for LangSmith (optional).

## Phase 6 - Delivery and Scheduling (MVP: automation)
Goal: daily or weekly generation and easy retrieval.

TODO:
- Add a simple scheduler (cron or Prefect).
- Add output persistence (local JSON, SQLite, or Notion export).
- Add a basic report format (topic, script, timestamp).

## Phase 7 - Quality and Iteration (MVP: measurable improvement)
Goal: continuous improvement of script quality.

TODO:
- Add prompt versioning and A/B test support.
- Track engagement metrics manually or via a sheet.
- Add feedback loop to refine prompts and hooks.
