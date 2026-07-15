# ETL Pipeline Architecture

## What This System Does

```mermaid
flowchart LR
    A[Production Databases] -->|Copy Data| B[Staging Area]
    B -->|Summarize| C[Summary Tables]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e9
```

**In simple terms:**
1. We **copy** data from 5 production databases into a staging area
2. We **combine** related data into one place (denormalization)
3. We **summarize** the data into easy-to-read reports

---

## The Big Picture

```mermaid
flowchart TB
    subgraph Sources["5 Production Databases"]
        S1[mytdp_remote<br/>Voter records]
        S2[tdp_events<br/>Rallies & events]
        S3[prod_mytdp_app<br/>Verification info]
        S4[tdp_feed<br/>News feeds]
        S5[tdp_calendar<br/>Calendar events]
    end
    
    subgraph DestDB["Staging Area (Destination)"]
        D1[mytdp schema<br/>Core voter data]
        D2[dakavara_pa schema<br/>Location data]
    end
    
    subgraph Transform["Processing"]
        T1[Denormalize<br/>Combine related data]
        T2[Summarize<br/>Create reports]
    end
    
    subgraph Reports["Summary Tables"]
        R1[Booth verification stats]
        R2[Location voter counts]
        R3[Custom reports]
    end
    
    Sources --> DestDB
    DestDB --> Transform
    Transform --> Reports
    
    style Sources fill:#e3f2fd
    style DestDB fill:#fff8e1
    style Transform fill:#f3e5f5
    style Reports fill:#e8f5e9
```

---

## Step-by-Step Flow

### Step 1: Copy Data (Extract)

```mermaid
sequenceDiagram
    participant P as Production DB
    participant S as Staging Area
    
    loop Every few minutes
        P->>S: What's new since last sync?
        S->>P: Here's what changed
        P->>S: Copy new/updated records
    end
    
    Note over P,S: We use "keyset pagination"<br/>to handle millions of records efficiently
```

**What happens:**
- We check each production database for new or updated records
- We copy only what changed (not the entire database)
- This happens automatically every few minutes

### Step 2: Combine Data (Denormalize)

```mermaid
flowchart LR
    subgraph Before["Before: Data scattered"]
        BV[booth_voter<br/>70M records]
        B[booth<br/>Booth details]
        S[state<br/>State names]
        C[cluster<br/>Cluster names]
    end
    
    subgraph After["After: Combined in one place"]
        DIM[dim_booth_voter<br/>All info combined]
    end
    
    BV -->|Join| DIM
    B -->|Join| DIM
    S -->|Join| DIM
    C -->|Join| DIM
    
    style Before fill:#ffebee
    style After fill:#e8f5e9
```

**Why we do this:**
- `booth_voter` has 70 million records
- If we join it with other tables multiple times, it's slow
- We combine everything ONCE into `dim_booth_voter`
- Then all reports read from this combined table (fast!)

### Step 3: Create Reports (Summarize)

```mermaid
flowchart TB
    DIM[dim_booth_voter<br/>Combined data] --> F1[fact_booth_sir<br/>Verification stats]
    DIM --> F2[fact_booth_cubs<br/>Active users stats]
    VI[voter_info] --> F3[fact_voter_location<br/>Location counts]
    
    style DIM fill:#fff3e0
    style F1 fill:#e8f5e9
    style F2 fill:#e8f5e9
    style F3 fill:#e8f5e9
```

**What we create:**
- **Booth verification stats**: How many voters verified per booth
- **Active user stats**: Who's actively using the system
- **Location counts**: How many voters in each area

---

## Key Concepts

### What is CDC?

**CDC (Change Data Capture)** = Only copying what changed

```mermaid
flowchart LR
    A[Full Database<br/>10 million records] -->|Traditional| B[Copy all 10M<br/>Slow!]
    A -->|CDC| C[Copy only 500 changed<br/>Fast!]
    
    style A fill:#e3f2fd
    style B fill:#ffebee
    style C fill:#e8f5e9
```

### What is Denormalization?

**Denormalization** = Combining related data into one table

```mermaid
flowchart TB
    subgraph Normal["Normal: Multiple lookups"]
        Q1[Query 1: Get voter] --> Q2[Query 2: Get booth name]
        Q2 --> Q3[Query 3: Get state name]
    end
    
    subgraph Denorm["Denormalized: One lookup"]
        Q4[Query: Get everything at once]
    end
    
    style Normal fill:#ffebee
    style Denorm fill:#e8f5e9
```

### What is a Fact Table?

**Fact Table** = A summary table with numbers/metrics

```mermaid
flowchart LR
    A[Raw Data<br/>Individual records] -->|Aggregate| B[Fact Table<br/>Summary numbers]
    
    style A fill:#e3f2fd
    style B fill:#e8f5e9
```

**Example:**
- Raw data: "Voter 1 verified", "Voter 2 verified", "Voter 3 not verified"
- Fact table: "2 voters verified, 1 not verified"

---

## Database Structure

### Source Databases (Production)

| Database | What it contains | Example |
|----------|------------------|---------|
| mytdp_remote | Voter records | 70M voter entries |
| tdp_events | Events & rallies | Rally attendance |
| prod_mytdp_app | Verification data | SIR verification status |
| tdp_feed | News feeds | Feed updates |
| tdp_calendar | Calendar events | Event schedules |

### Destination Database (Staging)

```mermaid
erDiagram
    mytdp_schema ||--o{ dim_booth_voter : "provides data"
    dakavara_pa_schema ||--o{ dim_booth_voter : "provides data"
    
    dim_booth_voter ||--o{ fact_booth_sir : "summarizes"
    dim_booth_voter ||--o{ fact_booth_cubs : "summarizes"
    
    mytdp_schema {
        booth_voter table "70M records"
        booth table "Booth details"
        state table "State names"
    }
    
    dakavara_pa_schema {
        cluster table "Cluster names"
        unit table "Unit names"
        constituency table "Constituency names"
    }
```

---

## Why This Design?

### Problem: Slow Queries

```mermaid
flowchart TD
    A[Query booth_voter<br/>70M rows] -->|Join with booth| B[Slow!]
    A -->|Join with state| C[Slow!]
    A -->|Join with cluster| D[Slow!]
    
    B --> E[Total: 210M rows processed]
    C --> E
    D --> E
    
    style B fill:#ffcdd2
    style C fill:#ffcdd2
    style D fill:#ffcdd2
    style E fill:#ffcdd2
```

### Solution: Denormalize Once

```mermaid
flowchart TD
    A[booth_voter<br/>70M rows] -->|Join once| B[dim_booth_voter<br/>Combined data]
    B -->|Read from| C[fact_booth_sir<br/>Fast!]
    B -->|Read from| D[fact_booth_cubs<br/>Fast!]
    
    E[Total: 70M + small reads]
    
    style B fill:#c8e6c9
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style E fill:#c8e6c9
```

---

## Navigation

- **[Home](../README.md)** — Back to main README
- **[SIR Domain](SIR_DOMAIN.md)** — See how SIR verification works
- **[Adding Transforms](ADDING_TRANSFORMS.md)** — How to add new features
- **[Technical Details](TECHNICAL.md)** — Deep dive for developers
