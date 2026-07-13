# ADR 0003: Default Local LLM — Qwen3 8B

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

The platform needs a default local LLM that balances reasoning quality, resource cost, and licensing. It must run on a modern developer laptop, ideally with a consumer GPU (8-12GB VRAM) but also function on CPU.

## Decision

Adopt **Qwen3 8B** (Q4_K_M quantization via Ollama) as the default general-purpose LLM.

| Property | Value |
|----------|-------|
| Ollama tag | `qwen3:8b` |
| License | Apache 2.0 |
| Quantized size | ~5GB |
| Context window | 32768 tokens |
| Min VRAM | 8GB |
| CPU fallback | Yes (slower) |

## Alternatives Considered

| Model | Size | License | Why not default |
|-------|------|---------|-----------------|
| Phi-4-mini | 3.8B / ~2.5GB | MIT | Lower reasoning quality on complex tasks; retained as fallback config |
| Mistral Small 3.1 | ~24B | Apache 2.0 | Heavier; needs more VRAM than typical laptop |
| gpt-oss 20B | 20B | Apache 2.0 | Larger RAM/VRAM footprint |
| Llama 4 Scout | 70B | Community (restricted) | License restrictions; too heavy |

## Usage Policy

- Prompts declare `model: qwen3:8b` by default.
- Phi-4-mini is configured for resource-constrained machines (see `models/llm-configs/phi-4-mini.yaml`).
- The runtime selects the model per task, allowing future swap without code changes.

## Consequences

**Positive:**
- Apache 2.0 license — no usage restrictions
- Strong reasoning and coding ability at 8B
- Runs on widely-available hardware
- Active ecosystem (Ollama, LM Studio)

**Negative:**
- 8B may struggle with very long context or highly specialized reasoning
- CPU inference is slow (mitigated by Phi-4-mini fallback)

## Revisit When

- A clearly superior Apache/MIT model of similar size ships
- Hardware upgrades allow a larger default (e.g. Mistral Small 3.1)
