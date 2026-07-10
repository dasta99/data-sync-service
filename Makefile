.PHONY: help install test test-cov lint format run run-local docker-up docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────

install: ## Install dependencies
	pip install -r requirements.txt -r requirements-dev.txt

install-dev: ## Install in editable mode with dev deps
	pip install -e ".[dev]"

# ─── Test ─────────────────────────────────────────────────────

test: ## Run all unit tests
	PYTHONPATH=src python -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	PYTHONPATH=src python -m pytest tests/ -v --cov=sync --cov-report=term-missing --cov-report=html

test-unit: ## Run only unit tests
	PYTHONPATH=src python -m pytest tests/unit/ -v

# ─── Lint ─────────────────────────────────────────────────────

lint: ## Run linter (ruff)
	ruff check src/ tests/

format: ## Auto-format code
	ruff format src/ tests/

# ─── Run ──────────────────────────────────────────────────────

run: ## Run sync service (production)
	PYTHONPATH=src python main.py

run-local: ## Run sync service (local Docker MySQL)
	PYTHONPATH=src python main.py --local

# ─── Docker ───────────────────────────────────────────────────

docker-up: ## Start local MySQL container
	docker-compose up -d

docker-down: ## Stop local MySQL container
	docker-compose down

docker-logs: ## Follow MySQL logs
	docker-compose logs -f mysql-local

docker-reset: ## Delete data and restart
	docker-compose down -v && docker-compose up -d

# ─── Clean ────────────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
