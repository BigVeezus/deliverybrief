from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from deliverybrief.generator import ReportGenerator
from deliverybrief.models import (
    EvidenceItem,
    GenerationResult,
    ProjectConfig,
    ReportingPeriod,
    RunRecord,
)
from deliverybrief.storage import RunStore
from deliverybrief.validator import approval_status, validate_report


def generate_and_record(
    generator: ReportGenerator,
    store: RunStore,
    project: ProjectConfig,
    period: ReportingPeriod,
    evidence: list[EvidenceItem],
) -> tuple[GenerationResult, RunRecord]:
    result = generator.generate(project, period, evidence)
    findings = validate_report(result.report, evidence)
    record = RunRecord(
        run_id=str(uuid4()),
        created_at=datetime.now(UTC),
        project_id=project.project_id,
        period=period,
        model=result.model,
        generator=result.generator,
        evidence_count=len(evidence),
        latency_ms=result.latency_ms,
        usage=result.usage,
        findings=findings,
        status=approval_status(findings),
    )
    store.save(record, result.report)
    return result, record
