# ETL Pipeline Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACT PHASE                             │
│                                                             │
│  5 Production Sources ──CDC──▶ Dest DB (mytdp + dakavara_pa) │
│                                                             │
│  mytdp_remote, tdp_events, prod_mytdp_app,                  │
│  tdp_feed, tdp_calendar                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRANSFORM PHASE                           │
│                                                             │
│  1. Denormalize ONCE into dimension tables                   │
│  2. Aggregate from dimensions into summary/fact tables       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEST DB (port 3307)                       │
│                                                             │
│  mytdp schema:        │  dakavara_pa schema:                │
│  - booth_voter (70M)  │  - cluster, unit                    │
│  - booth              │  - voter_info                       │
│  - assembly           │  - constituency                     │
│  - state              │  - cluster_booth, unit_booth        │
│                                                             │
│  + Summary Tables:                                         │
│    dim_booth_voter, fact_booth_sir, fact_booth_cubs, ...   │
└─────────────────────────────────────────────────────────────┘
```

---

## Extract Phase

### Production Sources

| Source | Database | Key Tables |
|--------|----------|------------|
| mytdp_remote | mytdp | booth_voter, booth, assembly, state |
| tdp_events | tdp_events | rallies, events |
| prod_mytdp_app | prod_mytdp_app | sir_verification_info |
| tdp_feed | tdp_feed | feed_data |
| tdp_calendar | tdp_calendar_db | calendar_events |

### How Extract Works

1. **CDC (Change Data Capture)** — reads from source, writes to dest
2. **Keyset Pagination** — cursor-based, handles large tables efficiently
3. **Watermark Tracking** — remembers last sync position per table

```sql
-- Example: Keyset pagination
SELECT * FROM booth_voter
WHERE (updated_at > '2026-07-15' OR (updated_at = '2026-07-15' AND id > 'BV00300'))
ORDER BY updated_at, id
LIMIT 500
```

### Dest Schemas

**mytdp schema** — core TDP data:
- `booth_voter` (70M rows) — voter records with SIR verification
- `booth` — booth details
- `assembly`, `state` — geographic hierarchy

**dakavara_pa schema** — supplementary data:
- `cluster`, `unit` — organizational hierarchy
- `cluster_booth`, `unit_booth` — mappings
- `voter_info` — voter details
- `constituency` — parliamentary constituencies

---

## Transform Phase

### Why Denormalize?

`booth_voter` has **70M rows**. Joining it multiple times is wasteful:

```
❌ BAD: Join booth_voter 3 times
  fact_booth_sir ← booth_voter JOIN booth JOIN state (70M join)
  fact_booth_cubs ← booth_voter JOIN booth JOIN state (70M join)
  Total: 140M rows processed

✅ GOOD: Denormalize once, aggregate from dim
  dim_booth_voter ← booth_voter JOIN booth JOIN state (70M join ONCE)
  fact_booth_sir ← dim_booth_voter (29 rows)
  fact_booth_cubs ← dim_booth_voter (29 rows)
  Total: 70M + 58 rows processed
```

### Transform Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. DENORMALIZE                                              │
│                                                             │
│  dim_booth_voter = booth_voter + booth + state + cluster    │
│                   + unit + constituency (single join)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. AGGREGATE                                               │
│                                                             │
│  fact_booth_sir ← dim_booth_voter (GROUP BY booth)          │
│  fact_booth_cubs ← dim_booth_voter (GROUP BY booth)         │
│  fact_voter_location ← voter_info (separate path)           │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

```
src/transform/
├── base.py           # TransformHandler + TransformHelper
├── registry.py       # Auto-discovers handlers
├── orchestrator.py   # Dependency dispatch
└── <domain>/         # One directory per domain
    ├── config.yaml   # Dependencies, outputs
    ├── handler.py    # Orchestrator (no SQL)
    └── transforms/   # Individual transform files
        ├── __init__.py
        └── <name>.py # Each does ONE thing
```

### Transform File Pattern

Each transform file has:
- `DEPENDS_ON: List[str]` — what data it needs
- `TABLE: str` — what table it writes to
- `class(TransformHelper)` — inherits fetch/write/make_upsert

```python
"""Example transform — builds fact_table from dim_table."""

import logging
from typing import List
from shared.interfaces import Database
from transform.base import TransformHelper

logger = logging.getLogger("transform.example")

TABLE = "fact_example"
DEPENDS_ON: List[str] = ["dim_booth_voter"]


