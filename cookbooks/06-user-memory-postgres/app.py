"""Recipe 06 — User memory: durable facts in SQLite (Postgres-shaped API)."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class UserMemoryStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memories (user_id TEXT, key TEXT, value TEXT, PRIMARY KEY (user_id, key))"
        )

    def put(self, user_id: str, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO memories(user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value),
        )
        self.conn.commit()

    def get(self, user_id: str, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM memories WHERE user_id = ? AND key = ?",
            (user_id, key),
        ).fetchone()
        return None if row is None else row[0]

    def all_for(self, user_id: str) -> dict[str, str]:
        rows = self.conn.execute(
            "SELECT key, value FROM memories WHERE user_id = ?", (user_id,)
        ).fetchall()
        return {k: v for k, v in rows}


if __name__ == "__main__":
    store = UserMemoryStore()
    store.put("jared", "role", "Account Executive")
    print(store.all_for("jared"))
