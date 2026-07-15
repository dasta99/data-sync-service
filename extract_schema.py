#!/usr/bin/env python3
"""Extract full schema from mytdp + dakavara_pa databases.

Outputs:
  - schema_dump.json    (structured, for programmatic use)
  - SCHEMA_REPORT.md    (human-readable, for analysis)

Usage:
  python extract_schema.py
  python extract_schema.py --output /custom/path
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymysql
from dotenv import load_dotenv

load_dotenv()

# ─── Database Connections ───────────────────────────────────────

DATABASES = {
    "mytdp": {
        "host": os.getenv("DEST_HOST"),
        "port": int(os.getenv("DEST_PORT", 3306)),
        "user": os.getenv("DEST_USER"),
        "password": os.getenv("DEST_PASS"),
        "database": os.getenv("DEST_DB", "mytdp"),
    },
    "dakavara_pa": {
        # Connect via mytdp, query dakavara_pa using cross-DB prefix
        "host": os.getenv("DEST_HOST"),
        "port": int(os.getenv("DEST_PORT", 3306)),
        "user": os.getenv("DEST_USER"),
        "password": os.getenv("DEST_PASS"),
        "database": "mytdp",  # Connect to mytdp, access dakavara_pa via prefix
    },
}


def get_connection(db_config: dict) -> pymysql.Connection:
    return pymysql.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=30,
    )


# ─── Schema Extraction Queries ─────────────────────────────────

def get_query_tables(schema_name: str) -> str:
    return f"""
SELECT 
    TABLE_NAME,
    TABLE_TYPE,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH,
    AUTO_INCREMENT,
    TABLE_COMMENT,
    CREATE_TIME,
    UPDATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
ORDER BY TABLE_NAME
"""

def get_query_columns(schema_name: str, table_name: str) -> str:
    return f"""
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_KEY,
    EXTRA,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_NAME = '{table_name}'
ORDER BY ORDINAL_POSITION
"""

def get_query_indexes(schema_name: str, table_name: str) -> str:
    return f"""
SELECT 
    INDEX_NAME,
    NON_UNIQUE,
    SEQ_IN_INDEX,
    COLUMN_NAME,
    COLLATION,
    CARDINALITY,
    SUB_PART,
    INDEX_TYPE
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_NAME = '{table_name}'
ORDER BY INDEX_NAME, SEQ_IN_INDEX
"""

def get_query_foreign_keys(schema_name: str, table_name: str) -> str:
    return f"""
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_NAME = '{table_name}'
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY CONSTRAINT_NAME
"""

def get_query_table_size(schema_name: str) -> str:
    return f"""
SELECT 
    TABLE_NAME,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) AS data_mb,
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS index_mb,
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS total_mb,
    TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_TYPE = 'BASE TABLE'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
