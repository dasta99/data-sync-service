# SIR Domain Implementation

This doc explains the SIR (Systematic Voters' Education and Electoral Participation) domain as a concrete implementation of the ETL architecture.

## Overview

The SIR domain tracks voter verification status across booths. It:
1. Denormalizes `booth_voter` with all dimensions into `dim_booth_voter`
2. Aggregates into `fact_booth_sir` (all voters) and `fact_booth_cubs` (verified voters only)
3. Tracks voter location counts from `voter_info`

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCE TABLES (in dest DB after extract)                    │
│                                                             │
│  mytdp: booth_voter (70M), booth, assembly, state           │
│  dakavara_pa: cluster, unit, constituency, voter_info       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. DENORMALIZE (denormalize.py)                             │
│                                                             │
│  dim_booth_voter = booth_voter                               │
│                 + booth (name, state_id, cluster_id, unit_id)│
│                 + state (state_name)                         │
│                 + cluster (cluster_name)                     │
│                 + unit (unit_name)                           │
│                 + constituency (constituency_name)           │
│                                                             │
│  Single join: 70M rows → ~30 rows (today's updates)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. AGGREGATE                                               │
│                                                             │
│  booth_sir.py: dim_booth_voter → fact_booth_sir              │
│  booth_cubs.py: dim_booth_voter → fact_booth_cubs            │
│  voter_location.py: voter_info → fact_voter_location         │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/transform/sir/
├── config.yaml           # Dependencies and outputs
├── handler.py            # Orchestrator (no SQL)
└── transforms/
    ├── __init__.py
    ├── denormalize.py    # dim_booth_voter
    ├── booth_sir.py      # fact_booth_sir
    ├── booth_cubs.py     # fact_booth_cubs
    └── voter_location.py # fact_voter_location
```

## Config

```yaml
name: sir
depends_on:
  - booth_voter
  - booth
  - assembly
  - parliament
  - state
  - mytdp_cluster
  - mytdp_unit
  - dp_booth
  - dp_constituency
  - dp_voter_info
outputs:
  - dim_booth_voter
  - fact_booth_sir
  - fact_booth_cubs
  - fact_voter_location
schedule_hint: 300
```

## Handler (Orchestrator)

```python
"""SIR handler — orchestrates transforms for SIR/CUBS domain."""

import time
from datetime import date
from typing import Any, Dict, List, Optional
from shared.interfaces import Database
from transform.base import TransformHandler, TransformResult
from transform.sir.transforms.denormalize import DenormalizeBoothVoter
from transform.sir.transforms.booth_sir import BoothSIR
from transform.sir.transforms.booth_cubs import BoothCUBS
from transform.sir.transforms.voter_location import VoterLocation

class Handler(TransformHandler):

    @property
    def name(self) -> str:
        return "sir"

    @property
    def depends_on(self) -> List[str]:
        return [
            "booth_voter", "booth", "assembly", "parliament", "state",
            "mytdp_cluster", "mytdp_unit",
            "dp_booth", "dp_constituency", "dp_voter_info",
        ]

    @property
    def outputs(self) -> List[str]:
        return ["dim_booth_voter", "fact_booth_sir", "fact_booth_cubs", "fact_voter_location"]

    def transform(self, source_db, dest_db, params):
        today = date.today()
        from_date = (params or {}).get("from_date", str(today))
        to_date = (params or {}).get("to_date", str(today))
        report_date = (params or {}).get("report_date", str(today))
        publication_date_id = (params or {}).get("publication_date_id", 42)

        transforms = [
            ("dim_booth_voter", DenormalizeBoothVoter()),
            ("fact_booth_sir", BoothSIR()),
            ("fact_booth_cubs", BoothCUBS()),
            ("fact_voter_location", VoterLocation()),
        ]

        for table_name, transform in transforms:
            rows = transform.run(dest_db, from_date, to_date, report_date, publication_date_id)

        dest_db.commit()
```

## Transforms

### 1. Denormalize (denormalize.py)

**Purpose**: Join `booth_voter` with all dimensions once.

```python
TABLE = "dim_booth_voter"
DEPENDS_ON = ["booth_voter", "booth", "assembly", "parliament", "state",
              "mytdp_cluster", "mytdp_unit", "dp_booth", "dp_constituency"]

class DenormalizeBoothVoter(TransformHelper):
    def run(self, db, from_date, to_date, report_date, publication_date_id):
        sql = """
            SELECT
                bv.id,
                bv.booth_id,
                bv.voter_id,
                bv.sir_verified,
                bv.sir_status,
                bv.sir_verified_by,
                bv.sir_mobile_number,
                bv.sir_caste_id,
                bv.sir_political_party_id,
                bv.file_path,
                bv.form_submitted_to_blo,
                bv.blo_digitized,
                bv.created_at,
                bv.updated_at,
                -- Dimensions
                bo.state_id,
                s.state_name,
                bo.cluster_id,
                cl.cluster_name,
                bo.unit_id,
                u.unit_name,
                bo.name AS booth_name,
                dpb.constituency_id,
                dpc.name AS constituency_name
            FROM booth_voter bv
            JOIN booth bo ON bv.booth_id = bo.id
            JOIN state s ON bo.state_id = s.id
            LEFT JOIN cluster cl ON bo.cluster_id = cl.id
            LEFT JOIN unit u ON bo.unit_id = u.id
            LEFT JOIN dakavara_pa.booth dpb ON bv.booth_id = dpb.booth_id
            LEFT JOIN dakavara_pa.constituency dpc ON dpb.constituency_id = dpc.constituency_id
            WHERE DATE(bv.updated_at) BETWEEN %s AND %s
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        self.write(db, upsert, params_list)
        return len(rows)
```

### 2. BoothSIR (booth_sir.py)

**Purpose**: Aggregate `dim_booth_voter` → `fact_booth_sir` (all voters).

```python
TABLE = "fact_booth_sir"
DEPENDS_ON = ["dim_booth_voter"]

class BoothSIR(TransformHelper):
    def run(self, db, from_date, to_date, report_date, publication_date_id):
        sql = """
            SELECT
                booth_id,
                booth_name,
                state_id,
                state_name,
                parliament_id,
                assembly_id,
                cluster_id,
                cluster_name,
                unit_id,
                unit_name,
                constituency_id,
                constituency_name,
                COUNT(DISTINCT voter_id) AS total_voters,
                SUM(CASE WHEN sir_verified = 1 THEN 1 ELSE 0 END) AS verified_voters,
                COUNT(DISTINCT CASE WHEN sir_verified = 1 THEN sir_verified_by END) AS active_users,
                SUM(CASE WHEN sir_status = 'available' THEN 1 ELSE 0 END) AS available_count,
                SUM(CASE WHEN sir_status = 'temporary shift' THEN 1 ELSE 0 END) AS temporary_shift_count,
                SUM(CASE WHEN sir_status = 'permanent shift' THEN 1 ELSE 0 END) AS permanent_shift_count,
                SUM(CASE WHEN sir_status = 'death' THEN 1 ELSE 0 END) AS death_count,
                SUM(CASE WHEN sir_status = 'duplicate' THEN 1 ELSE 0 END) AS duplicate_count,
                SUM(CASE WHEN sir_status = 'double vote' THEN 1 ELSE 0 END) AS double_count,
                SUM(CASE WHEN form_submitted_to_blo = 1 THEN 1 ELSE 0 END) AS forms_submitted_to_blo,
                SUM(CASE WHEN blo_digitized = 1 THEN 1 ELSE 0 END) AS blo_digitized
            FROM dim_booth_voter
            WHERE DATE(updated_at) BETWEEN %s AND %s
            GROUP BY booth_id, booth_name, state_id, state_name, parliament_id,
                     assembly_id, cluster_id, cluster_name, unit_id, unit_name,
                     constituency_id, constituency_name
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        self.write(db, upsert, params_list)
        return len(rows)
```

### 3. BoothCUBS (booth_cubs.py)

**Purpose**: Aggregate `dim_booth_voter` → `fact_booth_cubs` (verified voters only).

```python
TABLE = "fact_booth_cubs"
DEPENDS_ON = ["dim_booth_voter"]

class BoothCUBS(TransformHelper):
    def run(self, db, from_date, to_date, report_date, publication_date_id):
        sql = """
            SELECT
                booth_id,
                booth_name,
                state_id,
                state_name,
                parliament_id,
                constituency_id,
                constituency_name,
                cluster_id,
                cluster_name,
                unit_id,
                unit_name,
                COUNT(DISTINCT sir_mobile_number) AS mobile_count,
                COUNT(sir_caste_id) AS caste_count,
                COUNT(sir_political_party_id) AS party_count,
                COUNT(file_path) AS forms_count,
                ...
            FROM dim_booth_voter
            WHERE sir_verified = 1 AND DATE(updated_at) BETWEEN %s AND %s
            GROUP BY booth_id, ...
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        self.write(db, upsert, params_list)
        return len(rows)
```

### 4. VoterLocation (voter_location.py)

**Purpose**: Aggregate `voter_info` → `fact_voter_location` (separate path, no dim needed).

```python
TABLE = "fact_voter_location"
DEPENDS_ON = ["dp_voter_info"]

class VoterLocation(TransformHelper):
    def run(self, db, from_date, to_date, report_date, publication_date_id):
        sql = """
            SELECT
                vi.state_id,
                vi.parliament_id,
                vi.assembly_id,
                vi.constituency_id,
                vi.total_voters,
                vi.publication_date_id,
                ...
            FROM dakavara_pa.voter_info vi
            WHERE DATE(vi.created_date) BETWEEN %s AND %s
        """
        rows = self.fetch(db, sql, (from_date, to_date))
        self.write(db, upsert, params_list)
        return len(rows)
```

## Tables

### Dimension Table

**dim_booth_voter** — Denormalized booth_voter with all dimensions

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(26) | Primary key (from booth_voter) |
| booth_id | VARCHAR(26) | Booth identifier |
| voter_id | VARCHAR(26) | Voter identifier |
| sir_verified | TINYINT | 1 if verified |
| sir_status | VARCHAR(50) | available, temporary shift, etc. |
| state_id | INT | From booth → state |
| state_name | VARCHAR(200) | From state |
| cluster_id | INT | From booth → cluster |
| cluster_name | VARCHAR(200) | From cluster |
| unit_id | INT | From booth → unit |
| unit_name | VARCHAR(200) | From unit |
| constituency_id | INT | From dakavara_pa.booth → constituency |
| constituency_name | VARCHAR(200) | From constituency |

### Fact Tables

**fact_booth_sir** — Booth-level SIR stats (all voters)

| Column | Type | Description |
|--------|------|-------------|
| booth_id | VARCHAR(26) | Booth identifier |
| booth_name | VARCHAR(200) | Booth name |
| state_id | INT | State ID |
| state_name | VARCHAR(200) | State name |
| total_voters | BIGINT | Total voters in booth |
| verified_voters | BIGINT | Voters with sir_verified=1 |
| active_users | BIGINT | Distinct verifiers |
| available_count | BIGINT | Status: available |
| temporary_shift_count | BIGINT | Status: temporary shift |
| permanent_shift_count | BIGINT | Status: permanent shift |
| death_count | BIGINT | Status: death |
| duplicate_count | BIGINT | Status: duplicate |
| double_count | BIGINT | Status: double vote |
| forms_submitted_to_blo | BIGINT | Forms submitted |
| blo_digitized | BIGINT | BLO digitized |
| report_date | DATE | Report date |

**fact_booth_cubs** — Booth-level CUBS stats (verified voters only)

| Column | Type | Description |
|--------|------|-------------|
| booth_id | VARCHAR(26) | Booth identifier |
| booth_name | VARCHAR(200) | Booth name |
| mobile_count | BIGINT | Distinct mobile numbers |
| caste_count | BIGINT | Caste IDs recorded |
| party_count | BIGINT | Political party IDs |
| forms_count | BIGINT | File paths (forms) |
| available_count | BIGINT | Status: available |
| ... | ... | Same status columns as fact_booth_sir |

**fact_voter_location** — Location-level voter counts

| Column | Type | Description |
|--------|------|-------------|
| location_id | INT | Location identifier |
| location_type | ENUM | state, parliament, assembly, etc. |
| state_id | INT | State ID |
| parliament_id | INT | Parliament ID |
| assembly_id | INT | Assembly ID |
| constituency_id | INT | Constituency ID |
| total_voters | BIGINT | Total voters at location |
| publication_date_id | INT | Publication date ID |

## Dependencies

```
booth_voter ──────┐
booth ────────────┤
assembly ─────────┤
parliament ───────┼──▶ DenormalizeBoothVoter ──▶ dim_booth_voter
state ────────────┤                                    │
mytdp_cluster ────┤                                    ├──▶ BoothSIR ──▶ fact_booth_sir
mytdp_unit ───────┤                                    │
dp_booth ─────────┤                                    └──▶ BoothCUBS ──▶ fact_booth_cubs
dp_constituency ──┘
dp_voter_info ────────────────────────────────────────▶ VoterLocation ──▶ fact_voter_location
```

## Running

```bash
# Local development
python3 main.py --local

# Production
python3 main.py
```

## Key Design Decisions

1. **Denormalize once** — `booth_voter` (70M) joined with dimensions ONCE, not per summary table
2. **Read from dest** — transforms read from dest DB (after extract), not source
3. **Separate transforms** — each transform is independent file with own DEPENDS_ON
4. **Handler orchestrates** — handler.py contains NO SQL, just coordinates transforms
5. **Date defaults** — from_date, to_date, report_date all default to date.today()
