import argparse
import asyncio

from .config import Config
from .server import serve


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL MCP server")
    parser.add_argument("--config", help="Path to connections.yml", default=None)
    args = parser.parse_args()

    cfg = Config(path=args.config)
    asyncio.run(serve(cfg))


if __name__ == "__main__":
    main()
