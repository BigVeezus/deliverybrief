from datetime import date

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.generator import DemoReportGenerator, _anthropic_schema, estimate_generation_cost
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


def test_anthropic_schema_disallows_extra_object_fields() -> None:
    schema = {
        "type": "object",
        "properties": {
            "child": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"count": {"type": "integer"}},
                },
            },
        },
        "$defs": {
            "Nested": {
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
            }
        },
    }

    strict = _anthropic_schema(schema)

    assert strict["additionalProperties"] is False
    assert strict["properties"]["child"]["additionalProperties"] is False
    assert strict["properties"]["items"]["items"]["additionalProperties"] is False
    assert strict["$defs"]["Nested"]["additionalProperties"] is False


def test_generation_cost_estimate_has_upper_bound_tokens() -> None:
    estimate = estimate_generation_cost(
        "claude-haiku-4-5",
        ProjectConfig(),
        DEMO_PERIOD,
        demo_evidence(),
    )

    assert estimate.input_tokens > 0
    assert estimate.output_tokens == 6000
    assert estimate.estimated_cost_usd is not None
    assert estimate.estimated_cost_usd > 0
