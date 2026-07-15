.PHONY: start stop run seed clean logs

# Start databases
start:
	docker compose up -d

# Stop databases
stop:
	docker compose down

# Run pipeline (local)
run:
	python3 main.py --local

# Run pipeline (production)
run-prod:
	python3 main.py

# Seed test data
seed:
	./scripts/seed_source.sh 10

# Seed more data
seed-more:
	./scripts/seed_source.sh 20

# View logs
logs:
	docker compose logs -f

# Clean everything
clean:
	docker compose down -v
	rm -rf .pytest_cache __pycache__

# Run tests
test:
	python3 -m pytest tests/ -v

# Run tests with coverage
test-cov:
	python3 -m pytest tests/ -v --cov=src --cov-report=term-missing
