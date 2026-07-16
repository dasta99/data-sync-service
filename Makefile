.PHONY: start stop run seed clean logs clickhouse clickhouse-stop clickhouse-logs

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

# ClickHouse commands
clickhouse:
	docker compose up -d clickhouse

clickhouse-stop:
	docker compose stop clickhouse

clickhouse-logs:
	docker compose logs -f clickhouse

clickhouse-shell:
	docker compose exec clickhouse clickhouse-client --host localhost
