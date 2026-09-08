from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from deliverybrief.intake import evidence_fingerprint, fingerprint
from deliverybrief.models import (
    ApprovalStatus,
    EvidenceItem,
    FindingSeverity,
    RunRecord,
    ValidationFinding,
    WeeklyReport,
)
from deliverybrief.validator import validate_report


class RunStore:
    def __init__(self, path: Path, session_id: str = "local-cli") -> None:
        self.path = path
        self.session_id = fingerprint(session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
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
        with self._connect() as connection:
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

    def approve(
        self,
        run_id: str,
        report: WeeklyReport,
        edits_made: bool,
        *,
        client_reviewed: bool = False,
        acknowledged: list[str] | None = None,
    ) -> RunRecord:
        current = self.get(run_id)
        if current is None:
            raise KeyError(f"Run {run_id} does not exist")
        record, _ = current
        evidence = self.evidence(run_id)
        if not evidence or not record.evidence_fingerprint:
            raise ValueError("Legacy run has no evidence snapshot. Collect and generate again.")
        report = WeeklyReport.model_validate_json(report.model_dump_json())
        if report.period != record.period:
            raise ValueError("Reporting period changed. Generate a new run.")
        findings = self.findings(run_id, report)
        if any(f.severity == FindingSeverity.BLOCK for f in findings):
            raise ValueError("Approval blocked. Resolve the evidence or report findings first.")
        required = {f.code for f in findings if f.severity == FindingSeverity.WARNING}
        if not required <= set(acknowledged or []):
            raise ValueError("Review and acknowledge all warnings before approval.")
        if not client_reviewed:
            raise ValueError("Review factual support and client suitability before approval.")
        record.findings = findings
        record.client_reviewed = True
        record.warning_acknowledgements = sorted(required)
        record.report_fingerprint = fingerprint(report.model_dump(mode="json"))
        record.status = ApprovalStatus.APPROVED
        record.approved_at = datetime.now(UTC)
        record.edits_made = edits_made
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, record_json = ?, approved_report_json = ?
                WHERE run_id = ? AND session_id = ?
                """,
                (
                    record.status.value,
                    record.model_dump_json(),
                    report.model_dump_json(),
                    run_id,
                    self.session_id,
                ),
            )
        return record

    def get(self, run_id: str) -> tuple[RunRecord, WeeklyReport] | None:
        with self._connect() as connection:
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
        with self._connect() as connection:
            row = connection.execute(
                "SELECT evidence_json FROM runs WHERE run_id = ? AND session_id = ?",
                (run_id, self.session_id),
            ).fetchone()
        return (
            [EvidenceItem.model_validate(i) for i in json.loads(row[0])] if row and row[0] else []
        )

    def resolve(self, run_id: str, evidence_ids: list[str], reason: str) -> None:
        evidence = self.evidence(run_id)
        if (
            len(reason.strip()) < 20
            or not evidence_ids
            or not set(evidence_ids) <= {i.evidence_id for i in evidence}
        ):
            raise ValueError("Explain the resolution and select supporting evidence from this run.")
        with self._connect() as connection:
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
        self.invalidate(run_id)

    def findings(self, run_id: str, report: WeeklyReport) -> list[ValidationFinding]:
        findings = validate_report(report, self.evidence(run_id))
        with self._connect() as connection:
            row = connection.execute(
                "SELECT resolutions_json FROM runs WHERE run_id = ? AND session_id = ?",
                (run_id, self.session_id),
            ).fetchone()
        resolution = json.loads(row[0]) if row and row[0] else None
        if resolution:
            for finding in findings:
                if finding.code == "SOURCE_CONFLICT" and set(finding.evidence_ids) <= set(
                    resolution["evidence_ids"]
                ):
                    finding.severity = FindingSeverity.WARNING
                    finding.code = "RESOLVED_CONFLICT"
                    finding.message = "Recorded human resolution: " + resolution["reason"]
        return findings

    def audit(self, run_id: str, event: str, detail: str) -> None:
        from deliverybrief.privacy import redact

        with self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_events(session_id,run_id,created_at,event,detail) "
                "VALUES(?,?,?,?,?)",
                (self.session_id, run_id, datetime.now(UTC).isoformat(), event, redact(detail)),
            )

    def invalidate(self, run_id: str) -> None:
        current = self.get(run_id)
        if current is None:
            raise KeyError("Run unavailable in this session")
        record, _ = current
        record.status = ApprovalStatus.REVIEW_REQUIRED
        record.approved_at = None
        record.client_reviewed = False
        with self._connect() as connection:
            connection.execute(
                "UPDATE runs SET status = ?, record_json = ?, approved_report_json = NULL "
                "WHERE run_id = ? AND session_id = ?",
                (record.status.value, record.model_dump_json(), run_id, self.session_id),
            )

    def approved_snapshot(
        self,
        run_id: str,
        report: WeeklyReport,
        evidence: list[EvidenceItem],
    ) -> WeeklyReport:
        current = self.get(run_id)
        if current is None:
            raise ValueError("Run unavailable in this session.")
        record, snapshot = current
        if (
            record.status != ApprovalStatus.APPROVED
            or not record.client_reviewed
            or record.report_fingerprint != fingerprint(report.model_dump(mode="json"))
            or record.evidence_fingerprint != evidence_fingerprint(evidence)
        ):
            if record.status == ApprovalStatus.APPROVED:
                self.invalidate(run_id)
            raise ValueError("Report or evidence changed. Review and approve again.")
        if any(f.severity == FindingSeverity.BLOCK for f in self.findings(run_id, snapshot)):
            self.invalidate(run_id)
            raise ValueError("Export blocked by current validation.")
        return snapshot

    def export_rows(self) -> list[dict[str, object]]:
        with self._connect() as connection:
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
