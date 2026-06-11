<#
.SYNOPSIS
    Follow container logs.

.DESCRIPTION
    With no arguments, follows the api service. Pass one or more service names
    to follow those instead.

.EXAMPLE
    ./scripts/dev-logs.ps1
    ./scripts/dev-logs.ps1 api worker
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Services)

if (-not $Services) { $Services = @("api") }
docker compose logs -f @Services
