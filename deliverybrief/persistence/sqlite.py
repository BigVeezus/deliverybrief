from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from deliverybrief.intake import evidence_fingerprint, fingerprint
from deliverybrief.models import ApprovalStatus, EvidenceItem, RunRecord, WeeklyReport
from deliverybrief.privacy import redact


class SQLiteRunRepository:
    def __init__(self, path: Path, session_id: str = "local-cli") -> None:
        self.path = path
        self.session_id = fingerprint(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
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
            columns = {row[1] for row in connection.execute("PRAGMA table_info(runs)")}
            for name, declaration in {
                "session_id": "TEXT",
                "evidence_json": "TEXT",
                "resolutions_json": "TEXT",
            }.items():
                if name not in columns:
                    connection.execute(f"ALTER TABLE runs ADD COLUMN {name} {declaration}")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS audit_events (id INTEGER PRIMARY KEY, "
                "session_id TEXT, run_id TEXT, created_at TEXT, event TEXT, detail TEXT)"
            )

    def save(
        self,
        record: RunRecord,
        report: WeeklyReport,
        evidence: list[EvidenceItem] | None = None,
    ) -> None:
        record.evidence_fingerprint = (
            evidence_fingerprint(evidence) if evidence is not None else None
        )
        record.report_fingerprint = fingerprint(report.model_dump(mode="json"))
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO runs
                (run_id, created_at, project_id, status, record_json, report_json,
                 approved_report_json, session_id, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    record.run_id,
                    record.created_at.isoformat(),
                    record.project_id,
                    record.status.value,
                    record.model_dump_json(),
                    report.model_dump_json(),
                    self.session_id,
                    json.dumps([item.model_dump(mode="json") for item in evidence])
                    if evidence is not None
                    else None,
                ),
            )

    def get(self, run_id: str) -> tuple[RunRecord, WeeklyReport] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM runs WHERE run_id = ? AND (session_id = ? OR "
                "(session_id IS NULL AND ? = ?))",
                (run_id, self.session_id, self.session_id, fingerprint("local-cli")),
            ).fetchone()
        if row is None:
            return None
        report_json = row["approved_report_json"] or row["report_json"]
        return RunRecord.model_validate_json(row["record_json"]), WeeklyReport.model_validate_json(
            report_json
        )

    def evidence(self, run_id: str) -> list[EvidenceItem]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT evidence_json FROM runs WHERE run_id = ? AND session_id = ?",
                (run_id, self.session_id),
            ).fetchone()
        return (
            [EvidenceItem.model_validate(i) for i in json.loads(row[0])] if row and row[0] else []
        )

    def set_resolution(self, run_id: str, evidence_ids: list[str], reason: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE runs SET resolutions_json = ?, approved_report_json = NULL, status = ? "
                "WHERE run_id = ? AND session_id = ?",
                (
                    json.dumps(
                        {
                            "evidence_ids": evidence_ids,
                            "reason": reason,
                            "recorded_at": datetime.now(UTC).isoformat(),
                        }
                    ),
                    ApprovalStatus.REVIEW_REQUIRED.value,
                    run_id,
                    self.session_id,
                ),
            )

    def resolution(self, run_id: str) -> dict[str, object] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT resolutions_json FROM runs WHERE run_id = ? AND session_id = ?",
                (run_id, self.session_id),
            ).fetchone()
        return json.loads(row[0]) if row and row[0] else None

    def update_approval(
        self,
        run_id: str,
        record: RunRecord,
        report: WeeklyReport | None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, record_json = ?, approved_report_json = ?
                WHERE run_id = ? AND session_id = ?
                """,
                (
                    record.status.value,
                    record.model_dump_json(),
                    report.model_dump_json() if report else None,
                    run_id,
                    self.session_id,
                ),
            )

    def audit(self, run_id: str, event: str, detail: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO audit_events(session_id,run_id,created_at,event,detail) "
                "VALUES(?,?,?,?,?)",
                (self.session_id, run_id, datetime.now(UTC).isoformat(), event, redact(detail)),
            )

    def export_rows(self) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT run_id, created_at, project_id, status, record_json "
                "FROM runs WHERE session_id = ? ORDER BY created_at",
                (self.session_id,),
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
