# ADR-03: LLM Provider Strategy

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D3 — LLM provider strategy, fallback, rate-limit handling, local-model option.

## Context
Athena needs an LLM for orchestration (tool selection, report generation). Budget is free-tier or very low cost. Groq provides free access to open models but has rate limits and has historically deprecated models without long notice.

## Research Findings (verified 2026-10-08)
- **Groq free tier:** Rate limits vary by model. Typical: 30 RPM, 14,400 RPD, 6,000 TPM for free tier. Models rotate; availability is not guaranteed long-term.
- **Groq current models:** `llama-3.3-70b-versatile`, `qwen/qwen3-32b`, and others. Check at runtime.
- **Cerebras:** Free inference API with high speed. Similar risk profile to Groq.
- **OpenRouter:** Aggregator with some free models. Adds a layer of indirection.
- **Local models (Ollama):** Reliable but requires capable hardware. Not viable for deployment.

## Options

### Option A: Groq Primary + Configurable Fallback (Recommended)
Groq as the default provider, with the provider abstraction allowing any OpenAI-compatible API as a fallback.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Free |
| Performance | Fast (Groq is optimized for inference speed) |
| Reliability | Medium — rate limits, model deprecation risk |
| Complexity | Low — single client with provider config |
| Interview showcase | Good — demonstrates provider abstraction, resilience |

### Option B: OpenRouter as Aggregator
Route all calls through OpenRouter, which provides access to multiple providers.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Some free models; paid models at cost |
| Reliability | Higher — can fall back across providers |
| Complexity | Low — single endpoint |
| Risk | Dependency on OpenRouter as intermediary; free model availability varies |

### Option C: Multi-Provider with Automatic Failover
Implement a provider chain: try Groq, fall back to Cerebras, fall back to local Ollama.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Free (if using free tiers + local) |
| Reliability | High — multiple fallback layers |
| Complexity | High — must handle different API quirks, model capabilities |
| Risk | Over-engineering for a portfolio project |

## Decision
**Option A: Groq Primary + Configurable Fallback.**

Implementation:
1. **`LLMClient` abstraction:** A single interface with `chat(messages, tools) -> Response` that handles:
   - Provider selection via `LLM_PROVIDER` env var (default: `groq`)
   - Model ID via `LLM_MODEL` env var (default: current best available on Groq)
   - API key via `LLM_API_KEY` env var
   - Base URL via `LLM_BASE_URL` env var (allows pointing to any OpenAI-compatible endpoint)

2. **Rate-limit handling:**
   - Exponential backoff with jitter on 429 responses
   - Max 3 retries per call
   - User-facing SSE event: `{"type": "status", "message": "Waiting for LLM availability..."}`

3. **Record/replay cache:**
   - Hash of (model, messages, tools, seed) → cached response
   - Stored as JSON files in `benchmark/cache/`
   - Enabled via `LLM_CACHE_MODE` env var: `off` (default), `record`, `replay`, `auto` (replay if cached, else record)

4. **Local model support:**
   - Ollama with an OpenAI-compatible endpoint works out of the box via `LLM_BASE_URL`
   - Not tested in CI or documented as primary; mentioned as an option for development

## Consequences
- Must verify Groq model IDs at development time and make them easily updatable.
- Benchmark reliability depends on the record/replay cache.
- If Groq deprecates the chosen model, updating is a one-line env var change.
