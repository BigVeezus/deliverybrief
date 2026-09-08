"""Score saved reports using explicit human reviews. Makes no provider requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deliverybrief.evaluation import evaluate_report, load_cases
from deliverybrief.models import WeeklyReport
from deliverybrief.validator import validate_report

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run", type=Path, required=True)
parser.add_argument("--reviews", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
run = json.loads(args.run.read_text())
reviews = json.loads(args.reviews.read_text())
cases = {case.case_id: case for case in load_cases(Path(run["dataset"]))}
for row in run["results"]:
    if row.get("case_id") not in reviews:
        continue
    case = cases[row["case_id"]]
    report = WeeklyReport.model_validate(row["report"])
    row.update(
        evaluate_report(
            case,
            report,
            validate_report(report, case.evidence),
            row["latency_ms"],
            row["estimated_cost_usd"],
            reviews[case.case_id],
        )
    )
run["passed_cases"] = sum(r["status"] == "passed" for r in run["results"])
run["awaiting_review"] = sum(r["status"] == "awaiting_review" for r in run["results"])
run["pass_rate"] = run["passed_cases"] / max(1, run["scored_cases"])
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(run, indent=2) + "\n")
print(f"Saved reviewed scores to {args.output}; no model calls made.")
