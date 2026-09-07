from pathlib import Path

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.evaluation import estimate_evaluation_cost, load_cases, run_evaluation
from deliverybrief.generator import DemoReportGenerator
from deliverybrief.models import ProjectConfig
from deliverybrief.storage import RunStore
from deliverybrief.workflow import generate_and_record


def test_evaluation_dataset_and_demo_run() -> None:
    cases = load_cases(Path("evaluation/cases"))
    summary = run_evaluation(Path("evaluation/cases"), "demo")

    assert len(cases) == 10
    assert summary["scored_cases"] == 9
    assert summary["passed_cases"] >= 9


def test_evaluation_errors_count_against_pass_rate(tmp_path, monkeypatch) -> None:
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()
    (cases_dir / "cases.json").write_text(
        """
        [
          {
            "case_id": "broken",
            "title": "Broken generator case",
            "period": {"start": "2026-08-31", "end": "2026-09-04"},
            "evidence": [
              {
                "evidence_id": "E1",
                "source": "github",
                "title": "Evidence",
                "content": "Merged.",
                "occurred_at": "2026-09-01T10:00:00Z"
              }
            ],
            "expected_evidence_ids": ["E1"]
          }
        ]
        """,
        encoding="utf-8",
    )

    class BrokenGenerator:
        model = "broken"

        def generate(self, *args, **kwargs):
            raise RuntimeError("boom")

    import deliverybrief.evaluation as evaluation

    monkeypatch.setattr(evaluation, "DemoReportGenerator", BrokenGenerator)

    summary = evaluation.run_evaluation(cases_dir, "demo")

    assert summary["scored_cases"] == 1
    assert summary["passed_cases"] == 0
    assert summary["pass_rate"] == 0.0
    assert summary["results"][0]["status"] == "error"


def test_cost_estimate_makes_no_model_call() -> None:
    estimate = estimate_evaluation_cost(Path("evaluation/day1"), "primary")

    assert estimate["model"] == "claude-haiku-4-5"
    assert estimate["report_cases"] == 3
    assert estimate["estimated_input_tokens"] > 0
    assert estimate["max_output_tokens"] > 0
    assert estimate["estimated_cost_upper_bound_usd"] > 0


def test_workflow_records_generated_run(tmp_path) -> None:
    store = RunStore(tmp_path / "runs.db")
    result, record = generate_and_record(
        DemoReportGenerator(),
        store,
        ProjectConfig(),
        DEMO_PERIOD,
        demo_evidence(),
    )

    assert result.report.completed
    assert store.get(record.run_id) is not None
