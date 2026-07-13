# Career Agent — Setup Script
# Boots the full stack and pulls the default LLM model.

Write-Host "Starting Career Agent stack..." -ForegroundColor Cyan
docker compose up -d

Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "`nPulling default LLM (qwen3:8b) — one-time, ~5GB..." -ForegroundColor Cyan
docker exec career-agent-ollama ollama pull qwen3:8b

Write-Host "`nPulling embedding model (bge-m3)..." -ForegroundColor Cyan
docker exec career-agent-ollama ollama pull bge-m3

Write-Host "`nStack ready:" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000/api/v1/docs"
Write-Host "  Frontend : http://localhost:3000"
Write-Host "  Qdrant   : http://localhost:6333/dashboard"
Write-Host "  MinIO    : http://localhost:9001"
