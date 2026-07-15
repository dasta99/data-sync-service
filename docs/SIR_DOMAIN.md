# SIR Domain — Voter Verification Tracking

> **For non-technical readers:** This document explains how we track voter verification status using simple language and visual diagrams.

## What is SIR?

**SIR (Systematic Voters' Education and Electoral Participation)** is a system to verify voter information across polling booths.

```mermaid
flowchart LR
    A[Voter visits booth] --> B[Verifier checks info]
    B --> C{Verified?}
    C -->|Yes| D[Mark as verified]
    C -->|No| E[Mark as issue]
    
    style D fill:#c8e6c9
    style E fill:#ffcdd2
```

---

## What This System Does

```mermaid
flowchart TB
    subgraph Input["Input Data"]
        I1[Voter records<br/>70 million]
        I2[Booth information]
        I3[Location data]
    end
    
    subgraph Process["Processing"]
        P1[Combine all data<br/>into one place]
        P2[Calculate statistics<br/>per booth]
    end
    
    subgraph Output["Output Reports"]
        O1[Verification stats<br/>per booth]
        O2[Active user stats<br/>per booth]
        O3[Voter counts<br/>per location]
    end
    
    Input --> Process
    Process --> Output
    
    style Input fill:#e3f2fd
    style Process fill:#fff3e0
    style Output fill:#e8f5e9
```

---

## The Three Reports

### 1. Booth Verification Stats (`fact_booth_sir`)

Shows verification status for each polling booth.

```mermaid
flowchart TD
    A[Booth A] --> B[Total voters: 1500]
    A --> C[Verified: 1200]
    A --> D[Pending: 300]
    
    B --> E[📊 Verification Rate: 80%]
    
    style A fill:#e3f2fd
    style E fill:#e8f5e9
```

**What it tells us:**
- How many voters in each booth
- How many have been verified
- How many are still pending

### 2. Active User Stats (`fact_booth_cubs`)

Shows who's actively using the system.

```mermaid
flowchart TD
    A[Booth A] --> B[Mobile numbers: 800]
    A --> C[Caste info: 750]
    A --> D[Party info: 700]
    A --> E[Forms submitted: 650]
    
    B --> F[📊 Activity Rate: 81%]
    
    style A fill:#e3f2fd
    style F fill:#e8f5e9
```

**What it tells us:**
- How many voters have mobile numbers recorded
- How many have caste/party information
- How many forms have been submitted

### 3. Location Voter Counts (`fact_voter_location`)

Shows voter distribution across locations.

```mermaid
flowchart TD
    A[State: Andhra Pradesh] --> B[Total voters: 5 million]
    A --> C[Parliament: 10 districts]
    A --> D[Assembly: 175 constituencies]
    
    B --> E[📊 Average per booth: 1500]
    
    style A fill:#e3f2fd
    style E fill:#e8f5e9
```

**What it tells us:**
- How many voters in each state
- How many in each parliament/assembly area
- Distribution across locations

---

## How Data Flows

### Step 1: Combine Data (Denormalize)

```mermaid
flowchart TB
    subgraph Sources["Source Tables"]
        BV[booth_voter<br/>70M records]
        BO[booth<br/>Booth details]
        ST[state<br/>State names]
        CL[cluster<br/>Cluster names]
        UN[unit<br/>Unit names]
        CO[constituency<br/>Constituency names]
    end
    
    subgraph Combined["Combined Table"]
        DIM[dim_booth_voter<br/>All info in one place]
    end
    
    Sources --> Combined
    
    style Sources fill:#e3f2fd
    style Combined fill:#c8e6c9
```

**Why?** Because joining 70M records multiple times is slow. We do it once!

### Step 2: Create Reports

```mermaid
flowchart TB
    DIM[dim_booth_voter] -->|Count all voters| F1[fact_booth_sir]
    DIM -->|Count verified only| F2[fact_booth_cubs]
    VI[voter_info] -->|Count by location| F3[fact_voter_location]
    
    style DIM fill:#fff3e0
    style F1 fill:#e8f5e9
    style F2 fill:#e8f5e9
    style F3 fill:#e8f5e9
```

---

## Example: Booth A Verification

```mermaid
flowchart TD
    subgraph Step1["Step 1: Raw Data"]
        BV1[Voter 1: Verified ✅]
        BV2[Voter 2: Verified ✅]
        BV3[Voter 3: Pending ⏳]
        BV4[Voter 4: Verified ✅]
        BV5[Voter 5: Death ☠️]
    end
    
    subgraph Step2["Step 2: Combine with Booth Info"]
        DIM[dim_booth_voter:<br/>Voter 1 + Booth A + State X<br/>Voter 2 + Booth A + State X<br/>...]
    end
    
    subgraph Step3["Step 3: Summarize"]
        F1[fact_booth_sir:<br/>Booth A: 5 voters<br/>3 verified, 1 pending, 1 death]
    end
    
    Step1 --> Step2
    Step2 --> Step3
    
    style Step1 fill:#e3f2fd
    style Step2 fill:#fff3e0
    style Step3 fill:#e8f5e9
```

---

## Key Metrics Explained

### Verification Status

| Status | Meaning | Example |
|--------|---------|---------|
| ✅ Available | Voter is present and verified | "Yes, I'm here" |
| 🔄 Temporary shift | Voter temporarily moved | "I'm at different booth" |
| 🏠 Permanent shift | Voter permanently moved | "I moved to new address" |
| ☠️ Death | Voter has passed away | — |
| 👥 Duplicate | Multiple records for same voter | — |
| 🔄 Double vote | Voter voted in multiple places | — |

### Activity Metrics

| Metric | What it measures |
|--------|------------------|
| Mobile numbers | How many voters have phone numbers recorded |
| Caste info | How many have caste/category information |
| Party info | How many have political party affiliation |
| Forms submitted | How many physical forms have been submitted |

---

## Real-World Example

### Before System

```mermaid
flowchart TD
    A[Official visits booth] --> B[Checks 1500 voters manually]
    B --> C[Paper records]
    C --> D[Data entry at office]
    D --> E[Report next day]
    
    style A fill:#e3f2fd
    style E fill:#ffcdd2
    
    Note1[⏰ Time: 2 days<br/>❌ Errors: Frequent<br/>📊 Real-time: No]
```

### After System

```mermaid
flowchart TD
    A[Verifier scans voter ID] --> B[System updates instantly]
    B --> C[Dashboard shows real-time stats]
    C --> D[Decision makers see immediately]
    
    style A fill:#e3f2fd
    style D fill:#c8e6c9
    
    Note2[⏰ Time: Instant<br/>✅ Errors: Minimal<br/>📊 Real-time: Yes]
```

---

## Navigation

- **[Home](../README.md)** — Back to main README
- **[Architecture](ARCHITECTURE.md)** — How the system works
- **[Adding Transforms](ADDING_TRANSFORMS.md)** — How to add new features
- **[Technical Details](TECHNICAL.md)** — Deep dive for developers
