<#
.SYNOPSIS
    DESTRUCTIVE: wipe the database volume and recreate an empty, seeded DB.

.DESCRIPTION
    Tears the stack down WITH volumes (-v), so all Postgres data is lost, then
    brings the db back up, applies migrations + seeds via the api entrypoint.
    Use this only in development when you want a clean slate.

    Requires typing "reset" to confirm (skip with -Force).

.EXAMPLE
    ./scripts/reset-db.ps1
    ./scripts/reset-db.ps1 -Force
#>
param([switch]$Force)

$ErrorActionPreference = "Stop"

if (-not $Force) {
    Write-Host "This DELETES all data in the postgres/redis/scrape volumes." -ForegroundColor Yellow
    $answer = Read-Host "Type 'reset' to confirm"
    if ($answer -ne "reset") {
        Write-Host "Aborted."
        return
    }
}

docker compose --profile worker down -v
docker compose up -d db
Write-Host "Applying migrations and seeding reference data..."
docker compose run --rm api python -m backend.database.seed
Write-Host ""
Write-Host "Database reset and seeded. Bring the full stack up with scripts/dev-up.ps1." -ForegroundColor Green
