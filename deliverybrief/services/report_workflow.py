from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from deliverybrief.generation import ReportGenerator
from deliverybrief.intake import scoped_evidence
from deliverybrief.models import (
    EvidenceItem,
    GenerationResult,
    ProjectConfig,
    ReportingPeriod,
    RunRecord,
)
from deliverybrief.privacy import safe_evidence
from deliverybrief.storage import RunStore
from deliverybrief.validator import approval_status, validate_report


def generate_and_record(
    generator: ReportGenerator,
    store: RunStore,
    project: ProjectConfig,
    period: ReportingPeriod,
    evidence: list[EvidenceItem],
) -> tuple[GenerationResult, RunRecord]:
    evidence, _ = scoped_evidence(evidence, project)
    evidence = safe_evidence(evidence)
    run_id = str(uuid4())
    try:
        result = generator.generate(project, period, evidence)
    except Exception as error:
        store.audit(run_id, "generation_failed", type(error).__name__)
        raise
    findings = validate_report(result.report, evidence)
    record = RunRecord(
        run_id=run_id,
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
        attempts=result.attempts,
    )
    store.save(record, result.report, evidence)
    store.audit(run_id, "generated", result.model)
    return result, record
