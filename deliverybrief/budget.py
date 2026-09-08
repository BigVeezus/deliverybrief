"""Persistent conservative reservations. Unknown outcomes stay reserved."""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path


class BudgetLedger:
    def __init__(self, path: Path, limit_usd: float) -> None:
        if not math.isfinite(limit_usd) or limit_usd <= 0:
            raise ValueError("An explicit positive budget is required for paid requests.")
        self.path, self.limit = path, limit_usd
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, usd REAL)")

    def reserve(self, amount: float | None) -> None:
        if amount is None or not math.isfinite(amount) or amount <= 0:
            raise ValueError("Unknown pricing. Configure exact model rates before running.")
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            spent = float(
                db.execute("SELECT COALESCE(SUM(usd), 0) FROM reservations").fetchone()[0]
            )
            if spent + amount > self.limit:
                raise ValueError("Workflow budget exhausted. No request was sent.")
            db.execute("INSERT INTO reservations (usd) VALUES (?)", (amount,))

    @property
    def reserved(self) -> float:
        with sqlite3.connect(self.path) as db:
            return float(db.execute("SELECT COALESCE(SUM(usd), 0) FROM reservations").fetchone()[0])
