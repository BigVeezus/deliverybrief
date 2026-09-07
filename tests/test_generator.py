from datetime import date

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.generator import DemoReportGenerator
from deliverybrief.models import ProjectConfig


def test_demo_generator_produces_supported_report() -> None:
    result = DemoReportGenerator().generate(ProjectConfig(), DEMO_PERIOD, demo_evidence())
    report = result.report
    valid_ids = {item.evidence_id for item in demo_evidence()}

    assert report.completed
    assert report.in_progress
    assert report.blockers
    assert report.action_items
    assert set(report.executive_summary_evidence_ids) <= valid_ids
    assert all(set(item.evidence_ids) <= valid_ids for item in report.completed)
    assert any(action.due_date == date(2026, 9, 8) for action in report.action_items)
