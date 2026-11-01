param(
    [string]$Target = "help",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

switch ($Target) {
    "test" {
        Push-Location backend
        try { & .venv\Scripts\pytest -v @RemainingArgs } finally { Pop-Location }
    }
    "lint" {
        Push-Location backend
        try {
            & .venv\Scripts\ruff check .
            if ($LASTEXITCODE -eq 0) {
                & .venv\Scripts\mypy nirikshan
            }
        } finally { Pop-Location }
    }
    "dev" {
        Push-Location backend
        try { & .venv\Scripts\uvicorn nirikshan.main:app --reload --port 8000 --host 127.0.0.1 } finally { Pop-Location }
    }
    "eval" {
        Push-Location backend
        try { & .venv\Scripts\python scripts\evaluate.py --check-thresholds @RemainingArgs } finally { Pop-Location }
    }
    default {
        Write-Host "Available targets:"
        Write-Host "  .\make test  - Run test suite with pytest"
        Write-Host "  .\make lint  - Run ruff check and mypy type verification"
        Write-Host "  .\make dev   - Start local uvicorn development server"
        Write-Host "  .\make eval  - Run benchmark evaluation over synthetic fixtures"
    }
}
