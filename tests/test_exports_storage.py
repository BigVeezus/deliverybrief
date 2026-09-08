from datetime import UTC, datetime

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.exports import action_csv, email_bytes, report_json
from deliverybrief.generator import DemoReportGenerator
from deliverybrief.models import ApprovalStatus, ProjectConfig, RunRecord
from deliverybrief.storage import RunStore
from deliverybrief.validator import approval_status, validate_report


def test_exports_contain_expected_content() -> None:
    report = (
        DemoReportGenerator()
        .generate(
            project=ProjectConfig(),
            period=DEMO_PERIOD,
            evidence=demo_evidence(),
        )
        .report
    )

    assert "Weekly delivery update" in email_bytes(report).decode()
    assert "evidence_ids" in action_csv(report)
    assert '"project_name"' in report_json(report)


def test_store_round_trip_and_approval(tmp_path) -> None:
    project = ProjectConfig()
    generated = DemoReportGenerator().generate(project, DEMO_PERIOD, demo_evidence())
    findings = validate_report(generated.report, demo_evidence())
    record = RunRecord(
        run_id="run-1",
        created_at=datetime.now(UTC),
        project_id=project.project_id,
        period=DEMO_PERIOD,
        model=generated.model,
        generator=generated.generator,
        evidence_count=len(demo_evidence()),
        latency_ms=generated.latency_ms,
        usage=generated.usage,
        findings=findings,
        status=approval_status(findings),
    )
    store = RunStore(tmp_path / "runs.db")
    store.save(record, generated.report, demo_evidence())

    loaded = store.get("run-1")
    assert loaded is not None
    approved = store.approve(
        "run-1",
        generated.report,
        edits_made=False,
        client_reviewed=True,
        acknowledged=[f.code for f in findings],
    )
    assert approved.status == ApprovalStatus.APPROVED
