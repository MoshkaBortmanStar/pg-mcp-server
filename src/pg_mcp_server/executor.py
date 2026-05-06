import os
import subprocess
from typing import Optional

from .config import Config, ConnectionConfig


def run_query(psql_path: str, conn: ConnectionConfig, sql: str, timeout: int = 30) -> str:
    env = os.environ.copy()
    env["PGPASSWORD"] = conn.password
    env["PGAPPNAME"] = "pg-mcp"

    cmd = [
        psql_path,
        "-h", conn.host,
        "-p", str(conn.port),
        "-U", conn.user,
        "-d", conn.dbname,
        "--csv",
        "-c", sql,
    ]

    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


def get_tables(psql_path: str, conn: ConnectionConfig, schema: str = "public") -> str:
    sql = f"""
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = '{schema}'
ORDER BY table_name;
"""
    return run_query(psql_path, conn, sql)


def describe_table(psql_path: str, conn: ConnectionConfig, table: str, schema: str = "public") -> str:
    columns_sql = f"""
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = '{schema}' AND table_name = '{table}'
ORDER BY ordinal_position;
"""
    indexes_sql = f"""
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = '{schema}' AND tablename = '{table}'
ORDER BY indexname;
"""
    columns = run_query(psql_path, conn, columns_sql)
    indexes = run_query(psql_path, conn, indexes_sql)

    result = f"=== Columns ===\n{columns}"
    if indexes:
        result += f"\n\n=== Indexes ===\n{indexes}"
    return result
