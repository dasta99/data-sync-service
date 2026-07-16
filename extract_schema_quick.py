#!/usr/bin/env python3
"""Extract schema for key MYTDP tables only.

Focuses on tables used in dashboard queries:
- booth_voter, campaigns, meetings, events
- Geography: booth, constituency, state, tehsil, panchayat, cluster, unit
- Committee: tdp_committee, tdp_cadre, user_address

Outputs:
  - schema_dump.json    (structured)
  - SCHEMA_REPORT.md    (human-readable)

Usage:
  python extract_schema_quick.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import pymysql
from dotenv import load_dotenv

load_dotenv()

# ─── Database Connection ────────────────────────────────────────

def get_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.getenv("DEST_HOST"),
        port=int(os.getenv("DEST_PORT", 3306)),
        user=os.getenv("DEST_USER"),
        password=os.getenv("DEST_PASS"),
        database="mytdp",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=30,
    )


# ─── Key Tables to Extract ─────────────────────────────────────

KEY_TABLES = {
    "mytdp": [
        # Core SIR tables
        "booth_voter", "sir_form_counts",
        # Campaign
        "campaigns", "campaigns_address_mapping", "campaigns_assemblies", "campaign_address_mapping",
        "address_visit_info", "address_visit_info_temp",
        # Meetings
        "meetings", "meeting_schedules", "meeting_attendance", "meeting_invite_roles",
        "meeting_resolutions", "meeting_resolution_assignments",
        # Events/Training
        "event", "event_attendance", "trainings", "program", "program_attendance",
        # User/Role
        "user", "user_role_details", "user_access", "user_memberships", "membership",
        # Address
        "address", "person", "person_address", "phone",
        # Files
        "document", "files",
    ],
    "dakavara_pa": [
        # Geography
        "constituency", "state", "assembly", "parliament",
        "tehsil", "panchayat", "town", "ward", "mandal",
        "booth", "cluster", "unit",
        # Committee
        "tdp_committee", "tdp_committee_level", "tdp_committee_role",
        "tdp_committee_member", "tdp_cadre", "tdp_roles",
        # Address
        "user_address", "cluster_booth", "unit_booth",
        # Voter info
        "voter_info",
    ],
}


def extract_table(cur, schema_name: str, table_name: str) -> dict:
    """Extract schema for a single table."""
    # Columns
    cur.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, 
               COLUMN_DEFAULT, COLUMN_KEY, EXTRA, COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cur.fetchall()

    # Indexes
    cur.execute(f"""
        SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME, CARDINALITY, INDEX_TYPE
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
    """)
    indexes = cur.fetchall()

    # Size
    cur.execute(f"""
        SELECT TABLE_ROWS, 
               ROUND(DATA_LENGTH/1024/1024, 2) as data_mb,
               ROUND(INDEX_LENGTH/1024/1024, 2) as index_mb
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = '{schema_name}' AND TABLE_NAME = '{table_name}'
    """)
    size = cur.fetchone()

    return {
        "columns": columns,
        "indexes": indexes,
        "rows": size["TABLE_ROWS"] if size else 0,
        "data_mb": size["data_mb"] if size else 0,
        "index_mb": size["index_mb"] if size else 0,
    }


def generate_markdown(schemas: dict, output_path: str):
    """Generate markdown report."""
    lines = ["# MYTDP Schema Report", f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]

    for db_name, tables in schemas.items():
        lines.append(f"\n## {db_name}\n")

        # Summary table
        lines.append("| Table | Rows | Data MB | Index MB | Columns |")
        lines.append("|-------|------|---------|----------|---------|")
        
        sorted_tables = sorted(tables.items(), key=lambda x: x[1]["rows"] or 0, reverse=True)
        
        for tname, tdata in sorted_tables:
            lines.append(
                f"| `{tname}` | {(tdata['rows'] or 0):,} | {tdata['data_mb']:.1f} | "
                f"{tdata['index_mb']:.1f} | {len(tdata['columns'])} |"
            )
        lines.append("")

        # Column details
        for tname, tdata in sorted_tables:
            lines.append(f"\n### `{tname}`\n")
            lines.append("| Column | Type | Key | Nullable | Comment |")
            lines.append("|--------|------|-----|----------|---------|")
            
            for col in tdata["columns"]:
                key = col["COLUMN_KEY"] or ""
                if key == "PRI": key = "**PK**"
                elif key == "MUL": key = "FK"
                elif key == "UNI": key = "UQ"
                
                nullable = "Y" if col["IS_NULLABLE"] == "YES" else "N"
                comment = col.get("COLUMN_COMMENT", "") or ""
                lines.append(f"| `{col['COLUMN_NAME']}` | {col['COLUMN_TYPE']} | {key} | {nullable} | {comment} |")
            
            if tdata["indexes"]:
                lines.append("\n**Indexes:**\n")
                lines.append("| Index | Column | Unique |")
                lines.append("|-------|--------|--------|")
                for idx in tdata["indexes"]:
                    unique = "YES" if idx["NON_UNIQUE"] == 0 else "NO"
                    lines.append(f"| `{idx['INDEX_NAME']}` | `{idx['COLUMN_NAME']}` | {unique} |")
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(output_dir, exist_ok=True)

    conn = get_connection()
    all_schemas = {}

    try:
        with conn.cursor() as cur:
            for db_name, table_list in KEY_TABLES.items():
                print(f"\n{'='*50}")
                print(f"  {db_name}: {len(table_list)} tables")
                print(f"{'='*50}")
                
                db_tables = {}
                for i, table_name in enumerate(table_list, 1):
                    print(f"  [{i}/{len(table_list)}] {table_name}", end=" ", flush=True)
                    try:
                        schema = extract_table(cur, db_name, table_name)
                        db_tables[table_name] = schema
                        print(f"({schema['rows']:,} rows)")
                    except Exception as e:
                        print(f"ERROR: {e}")
                
                all_schemas[db_name] = db_tables
    finally:
        conn.close()

    # Write JSON
    json_path = os.path.join(output_dir, "schema_dump.json")
    with open(json_path, "w") as f:
        json.dump(all_schemas, f, indent=2, default=str)
    print(f"\nJSON: {json_path}")

    # Write Markdown
    md_path = os.path.join(output_dir, "SCHEMA_REPORT.md")
    generate_markdown(all_schemas, md_path)
    print(f"Markdown: {md_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
