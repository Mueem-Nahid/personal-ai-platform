# Career Agent Models

Model configurations, embedding model specs, reranker configs, and Ollama manifests for the career-agent platform. This folder holds only configs and pointers — actual weights live in Ollama's model store or on disk.

## Structure

```
embeddings/        # embedding model configs
rerankers/         # reranker model configs (later)
llm-configs/       # LLM configs + Ollama Modelfiles
```

## Default Models

| Purpose | Model | Size | License |
|---------|-------|------|---------|
| General reasoning | qwen3:8b | ~5GB (Q4) | Apache 2.0 |
| Lightweight fallback | phi-4-mini | ~2.5GB | MIT |
| Embeddings | bge-m3 | ~1.2GB | MIT |

## Usage

```bash
# Pull defaults via Ollama
ollama pull qwen3:8b
ollama pull bge-m3

# Or use the manifest in this repo
ollama create career-qwen3 -f llm-configs/ollama-manifests/qwen3-8b.modelfile
```
