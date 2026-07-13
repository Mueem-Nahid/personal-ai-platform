# Career Agent — Setup Script (PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Do NOT run this file in bash — use scripts\setup.sh for bash/Git Bash.

$ErrorActionPreference = "Stop"

Write-Host "Starting Career Agent stack..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up failed. Fix build errors then rerun this script." -ForegroundColor Red
    exit 1
}

Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "`nPulling default LLM (qwen3:8b) — one-time, ~5GB..." -ForegroundColor Cyan
docker exec career-agent-ollama ollama pull qwen3:8b
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not pull qwen3:8b — is the ollama container running?" -ForegroundColor Yellow
    Write-Host "  Run manually: docker exec career-agent-ollama ollama pull qwen3:8b" -ForegroundColor Yellow
}

Write-Host "`nPulling embedding model (bge-m3)..." -ForegroundColor Cyan
docker exec career-agent-ollama ollama pull bge-m3
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not pull bge-m3." -ForegroundColor Yellow
    Write-Host "  Run manually: docker exec career-agent-ollama ollama pull bge-m3" -ForegroundColor Yellow
}

Write-Host "`nStack ready:" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000/api/v1/docs"
Write-Host "  Frontend : http://localhost:3000"
Write-Host "  Qdrant   : http://localhost:6333/dashboard"
Write-Host "  MinIO    : http://localhost:9001"
