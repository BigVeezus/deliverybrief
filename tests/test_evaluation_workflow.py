from pathlib import Path

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.evaluation import load_cases, run_evaluation
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
