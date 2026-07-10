# Data Sync Service

Incremental MySQL-to-MySQL sync with adaptive polling, keyset pagination, and transactional batch writes. Replaces the legacy Java cron job that polls every 10 minutes.

---

## Architecture

```
┌──────────────────┐     ┌──────────────────────────────┐     ┌──────────────────┐
│  Source MySQL DBs │────▶│        Sync Service          │────▶│  Aurora MySQL    │
│  (5 sources)      │     │                              │     │  (mytdp)         │
└──────────────────┘     │  ┌─────────┐  ┌───────────┐  │     └──────────────────┘
                          │  │ Worker  │──│ Batch     │  │
                          │  │ (per    │  │ Writer    │  │     ┌──────────────────┐
                          │  │ table)  │  │ (upsert)  │  │────▶│  sync_config     │
                          │  └─────────┘  └───────────┘  │     │  sync_status     │
                          │                              │     │  sync_history    │
                          │  ┌─────────────────────────┐ │     └──────────────────┘
                          │  │  Health API (:8090)     │ │
                          │  │  /health /config        │ │
                          │  └─────────────────────────┘ │
                          └──────────────────────────────┘
                                    ▲
                                    │ PM2 (autorestart)
                                    ▼
                          ┌──────────────────┐
                          │   EC2 Instance    │
                          └──────────────────┘
```

### Data Flow

```
1. Config loaded from sync_config table (DB-driven, no restart needed)
2. Watermark fetched (last_synced_at + last_record_id)
3. Source queried: SELECT ... WHERE updated_at > watermark ORDER BY updated_at, id LIMIT batch_size
4. Rows upserted into destination (INSERT ... ON DUPLICATE KEY UPDATE)
5. Watermark advanced
6. Sleep (adaptive interval based on data activity)
```

---

## Project Structure

```
sync_service/
├── main.py                          # Entry point — signals, CLI, launch
├── config.yaml                      # DB connection configs (env var resolution)
├── ecosystem.config.js              # PM2 process config
├── deploy.sh                        # One-command deployment script
├── docker-compose.yml               # Local MySQL 8.0 for testing
├── Dockerfile                       # Container build
├── Makefile                         # Build/test/run shortcuts
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Package config, pytest, ruff
│
├── migrations/
│   ├── 001_create_tables.sql        # sync_config, sync_status, sync_history DDL
│   └── 002_test_schema.sql          # booth_voter table for local testing
│
├── src/sync/
│   ├── abstractions/
│   │   └── interfaces.py            # Protocol classes (Database, Cursor, QueryBuilder, etc.)
│   │
│   ├── database/
│   │   ├── config.py                # YAML config loader with ${ENV_VAR} resolution
│   │   ├── connections.py           # PooledDatabaseFactory, PyMySQL wrappers
│   │   ├── repositories.py          # SchemaManager, TableConfigRepository, WatermarkRepository
│   │   └── mode.py                  # Shared local/prod mode flag
│   │
│   ├── engine/
│   │   ├── query_builder.py         # KeysetQueryBuilder (SELECT + UPSERT SQL)
│   │   ├── batch_writer.py          # TransactionalBatchWriter (COMMIT/ROLLBACK)
│   │   ├── retry.py                 # SimpleRetryPolicy with backoff
│   │   ├── worker.py                # BaseSyncWorker — orchestrates one table's sync
│   │   └── loop.py                  # sync_table + run_sync_loop (adaptive polling)
│   │
│   ├── monitoring/
│   │   ├── status.py                # StatusWriter (sync_status table)
│   │   ├── history.py               # HistoryLogger (sync_history table)
│   │   └── logger.py                # SyncJsonLogger (structured stdout)
│   │
│   └── api/
│       ├── __init__.py              # FastAPI app, mounts routers
│       ├── health.py                # /health, /health/ready, /health/sync
│       └── config.py                # CRUD: GET/POST/PUT/DELETE /config
│
└── tests/
    └── unit/
        ├── test_query_builder.py    # 9 tests
        ├── test_batch_writer.py     # 4 tests
        ├── test_retry.py            # 6 tests
        ├── test_worker.py           # 9 tests
        ├── test_status_history.py   # 10 tests
        ├── test_adaptive_polling.py # 11 tests
        └── test_config_api.py       # 12 tests
```