"""


def extract_table_schema(conn: pymysql.Connection, db_name: str, table_name: str) -> dict:
    """Extract full schema for a single table."""
    with conn.cursor() as cur:
        # Columns
        cur.execute(get_query_columns(db_name, table_name))
        columns = cur.fetchall()

        # Indexes
        cur.execute(get_query_indexes(db_name, table_name))
        indexes = cur.fetchall()

        # Foreign keys
        cur.execute(get_query_foreign_keys(db_name, table_name))
        foreign_keys = cur.fetchall()

    return {
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys,
    }


def extract_database_schema(db_name: str, db_config: dict) -> dict:
    """Extract full schema for a database."""
    print(f"\n{'='*60}")
    print(f"  Extracting: {db_name} ({db_config['host']})")
    print(f"{'='*60}")

    conn = get_connection(db_config)
    result = {"database": db_name, "tables": {}, "summary": {}}

    try:
        with conn.cursor() as cur:
            # Get all tables
            cur.execute(get_query_tables(db_name))
            tables = cur.fetchall()
            print(f"  Found {len(tables)} tables/views")

            # Get table sizes
            cur.execute(get_query_table_size(db_name))
            size_rows = cur.fetchall()
            size_map = {r["TABLE_NAME"]: r for r in size_rows}

        # Extract each table
        for i, tbl in enumerate(tables, 1):
            table_name = tbl["TABLE_NAME"]
            table_type = tbl["TABLE_TYPE"]
            table_rows = tbl["TABLE_ROWS"] or 0

            print(f"  [{i}/{len(tables)}] {table_name} ({table_type}, ~{table_rows:,} rows)")

            schema = extract_table_schema(conn, db_name, table_name)

            result["tables"][table_name] = {
                "type": table_type,
                "estimated_rows": table_rows,
                "size": size_map.get(table_name, {}),
                "comment": tbl.get("TABLE_COMMENT", ""),
                "created": str(tbl.get("CREATE_TIME", "")),
                "updated": str(tbl.get("UPDATE_TIME", "")),
                **schema,
            }

        # Summary
        base_tables = [t for t in tables if t["TABLE_TYPE"] == "BASE TABLE"]
        views = [t for t in tables if t["TABLE_TYPE"] == "VIEW"]
        total_rows = sum(t["TABLE_ROWS"] or 0 for t in base_tables)
        total_size = sum(
            (size_map.get(t["TABLE_NAME"], {}).get("total_mb", 0) or 0)
            for t in base_tables
        )

        result["summary"] = {
            "total_tables": len(base_tables),
            "total_views": len(views),
            "total_estimated_rows": total_rows,
            "total_size_mb": round(total_size, 2),
        }

        print(f"  Summary: {len(base_tables)} tables, {len(views)} views, ~{total_rows:,} rows, {total_size:.1f} MB")

    finally:
        conn.close()

    return result


# ─── Markdown Report Generator ─────────────────────────────────

def generate_markdown(all_schemas: dict, output_path: str):
    """Generate human-readable markdown report."""
    lines = []
    lines.append("# MYTDP Schema Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Grand summary
    total_tables = 0
    total_views = 0
    total_estimated_rows = 0
    total_size = 0

    for db_name, schema in all_schemas.items():
        s = schema["summary"]
        total_tables += s["total_tables"]
        total_views += s["total_views"]
        total_estimated_rows += s["total_estimated_rows"]
        total_size += s["total_size_mb"]

    lines.append("## Grand Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Databases | {len(all_schemas)} |")
    lines.append(f"| Total Tables | {total_tables} |")
    lines.append(f"| Total Views | {total_views} |")
    lines.append(f"| Total Rows (est.) | {total_estimated_rows:,} |")
    lines.append(f"| Total Size | {total_size:.1f} MB |")
    lines.append("")

    # Per-database
    for db_name, schema in all_schemas.items():
        lines.append(f"\n---\n\n## Database: `{db_name}`\n")
        s = schema["summary"]
        lines.append(f"- **Tables:** {s['total_tables']}")
        lines.append(f"- **Views:** {s['total_views']}")
        lines.append(f"- **Est. Rows:** {s['total_estimated_rows']:,}")
        lines.append(f"- **Size:** {s['total_size_mb']:.1f} MB")
        lines.append("")

        # Size table
        lines.append("### Table Sizes\n")
        lines.append("| Table | Rows | Data MB | Index MB | Total MB |")
        lines.append("|-------|------|---------|----------|----------|")
        
        sorted_tables = sorted(
            schema["tables"].items(),
            key=lambda x: x[1].get("size", {}).get("total_mb", 0) or 0,
            reverse=True,
        )
        
        for table_name, tbl in sorted_tables:
            size = tbl.get("size", {})
            rows = tbl.get("estimated_rows", 0)
            data_mb = size.get("data_mb", 0) or 0
            idx_mb = size.get("index_mb", 0) or 0
            total_mb = size.get("total_mb", 0) or 0
            if total_mb > 0.01 or rows > 0:
                lines.append(f"| `{table_name}` | {rows:,} | {data_mb:.1f} | {idx_mb:.1f} | {total_mb:.1f} |")
        lines.append("")

        # Column details per table
        lines.append("### Table Schemas\n")
        
        for table_name, tbl in sorted_tables:
            if tbl["type"] != "BASE TABLE":
                continue
                
            lines.append(f"\n#### `{table_name}`")
            if tbl.get("comment"):
                lines.append(f"_{tbl['comment']}_")
            lines.append(f"\n~{tbl.get('estimated_rows', 0):,} rows\n")
            
            # Columns
            lines.append("| # | Column | Type | Nullable | Key | Default | Extra | Comment |")
            lines.append("|---|--------|------|----------|-----|---------|-------|---------|")
            
            for i, col in enumerate(tbl["columns"], 1):
                nullable = "YES" if col["IS_NULLABLE"] == "YES" else "NO"
                key = col["COLUMN_KEY"] or ""
                default = col["COLUMN_DEFAULT"] or ""
                extra = col["EXTRA"] or ""
                comment = col.get("COLUMN_COMMENT", "") or ""
                
                # Highlight keys
                if key == "PRI":
                    key = "**PRI**"
                elif key == "MUL":
                    key = "MUL"
                elif key == "UNI":
                    key = "UNI"
                
                lines.append(
                    f"| {i} | `{col['COLUMN_NAME']}` | {col['COLUMN_TYPE']} | "
                    f"{nullable} | {key} | {default} | {extra} | {comment} |"
                )
            
            # Indexes
            if tbl["indexes"]:
                lines.append("\n**Indexes:**\n")
                lines.append("| Index | Column | Unique | Cardinality |")
                lines.append("|-------|--------|--------|-------------|")
                
                for idx in tbl["indexes"]:
                    unique = "YES" if idx["NON_UNIQUE"] == 0 else "NO"
                    card = idx["CARDINALITY"] or ""
                    lines.append(
                        f"| `{idx['INDEX_NAME']}` | `{idx['COLUMN_NAME']}` | "
                        f"{unique} | {card} |"
                    )
            
            # Foreign keys
            if tbl["foreign_keys"]:
                lines.append("\n**Foreign Keys:**\n")
                lines.append("| Constraint | Column | References |")
                lines.append("|------------|--------|------------|")
                
                for fk in tbl["foreign_keys"]:
                    lines.append(
                        f"| `{fk['CONSTRAINT_NAME']}` | `{fk['COLUMN_NAME']}` | "
                        f"`{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}` |"
                    )
            
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    
    print(f"\nMarkdown report: {output_path}")


# ─── Main ───────────────────────────────────────────────────────

def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(output_dir, exist_ok=True)

    all_schemas = {}

    for db_name, db_config in DATABASES.items():
        try:
            schema = extract_database_schema(db_name, db_config)
            all_schemas[db_name] = schema
        except Exception as e:
            print(f"\n  ERROR connecting to {db_name}: {e}")
            print(f"  Skipping {db_name}...")
            continue

    # Write JSON
    json_path = os.path.join(output_dir, "schema_dump.json")
    with open(json_path, "w") as f:
        json.dump(all_schemas, f, indent=2, default=str)
    print(f"\nJSON dump: {json_path}")

    # Write Markdown
    md_path = os.path.join(output_dir, "SCHEMA_REPORT.md")
    generate_markdown(all_schemas, md_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
