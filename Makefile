.PHONY: help install lint format test benchmark clean run

help:
	@echo "Athena Development Commands:"
	@echo "  make install    - Install package and development dependencies"
	@echo "  make lint       - Run ruff linter checks across all code"
	@echo "  make format     - Run ruff formatter across all code"
	@echo "  make test       - Run full pytest test suite"
	@echo "  make benchmark  - Run benchmark smoke test suite"
	@echo "  make clean      - Purge temporary artifacts and caches"
	@echo "  make run        - Start Athena API server on port 8000"

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/ benchmark/ scripts/
	ruff format --check src/ tests/ benchmark/ scripts/

format:
	ruff format src/ tests/ benchmark/ scripts/
	ruff check --fix src/ tests/ benchmark/ scripts/

test:
	pytest tests/ -v

benchmark:
	python -m scripts.run_benchmarks --questions smoke --system A1

clean:
	python -m scripts.clean_artifacts

run:
	python -m uvicorn athena.api.main:app --host 0.0.0.0 --port 8000 --reload
