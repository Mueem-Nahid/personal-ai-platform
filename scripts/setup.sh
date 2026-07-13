#!/usr/bin/env bash
# Career Agent — Setup Script (Linux/macOS)
set -euo pipefail

echo "Starting Career Agent stack..."
docker compose up -d

echo -e "\nWaiting for services to be healthy..."
sleep 8

echo -e "\nPulling default LLM (qwen3:8b) — one-time, ~5GB..."
docker exec career-agent-ollama ollama pull qwen3:8b

echo -e "\nPulling embedding model (bge-m3)..."
docker exec career-agent-ollama ollama pull bge-m3

echo -e "\nStack ready:"
echo "  Backend  : http://localhost:8000/api/v1/docs"
echo "  Frontend : http://localhost:3000"
echo "  Qdrant   : http://localhost:6333/dashboard"
echo "  MinIO    : http://localhost:9001"
