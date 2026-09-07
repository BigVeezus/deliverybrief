from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from deliverybrief.config import load_settings
from deliverybrief.generator import AnthropicReportGenerator, DemoReportGenerator
from deliverybrief.models import (
    EvidenceItem,
    ProjectConfig,
    ReportingPeriod,
    WeeklyReport,
    report_items,
)
from deliverybrief.validator import validate_report


class EvaluationCase(BaseModel):
    case_id: str
    title: str
    case_type: str = "report"
    period: ReportingPeriod
    evidence: list[EvidenceItem] = Field(default_factory=list)
    expected_evidence_ids: list[str] = Field(default_factory=list)
    expected_finding_codes: list[str] = Field(default_factory=list)
    expected_action_owners: list[str] = Field(default_factory=list)
    prohibited_output: list[str] = Field(default_factory=list)
    test_reference: str | None = None


def evaluate_report(
    case: EvaluationCase,
    report: WeeklyReport,
    findings: list[Any],
    latency_ms: int,
    estimated_cost_usd: float | None,
) -> dict[str, Any]:
    valid_ids = {item.evidence_id for item in case.evidence}
    used_ids = set(report.executive_summary_evidence_ids)
    substantive_ids: set[str] = set()
    citation_count = len(report.executive_summary_evidence_ids)
    for _, _, item in report_items(report):
        used_ids.update(item.evidence_ids)
        substantive_ids.update(item.evidence_ids)
        citation_count += len(item.evidence_ids)
    for action in report.action_items:
        used_ids.update(action.evidence_ids)
        substantive_ids.update(action.evidence_ids)
        citation_count += len(action.evidence_ids)
    valid_citations = sum(1 for item in used_ids if item in valid_ids)
    grounding = valid_citations / max(1, len(used_ids))
    expected = set(case.expected_evidence_ids)
    coverage = len(expected & substantive_ids) / max(1, len(expected))

    owners = {item.owner for item in report.action_items if item.owner}
    expected_owners = set(case.expected_action_owners)
    action_accuracy = len(expected_owners & owners) / max(1, len(expected_owners))
    if not expected_owners:
        action_accuracy = 1.0

    actual_codes = {item.code for item in findings}
    expected_codes = set(case.expected_finding_codes)
    exception_handling = len(expected_codes & actual_codes) / max(1, len(expected_codes))
    if not expected_codes:
        exception_handling = 1.0

    output = report.model_dump_json().casefold()
    safety_pass = not any(value.casefold() in output for value in case.prohibited_output)
    weighted = (
        0.35 * grounding + 0.25 * coverage + 0.20 * action_accuracy + 0.20 * exception_handling
    )
    passed = (
        grounding >= 0.95
        and coverage >= 0.90
        and action_accuracy >= 0.85
        and exception_handling >= 1.0
        and safety_pass
    )
    return {
        "case_id": case.case_id,
        "title": case.title,
        "status": "passed" if passed else "failed",
        "grounding": round(grounding, 4),
        "coverage": round(coverage, 4),
        "action_accuracy": round(action_accuracy, 4),
        "exception_handling": round(exception_handling, 4),
        "safety_pass": safety_pass,
        "weighted_quality": round(weighted, 4),
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost_usd,
        "citation_count": citation_count,
        "finding_codes": sorted(actual_codes),
    }


def load_cases(dataset: Path) -> list[EvaluationCase]:
    source = dataset / "cases.json" if dataset.is_dir() else dataset
    return [EvaluationCase.model_validate(item) for item in json.loads(source.read_text())]


def run_evaluation(dataset: Path, model_choice: str) -> dict[str, Any]:
    settings = load_settings()
    cases = load_cases(dataset)
    if model_choice == "demo":
        generator: Any = DemoReportGenerator()
    else:
        if not settings.anthropic_api_key:
            raise SystemExit("ANTHROPIC_API_KEY is required for primary or quality evaluation")
        model = settings.primary_model if model_choice == "primary" else settings.quality_model
        generator = AnthropicReportGenerator(settings.anthropic_api_key, model)

    results: list[dict[str, Any]] = []
    project = ProjectConfig()
    for case in cases:
        if case.case_type != "report":
            results.append(
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "status": "covered_by_test",
                    "test_reference": case.test_reference,
                }
            )
            continue
        try:
            generated = generator.generate(project, case.period, case.evidence)
            findings = validate_report(generated.report, case.evidence)
            results.append(
                evaluate_report(
                    case,
                    generated.report,
                    findings,
                    generated.latency_ms,
                    generated.usage.estimated_cost_usd,
                )
            )
        except Exception as error:
            results.append(
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "status": "error",
                    "error": str(error),
                }
            )

    scored = [item for item in results if item["status"] in {"passed", "failed"}]
    passed = sum(item["status"] == "passed" for item in scored)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "model_choice": model_choice,
        "model": getattr(generator, "model", "unknown"),
        "dataset": str(dataset),
        "scored_cases": len(scored),
        "passed_cases": passed,
        "pass_rate": round(passed / max(1, len(scored)), 4),
        "results": results,
        "note": "This file records an executed run. It does not contain user-observation metrics.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DeliveryBrief against its case set")
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/cases"))
    parser.add_argument("--model", choices=["demo", "primary", "quality"], default="demo")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = run_evaluation(args.dataset, args.model)
    output = args.output
    if output is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = Path("evaluation/results") / f"{stamp}-{args.model}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "pass_rate": summary["pass_rate"]}, indent=2))


if __name__ == "__main__":
    main()
