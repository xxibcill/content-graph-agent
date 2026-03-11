# Project Status: Content Graph Agent

Last updated: 2026-03-11

## Executive Summary

This project is a Python-based multi-agent content generation workflow for short-form personal brand content. It uses LangGraph to orchestrate four main stages:

1. Research a topic using a search API.
2. Write a draft script with an LLM.
3. Validate the draft against tone and rule constraints.
4. Creatively rewrite the validated draft for stronger engagement.

The repository is beyond the idea stage. The core pipeline is implemented, runnable from the command line, configurable through environment variables, and structured with separate agent modules. It also includes practical supporting features such as retry logic, research caching, prompt versioning, JSONL persistence, and manual metric logging.

At the same time, the project is still an early-stage application rather than a production product. It has no automated test suite, no CI, no API server, no scheduler implementation, no UI, and no deployment setup. Several ideas described in the research and implementation plan are only partially realized or remain future work.

## What This Project Does

The project generates short-form script outputs for topics related to personal branding or creator-style content.

Given a topic such as `"personal branding"` and an optional niche such as `"creator economy"`, the system:

- builds a search query for recent topics and facts
- calls a research provider (`Tavily` or `Serper`)
- normalizes the search results into short research bullets
- feeds those bullets into a writer prompt
- validates the resulting script for sentence length, blocked terms, and general guideline alignment
- optionally loops back to rewrite when validation requests a revision
- runs a creative rewrite pass to improve the hook, flow, and CTA
- optionally saves the run to disk and later records engagement metrics against that run

The final output is not a long article. It is a short script intended for short-form video or direct-to-camera content.

## How It Works

### Core architecture

The main orchestration lives in `graph/content_graph.py` and is built with `langgraph`.

The workflow is:

`START -> research -> writer -> validate -> creative -> END`

There is one conditional branch:

- if validation returns `"rewrite"` and retry is enabled, the graph routes back to `writer`
- otherwise it proceeds to `creative`

Shared workflow data is stored in a typed state object in `graph/state.py`. That state carries topic, niche, research notes, source URLs, drafts, validation feedback, retry counters, final script, and optional manual feedback.

### Agent responsibilities

#### 1. Research agent

File: `agents/research_agent.py`

Current behavior:

- builds a search query from topic and niche
- supports two providers: `Tavily` and `Serper`
- normalizes provider responses into bullet points plus source URLs
- caches research responses on disk under `.cache/research`
- retries failed API calls with exponential backoff

This is a lightweight search-and-summarize stage, not a deep crawler or multi-source synthesis engine.

#### 2. Writer agent

File: `agents/writer_agent.py`

Current behavior:

- loads a versioned prompt template from `prompts/`
- injects topic, brand voice, research bullets, sentence limit, and revision notes
- calls an OpenAI-compatible chat completion API
- supports prompt variants for simple A/B testing through random selection

The writer can revise an existing draft when validation feedback or manual feedback is present.

#### 3. Validation agent

File: `agents/validation_agent.py`

Current behavior:

- checks sentence count deterministically
- checks a configurable blocklist deterministically
- sends the script plus detected issues to an LLM reviewer/editor
- expects either exactly `OK` or a rewritten script

This means validation is hybrid:

- rules like sentence count and blocked terms are deterministic
- broader tone/guideline enforcement is delegated to the LLM

#### 4. Creative agent

File: `agents/creative_agent.py`

Current behavior:

- loads a versioned creative prompt template
- rewrites the script to strengthen hook, story beat, and CTA
- uses configurable model and temperature settings

This stage is responsible for making the output feel more engaging, not for factual research.

## Current Status by Area

### Implemented and usable now

- LangGraph pipeline with four working nodes
- CLI entrypoint for the full workflow: `scripts/run_graph.py`
- CLI entrypoint for research-only runs: `scripts/run_research.py`
- JSONL run persistence via `utils/persistence.py`
- JSONL metrics recording via `scripts/record_metrics.py`
- Prompt versioning for writer and creative agents
- Random prompt variant selection for basic A/B experimentation
- Retry logic for external API calls
- File-based research cache
- Centralized environment-based configuration
- Support for multiple OpenAI-compatible LLM providers:
  - OpenAI
  - OpenRouter
  - Groq
  - DeepSeek

### Verified locally during this review

The following local checks succeeded on 2026-03-11:

- `scripts/run_graph.py --help`
- `scripts/run_research.py --help`
- graph compilation through `build_graph()`
- settings loading through `get_settings()`

This confirms the project structure is runnable locally at the CLI/import level.

### Implemented, but still lightweight

