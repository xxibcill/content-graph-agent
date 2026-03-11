# Personal Branding AI Agent Workflow

This repo builds a multi-agent workflow for short-form content development, based on `research.md`. The current state includes research, writing, validation, and creative polishing, plus prompt versioning, A/B hooks, metrics tracking, retries, logging, and output persistence.

It now also includes:

- a small FastAPI service layer for HTTP access
- an automated unittest suite for core workflow behavior
- a GitHub Actions CI workflow that runs the test suite

## Workflow

- Research agent gathers trends and facts
- Writer agent drafts a script from research notes
- Validation agent enforces brand voice and guidelines
- Creative agent sharpens hook and narrative flow

## Requirements

- Python 3.10+ recommended
- One search API key:
  - Tavily: `TAVILY_API_KEY`
  - Serper: `SERPER_API_KEY`
- One LLM provider API key (OpenAI, OpenRouter, Groq, or DeepSeek)

Install dependencies (uv recommended):

```bash
uv pip install -r requirements.txt
```

Optional: create a virtual environment managed by uv.

```bash
uv venv
```

## Quickstart

```bash
uv run python scripts/run_graph.py --topic "personal branding" --niche "creator economy" --show-sources
```

## Usage

Research only:

```bash
uv run python scripts/run_research.py --topic "personal branding" --niche "creator economy"
```

Full workflow (research + writer + validation + creative):

```bash
uv run python scripts/run_graph.py --topic "personal branding" --niche "creator economy" --show-sources
```

Run the API locally:

```bash
uv run uvicorn api.main:app --reload
```

Then open:

- `GET /health`
- `POST /research`
- `POST /generate`

Provide manual feedback for revisions:

```bash
uv run python scripts/run_graph.py --topic "personal branding" --feedback "Make it more punchy and cut one sentence."
```

Show prompt versions used:

```bash
uv run python scripts/run_graph.py --topic "personal branding" --show-versions
```

Save output to disk (prints `saved_run_id` and path):

```bash
uv run python scripts/run_graph.py --topic "personal branding" --save-output
```

Output full JSON (includes sources and raw payload):

```bash
uv run python scripts/run_research.py --topic "personal branding" --json
```

Record engagement metrics:

```bash
uv run python scripts/record_metrics.py --run-id <RUN_ID> --views 1200 --likes 120 --comments 14
```

A/B test prompt variants (example):

```bash
export WRITER_PROMPT_VARIANTS="v1,v2"
export CREATIVE_PROMPT_VARIANTS="v1,v2"
```

Provider examples:

```bash
export LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=<KEY>
export WRITER_MODEL="meta-llama/llama-3.1-8b-instruct"
```

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=<KEY>
export WRITER_MODEL="llama-3.1-8b-instant"
```

```bash
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=<KEY>
export WRITER_MODEL="deepseek-chat"
```

## Output files

- Runs are saved to `outputs/runs-YYYYMMDD.jsonl` by default
- Metrics append to `outputs/metrics.jsonl`

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Configuration (env vars)

The CLIs load environment variables from a local `.env` file if present.

Research
- `RESEARCH_PROVIDER`: `tavily` (default) or `serper`
- `TAVILY_API_KEY`: Tavily API key (required if provider is tavily)
- `SERPER_API_KEY`: Serper API key (required if provider is serper)
- `RESEARCH_CACHE_DIR`: cache path (default `.cache/research`)
- `RESEARCH_CACHE_TTL_SECONDS`: cache TTL in seconds (default `86400`)
- `RESEARCH_RESULT_LIMIT`: max results to keep (default `5`)

LLM Provider
- `LLM_PROVIDER`: `openai`, `openrouter`, `groq`, or `deepseek` (default `openai`)
- `LLM_MODEL`: global default model (optional)
- `OPENAI_API_KEY`: OpenAI API key (required if provider is openai)
- `OPENAI_BASE_URL`: override OpenAI base URL (optional)
- `OPENROUTER_API_KEY`: OpenRouter API key (required if provider is openrouter)
- `OPENROUTER_BASE_URL`: override OpenRouter base URL (optional)
- `GROQ_API_KEY`: Groq API key (required if provider is groq)
- `GROQ_BASE_URL`: override Groq base URL (optional)
- `DEEPSEEK_API_KEY`: DeepSeek API key (required if provider is deepseek)
- `DEEPSEEK_BASE_URL`: override DeepSeek base URL (optional)
- `OPENAI_MODEL`: legacy global default model (optional)

If no model env vars are set, a provider-specific default is used.

Writer
- `WRITER_MODEL`: model name for writer agent
- `WRITER_TEMPERATURE`: temperature for writer agent (default `0.7`)
- `WRITER_MAX_SENTENCES`: max sentences in writer output (default `5`)
- `WRITER_PROMPT_VERSION`: prompt version for writer (default `v1`)
- `WRITER_PROMPT_VARIANTS`: comma-separated prompt versions for A/B testing

Validation
- `VALIDATION_MODEL`: model name for validation agent (default `gpt-4o-mini`)
- `VALIDATION_TEMPERATURE`: temperature for validation agent (default `0.2`)
- `VALIDATION_MAX_SENTENCES`: max sentences for validation output (default `5`)
- `VALIDATION_BLOCKLIST`: comma-separated blocked terms
- `VALIDATION_GUIDELINES`: extra validation guidelines string
- `VALIDATION_RETRY_ENABLED`: enable validation retry loop (default `false`)
- `VALIDATION_MAX_RETRIES`: max validation retry loops (default `1`)

Creative
- `CREATIVE_MODEL`: model name for creative agent (default `gpt-4o-mini`)
- `CREATIVE_TEMPERATURE`: temperature for creative agent (default `0.8`)
- `CREATIVE_MAX_SENTENCES`: max sentences for creative output (default `5`)
- `CREATIVE_GUIDELINES`: extra creative guidelines string
- `CREATIVE_PROMPT_VERSION`: prompt version for creative (default `v1`)
- `CREATIVE_PROMPT_VARIANTS`: comma-separated prompt versions for A/B testing

Ops
- `LOG_LEVEL`: logging level (default `INFO`)
- `OUTPUT_DIR`: output directory for saved runs (default `outputs`)

## Prompt templates

Prompt templates live in `prompts/` and are versioned:

- `prompts/writer_v1.txt`
- `prompts/writer_v2.txt`
- `prompts/creative_v1.txt`
- `prompts/creative_v2.txt`

## Scheduling

Example cron (daily at 9am):

```bash
0 9 * * * cd /path/to/content-graph-agent && uv run python scripts/run_graph.py --topic "personal branding" --save-output
```

## Phase roadmap

See `implementation-plan.md` for the phased MVP plan.
