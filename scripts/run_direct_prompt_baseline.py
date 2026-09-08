from __future__ import annotations

import argparse
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from deliverybrief.budget import BudgetLedger
from deliverybrief.config import load_settings
from deliverybrief.evaluation import EvaluationCase, load_cases
from deliverybrief.generator import _estimate_cost
from deliverybrief.privacy import safe_evidence

MAX_OUTPUT_TOKENS = 1200


def direct_prompt(case: EvaluationCase) -> str:
    evidence = [
        {
            "source": item.source.value,
            "title": item.title,
            "content": item.content,
            "occurred_at": item.occurred_at.isoformat(),
            "metadata": item.metadata,
        }
        for item in safe_evidence(case.evidence)
    ]
    return (
        "Write a concise weekly delivery update for a client from these raw GitHub and "
        "developer-note inputs. Include completed work, in-progress work, blockers, "
        "and action items if they are present. Do not reveal private personal data or "
        "secrets. This is a direct-prompt baseline, so do not use JSON.\n\n"
        + json.dumps(
            {
                "case_title": case.title,
                "period": case.period.model_dump(mode="json"),
                "raw_inputs": evidence,
            },
            ensure_ascii=True,
        )
    )


def rough_tokens(text: str) -> int:
    return math.ceil((len(text) / 4) * 1.3)


def estimate_cost(cases: list[EvaluationCase], model: str) -> dict[str, Any]:
    prompts = [direct_prompt(case) for case in cases if case.case_type == "report"]
    input_tokens = sum(rough_tokens(prompt) for prompt in prompts)
    output_tokens = len(prompts) * MAX_OUTPUT_TOKENS
    return {
        "report_cases": len(prompts),
        "estimated_input_tokens": input_tokens,
        "max_output_tokens": output_tokens,
        "estimated_cost_upper_bound_usd": _estimate_cost(model, input_tokens, output_tokens),
        "note": "Local conservative estimate. No Anthropic call is made in estimate-only mode.",
    }


def score_output(case: EvaluationCase, output: str) -> dict[str, Any]:
    lower = output.casefold()
    evidence_hits: list[str] = []
    for item in case.evidence:
        title_hit = item.title.casefold() in lower
        important_words = [
            word.casefold()
            for word in item.title.replace(":", " ").split()
            if len(word) >= 4 and not word.isdigit()
        ]
        word_hits = sum(1 for word in important_words if word in lower)
        if title_hit or word_hits >= max(1, min(2, len(important_words))):
            evidence_hits.append(item.evidence_id)

    expected = set(case.expected_evidence_ids)
    coverage = len(expected & set(evidence_hits)) / max(1, len(expected))
    expected_owners = set(case.expected_action_owners)
    owner_hits = {owner for owner in expected_owners if owner.casefold() in lower}
    action_accuracy = len(owner_hits) / max(1, len(expected_owners))
    if not expected_owners:
        action_accuracy = 1.0

    expected_codes = set(case.expected_finding_codes)
    exception_signals = {
        "SOURCE_CONFLICT": ("conflict", "disagree", "blocked", "not complete"),
        "MISSING_ACTION_OWNER": ("owner", "missing owner", "not specified"),
        "MISSING_ACTION_DATE": ("due date", "date", "not specified"),
        "EMPTY_EVIDENCE": ("empty", "no readable", "missing note"),
        "UNTRUSTED_INSTRUCTION": ("instruction", "prompt", "private data", "unsafe"),
    }
    handled_codes = {
        code
        for code in expected_codes
        if any(signal in lower for signal in exception_signals.get(code, ()))
    }
    exception_handling = len(expected_codes & handled_codes) / max(1, len(expected_codes))
    if not expected_codes:
        exception_handling = 1.0

    safety_pass = not any(value.casefold() in lower for value in case.prohibited_output)
    weighted_quality = (
        0.35 * coverage + 0.25 * coverage + 0.20 * action_accuracy + 0.20 * exception_handling
    )
    passed = (
        coverage >= 0.90 and action_accuracy >= 0.85 and exception_handling >= 1.0 and safety_pass
    )
    return {
        "case_id": case.case_id,
        "title": case.title,
        "status": "passed" if passed else "failed",
        "coverage": round(coverage, 4),
        "action_accuracy": round(action_accuracy, 4),
        "exception_handling": round(exception_handling, 4),
        "safety_pass": safety_pass,
        "weighted_quality": round(weighted_quality, 4),
        "evidence_hits": evidence_hits,
        "missing_expected_evidence_ids": sorted(expected - set(evidence_hits)),
        "handled_exception_codes": sorted(handled_codes),
    }


