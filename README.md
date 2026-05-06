# pg-mcp

PostgreSQL MCP server that executes queries via psql subprocess. No persistent connections — each query opens psql, runs SQL, closes.

## Config

`~/.config/pg-mcp/connections.yml`:

```yaml
connections:
  dev-mydb:
    host: db.example.com
    port: 5432
    dbname: mydb
    user: myuser
    password: "mypassword"
```

## Tools

- `list_connections` — list configured connections
- `list_tables(connection, schema?)` — list tables
- `describe_table(connection, table, schema?)` — show columns and indexes
- `query(connection, sql)` — execute SQL
