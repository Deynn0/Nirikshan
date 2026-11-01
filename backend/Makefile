VENV_BIN := .venv/Scripts
ifeq ($(OS),Windows_NT)
    BIN := $(VENV_BIN)
else
    BIN := .venv/bin
endif

PYTHON  := $(if $(wildcard $(BIN)/python*),$(BIN)/python,python)
PYTEST  := $(if $(wildcard $(BIN)/pytest*),$(BIN)/pytest,pytest)
RUFF    := $(if $(wildcard $(BIN)/ruff*),$(BIN)/ruff,ruff)
MYPY    := $(if $(wildcard $(BIN)/mypy*),$(BIN)/mypy,mypy)
UVICORN := $(if $(wildcard $(BIN)/uvicorn*),$(BIN)/uvicorn,uvicorn)

.PHONY: test lint dev eval help

help:
	@echo "Available targets:"
	@echo "  make test  - Run test suite with pytest"
	@echo "  make lint  - Run ruff check and mypy type verification"
	@echo "  make dev   - Start local uvicorn development server"
	@echo "  make eval  - Run benchmark evaluation over synthetic fixtures"

test:
	$(PYTEST) -v

lint:
	$(RUFF) check .
	$(MYPY) nirikshan

dev:
	$(UVICORN) nirikshan.main:app --reload --port 8000 --host 127.0.0.1

eval:
	$(PYTHON) scripts/evaluate.py --check-thresholds
