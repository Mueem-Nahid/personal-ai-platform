#!/usr/bin/env bash
# Career Agent — Dev Script (Linux/macOS)
set -euo pipefail

echo "Starting infra services only (postgres, qdrant, redis, minio, ollama)..."
docker compose up -d --wait postgres qdrant redis minio ollama

echo -e "\nChecking embedding model (bge-m3)..."
if ! docker exec career-agent-ollama ollama show bge-m3 >/dev/null 2>&1; then
  if ! docker exec career-agent-ollama ollama pull bge-m3; then
    echo "ERROR: Embedding model installation failed. Document processing requires bge-m3." >&2
    exit 1
  fi
fi

echo -e "\nRunning database migrations..."
(cd backend && alembic upgrade head)

echo -e "\nStarting backend (uvicorn) in background..."
(cd backend && uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

echo "Starting ARQ worker in background..."
(cd backend && arq workers.arq_worker.WorkerSettings) &
WORKER_PID=$!

echo "Starting frontend (next dev) in background..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $WORKER_PID $FRONTEND_PID 2>/dev/null || true" EXIT

echo -e "\nDev servers launching:"
echo "  Backend  : http://localhost:8000/api/v1/docs"
echo "  Frontend : http://localhost:3000"
wait
