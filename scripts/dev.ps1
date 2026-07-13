# Career Agent — Dev Script
# Runs backend + frontend with hot reload (assumes DB/Qdrant/Ollama already up).

Write-Host "Starting infra services only (postgres, qdrant, redis, minio, ollama)..." -ForegroundColor Cyan
docker compose up -d postgres qdrant redis minio ollama

Write-Host "`nStarting backend (uvicorn) in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd backend; uvicorn main:app --reload --port 8000"

Write-Host "Starting frontend (next dev) in new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd frontend; npm run dev"

Write-Host "`nDev servers launching:" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000/api/v1/docs"
Write-Host "  Frontend : http://localhost:3000"
