from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import Config
from . import executor

app = Server("pg-mcp")


def _config(cfg: Config):
    def list_connections_tool():
        connections = cfg.list_connections()
        if not connections:
            return "No connections configured."
        return "\n".join(f"- {name}: {dsn}" for name, dsn in connections.items())

    def query_tool(connection: str, sql: str) -> str:
        conn = cfg.get_connection(connection)
        psql = cfg.get_psql_path()
        return executor.run_query(psql, conn, sql)

    def list_tables_tool(connection: str, schema: str = "public") -> str:
        conn = cfg.get_connection(connection)
        psql = cfg.get_psql_path()
        return executor.get_tables(psql, conn, schema)

    def describe_table_tool(connection: str, table: str, schema: str = "public") -> str:
        conn = cfg.get_connection(connection)
        psql = cfg.get_psql_path()
        return executor.describe_table(psql, conn, table, schema)

    return list_connections_tool, query_tool, list_tables_tool, describe_table_tool


def create_server(cfg: Config) -> Server:
    list_connections_fn, query_fn, list_tables_fn, describe_table_fn = _config(cfg)

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="list_connections",
                description="List all configured PostgreSQL connections",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="query",
                description=(
                    "Execute a SQL query on a PostgreSQL connection. "
                    "The query MUST start with a READ ONLY transaction: "
                    "BEGIN READ ONLY; <sql>; ROLLBACK;"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {"type": "string", "description": "Connection name, e.g. dev-metadata"},
                        "sql": {
                            "type": "string",
                            "description": (
                                "SQL query wrapped in a READ ONLY transaction. "
                                "Example: BEGIN READ ONLY; SELECT * FROM users; ROLLBACK;"
                            ),
                        },
                    },
                    "required": ["connection", "sql"],
                },
            ),
            Tool(
                name="list_tables",
                description="List tables in a PostgreSQL connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {"type": "string", "description": "Connection name, e.g. dev-metadata"},
                        "schema": {"type": "string", "description": "Schema name (default: public)"},
                    },
                    "required": ["connection"],
                },
            ),
            Tool(
                name="describe_table",
                description="Show columns and indexes of a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {"type": "string", "description": "Connection name, e.g. dev-metadata"},
                        "table": {"type": "string", "description": "Table name"},
                        "schema": {"type": "string", "description": "Schema name (default: public)"},
                    },
                    "required": ["connection", "table"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "list_connections":
                result = list_connections_fn()
            elif name == "query":
                result = query_fn(arguments["connection"], arguments["sql"])
            elif name == "list_tables":
                result = list_tables_fn(arguments["connection"], arguments.get("schema", "public"))
            elif name == "describe_table":
                result = describe_table_fn(
                    arguments["connection"],
                    arguments["table"],
                    arguments.get("schema", "public"),
                )
            else:
                result = f"Unknown tool: {name}"
        except Exception as e:
            result = f"Error: {e}"

        return [TextContent(type="text", text=result)]

    return app


async def serve(cfg: Config):
    server = create_server(cfg)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
