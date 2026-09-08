from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.exports import approved_exports
from deliverybrief.generator import DemoReportGenerator
from deliverybrief.models import ApprovalStatus, FindingSeverity, ProjectConfig
from deliverybrief.services.tool_selector import ToolSelectorInput, select_tools
from deliverybrief.services.tracing import fail_step, finish_step, instant_step, start_step
from deliverybrief.storage import RunStore
from deliverybrief.workflow import generate_and_record


def _selection_by_name(config: ToolSelectorInput) -> dict[str, object]:
    return {item.tool_name: item for item in select_tools(config)}


def _approve_with_warnings(store: RunStore, record_id: str, report) -> None:
    findings = store.findings(record_id, report)
    assert not any(finding.severity == FindingSeverity.BLOCK for finding in findings)
    store.approve(
        record_id,
        report,
        edits_made=False,
        client_reviewed=True,
        acknowledged=[finding.code for finding in findings],
    )


def test_demo_mode_selects_sample_and_skips_claude() -> None:
    selections = _selection_by_name(ToolSelectorInput(mode="demo"))

    assert selections["sample_evidence"].selected is True
    assert selections["deterministic_demo_generator"].selected is True
    assert selections["claude_structured_generation"].selected is False
    assert "ANTHROPIC_API_KEY" in selections["claude_structured_generation"].missing_config


def test_live_mode_without_budget_skips_claude_before_api_call() -> None:
    selections = _selection_by_name(
        ToolSelectorInput(
            mode="live",
            github_repository="owner/repo",
            github_token="ghp_fake",
            google_service_account_json='{"client_email":"reader@example.com"}',
            google_drive_folder_id="folder",
            anthropic_api_key="sk-ant-fake",
            budget_usd=0,
        )
    )

    claude = selections["claude_structured_generation"]
    assert claude.selected is False
    assert "DELIVERYBRIEF_BUDGET_USD" in claude.missing_config


def test_configured_drive_and_user_supplied_sources_are_selected() -> None:
    selections = _selection_by_name(
        ToolSelectorInput(
            mode="live",
            google_service_account_json='{"type":"service_account"}',
            google_drive_folder_id="folder",
            has_upload=True,
            has_pasted_note=True,
        )
    )

    assert selections["google_drive_notes"].selected is True
    assert selections["evidence_json_upload"].selected is True
    assert selections["pasted_developer_note"].selected is True


