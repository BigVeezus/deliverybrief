from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from anthropic import RateLimitError
from streamlit.testing.v1 import AppTest

from deliverybrief.budget import BudgetLedger
from deliverybrief.demo_data import DEMO_PERIOD
from deliverybrief.evaluation import EvaluationCase, evaluate_report
from deliverybrief.generator import AnthropicReportGenerator, DemoReportGenerator
from deliverybrief.intake import parse_upload
from deliverybrief.integrations.github import GitHubEvidenceClient
from deliverybrief.models import ProjectConfig
from deliverybrief.scenarios import scenario_evidence
from deliverybrief.storage import RunStore


def test_valid_citation_is_not_factual_grounding():
    evidence = scenario_evidence("normal")
    report = DemoReportGenerator().generate(ProjectConfig(), DEMO_PERIOD, evidence).report
    report.executive_summary = "The client has approved next year's delivery budget."
    case = EvaluationCase(
        case_id="unsupported",
        title="Wrong fact valid ID",
        period=DEMO_PERIOD,
        evidence=evidence,
        expected_facts=["No budget approval evidence exists"],
    )
    output = evaluate_report(case, report, [], 0, 0)
    assert output["citation_validity"] == 1
    assert output["factual_grounding"] is None
    review = {
        "reviewer": "synthetic test reviewer",
        "report_fingerprint": output["report_fingerprint"],
        "supported_claims": [False] * len(output["claims_for_review"]),
        "covered_facts": [False],
        "matched_actions": [],
    }
    reviewed = evaluate_report(case, report, [], 0, 0, review)
    assert reviewed["status"] == "failed" and reviewed["factual_grounding"] == 0
    report.executive_summary = "Changed report"
    with pytest.raises(ValueError, match="fingerprint"):
        evaluate_report(case, report, [], 0, 0, review)


@pytest.mark.parametrize("failure", ["truncated", "invalid", "permission", "rate_limit"])
def test_model_failures_are_bounded_and_never_demo(tmp_path, monkeypatch, failure):
    evidence = scenario_evidence("normal")
    ledger = BudgetLedger(tmp_path / "budget.db", 2)
    gen = AnthropicReportGenerator("synthetic", "claude-haiku-4-5", ledger)
    gen.client = MagicMock()
    monkeypatch.setattr("deliverybrief.generator.time.sleep", lambda _: None)
    if failure == "rate_limit":
        response = httpx.Response(429, request=httpx.Request("POST", "https://example.test"))
        gen.client.messages.create.side_effect = RateLimitError("test", response=response, body={})
    elif failure == "permission":
        from anthropic import PermissionDeniedError

        response = httpx.Response(403, request=httpx.Request("POST", "https://example.test"))
        gen.client.messages.create.side_effect = PermissionDeniedError(
            "test", response=response, body={}
        )
    else:
        gen.client.messages.create.return_value = SimpleNamespace(
            stop_reason="max_tokens" if failure == "truncated" else "end_turn",
            content=[SimpleNamespace(type="text", text="not JSON")],
        )
    with pytest.raises(RuntimeError, match="No demo fallback"):
        gen.generate(ProjectConfig(), DEMO_PERIOD, evidence)
    assert gen.client.messages.create.call_count == (3 if failure == "rate_limit" else 1)
    assert ledger.reserved > 0


def test_budget_missing_and_oversized_input_make_zero_requests(tmp_path):
    evidence = scenario_evidence("normal")
    gen = AnthropicReportGenerator("synthetic", "claude-haiku-4-5")
    gen.client = MagicMock()
    with pytest.raises(RuntimeError, match="budget"):
        gen.generate(ProjectConfig(), DEMO_PERIOD, evidence)
    gen.budget = BudgetLedger(tmp_path / "budget.db", 2)
    evidence[0].content = "x" * 30000
    with pytest.raises(RuntimeError, match="input limit"):
        gen.generate(ProjectConfig(), DEMO_PERIOD, evidence)
    gen.client.messages.create.assert_not_called()


