<#
.SYNOPSIS
    Build and start the core dev stack, then seed reference data.

.DESCRIPTION
    Starts db, redis, api, and frontend (the fast dev loop). The Celery
    worker and beat services live behind the "worker" compose profile and
    are NOT started by default -- pass -Worker to include them.

.EXAMPLE
    ./scripts/dev-up.ps1
    ./scripts/dev-up.ps1 -Worker
#>
param([switch]$Worker)

$ErrorActionPreference = "Stop"

$profileArgs = @()
if ($Worker) { $profileArgs = @("--profile", "worker") }

docker compose @profileArgs up -d --build

Write-Host ""
Write-Host "Seeding reference data (super admin, platforms, countries)..."
# `run --rm` waits for the db healthcheck and runs migrations via the api
# entrypoint before seeding. Safe to re-run; seeding is idempotent.
docker compose run --rm api python -m backend.database.seed

Write-Host ""
Write-Host "Stack is up:" -ForegroundColor Green
Write-Host "  API docs:  http://localhost:8001/docs"
Write-Host "  Frontend:  http://localhost:3001"
if (-not $Worker) {
    Write-Host ""
    Write-Host "  (Celery worker/beat not started. Re-run with -Worker to include them.)" -ForegroundColor DarkGray
}