def test_trace_helpers_redact_sensitive_details() -> None:
    step = start_step(
        "collect_drive_notes",
        "google_drive_notes",
        "Use token ghp_1234567890abcdefghijklmnop and email elvis@example.com",
        metadata={
            "private_url": "https://github.com/acme/private-repo/pull/1",
            "google_key": "-----BEGIN " + "PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        },
    )
    failed = fail_step(step, "Anthropic key sk-ant-" + ("FAKE" * 6) + " and elvis@example.com")
    rendered = failed.model_dump_json()

    assert "elvis@example.com" not in rendered
    assert "ghp_1234567890abcdefghijklmnop" not in rendered
    assert "sk-ant-FAKEFAKEFAKE" not in rendered
    assert "abc" not in rendered
    assert "github.com/acme/private-repo" not in rendered


def test_generation_validation_approval_and_export_trace_are_stored(tmp_path) -> None:
    store = RunStore(tmp_path / "runs.db")
    initial_step = finish_step(
        start_step("collect_sample_evidence", "sample_evidence", "Loaded sample evidence."),
        output_count=len(demo_evidence()),
    )
    result, record = generate_and_record(
        DemoReportGenerator(),
        store,
        ProjectConfig(),
        DEMO_PERIOD,
        demo_evidence(),
        trace=[initial_step],
    )

    stored = store.get(record.run_id)
    assert stored is not None
    steps = [step.step_name for step in stored[0].trace]
    assert steps == ["collect_sample_evidence", "generate_report", "validate_report"]

    _approve_with_warnings(store, record.run_id, result.report)
    exports = approved_exports(store, record.run_id, result.report, demo_evidence())
    stored = store.get(record.run_id)
    assert stored is not None
    steps = [step.step_name for step in stored[0].trace]

    assert stored[0].status == ApprovalStatus.APPROVED
    assert "approve_report" in steps
    assert "export_files" in steps
    assert "Workflow trace.json" in exports
    assert b"export_files" in exports["Workflow trace.json"]


def test_edit_after_approval_invalidates_export_and_records_reason(tmp_path) -> None:
    store = RunStore(tmp_path / "runs.db")
    result, record = generate_and_record(
        DemoReportGenerator(), store, ProjectConfig(), DEMO_PERIOD, demo_evidence()
    )
    _approve_with_warnings(store, record.run_id, result.report)
    edited = result.report.model_copy(deep=True)
    edited.executive_summary = "Changed after approval."

    with pytest.raises(ValueError, match="changed"):
        approved_exports(store, record.run_id, edited, demo_evidence())

    stored = store.get(record.run_id)
    assert stored is not None
    assert stored[0].status != ApprovalStatus.APPROVED
    statuses = {(step.step_name, step.status) for step in stored[0].trace}
    assert ("check_approved_snapshot", "blocked") in statuses
    assert ("export_files", "blocked") in statuses


def test_live_smoke_console_script_is_registered() -> None:
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert config["project"]["scripts"]["deliverybrief-live-smoke"] == "scripts.live_smoke:main"


def test_importing_live_smoke_does_not_run_api_calls(monkeypatch) -> None:
    live_smoke = _load_live_smoke_module()

    def fail_if_called(*args, **kwargs):  # pragma: no cover - only fails if import is unsafe
        raise AssertionError("live smoke should not run during import")

    monkeypatch.setattr(live_smoke, "collect_live", fail_if_called)

    assert callable(live_smoke.main)


def test_live_smoke_estimate_only_does_not_construct_generator(monkeypatch, capsys) -> None:
    live_smoke = _load_live_smoke_module()
    project = ProjectConfig(
        github_repository="owner/repo",
        google_drive_folder_id="folder",
    )
    settings = SimpleNamespace(
        mode="live",
        project=project,
        primary_model="claude-haiku-4-5",
        anthropic_api_key="sk-ant-" + ("FAKE" * 6),
        github_token="ghp_" + ("A" * 24),
        google_service_account_json='{"type":"service_account"}',
        live_readiness_errors=lambda: [],
    )
    trace = [
        finish_step(
            start_step("collect_github", "github_rest_api", "Mocked collection."),
            output_count=2,
        )
    ]

    def fail_generator(*args, **kwargs):  # pragma: no cover - only fails on spend path
        raise AssertionError("estimate-only must not construct an Anthropic generator")

    monkeypatch.setattr(sys, "argv", ["live_smoke.py", "--estimate-only", "--max-cost-usd", "0.08"])
    monkeypatch.setattr(live_smoke, "load_settings", lambda: settings)
    monkeypatch.setattr(
        live_smoke,
        "collect_live",
        lambda *_args: {
            "documents": [{"id": "doc", "name": "note"}],
            "selected_documents": [{"id": "doc", "name": "note"}],
            "evidence": demo_evidence(),
            "trace": trace,
        },
    )
    monkeypatch.setattr(
        live_smoke,
        "estimate_generation_cost",
        lambda *_args: SimpleNamespace(estimated_cost_usd=0.01),
    )
    monkeypatch.setattr(live_smoke, "AnthropicReportGenerator", fail_generator)

    live_smoke.main()

    output = capsys.readouterr().out
    assert '"status": "estimated"' in output
    assert '"trace_steps": 1' in output


def _load_live_smoke_module():
    path = Path("scripts/live_smoke.py")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    live_smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live_smoke)
    return live_smoke


def test_instant_step_can_record_tool_selector_result() -> None:
    step = instant_step(
        "select_tools",
        "tool_selector",
        "success",
        "Tool availability was evaluated.",
        input_count=8,
        output_count=3,
    )

    assert step.status == "success"
    assert step.latency_ms == 0
