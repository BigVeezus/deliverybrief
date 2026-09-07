from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceType(StrEnum):
    GITHUB = "github"
    GOOGLE_DOC = "google_doc"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCK = "block"


class ApprovalStatus(StrEnum):
    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    APPROVED = "approved"


class ReportingPeriod(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def end_is_not_before_start(self) -> ReportingPeriod:
        if self.end < self.start:
            raise ValueError("Reporting period end must be on or after start")
        return self


class ProjectConfig(BaseModel):
    project_id: str = "demo"
    display_name: str = "Northstar Portal"
    client_label: str = "Client Northstar"
    github_repository: str = "deliverybrief/demo"
    google_drive_folder_id: str | None = None
    timezone: str = "Africa/Lagos"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_id: str
    source: SourceType
    title: str
    content: str
    occurred_at: datetime
    source_url: str | None = None
    author_alias: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportItem(BaseModel):
    text: str
    evidence_ids: list[str] = Field(min_length=1)


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    due_date: date | None = None
    evidence_ids: list[str] = Field(min_length=1)
    review_status: Literal["confirmed", "needs_review"] = "needs_review"


class WeeklyReport(BaseModel):
    project_name: str
    client_label: str
    period: ReportingPeriod
    executive_summary: str
    executive_summary_evidence_ids: list[str] = Field(min_length=1)
    completed: list[ReportItem] = Field(default_factory=list)
    in_progress: list[ReportItem] = Field(default_factory=list)
    blockers: list[ReportItem] = Field(default_factory=list)
    decisions: list[ReportItem] = Field(default_factory=list)
    next_priorities: list[ReportItem] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    source_limitations: list[str] = Field(default_factory=list)


class ValidationFinding(BaseModel):
    severity: FindingSeverity
    code: str
    message: str
    field_path: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class UsageRecord(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None


class GenerationResult(BaseModel):
    report: WeeklyReport
    model: str
    latency_ms: int
    usage: UsageRecord = Field(default_factory=UsageRecord)
    generator: Literal["anthropic", "demo"]


class RunRecord(BaseModel):
    run_id: str
    created_at: datetime
    project_id: str
    period: ReportingPeriod
    model: str
    generator: str
    evidence_count: int
    latency_ms: int
    usage: UsageRecord
    findings: list[ValidationFinding]
    status: ApprovalStatus
    approved_at: datetime | None = None
    edits_made: bool = False


class EvaluationResult(BaseModel):
    case_id: str
    model: str
    grounding: float
    coverage: float
    action_accuracy: float
    exception_handling: float
    safety_pass: bool
    passed: bool
    latency_ms: int
    estimated_cost_usd: float | None = None
    failure_reason: str | None = None


def report_items(report: WeeklyReport) -> list[tuple[str, int, ReportItem]]:
    rows: list[tuple[str, int, ReportItem]] = []
    for section in (
        "completed",
        "in_progress",
        "blockers",
        "decisions",
        "next_priorities",
    ):
        for index, item in enumerate(getattr(report, section)):
            rows.append((section, index, item))
    return rows
