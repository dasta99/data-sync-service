# Data Sync Service

> **ETL pipeline that syncs data from production databases and creates summary reports.**

## What This System Does

```mermaid
flowchart LR
    A[5 Production<br/>Databases] -->|Copy| B[Staging<br/>Area]
    B -->|Process| C[Summary<br/>Reports]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#e8f5e9
```

**Simple explanation:**
1. **Copy** data from 5 production databases
2. **Combine** related data into one place
3. **Summarize** into easy-to-read reports

---

## Quick Start

```bash
# Start databases
docker compose up -d

# Run pipeline
python3 main.py --local
```

---

## Documentation

### For Everyone

| Document | Description |
|----------|-------------|
| [**Architecture**](docs/ARCHITECTURE.md) | How the system works (with diagrams) |
| [**SIR Domain**](docs/SIR_DOMAIN.md) | Voter verification tracking example |

### For Developers

| Document | Description |
|----------|-------------|
| [**Adding Transforms**](docs/ADDING_TRANSFORMS.md) | How to add new features |
| [**Technical Details**](docs/TECHNICAL.md) | Deep dive for developers |

---

## How It Works

```mermaid
flowchart TB
    subgraph Sources["Production Databases"]
        S1[mytdp_remote]
        S2[tdp_events]
        S3[prod_mytdp_app]
        S4[tdp_feed]
        S5[tdp_calendar]
    end
    
    subgraph Staging["Staging Area"]
        D1[mytdp schema]
        D2[dakavara_pa schema]
    end
    
    subgraph Reports["Summary Tables"]
        R1[Booth verification stats]
        R2[Location voter counts]
    end
    
    Sources --> Staging
    Staging --> Reports
    
    style Sources fill:#e3f2fd
    style Staging fill:#fff3e0
    style Reports fill:#e8f5e9
```

---

## Key Features

### 1. Efficient Data Sync
- Only copies what changed (not entire database)
- Handles millions of records efficiently

### 2. Smart Denormalization
- Combines related data ONCE (not multiple times)
- Makes queries fast and efficient

### 3. Real-time Reports
- Booth verification stats
- Active user stats
- Location voter counts

---

## Project Structure

```
src/
├── extract/      # Copy data from production
├── transform/    # Process and summarize
├── load/         # Save to database
└── shared/       # Common utilities
```

---

## Commands

```bash
# Local development
python3 main.py --local

# Production
python3 main.py
```

---

## Learn More

- [**Architecture**](docs/ARCHITECTURE.md) — Detailed system design
- [**SIR Domain**](docs/SIR_DOMAIN.md) — Voter verification example
- [**Adding Transforms**](docs/ADDING_TRANSFORMS.md) — Developer guide
