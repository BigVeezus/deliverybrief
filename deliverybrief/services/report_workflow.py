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
    WorkflowTraceStep,
)
from deliverybrief.privacy import safe_evidence
from deliverybrief.storage import RunStore
from deliverybrief.validator import approval_status, validate_report

from .tracing import fail_step, finish_step, start_step


def generate_and_record(
    generator: ReportGenerator,
    store: RunStore,
    project: ProjectConfig,
    period: ReportingPeriod,
    evidence: list[EvidenceItem],
    trace: list[WorkflowTraceStep] | None = None,
) -> tuple[GenerationResult, RunRecord]:
    trace = list(trace or [])
    evidence, _ = scoped_evidence(evidence, project)
    evidence = safe_evidence(evidence)
    run_id = str(uuid4())
    generation_step = start_step(
        "generate_report",
        f"{generator.kind}_generator",
        "Generate a structured weekly report from normalized evidence.",
        input_count=len(evidence),
    )
    try:
        result = generator.generate(project, period, evidence)
    except Exception as error:
        trace.append(fail_step(generation_step, error))
        store.audit(run_id, "generation_failed", type(error).__name__)
        raise
    trace.append(
        finish_step(
            generation_step,
            output_count=1,
            attempts=result.attempts,
            metadata={
                "model": result.model,
                "estimated_cost_usd": result.usage.estimated_cost_usd,
            },
        )
    )
    validation_step = start_step(
        "validate_report",
        "deterministic_validator",
        "Check citations, dates, safety patterns, source limits, and action completeness.",
        input_count=len(evidence),
    )
    findings = validate_report(result.report, evidence)
    trace.append(
        finish_step(
            validation_step,
            output_count=len(findings),
            metadata={"finding_codes": [finding.code for finding in findings]},
        )
    )
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
        trace=trace,
    )
    store.save(record, result.report, evidence)
    store.audit(run_id, "generated", result.model)
    return result, record
