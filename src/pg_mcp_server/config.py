import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "pg-mcp" / "connections.yml"


@dataclass
class ConnectionConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


class Config:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path) if path else DEFAULT_CONFIG_PATH
        self._data: dict = {}
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)

    def _connections(self) -> dict:
        self._load()
        return self._data.get("connections", {})

    def get_connection(self, name: str) -> ConnectionConfig:
        connections = self._connections()
        if name not in connections:
            available = list(connections.keys())
            raise ValueError(f"Connection '{name}' not found. Available: {available}")
        c = connections[name]
        return ConnectionConfig(
            host=c["host"],
            port=int(c["port"]),
            dbname=c["dbname"],
            user=c["user"],
            password=c["password"],
        )

    def list_connections(self) -> Dict[str, str]:
        connections = self._connections()
        return {name: f"{c['host']}:{c['port']}/{c['dbname']}" for name, c in connections.items()}

    def update_password(self, new_password: str):
        connections = self._data.get("connections", {})
        for name in connections:
            connections[name]["password"] = new_password
        self._save()

    def get_psql_path(self) -> str:
        if "psql_path" in self._data:
            return self._data["psql_path"]
        found = shutil.which("psql")
        if found:
            return found
        candidates = [
            # Windows — Scoop
            Path.home() / "scoop" / "apps" / "postgresql" / "current" / "bin" / "psql.exe",
            # macOS — Homebrew libpq keg-only (Apple Silicon)
            Path("/opt/homebrew/opt/libpq/bin/psql"),
            # macOS — Homebrew libpq keg-only (Intel)
            Path("/usr/local/opt/libpq/bin/psql"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        raise RuntimeError(
            "psql not found. Install PostgreSQL client or set 'psql_path' in config."
        )
