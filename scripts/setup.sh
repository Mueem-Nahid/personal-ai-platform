#!/usr/bin/env bash
# Career Agent — Setup Script (Linux/macOS/Git Bash)
# Usage: bash scripts/setup.sh
set -euo pipefail

echo "Starting Career Agent stack..."
if ! docker compose up -d; then
  echo "ERROR: docker compose up failed. Fix build errors then rerun this script." >&2
  exit 1
fi

echo -e "\nWaiting for services to be healthy..."
sleep 8

echo -e "\nPulling default LLM (qwen3:8b) — one-time, ~5GB..."
if ! docker exec career-agent-ollama ollama pull qwen3:8b; then
  echo "WARNING: Could not pull qwen3:8b — is the ollama container running?" >&2
  echo "  Run manually: docker exec career-agent-ollama ollama pull qwen3:8b" >&2
fi

echo -e "\nPulling embedding model (bge-m3)..."
if ! docker exec career-agent-ollama ollama pull bge-m3; then
  echo "WARNING: Could not pull bge-m3." >&2
  echo "  Run manually: docker exec career-agent-ollama ollama pull bge-m3" >&2
fi

echo -e "\nStack ready:"
echo "  Backend  : http://localhost:8000/api/v1/docs"
echo "  Frontend : http://localhost:3000"
echo "  Qdrant   : http://localhost:6333/dashboard"
echo "  MinIO    : http://localhost:9001"
