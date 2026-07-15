# data-sync-service

ETL pipeline that extracts data from 5 production TDP sources, syncs into dest warehouse (mytdp + dakavara_pa schemas), then denormalizes and transforms into OLAP-friendly summary tables.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for general architecture.

See [docs/SIR_DOMAIN.md](docs/SIR_DOMAIN.md) for SIR domain implementation example.

```
┌─────────────────────────────────────────────────────────────┐
│                  5 PRODUCTION SOURCES                        │
│                                                             │
│  mytdp_remote    ─┐                                         │
│  tdp_events      ─┼──▶ Dest DB (mytdp + dakavara_pa)        │
│  prod_mytdp_app  ─┤     port 3307                           │
│  tdp_feed        ─┤                                         │
│  tdp_calendar    ─┘                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRANSFORM PHASE                          │
│                                                             │
│  1. Denormalize ONCE into dimension tables                   │
│  2. Aggregate from dimensions into summary/fact tables       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Start databases
docker compose up -d tdp-source dest-warehouse

# Seed test data
./scripts/seed_source.sh 10

# Run pipeline
python3 main.py --local
```

## Project Structure

```
src/
├── extract/              # CDC extraction
├── transform/            # Domain transforms
│   ├── base.py           # TransformHandler + TransformHelper
│   ├── registry.py       # Auto-discovers handlers
│   ├── orchestrator.py   # Dependency dispatch
│   └── sir/              # SIR domain (example)
│       ├── handler.py
│       └── transforms/
│           ├── denormalize.py
│           ├── booth_sir.py
│           ├── booth_cubs.py
│           └── voter_location.py
├── load/                 # Upsert/load strategies
└── shared/               # Config, connections, interfaces
migrations/
├── prod/                 # Production schemas
└── local/                # Seeds, staging, configs
docs/
├── ARCHITECTURE.md       # General architecture
├── SIR_DOMAIN.md         # SIR implementation example
└── ADDING_TRANSFORMS.md  # How to add new domains
```

## Commands

```bash
python3 main.py --local    # Local Docker MySQL (port 3307)
python3 main.py            # Production (reads .env)
```

## Adding a New Transform

See [docs/ADDING_TRANSFORMS.md](docs/ADDING_TRANSFORMS.md)
