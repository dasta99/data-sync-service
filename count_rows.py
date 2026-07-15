#!/usr/bin/env python3
"""Get exact row counts for all key tables with timing.

Shows:
  - Exact row counts (not estimates)
  - Time to count (indicates index efficiency)
  - Size on disk

Usage:
  python count_rows.py
  python count_rows.py --output counts.json
"""

import json
import os
import sys
import time
from datetime import datetime

import pymysql
from dotenv import load_dotenv

load_dotenv()

# ─── All tables to count ────────────────────────────────────────

TABLES = {
    "mytdp": [
        "booth_voter", "sir_form_counts",
        "campaigns", "campaigns_address_mapping", "campaigns_assemblies", "campaign_address_mapping",
        "address_visit_info", "address_visit_info_temp",
        "meetings", "meeting_schedules", "meeting_attendance", "meeting_invite_roles",
        "meeting_resolutions", "meeting_resolution_assignments",
        "event", "event_attendance", "trainings", "program", "program_attendance",
        "user", "user_role_details", "user_access", "user_memberships", "membership",
        "address", "person", "person_address", "phone",
        "document", "files", "data_sync", "data_sync_track",
    ],
    "dakavara_pa": [
        "constituency", "state", "assembly", "parliament",
        "tehsil", "panchayat", "town", "ward", "mandal",
        "booth", "cluster", "unit",
        "tdp_committee", "tdp_committee_level", "tdp_committee_role",
        "tdp_committee_member", "tdp_cadre", "tdp_roles",
        "user_address", "cluster_booth", "unit_booth",
        "voter_info",
    ],
}


def get_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.getenv("DEST_HOST"),
        port=int(os.getenv("DEST_PORT", 3306)),
        user=os.getenv("DEST_USER"),
        password=os.getenv("DEST_PASS"),
        database="mytdp",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=300,  # 5 min timeout for large COUNT(*) queries
    )


def count_table(cur, schema: str, table: str) -> dict:
    """Get exact row count with timing."""
    # Get estimated count and size from information_schema first
    cur.execute(f"""
        SELECT TABLE_ROWS, 
               ROUND(DATA_LENGTH/1024/1024, 2) as data_mb,
               ROUND(INDEX_LENGTH/1024/1024, 2) as index_mb
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
    """)
    info = cur.fetchone()
    
    estimated_rows = info["TABLE_ROWS"] if info else 0
    data_mb = info["data_mb"] if info else 0
    index_mb = info["index_mb"] if info else 0

    # For very large tables (>10M), use estimate to avoid long waits
    if estimated_rows and estimated_rows > 10_000_000:
        return {
            "exact_count": None,
            "estimated_count": estimated_rows,
            "count_time_ms": None,
            "data_mb": data_mb,
            "index_mb": index_mb,
            "note": "Using estimate (table >10M rows)"
        }

    # Exact count for smaller tables
    start = time.time()
    try:
        cur.execute(f"SELECT COUNT(*) as cnt FROM `{schema}`.`{table}`")
        result = cur.fetchone()
        exact_count = result["cnt"]
        elapsed_ms = int((time.time() - start) * 1000)
    except Exception as e:
        return {
            "exact_count": None,
            "estimated_count": estimated_rows,
            "count_time_ms": None,
            "data_mb": data_mb,
            "index_mb": index_mb,
            "error": str(e)
        }

    return {
        "exact_count": exact_count,
        "estimated_count": estimated_rows,
        "count_time_ms": elapsed_ms,
        "data_mb": data_mb,
        "index_mb": index_mb,
    }


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "row_counts.json"
    
    conn = get_connection()
    results = {}
    
    try:
        with conn.cursor() as cur:
            for schema, tables in TABLES.items():
                print(f"\n{'='*60}")
                print(f"  {schema}: {len(tables)} tables")
                print(f"{'='*60}")
                
                results[schema] = {}
                
                for i, table in enumerate(tables, 1):
                    print(f"  [{i}/{len(tables)}] {table}...", end=" ", flush=True)
                    
                    data = count_table(cur, schema, table)
                    results[schema][table] = data
                    
                    if data["exact_count"] is not None:
                        count_str = f"{data['exact_count']:,}"
                        time_str = f" ({data['count_time_ms']}ms)" if data["count_time_ms"] else ""
                        print(f"{count_str}{time_str}")
                    else:
                        est = data.get("estimated_count", "?")
                        print(f"~{est:,} (estimate)")
    finally:
        conn.close()

    # Add metadata
    output = {
        "generated_at": datetime.now().isoformat(),
        "databases": results,
    }

    # Write JSON
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved: {output_file}")

    # Print summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    for schema, tables in results.items():
        total = 0
        for t, data in tables.items():
            count = data.get("exact_count") or data.get("estimated_count") or 0
            total += count
        print(f"  {schema}: ~{total:,} total rows")
    
    print()


if __name__ == "__main__":
    main()
