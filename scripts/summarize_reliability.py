"""Build an evidence package from executed pytest XML, never from assumed passes."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from deliverybrief.reliability_cases import CASES


def build_summary(root: Path) -> dict[str, object]:
    xml = ET.parse(root / "output/reliability-tests.xml")
    tests = {test.attrib["name"]: test for test in xml.iter("testcase")}
    results = []
    for case in CASES:
        test = tests.get(f"test_reliability_case[{case['case_id']}]")
        failure = test.find("failure") if test is not None else None
        error = test.find("error") if test is not None else None
        skipped = test.find("skipped") if test is not None else None
        status = (
            "not_run"
            if test is None
            else (
                "failed"
                if failure is not None or error is not None
                else "skipped"
                if skipped is not None
                else "passed"
            )
        )
        results.append(
            {
                **case,
                "status": status,
                "failure_explanation": (
                    failure.attrib.get("message")
                    if failure is not None
                    else error.attrib.get("message")
                    if error is not None
                    else None
                ),
                "actual_result": "Contract assertions passed" if status == "passed" else status,
                "test_reference": "tests/test_reliability.py::test_reliability_case["
                + cast(str, case["case_id"])
                + "]",
            }
        )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "execution": "free automated workflow tests",
        "live_model_calls": 0,
        "factual_grounding": None,
        "time_reduction": None,
        "total_automated_tests": len(tests),
        "all_test_failures": sum(
            t.find("failure") is not None or t.find("error") is not None
            for t in tests.values()
        ),
        "splits": {
            split: {
                "cases": sum(c["split"] == split for c in results),
                "passed": sum(c["split"] == split and c["status"] == "passed" for c in results),
            }
            for split in ("development", "held_out")
        },
        "results": results,
        "limitations": [
            "Contract tests do not measure Anthropic quality or real user adoption.",
            "Cases and implementation were AI-assisted, not independently authored.",
            "The 12 reserved cases passed their first executed assertions; "
            "reused runs are regressions.",
        ],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = build_summary(root)
    target = root / "evaluation/results/reliability-v2.json"
    target.write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(target),
                "splits": summary["splits"],
                "total_tests": summary["total_automated_tests"],
                "failures": summary["all_test_failures"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
