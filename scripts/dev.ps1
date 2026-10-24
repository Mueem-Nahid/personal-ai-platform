# Career Agent — Dev Script
# Runs backend + frontend with hot reload (assumes DB/Qdrant/Ollama already up).

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting infra services only (postgres, qdrant, redis, minio, ollama)..." -ForegroundColor Cyan
docker compose up -d --wait postgres qdrant redis minio ollama
if ($LASTEXITCODE -ne 0) {
    throw "Infrastructure startup failed. Fix the Docker error before launching dev servers."
}

Write-Host "`nRunning database migrations..." -ForegroundColor Yellow
Push-Location backend
try {
    alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Database migration failed. Fix the migration error before launching dev servers."
    }
} finally {
    Pop-Location
}

Write-Host "`nStarting backend (uvicorn) in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn main:app --reload --port 8000"

Write-Host "Starting ARQ worker in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; arq workers.arq_worker.WorkerSettings"

Write-Host "Starting frontend (next dev) in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nDev servers launching:" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000/api/v1/docs"
Write-Host "  Frontend : http://localhost:3000"
