from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SeenStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_items (
                item_id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                keyword TEXT,
                item_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def has_seen(self, item_id: str) -> bool:
        if not item_id:
            return False
        row = self.conn.execute("SELECT 1 FROM seen_items WHERE item_id = ?", (item_id,)).fetchone()
        return row is not None

    def mark_seen(self, item: dict[str, Any]) -> None:
        item_id = str(item.get("item_id") or "")
        if not item_id:
            return
        self.conn.execute(
            """
            INSERT OR IGNORE INTO seen_items(item_id, title, price, keyword, item_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item_id,
                item.get("title", ""),
                item.get("price"),
                item.get("keyword", ""),
                json.dumps(item, ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT item_json FROM seen_items ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for row in rows:
            try:
                result.append(json.loads(row[0]))
            except Exception:
                continue
        return result