---

## How It Works

### Keyset Pagination

Instead of OFFSET-based pagination (slow for large tables), uses timestamp + ID watermark:

```sql
SELECT * FROM source_table
WHERE (updated_at > '2026-07-10 00:00:00'
   OR (updated_at = '2026-07-10 00:00:00' AND id > '0'))
ORDER BY updated_at, id
LIMIT 500
```

This prevents infinite loops when 1M+ rows share the same `updated_at`.

### Adaptive Polling

When no new data is found, the poll interval increases exponentially:

```
Cycle 1: data found    → 30s (base)
Cycle 2: no data       → 30s (under threshold)
Cycle 3: no data       → 30s (threshold hit)
Cycle 4: no data       → 60s (30 × 2^1)
Cycle 5: no data       → 120s (30 × 2^2)
Cycle 6: data found    → 30s (reset)
```

Configurable per table: `no_data_threshold`, `backoff_multiplier`, `max_poll_interval`.

### Transactional Batch Writes

Each batch runs in a transaction:
- `BEGIN` → `executemany(upsert)` → `COMMIT`
- On error: `ROLLBACK` → retry with backoff

No table-level locks. Source reads are never blocked.

### UPSERT (No Duplicates)

```sql
INSERT INTO dest_table (id, booth_id, voter_id, ...)
VALUES (%s, %s, %s, ...)
ON DUPLICATE KEY UPDATE
    booth_id = VALUES(booth_id),
    voter_id = VALUES(voter_id),
    ...
```

---

## Database Schema

### sync_config

Stores which tables to sync and how. DB-driven — changes take effect on next poll cycle, no restart needed.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `table_name` | VARCHAR(100) | PK | Unique table identifier |
| `source_name` | VARCHAR(100) | — | Reference to `config.yaml` source |
| `source_table` | VARCHAR(100) | — | Table name on source |
| `dest_table` | VARCHAR(100) | — | Table name on destination |
| `enabled` | TINYINT(1) | 1 | Enable/disable sync |
| `poll_interval` | INT | 30 | Seconds between polls |
| `batch_size` | INT | 500 | Rows per batch |
| `watermark_column` | VARCHAR(100) | updated_at | Column for incremental sync |
| `primary_key` | VARCHAR(100) | id | Primary key column |
| `columns_json` | TEXT | — | JSON array of columns to sync |
| `filters_json` | TEXT | — | JSON array of WHERE conditions |
| `timezone_offset` | INT | 0 | Hours offset from UTC |
| `no_data_threshold` | INT | 2 | Empty polls before backoff |
| `backoff_multiplier` | INT | 2 | Multiplier per empty poll |
| `max_poll_interval` | INT | 600 | Max poll interval (seconds) |
| `last_synced_at` | DATETIME | — | Last synced timestamp |
| `last_record_id` | VARCHAR(100) | — | Last synced record ID |

### sync_status

Live runtime status per table.

| Column | Type | Description |
|--------|------|-------------|
| `table_name` | VARCHAR(100) | Unique table identifier |
| `status` | ENUM | running / idle / error / disabled |
| `last_sync_at` | DATETIME | When last sync completed |
| `last_sync_duration_ms` | INT | Last sync duration |
| `last_sync_rows` | INT | Rows synced in last run |
| `last_error` | TEXT | Last error message |
| `consecutive_errors` | INT | Error streak count |
| `total_rows_synced` | BIGINT | Cumulative rows synced |

### sync_history

Audit log — last 10 runs per table.

| Column | Type | Description |
|--------|------|-------------|
| `table_name` | VARCHAR(100) | Table name |
| `status` | ENUM | success / error |
| `rows_synced` | INT | Rows synced |
| `duration_ms` | INT | Duration in milliseconds |
| `error_message` | TEXT | Error details (if failed) |
| `started_at` | DATETIME | When sync started |
| `completed_at` | DATETIME | When sync completed |

---

## API Endpoints