def test_timezone_boundary_and_repository_id():
    client = GitHubEvidenceClient("synthetic", "owner/repo", timezone="Africa/Lagos")
    client._paginate = MagicMock(
        side_effect=[
            [
                {
                    "number": 1,
                    "title": "start",
                    "updated_at": "2026-08-30T23:00:00Z",
                    "state": "open",
                },
                {
                    "number": 2,
                    "title": "end",
                    "updated_at": "2026-09-04T23:00:00Z",
                    "state": "open",
                },
            ],
            [],
        ]
    )
    try:
        evidence = client.collect(DEMO_PERIOD)
        assert [i.evidence_id for i in evidence] == ["GH-owner/repo-ISSUE-1"]
        with pytest.raises(RuntimeError, match="outside"):
            client._get("/repos/other/repo/issues", {})
    finally:
        client.close()


def test_upload_provenance_and_record_limit():
    import json

    rows = [i.model_dump(mode="json") for i in scenario_evidence("normal")]
    uploaded = parse_upload(json.dumps(rows).encode())
    assert all(i.source.value == "upload" for i in uploaded)
    assert all(i.metadata["ingestion"] == "user_upload" for i in uploaded)
    with pytest.raises(ValueError, match="200"):
        parse_upload(json.dumps([rows[0]] * 201).encode())


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_ui_approval_edit_and_repeat_generation(tmp_path, monkeypatch):
    monkeypatch.setenv("DELIVERYBRIEF_MODE", "demo")
    monkeypatch.setenv("DELIVERYBRIEF_DB_PATH", str(tmp_path / "ui.db"))
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    button(app, "Load evidence").click().run()
    button(app, "Generate weekly brief").click().run()
    assert not app.exception
    first_run = app.session_state.record.run_id
    button(app, "Generate weekly brief").click().run()
    assert app.session_state.record.run_id == first_run
    for checkbox in app.checkbox:
        if (
            checkbox.label.startswith("I checked")
            or checkbox.label == "I reviewed the remaining warnings"
        ):
            checkbox.check()
    app.run()
    button(app, "Approve report").click().run()
    assert not app.exception
    assert any("Approved version ready" in s.value for s in app.success)
    app.text_area(key=f"{first_run}-summary").set_value("Updated summary requiring review").run()
    assert not any("Approved version ready" in s.value for s in app.success)
    store = RunStore(tmp_path / "ui.db", app.session_state.session_id)
    assert store.get(first_run)[0].approved_at is None


def test_ui_unsafe_sample_blocks_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("DELIVERYBRIEF_MODE", "demo")
    monkeypatch.setenv("DELIVERYBRIEF_DB_PATH", str(tmp_path / "unsafe.db"))
    app = AppTest.from_file("../app.py", default_timeout=20).run()
    app.selectbox[0].select("unsafe").run()
    button(app, "Load evidence").click().run()
    button(app, "Generate weekly brief").click().run()
    assert not app.exception
    assert button(app, "Approve report").disabled


def test_resolution_requires_support_and_invalidates_approval(tmp_path):
    from deliverybrief.workflow import generate_and_record

    evidence = scenario_evidence("mobile")
    store = RunStore(tmp_path / "conflict.db")
    result, record = generate_and_record(
        DemoReportGenerator(), store, ProjectConfig(), DEMO_PERIOD, evidence
    )
    with pytest.raises(ValueError):
        store.resolve(record.run_id, ["UNKNOWN"], "Long but unsupported reason to dismiss conflict")
    store.resolve(
        record.run_id,
        [i.evidence_id for i in evidence],
        "Backend merge and mobile readiness are different; keep mobile blocked in this update.",
    )
    assert "RESOLVED_CONFLICT" in {f.code for f in store.findings(record.run_id, result.report)}
    assert store.get(record.run_id)[0].approved_at is None
