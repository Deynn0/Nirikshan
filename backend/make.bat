@echo off
if "%1"=="test" (
    .venv\Scripts\pytest -v %2 %3
) else if "%1"=="lint" (
    .venv\Scripts\ruff check .
    if %errorlevel% equ 0 (
        .venv\Scripts\mypy nirikshan tests
    )
) else if "%1"=="dev" (
    .venv\Scripts\uvicorn nirikshan.main:app --reload --port 8000 --host 127.0.0.1
) else if "%1"=="eval" (
    .venv\Scripts\python scripts\evaluate.py --check-thresholds %2 %3
) else (
    echo Usage: make [test^|lint^|dev^|eval]
)
