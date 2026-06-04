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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                price REAL,
                keyword TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._ensure_column("seen_items", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        cols = [row[1] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def has_seen(self, item_id: str) -> bool:
        if not item_id:
            return False
        row = self.conn.execute("SELECT 1 FROM seen_items WHERE item_id = ?", (item_id,)).fetchone()
        return row is not None

    def get_seen(self, item_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT item_json FROM seen_items WHERE item_id = ?", (item_id,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def mark_seen(self, item: dict[str, Any]) -> None:
        item_id = str(item.get("item_id") or "")
        if not item_id:
            return
        payload = json.dumps(item, ensure_ascii=False)
        self.conn.execute(
            """
            INSERT INTO seen_items(item_id, title, price, keyword, item_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                title = excluded.title,
                price = excluded.price,
                keyword = excluded.keyword,
                item_json = excluded.item_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                item_id,
                item.get("title", ""),
                item.get("price"),
                item.get("keyword", ""),
                payload,
            ),
        )
        self.conn.commit()

    def record_price(self, item: dict[str, Any]) -> float | None:
        item_id = str(item.get("item_id") or "")
        price = item.get("price")
        if not item_id or price in (None, ""):
            return None
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            return None

        self.conn.execute(
            """
            INSERT INTO price_history(item_id, price, keyword, title)
            VALUES (?, ?, ?, ?)
            """,
            (item_id, price_value, item.get("keyword", ""), item.get("title", "")),
        )
        self.conn.commit()
        return price_value

    def previous_price(self, item_id: str) -> float | None:
        row = self.conn.execute(
            """
            SELECT price FROM price_history
            WHERE item_id = ? AND price IS NOT NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (item_id,),
        ).fetchone()
        if not row:
            return None
        try:
            return float(row[0])
        except (TypeError, ValueError):
            return None

    def price_history(self, item_id: str, limit: int = 30) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT price, keyword, title, created_at FROM price_history
            WHERE item_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (item_id, limit),
        ).fetchall()
        return [
            {"price": row[0], "keyword": row[1], "title": row[2], "created_at": row[3]}
            for row in rows
        ]

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT item_json FROM seen_items ORDER BY updated_at DESC, created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for row in rows:
            try:
                result.append(json.loads(row[0]))
            except Exception:
                continue
        return result