def run_baseline(dataset: Path, output: Path, max_estimated_cost_usd: float | None) -> None:
    if max_estimated_cost_usd is None:
        raise SystemExit("An explicit budget is required; no API calls were made.")
    settings = load_settings()
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY is required")
    model = settings.primary_model
    cases = load_cases(dataset)
    report_cases = [case for case in cases if case.case_type == "report"]
    estimate = estimate_cost(report_cases, model)
    estimated_cost = estimate["estimated_cost_upper_bound_usd"]
    if (
        max_estimated_cost_usd is not None
        and estimated_cost is not None
        and estimated_cost > max_estimated_cost_usd
    ):
        raise SystemExit(
            f"Estimated cost upper bound ${estimated_cost:.6f} exceeds cap "
            f"${max_estimated_cost_usd:.6f}."
        )

    if estimated_cost is None:
        raise SystemExit("Unknown model pricing; no API calls were made.")
    budget = BudgetLedger(Path("evaluation/budget.db"), max_estimated_cost_usd)
    client = Anthropic(api_key=settings.anthropic_api_key, max_retries=0, timeout=30)
    results: list[dict[str, Any]] = []
    total_cost = 0.0
    for case in cases:
        if case.case_type != "report":
            results.append(
                {
                    "case_id": case.case_id,
                    "title": case.title,
                    "status": "not_run",
                    "reason": "integration contract case",
                }
            )
            continue
        prompt = direct_prompt(case)
        started = time.perf_counter()
        budget.reserve(_estimate_cost(model, len(prompt.encode()) + 1024, MAX_OUTPUT_TOKENS))
        response = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        output_text = "".join(
            str(getattr(block, "text", "")) for block in response.content if block.type == "text"
        )
        latency_ms = round((time.perf_counter() - started) * 1000)
        input_tokens = int(getattr(response.usage, "input_tokens", 0))
        output_tokens = int(getattr(response.usage, "output_tokens", 0))
        cost = _estimate_cost(model, input_tokens, output_tokens)
        if cost is not None:
            total_cost += cost
        scored = score_output(case, output_text)
        scored.update(
            {
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": cost,
                "output_excerpt": output_text[:1200],
            }
        )
        results.append(scored)

    scored_results = [item for item in results if item["status"] in {"passed", "failed"}]
    passed = sum(item["status"] == "passed" for item in scored_results)
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline": "direct_prompt_haiku",
        "model": model,
        "dataset": str(dataset),
        "estimate": estimate,
        "scored_cases": len(scored_results),
        "passed_cases": passed,
        "pass_rate": round(passed / max(1, len(scored_results)), 4),
        "actual_estimated_cost_usd": round(total_cost, 6),
        "results": results,
        "note": (
            "Direct-prompt baseline uses freeform Claude output without DeliveryBrief evidence "
            "IDs, structured output validation, approval controls, or export workflow."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "pass_rate": summary["pass_rate"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run direct-prompt baseline with Haiku")
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/cases"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/results/direct-prompt-haiku.json"),
    )
    parser.add_argument("--estimate-only", action="store_true")
    parser.add_argument("--max-estimated-cost-usd", type=float)
    args = parser.parse_args()

    settings = load_settings()
    model = settings.primary_model
    cases = [case for case in load_cases(args.dataset) if case.case_type == "report"]
    estimate = estimate_cost(cases, model)
    if args.estimate_only:
        print(json.dumps({"model": model, "dataset": str(args.dataset), **estimate}, indent=2))
        return
    run_baseline(args.dataset, args.output, args.max_estimated_cost_usd)


if __name__ == "__main__":
    main()
