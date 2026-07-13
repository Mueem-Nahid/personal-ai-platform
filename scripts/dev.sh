#!/usr/bin/env bash
# Career Agent — Dev Script (Linux/macOS)
set -euo pipefail

echo "Starting infra services only (postgres, qdrant, redis, minio, ollama)..."
docker compose up -d postgres qdrant redis minio ollama

echo -e "\nStarting backend (uvicorn) in background..."
(cd backend && uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

echo "Starting frontend (next dev) in background..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT

echo -e "\nDev servers launching:"
echo "  Backend  : http://localhost:8000/api/v1/docs"
echo "  Frontend : http://localhost:3000"
wait