Health server runs on port `8090` (configurable via `HEALTH_PORT`).

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/ready` | Readiness (DB connectivity) |
| `GET` | `/health/sync` | All tables status + overall health |
| `GET` | `/health/history/{table_name}` | Last N sync runs for a table |

### Config CRUD

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/config` | List enabled tables |
| `GET` | `/config?enabled_only=false` | List all (including disabled) |
| `GET` | `/config/{table_name}` | Get one table config |
| `POST` | `/config` | Create new table config |
| `PUT` | `/config/{table_name}` | Partial update |
| `DELETE` | `/config/{table_name}` | Delete table config |

**Example — Create a new sync:**

```bash
curl -X POST http://localhost:8090/config \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "events",
    "source_name": "tdp_events",
    "source_table": "events",
    "dest_table": "events",
    "columns": ["id", "title", "created_at"],
    "poll_interval": 60
  }'
```

**Example — Disable a table:**

```bash
curl -X PUT http://localhost:8090/config/booth_voter \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## Quick Start (Local)

### Prerequisites
- Python 3.9+
- Docker (for local MySQL)

### 1. Start local MySQL

```bash
docker-compose up -d
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the service

```bash
python main.py --local
```

### 4. Verify

```bash
# Health check
curl http://localhost:8090/health

# Sync status
curl http://localhost:8090/health/sync

# Config
curl http://localhost:8090/config
```

---

## Deployment (EC2 + PM2)

### Prerequisites
- EC2 instance with Python 3.11 and PM2 installed

### 1. Copy files to EC2

```bash
scp -r sync_service/ ec2-user@<EC2_IP>:/opt/data-sync-service/
```

### 2. Configure environment

```bash
ssh ec2-user@<EC2_IP>
cd /opt/data-sync-service
cp .env.example .env
nano .env  # fill in credentials
```

### 3. Deploy

```bash
bash deploy.sh
```

### 4. Verify

```bash
pm2 status
pm2 logs data-sync-service
curl http://localhost:8090/health
```

### PM2 Commands

```bash
pm2 logs data-sync-service    # watch logs
pm2 restart data-sync-service # restart
pm2 stop data-sync-service    # stop
pm2 monit                     # monitoring dashboard
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Destination (Aurora)
DEST_HOST=db-projectk-prod.cluster-xxx.us-east-1.rds.amazonaws.com
DEST_PORT=3306
DEST_USER=read_only_ashok
DEST_PASS=<password>
DEST_DB=mytdp

# Sources
MYTDP_HOST=<host>
MYTDP_PORT=3306
MYTDP_USER=<user>
MYTDP_PASS=<password>
# ... (TDP_EVENTS_HOST, PROD_MYTDP_HOST, TDP_FEED_HOST, TDP_CALENDAR_HOST)

# Service
HEALTH_PORT=8090
```

### Per-Table Settings (via API or direct DB)

```sql
UPDATE sync_config SET
    poll_interval = 60,
    batch_size = 1000,
    no_data_threshold = 5,
    backoff_multiplier = 3,
    max_poll_interval = 900
WHERE table_name = 'booth_voter';
```

---

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
PYTHONPATH=src pytest tests/unit/test_worker.py -v
```

**Test coverage:** 60 tests across 7 test files covering query building, batch writing, retry logic, worker orchestration, status/history tracking, adaptive polling, and API routes.

---

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all commands |
| `make install` | Install dependencies |
| `make test` | Run all tests |
| `make test-cov` | Tests with coverage |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code |
| `make run` | Run service (production) |
| `make run-local` | Run service (local Docker) |
| `make docker-up` | Start local MySQL |
| `make docker-down` | Stop local MySQL |
| `make docker-reset` | Delete data and restart |
| `make clean` | Remove build artifacts |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Keyset pagination over OFFSET | Handles 1M+ rows with same `updated_at` without infinite loops |
| DB-driven config (no restart) | Toggle tables via API, no service restart needed |
| Adaptive polling | Reduces unnecessary source DB queries when idle |
| Transactional batches | No table-level locks on destination |
| Protocol-based abstractions | Testable with mocks, swappable implementations |
| PM2 over systemd | Auto-restart, log rotation, matches existing stack |
| UPSERT over INSERT | Idempotent — safe to re-run, no duplicates |
