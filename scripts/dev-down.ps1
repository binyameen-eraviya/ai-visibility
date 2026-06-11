<#
.SYNOPSIS
    Stop the stack (containers removed, named volumes preserved).

.DESCRIPTION
    Data in the postgres_data / redis_data / scrape_storage volumes survives.
    Use scripts/reset-db.ps1 for a destructive wipe.
#>
$ErrorActionPreference = "Stop"
docker compose --profile worker down