class ExampleTransform(TransformHelper):

    def run(self, db: Database, from_date: str, to_date: str, report_date: str, publication_date_id: int) -> int:
        sql = """
            SELECT booth_id, state_id, state_name, COUNT(*)
            FROM dim_booth_voter
            WHERE DATE(updated_at) BETWEEN %s AND %s
            GROUP BY booth_id, state_id, state_name
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        if not rows:
            return 0

        upsert = self.make_upsert(TABLE, [
            "booth_id", "state_id", "state_name", "total_voters", "report_date",
        ], pk="booth_id,report_date")

        params_list = [(
            r["booth_id"], r["state_id"], r["state_name"], r["total_voters"], report_date,
        ) for r in rows]

        self.write(db, upsert, params_list)
        logger.info(f"  {TABLE}: {len(rows)} rows")
        return len(rows)
```

### Handler Pattern (Orchestrator)

Handler coordinates transforms — NO SQL, just imports and runs:

```python
"""Handler — orchestrates transforms for a domain."""

import time
from datetime import date
from typing import Any, Dict, List, Optional
from shared.interfaces import Database
from transform.base import TransformHandler, TransformResult
from transform.example.transforms.example_transform import ExampleTransform

class Handler(TransformHandler):

    @property
    def name(self) -> str:
        return "example"

    @property
    def depends_on(self) -> List[str]:
        return ["booth_voter", "booth", "state"]  # Extract tables needed

    @property
    def outputs(self) -> List[str]:
        return ["dim_booth_voter", "fact_example"]

    def transform(self, source_db, dest_db, params):
        today = date.today()
        from_date = (params or {}).get("from_date", str(today))
        to_date = (params or {}).get("to_date", str(today))
        report_date = (params or {}).get("report_date", str(today))
        publication_date_id = (params or {}).get("publication_date_id", 42)

        transforms = [
            ("dim_booth_voter", DenormalizeBoothVoter()),
            ("fact_example", ExampleTransform()),
        ]

        for table_name, transform in transforms:
            rows = transform.run(dest_db, from_date, to_date, report_date, publication_date_id)

        dest_db.commit()
```

### Dependency Graph

```
Production Sources
    │
    ▼ (CDC sync)
Dest DB
    │
    ├──▶ booth_voter ──┬──▶ DenormalizeBoothVoter ──▶ dim_booth_voter
    │                  │                                    │
    ├──▶ booth ────────┤                                    ├──▶ FactA
    │                  │                                    └──▶ FactB
    ├──▶ state ────────┘
    │
    └──▶ voter_info ──────────────────────────────────────▶ FactC
```

---

## Adding a New Domain

### Step 1: Create directory structure

```
src/transform/my_domain/
├── config.yaml
├── handler.py
└── transforms/
    ├── __init__.py
    └── my_transform.py
```

### Step 2: Create `config.yaml`

```yaml
name: my_domain
depends_on:
  - booth_voter
  - booth
  - state
outputs:
  - dim_booth_voter
  - fact_my_table
schedule_hint: 300
```

### Step 3: Create `handler.py`

```python
from transform.my_domain.transforms.my_transform import MyTransform

class Handler(TransformHandler):
    @property
    def name(self) -> str:
        return "my_domain"

    @property
    def depends_on(self) -> List[str]:
        return ["booth_voter", "booth", "state"]

    @property
    def outputs(self) -> List[str]:
        return ["fact_my_table"]

    def transform(self, source_db, dest_db, params):
        # Import and run transforms
        transforms = [("fact_my_table", MyTransform())]
        for name, transform in transforms:
            transform.run(dest_db, from_date, to_date, report_date, publication_date_id)
```

### Step 4: Create transform file

```python
"""My Transform — builds fact_my_table."""

TABLE = "fact_my_table"
DEPENDS_ON: List[str] = ["booth_voter", "booth"]

class MyTransform(TransformHelper):
    def run(self, db, from_date, to_date, report_date, publication_date_id):
        sql = "SELECT ... FROM booth_voter bv JOIN booth bo ..."
        rows = self.fetch(db, sql, (from_date, to_date))
        self.write(db, upsert, params_list)
        return len(rows)
```

### Step 5: Create dest table in migrations

```sql
CREATE TABLE IF NOT EXISTS fact_my_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booth_id VARCHAR(26) NOT NULL,
    some_value BIGINT DEFAULT 0,
    report_date DATE DEFAULT NULL,
    UNIQUE KEY uk_fact_my (booth_id, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Step 6: Run

```bash
python3 main.py --local
```

---

## TransformHelper Reference

| Method | What it does |
|--------|--------------|
| `fetch(db, sql, params)` | Run SELECT, return list of dicts |
| `write(db, sql, params_list)` | Bulk INSERT/UPDATE |
| `make_upsert(table, columns, pk)` | Generate INSERT ... ON DUPLICATE KEY UPDATE |

---

## Common Patterns

### Reading from Dimension Tables

```python
# Instead of joining booth_voter directly
sql = """
    SELECT booth_id, state_id, state_name, COUNT(*)
    FROM dim_booth_voter  -- Pre-joined, fast
    GROUP BY booth_id, state_id, state_name
"""
```

### Writing with Upsert

```python
upsert = self.make_upsert(
    "fact_table",
    columns=["booth_id", "state_id", "value", "report_date"],
    pk="booth_id,report_date"  # Composite primary key
)
self.write(db, upsert, params_list)
```

### Handling Date Ranges

```python
def run(self, db, from_date, to_date, report_date, publication_date_id):
    sql = "SELECT ... WHERE DATE(updated_at) BETWEEN %s AND %s"
    rows = self.fetch(db, sql, (from_date, to_date))
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Table doesn't exist | Check migrations/prod/ for DDL |
| Unknown column | Check columns_json in sync_config |
| Transform not running | Check depends_on in config.yaml |
| Slow queries | Ensure dim tables are populated first |
