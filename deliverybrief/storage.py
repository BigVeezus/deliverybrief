from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from deliverybrief.models import ApprovalStatus, RunRecord, WeeklyReport


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    approved_report_json TEXT
                )
                """
            )

    def save(self, record: RunRecord, report: WeeklyReport) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO runs
                (run_id, created_at, project_id, status, record_json, report_json,
                 approved_report_json)
                VALUES (?, ?, ?, ?, ?, ?,
                    COALESCE((SELECT approved_report_json FROM runs WHERE run_id = ?), NULL))
                """,
                (
                    record.run_id,
                    record.created_at.isoformat(),
                    record.project_id,
                    record.status.value,
                    record.model_dump_json(),
                    report.model_dump_json(),
                    record.run_id,
                ),
            )

    def approve(self, run_id: str, report: WeeklyReport, edits_made: bool) -> RunRecord:
        current = self.get(run_id)
        if current is None:
            raise KeyError(f"Run {run_id} does not exist")
        record, _ = current
        record.status = ApprovalStatus.APPROVED
        record.approved_at = datetime.now(UTC)
        record.edits_made = edits_made
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, record_json = ?, approved_report_json = ?
                WHERE run_id = ?
                """,
                (record.status.value, record.model_dump_json(), report.model_dump_json(), run_id),
            )
        return record

    def get(self, run_id: str) -> tuple[RunRecord, WeeklyReport] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        report_json = row["approved_report_json"] or row["report_json"]
        return RunRecord.model_validate_json(row["record_json"]), WeeklyReport.model_validate_json(
            report_json
        )

    def export_rows(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT run_id, created_at, project_id, status, record_json "
                "FROM runs ORDER BY created_at"
            ).fetchall()
        return [
            {
                "run_id": row["run_id"],
                "created_at": row["created_at"],
                "project_id": row["project_id"],
                "status": row["status"],
                "record": json.loads(row["record_json"]),
            }
            for row in rows
        ]
