from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from deliverybrief.intake import evidence_fingerprint, fingerprint
from deliverybrief.models import (
    ApprovalStatus,
    EvidenceItem,
    FindingSeverity,
    RunRecord,
    ValidationFinding,
    WeeklyReport,
    WorkflowTraceStep,
)
from deliverybrief.persistence import SQLiteRunRepository
from deliverybrief.services.tracing import fail_step, finish_step, instant_step, start_step
from deliverybrief.validator import validate_report


class ApprovalService:
    """Coordinates approval rules over stored report and evidence snapshots."""

    def __init__(self, path: Path, session_id: str = "local-cli") -> None:
        self.repository = SQLiteRunRepository(path, session_id)

    @property
    def path(self) -> Path:
        return self.repository.path

    @property
    def session_id(self) -> str:
        return self.repository.session_id

    def save(
        self,
        record: RunRecord,
        report: WeeklyReport,
        evidence: list[EvidenceItem] | None = None,
    ) -> None:
        self.repository.save(record, report, evidence)

    def get(self, run_id: str) -> tuple[RunRecord, WeeklyReport] | None:
        return self.repository.get(run_id)

    def evidence(self, run_id: str) -> list[EvidenceItem]:
        return self.repository.evidence(run_id)

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
        step = start_step(
            "approve_report",
            "approval_service",
            "Revalidate the stored evidence snapshot before approval.",
            input_count=len(evidence),
            metadata={"warnings": sorted(required)},
        )
        record.findings = findings
        record.client_reviewed = True
        record.warning_acknowledgements = sorted(required)
        record.report_fingerprint = fingerprint(report.model_dump(mode="json"))
        record.status = ApprovalStatus.APPROVED
        record.approved_at = datetime.now(UTC)
        record.edits_made = edits_made
        record.trace.append(
            finish_step(
                step,
                output_count=1,
                metadata={"edits_made": edits_made, "acknowledged": sorted(required)},
            )
        )
        self.repository.update_approval(run_id, record, report)
        return record

    def resolve(self, run_id: str, evidence_ids: list[str], reason: str) -> None:
        evidence = self.evidence(run_id)
        if (
            len(reason.strip()) < 20
            or not evidence_ids
            or not set(evidence_ids) <= {i.evidence_id for i in evidence}
        ):
            raise ValueError("Explain the resolution and select supporting evidence from this run.")
        self.repository.set_resolution(run_id, evidence_ids, reason)
        current = self.get(run_id)
        if current:
            record, _ = current
            record.trace.append(
                instant_step(
                    "resolve_conflict",
                    "approval_service",
                    "success",
                    "Human resolution recorded with supporting evidence.",
                    input_count=len(evidence_ids),
                    output_count=1,
                )
            )
            self.repository.update_record(run_id, record)
        self.invalidate(run_id)

    def findings(self, run_id: str, report: WeeklyReport) -> list[ValidationFinding]:
        findings = validate_report(report, self.evidence(run_id))
        resolution = self.repository.resolution(run_id)
        if resolution:
            resolved_ids = set(cast(list[str], resolution["evidence_ids"]))
            for finding in findings:
                if finding.code == "SOURCE_CONFLICT" and set(finding.evidence_ids) <= resolved_ids:
                    finding.severity = FindingSeverity.WARNING
                    finding.code = "RESOLVED_CONFLICT"
                    finding.message = "Recorded human resolution: " + str(resolution["reason"])
        return findings

    def audit(self, run_id: str, event: str, detail: str) -> None:
        self.repository.audit(run_id, event, detail)

    def invalidate(self, run_id: str) -> None:
        current = self.get(run_id)
        if current is None:
            raise KeyError("Run unavailable in this session")
        record, _ = current
        record.status = ApprovalStatus.REVIEW_REQUIRED
        record.approved_at = None
        record.client_reviewed = False
        record.trace.append(
            instant_step(
                "invalidate_approval",
                "approval_service",
                "success",
                "Approval was cleared because the report, evidence, or resolution changed.",
                output_count=1,
            )
        )
        self.repository.update_approval(run_id, record, None)

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
            step = start_step(
                "check_approved_snapshot",
                "approval_service",
                "Confirm report and evidence fingerprints before export.",
                input_count=len(evidence),
            )
            if record.status == ApprovalStatus.APPROVED:
                self.invalidate(run_id)
                current = self.get(run_id)
                if current:
                    current_record, _ = current
                    current_record.trace.append(
                        fail_step(
                            step,
                            "Report or evidence changed. Review and approve again.",
                            status="blocked",
                        )
                    )
                    self.repository.update_record(run_id, current_record)
            raise ValueError("Report or evidence changed. Review and approve again.")
        if any(f.severity == FindingSeverity.BLOCK for f in self.findings(run_id, snapshot)):
            self.invalidate(run_id)
            raise ValueError("Export blocked by current validation.")
        return snapshot

    def append_trace(self, run_id: str, step: WorkflowTraceStep) -> None:
        current = self.get(run_id)
        if current is None:
            raise KeyError("Run unavailable in this session")
        record, _ = current
        record.trace.append(step)
        self.repository.update_record(run_id, record)

    def export_rows(self) -> list[dict[str, object]]:
        return self.repository.export_rows()
