import os
import re
import subprocess

from .config import ConnectionConfig

# Matches any valid PostgreSQL READ ONLY transaction opener at the start of the SQL
_READ_ONLY_RE = re.compile(
    r"^\s*(?:BEGIN|START\s+TRANSACTION)\s+(?:TRANSACTION\s+)?READ\s+ONLY",
    re.IGNORECASE,
)


def _assert_read_only(sql: str) -> None:
    """Проверяет, что запрос открывается транзакцией READ ONLY."""
    if not _READ_ONLY_RE.match(sql):
        raise ValueError(
            "Запрос должен выполняться в транзакции READ ONLY. "
            "Оберните SQL конструкцией: BEGIN READ ONLY; <sql>; ROLLBACK;"
        )


def run_query(
    psql_path: str,
    conn: ConnectionConfig,
    sql: str,
    timeout: int = 30,
    validate_read_only: bool = True,
) -> str:
    if validate_read_only:
        _assert_read_only(sql)

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
    return run_query(psql_path, conn, sql, validate_read_only=False)


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
    columns = run_query(psql_path, conn, columns_sql, validate_read_only=False)
    indexes = run_query(psql_path, conn, indexes_sql, validate_read_only=False)

    result = f"=== Columns ===\n{columns}"
    if indexes:
        result += f"\n\n=== Indexes ===\n{indexes}"
    return result
