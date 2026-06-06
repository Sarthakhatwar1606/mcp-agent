"""MCP server — DuckDB data catalog (Unity Catalog replacement, free)."""
import json
import sys
from pathlib import Path

import duckdb
from mcp.server.fastmcp import FastMCP

DB_PATH = str(Path(__file__).parent.parent / "data" / "catalog.duckdb")
mcp = FastMCP("Data Catalog")


def _db(read_only: bool = True):
    return duckdb.connect(DB_PATH, read_only=read_only)


@mcp.tool()
def list_tables() -> str:
    """List all tables available in the enterprise data catalog."""
    db = _db()
    rows = db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
    ).fetchall()
    db.close()
    return json.dumps([r[0] for r in rows])


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get column schema, row count, and 3 sample rows for a catalog table."""
    db = _db()
    try:
        schema = db.execute(f"DESCRIBE {table_name}").fetchall()
        count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        sample = db.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf().to_dict(orient="records")
    finally:
        db.close()
    return json.dumps(
        {
            "table": table_name,
            "schema": [{"column": r[0], "type": r[1]} for r in schema],
            "row_count": count,
            "sample_rows": sample,
        },
        default=str,
    )


@mcp.tool()
def run_sql(query: str) -> str:
    """Execute a read-only SQL SELECT query on the data catalog and return JSON results (max 50 rows)."""
    if not query.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are permitted."})
    db = _db()
    try:
        df = db.execute(query).fetchdf()
        result = df.head(50).to_dict(orient="records")
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()
    return json.dumps(result, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")
