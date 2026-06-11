<#
.SYNOPSIS
    Run the backend test suite (inside the api container) with coverage.

.DESCRIPTION
    Requires the api container to be running (scripts/dev-up.ps1). Any extra
    arguments are forwarded to pytest, e.g. a single file or -k filter.

.EXAMPLE
    ./scripts/test.ps1
    ./scripts/test.ps1 backend/tests/test_auth.py
    ./scripts/test.ps1 -k tenancy
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PytestArgs)

$ErrorActionPreference = "Stop"

$default = @("backend/tests/", "-v", "--cov=backend", "--cov-report=term-missing")
docker compose exec api pytest @default @PytestArgs
