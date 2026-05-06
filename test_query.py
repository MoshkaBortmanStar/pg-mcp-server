import sys
sys.path.insert(0, 'src')

from pg_mcp_server.config import Config
from pg_mcp_server.executor import get_tables, run_query

cfg = Config()
psql = cfg.get_psql_path()

conn_data = cfg.get_connection('local-data')
conn_delta = cfg.get_connection('local-delta')

print("=== local-data tables (schema: naruto) ===")
print(get_tables(psql, conn_data, schema="naruto"))

print("\n=== local-delta tables (schema: naruto) ===")
print(get_tables(psql, conn_delta, schema="naruto"))

print("\n=== naruto.ninja (first 5) ===")
print(run_query(psql, conn_data, "SELECT * FROM naruto.ninja LIMIT 5"))

print("\n=== naruto.mission (first 5) ===")
print(run_query(psql, conn_delta, "SELECT * FROM naruto.mission LIMIT 5"))