- Validation retry loop exists, but only supports a simple rewrite cycle with a retry counter
- A/B testing exists, but only as random prompt-version selection with no built-in evaluation logic
- Metrics recording exists, but there is no reporting or analytics layer on top of the stored metrics
- Output persistence exists, but only as append-only local JSONL files
- Logging exists, but is basic standard logging rather than a full tracing/observability setup

### Not implemented yet

- automated unit or integration tests
- CI workflow
- API service layer such as FastAPI
- web UI or operator dashboard
- scheduler implementation inside the project
- deployment manifests or containerization
- database-backed persistence
- human approval workflow inside the graph
- rich observability such as LangSmith tracing
- metric analysis or automatic feedback optimization
- stronger source quality filtering or factual verification beyond search result snippets

## What “Current Status” Really Means

The project is in a strong MVP or prototype state.

It is not just scaffolding. The repository contains real execution paths, real provider integrations, and real agent prompts. A developer with valid API keys can run the workflow today and generate outputs.

However, it is still optimized for local experimentation rather than team-scale operation or production reliability. The codebase has clean separation by concern, but the surrounding engineering systems that usually turn a prototype into a product are still missing.

## Gaps and Risks

### Product and workflow risks

- Research quality depends heavily on search snippets, not full document analysis.
- Validation relies partly on an LLM judge, which can be inconsistent.
- Creative rewriting can improve engagement but may drift from factual precision if prompts are not tightly controlled.
- There is no explicit brand profile system beyond plain text `brand_voice` and guideline strings.

### Engineering risks

- No test coverage means regressions are easy to introduce.
- No CI means repository health is not automatically enforced.
- No pinned lockfile or packaging standard beyond `requirements.txt`.
- No structured schema validation around persisted outputs.
- No failure recovery beyond simple retries.

### Operational risks

- End-to-end success depends on external API keys and network access.
- Costs can grow because multiple LLM calls are made per run.
- There is no built-in rate limiting, queueing, or concurrency control.
- There is no secret-management strategy beyond local environment variables.

## How the Project Is Likely to Develop Further

The most sensible development path is not to add more agents immediately. The stronger next step is to harden the existing workflow.

### Near-term development

These are the highest-value next steps:

1. Add tests.
   - unit tests for query building, normalization, cache behavior, retries, validation helpers, and persistence
   - integration tests that mock LLM/search clients

2. Add CI.
   - run linting and tests on every change
   - fail fast on import or packaging issues

3. Improve observability.
   - structured logs per node
   - token/cost tracking per run
   - optional LangSmith tracing

4. Improve output quality controls.
   - better validation rules
   - clearer factuality checks
   - source scoring or filtering

5. Add a first-class brand configuration model.
   - reusable brand profiles
   - stronger guidelines than a single free-text string

### Mid-term development

Once the pipeline is stable, the next layer should be operationalization:

1. Add an API service.
   - expose the workflow through FastAPI
   - allow external apps or automations to trigger generation

2. Add persistent storage.
   - move runs and metrics from JSONL to SQLite or Postgres
   - enable search, reporting, and history views

3. Add scheduling.
   - scheduled daily or weekly content generation
   - generated run history tied to topics, niches, and prompt versions

4. Add evaluation.
   - compare prompt versions against engagement metrics
   - identify which hooks or formats work best

### Longer-term development

If the project continues beyond MVP hardening, possible directions include:

- a user interface for topic entry, review, and approval
- human-in-the-loop checkpoints after writer or validation stages
- richer research sources beyond search APIs
- multi-format output generation for different platforms
- automated prompt optimization based on historical performance
- team features such as shared workspaces, brand presets, and review workflows

## Recommended Development Priorities

If this project is going to continue, the recommended order is:

1. Stabilize what already exists.
2. Add tests and CI.
3. Add observability and analytics.
4. Move persistence to a real database.
5. Add API and scheduling surfaces.
6. Only then expand product scope with UI, richer retrieval, or more agents.

This order matters because the current architecture is already sufficient to learn from real runs. The main limitation is not missing creative ideas. It is missing reliability, measurement, and operational tooling.

## Repo Structure Summary

```text
agents/
  research_agent.py
  writer_agent.py
  validation_agent.py
  creative_agent.py
graph/
  content_graph.py
  state.py
configs/
  settings.py
scripts/
  run_graph.py
  run_research.py
  record_metrics.py
utils/
  llm.py
  prompts.py
  cache.py
  retry.py
  persistence.py
  logging.py
prompts/
  writer_v1.txt
  writer_v2.txt
  creative_v1.txt
  creative_v2.txt
```

## Bottom Line

This repository currently works as a local, CLI-based MVP for AI-assisted short-form content generation. It already has a real multi-agent pipeline and enough engineering around it to run experiments productively.

What it still needs is the set of systems that make an MVP durable: tests, CI, observability, stronger evaluation, and a more operational delivery surface. That is the most credible path for further development.
