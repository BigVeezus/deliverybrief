from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from deliverybrief.budget import BudgetLedger
from deliverybrief.config import load_settings
from deliverybrief.generator import (
    AnthropicReportGenerator,
    DemoReportGenerator,
    estimate_generation_cost,
)
from deliverybrief.intake import fingerprint
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
    provenance: str = "legacy fixture; provenance requires review"
    split: str = "development"
    expected_facts: list[str] = Field(default_factory=list)
    expected_actions: list[dict[str, str | None]] = Field(default_factory=list)
    expected_blocked: bool = False


def evaluate_report_legacy(
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
    handled_ids = set(substantive_ids)
    for finding in findings:
        handled_ids.update(finding.evidence_ids)
    coverage = len(expected & handled_ids) / max(1, len(expected))
    missing_expected_ids = sorted(expected - handled_ids)

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
        "metric_version": "v1-citation-proxy",
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
        "used_evidence_ids": sorted(used_ids),
        "missing_expected_evidence_ids": missing_expected_ids,
        "finding_codes": sorted(actual_codes),
    }


def evaluate_report(
    case: EvaluationCase,
    report: WeeklyReport,
    findings: list[Any],
    latency_ms: int,
    estimated_cost_usd: float | None,
    review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Never infer semantic support from citation presence or string overlap."""
    proxy = evaluate_report_legacy(case, report, findings, latency_ms, estimated_cost_usd)
    claims: list[dict[str, Any]] = [
        {"text": report.executive_summary, "evidence_ids": report.executive_summary_evidence_ids}
    ]
    claims.extend(
        {"text": item.text, "evidence_ids": item.evidence_ids}
        for _, _, item in report_items(report)
    )
    claims.extend(
        {
            "text": item.task,
            "owner": item.owner,
            "due_date": str(item.due_date) if item.due_date else None,
            "evidence_ids": item.evidence_ids,
        }
        for item in report.action_items
    )
    digest = fingerprint(report.model_dump(mode="json"))
    blocked = any(f.severity.value == "block" for f in findings)
    result: dict[str, Any] = {
        "metric_version": "v2-human-reviewed",
        "case_id": case.case_id,
        "split": case.split,
        "provenance": case.provenance,
        "status": "awaiting_review",
        "citation_validity": proxy["grounding"],
        "factual_grounding": None,
        "coverage": None,
        "action_accuracy": None,
        "safety_pass": proxy["safety_pass"],
        "correct_blocking": blocked == case.expected_blocked,
        "unnecessary_blocking": blocked and not case.expected_blocked,
        "latency_ms": latency_ms,
        "estimated_cost_usd": estimated_cost_usd,
        "report_fingerprint": digest,
        "report": report.model_dump(mode="json"),
        "claims_for_review": claims,
        "expected_facts": case.expected_facts,
        "expected_actions": case.expected_actions,
        "review_instructions": "I must review every claim, fact and action against evidence. "
        "A reviewer name and this exact report fingerprint are required.",
    }
    if review is None:
        return result
    if review.get("report_fingerprint") != digest or not review.get("reviewer"):
        raise ValueError("Review must identify its reviewer and exact report fingerprint.")
    supported = review.get("supported_claims", [])
    covered = review.get("covered_facts", [])
    matched = review.get("matched_actions", [])
    if (
        len(supported) != len(claims)
        or len(covered) != len(case.expected_facts)
        or any(type(value) is not bool for value in supported + covered)
    ):
        raise ValueError("Review every claim and every expected fact with true or false.")
    # One-to-one human verified mappings prevent extra actions inflating recall.
    if any(not isinstance(pair, list) or len(pair) != 2 for pair in matched):
        raise ValueError("Action matches must be [output_index, expected_index] pairs.")
    left, right = [p[0] for p in matched], [p[1] for p in matched]
    if (
        len(set(left)) != len(left)
        or len(set(right)) != len(right)
        or any(type(i) is not int or not 0 <= i < len(report.action_items) for i in left)
        or any(type(i) is not int or not 0 <= i < len(case.expected_actions) for i in right)
    ):
        raise ValueError("Action review requires unique valid output and expected indices.")
    grounding = sum(supported) / max(1, len(supported))
    coverage = sum(covered) / len(covered) if covered else 1.0
    denominator = len(report.action_items) + len(case.expected_actions)
    accuracy = 2 * len(matched) / denominator if denominator else 1.0
    result.update(
        factual_grounding=grounding,
        coverage=coverage,
        action_accuracy=accuracy,
        reviewer=review["reviewer"],
        weighted_quality=(
            0.35 * grounding
            + 0.25 * coverage
            + 0.20 * accuracy
            + 0.20 * float(blocked == case.expected_blocked)
        ),
    )
    result["status"] = (
        "passed"
        if (
            grounding >= 0.95
            and coverage >= 0.9
            and accuracy >= 0.85
            and result["citation_validity"] >= 0.95
            and result["safety_pass"]
            and result["correct_blocking"]
        )
        else "failed"
    )
    return result


def load_cases(dataset: Path) -> list[EvaluationCase]:
    source = dataset / "cases.json" if dataset.is_dir() else dataset
    return [EvaluationCase.model_validate(item) for item in json.loads(source.read_text())]


def run_evaluation(
    dataset: Path,
    model_choice: str,
    budget: BudgetLedger | None = None,
) -> dict[str, Any]:
    settings = load_settings()
    cases = load_cases(dataset)
    if model_choice == "demo":
        generator: Any = DemoReportGenerator()
    else:
        if not settings.anthropic_api_key:
            raise SystemExit("ANTHROPIC_API_KEY is required for primary or quality evaluation")
        model = settings.primary_model if model_choice == "primary" else settings.quality_model
        if budget is None:
            raise ValueError("Paid evaluation requires an explicit budget.")
        generator = AnthropicReportGenerator(settings.anthropic_api_key, model, budget)

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
                    "error": type(error).__name__,
                }
            )

    scored = [item for item in results if item["status"] != "covered_by_test"]
    passed = sum(item["status"] == "passed" for item in scored)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "model_choice": model_choice,
        "metric_version": "v2-human-reviewed",
        "execution_type": "deterministic_simulation"
        if model_choice == "demo"
        else "live_anthropic",
        "awaiting_review": sum(i["status"] == "awaiting_review" for i in results),
        "model": getattr(generator, "model", "unknown"),
        "dataset": str(dataset),
        "scored_cases": len(scored),
        "passed_cases": passed,
        "pass_rate": round(passed / max(1, len(scored)), 4),
        "results": results,
        "note": "This file records an executed run. It does not contain user-observation metrics.",
    }


def estimate_evaluation_cost(dataset: Path, model_choice: str) -> dict[str, Any]:
    settings = load_settings()
    cases = [case for case in load_cases(dataset) if case.case_type == "report"]
    project = ProjectConfig()
    if model_choice == "demo":
        model = "deterministic-demo-v1"
    else:
        model = settings.primary_model if model_choice == "primary" else settings.quality_model

    estimates = [
        estimate_generation_cost(model, project, case.period, case.evidence) for case in cases
    ]
    input_tokens = sum(item.input_tokens for item in estimates)
    output_tokens = sum(item.output_tokens for item in estimates)
    estimated_costs = [item.estimated_cost_usd for item in estimates]
    total_cost = (
        round(3 * sum(cost for cost in estimated_costs if cost is not None), 6)
        if all(cost is not None for cost in estimated_costs)
        else None
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "model_choice": model_choice,
        "model": model,
        "dataset": str(dataset),
        "report_cases": len(cases),
        "estimated_input_tokens": input_tokens,
        "max_output_tokens": output_tokens,
        "estimated_cost_upper_bound_usd": total_cost,
        "note": (
            "This is a local conservative estimate. It makes no Anthropic API call and assumes "
            "each report uses max output tokens and all three reserved attempts. "
            "This application estimate is not a provider-wide billing guarantee."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DeliveryBrief against its case set")
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/cases"))
    parser.add_argument("--model", choices=["demo", "primary", "quality"], default="demo")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        help="Estimate maximum Anthropic cost locally without making API calls.",
    )
    parser.add_argument(
        "--max-estimated-cost-usd",
        type=float,
        help="Abort before model calls if the local cost estimate exceeds this amount.",
    )
    args = parser.parse_args()
    if args.estimate_only:
        estimate = estimate_evaluation_cost(args.dataset, args.model)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(estimate, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(estimate, indent=2))
        return

    if args.model != "demo" and args.max_estimated_cost_usd is None:
        raise SystemExit("Paid evaluation requires --max-estimated-cost-usd; no calls made.")
    if args.max_estimated_cost_usd is not None:
        estimate = estimate_evaluation_cost(args.dataset, args.model)
        estimated_cost = estimate["estimated_cost_upper_bound_usd"]
        if estimated_cost is None or estimated_cost > args.max_estimated_cost_usd:
            raise SystemExit(
                "Estimated cost upper bound "
                f"{estimated_cost} is unknown or exceeds cap ${args.max_estimated_cost_usd:.6f}. "
                "Run with a higher cap only if I approve it."
            )

    budget = (
        BudgetLedger(Path("evaluation/budget.db"), args.max_estimated_cost_usd)
        if args.model != "demo"
        else None
    )
    summary = run_evaluation(args.dataset, args.model, budget)
    output = args.output
    if output is None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = Path("evaluation/results") / f"{stamp}-{args.model}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "pass_rate": summary["pass_rate"]}, indent=2))


if __name__ == "__main__":
    main()
