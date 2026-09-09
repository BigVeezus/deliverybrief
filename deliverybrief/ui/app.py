from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import streamlit as st

from deliverybrief.budget import BudgetLedger
from deliverybrief.config import load_settings
from deliverybrief.demo_data import DEMO_PERIOD
from deliverybrief.exports import approved_exports
from deliverybrief.generator import AnthropicReportGenerator, DemoReportGenerator
from deliverybrief.intake import evidence_fingerprint, pasted_note, scoped_evidence
from deliverybrief.integrations.github import GitHubEvidenceClient
from deliverybrief.integrations.google_docs import GoogleDocsEvidenceClient
from deliverybrief.models import ApprovalStatus, EvidenceItem, FindingSeverity, ReportingPeriod
from deliverybrief.privacy import redact, safe_evidence
from deliverybrief.scenarios import SCENARIOS, scenario_evidence
from deliverybrief.services.tool_selector import ToolSelectorInput, select_tools
from deliverybrief.services.tracing import fail_step, finish_step, instant_step, start_step
from deliverybrief.storage import RunStore
from deliverybrief.workflow import generate_and_record

st.set_page_config(page_title="DeliveryBrief", page_icon="DB", layout="wide")
st.markdown(
    "<style>.block-container{max-width:1120px;padding-top:2rem}</style>", unsafe_allow_html=True
)
settings = load_settings()
session_defaults: dict[str, Any] = {
    "session_id": str(uuid4()),
    "sources": {},
    "result": None,
    "record": None,
    "cache": {},
    "documents": [],
    "busy": False,
    "collection_errors": {},
    "trace": [],
}
for name, default in session_defaults.items():
    if name not in st.session_state:
        st.session_state[name] = default
store = RunStore(settings.database_path, st.session_state.session_id)


def reset_draft() -> None:
    if st.session_state.record:
        store.invalidate(st.session_state.record.run_id)
    st.session_state.result = st.session_state.record = None


def put_source(name: str, items: list[EvidenceItem]) -> None:
    reset_draft()
    st.session_state.sources[name] = safe_evidence(items)
    st.session_state.collection_errors.pop(name, None)


def add_trace(step: Any) -> None:
    st.session_state.trace.append(step)


def budget_value() -> float | None:
    value = os.getenv("DELIVERYBRIEF_BUDGET_USD")
    try:
        return float(value) if value else None
    except ValueError:
        return None


def tool_selector_input(
    *,
    has_upload: bool = False,
    has_pasted_note: bool = False,
    approved_snapshot_valid: bool = False,
) -> ToolSelectorInput:
    return ToolSelectorInput(
        mode=settings.mode,
        github_repository=settings.project.github_repository,
        github_token=settings.github_token,
        google_service_account_json=settings.google_service_account_json,
        google_drive_folder_id=settings.project.google_drive_folder_id,
        anthropic_api_key=settings.anthropic_api_key,
        budget_usd=budget_value(),
        has_upload=has_upload,
        has_pasted_note=has_pasted_note,
        approved_snapshot_valid=approved_snapshot_valid,
    )


def trace_rows(steps: list[Any]) -> list[dict[str, object]]:
    return [
        {
            "Step": step.step_name,
            "Tool": step.tool_name,
            "Status": step.status,
            "Reason": step.reason,
            "Outputs": step.output_count,
            "Time ms": step.latency_ms,
            "Error": step.error,
        }
        for step in steps
    ]


st.title("DeliveryBrief")
st.write("Prepare a weekly client update from delivery evidence, with a review before export.")
st.caption("Collect → Check sources → Draft → Review → Approve → Download")
with st.sidebar:
    st.subheader("Your reporting week")
    st.write(settings.project.display_name)
    st.write("Free simulation" if settings.is_demo else "Live integrations")
    st.link_button("Source code and setup", settings.repository_url)
    st.caption("Drafts only. No emails are sent and source systems are read-only.")
if settings.is_demo:
    period = DEMO_PERIOD
    st.info("Free simulation using labeled sample evidence. This mode does not call Anthropic.")
else:
    today = date.today()
    start = st.date_input("Week starts", today - timedelta(days=today.weekday()))
    end = st.date_input("Week ends", start + timedelta(days=6))
    if end < start:
        st.error("The end date must be on or after the start date.")
        st.stop()
    period = ReportingPeriod(start=start, end=end)
    if st.session_state.get("collection_period") != str(period):
        reset_draft()
        st.session_state.sources = {}
        st.session_state.collection_errors = {}
        st.session_state.trace = []
        st.session_state.collection_period = str(period)
st.header("1 Collect evidence")
if settings.is_demo:
    scenario_keys = list(SCENARIOS)
    selected = st.selectbox(
        "Choose an example",
        scenario_keys,
        format_func=lambda key: SCENARIOS[str(key)],
    )
    if st.button("Load evidence", type="primary"):
        step = start_step(
            "collect_sample_evidence",
            "sample_evidence",
            "Demo mode uses bundled public-safe evidence.",
        )
        st.session_state.sources = {}
        items = scenario_evidence(selected)
        put_source("sample", items)
        add_trace(finish_step(step, output_count=len(items)))
else:
    st.caption(f"Configured repository: {settings.project.github_repository}")
    if st.button("Fetch work from GitHub / retry"):
        step = start_step(
            "collect_github",
            "github_rest_api",
            "GitHub token and repository are configured.",
        )
        try:
            if not settings.github_token:
                raise ValueError("Configure GITHUB_TOKEN for read-only access.")
            with GitHubEvidenceClient(
                settings.github_token,
                settings.project.github_repository,
                timezone=settings.project.timezone,
            ) as client:
                items = client.collect(period)
                put_source("github", items)
                add_trace(finish_step(step, output_count=len(items)))
        except Exception as error:
            st.session_state.collection_errors["github"] = redact(str(error))
            add_trace(fail_step(step, error))
    if st.button("Find developer notes in Drive"):
        step = start_step(
            "list_drive_notes",
            "google_drive_notes",
            "Google Drive service account and folder are configured.",
        )
        try:
            google = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            st.session_state.documents = google.list_documents()
            add_trace(finish_step(step, output_count=len(st.session_state.documents)))
        except Exception:
            st.error("Cannot list notes. Check the folder and service-account access.")
            add_trace(
                fail_step(step, "Cannot list notes. Check folder and service-account access.")
            )
    docs = st.session_state.documents
    selected_ids = st.multiselect(
        "Select one or more developer notes",
        [d["id"] for d in docs],
        format_func=lambda key: next(d["name"] for d in docs if d["id"] == key),
    )
    st.caption("Choose every note that belongs to this weekly update.")
    if st.button("Add selected notes to this update / retry", disabled=not selected_ids):
        step = start_step(
            "collect_drive_notes",
            "google_drive_notes",
            "Read selected project-note files from the configured Drive folder.",
            input_count=len(selected_ids),
        )
        try:
            google = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            collected = 0
            for doc_id in selected_ids:
                try:
                    items = google.collect([doc_id])
                    put_source(f"google-{doc_id}", items)
                    collected += len(items)
                except Exception:
                    st.session_state.collection_errors[f"google-{doc_id}"] = (
                        "Cannot read note. Check access and retry."
                    )
            add_trace(finish_step(step, output_count=collected))
        except Exception:
            st.error("Cannot connect to Google. Check credentials and folder configuration.")
            add_trace(fail_step(step, "Cannot connect to Google. Check credentials and folder."))
with st.expander("Paste an extra developer note"):
    st.caption("Use this when an update came through chat or a quick message instead of Drive.")
    notes = st.text_area("Paste developer notes")
    if st.button("Add developer note", disabled=not notes.strip()):
        step = start_step(
            "load_pasted_note",
            "pasted_developer_note",
            "Convert pasted developer notes into a user-supplied evidence item.",
            input_count=1,
        )
        try:
            items = [
                pasted_note(
                    notes,
                    settings.project,
                    datetime.combine(period.end, datetime.min.time(), tzinfo=UTC),
                )
            ]
            put_source("pasted", items)
            add_trace(finish_step(step, output_count=len(items)))
        except ValueError as error:
            st.error(str(error))
            add_trace(fail_step(step, error))

with st.expander("Tool selector", expanded=False):
    selections = select_tools(
        tool_selector_input(
            has_upload=False,
            has_pasted_note=bool(notes.strip()),
            approved_snapshot_valid=False,
        )
    )
    visible_selections = [
        item for item in selections if item.tool_name != "evidence_json_upload"
    ]
    st.table(
        [
            {
                "Tool": item.tool_name,
                "Category": item.category,
                "Selected": item.selected,
                "Reason": item.reason,
                "Missing": ", ".join(item.missing_config),
            }
            for item in visible_selections
        ]
    )
    if not st.session_state.trace:
        add_trace(
            instant_step(
                "select_tools",
                "tool_selector",
                "success",
                "Tool availability was evaluated from mode, credentials, and provided inputs.",
                input_count=len(visible_selections),
                output_count=sum(1 for item in visible_selections if item.selected),
            )
        )
for source, message in st.session_state.collection_errors.items():
    st.warning(f"{source}: {message}. Successfully collected evidence is preserved.")
try:
    evidence, excluded = scoped_evidence(
        [i for group in st.session_state.sources.values() for i in group], settings.project
    )
except ValueError as error:
    st.error(str(error))
    st.stop()
if excluded:
    st.warning(f"Excluded {len(excluded)} records explicitly assigned to another project.")
if not evidence:
    st.caption("Load a sample, fetch GitHub work, add Drive notes, or paste a note to begin.")
    st.stop()
st.header("2 Check sources")
st.caption(f"{len(evidence)} records · {period.start} to {period.end}")
with st.expander("Inspect evidence and context"):
    for item in evidence:
        st.write(f"{item.evidence_id} — {item.title}")
        st.caption(
            f"{item.source.value} · {item.occurred_at.isoformat()} · "
            f"{item.metadata.get('timestamp_kind', 'source timestamp')}"
        )
        st.text(item.content)
        if item.source_url and item.source_url.startswith("https://"):
            st.link_button("Open source", item.source_url)
partial = len({i.source for i in evidence}) < 2 or bool(st.session_state.collection_errors)
ack_partial = st.checkbox("I understand some sources may be missing") if partial else True
st.header("3 Generate draft")
key = evidence_fingerprint(evidence) + str(period) + settings.primary_model
regenerate = st.checkbox("Generate a new attempt instead of reusing this session's result")
if st.button("Generate weekly brief", disabled=not ack_partial or st.session_state.busy):
    st.session_state.busy = True
    try:
        if not regenerate and key in st.session_state.cache:
            result, record = st.session_state.cache[key]
        else:
            generator = (
                DemoReportGenerator()
                if settings.is_demo
                else AnthropicReportGenerator(
                    settings.anthropic_api_key or "",
                    settings.primary_model,
                    BudgetLedger(
                        Path("workflow-budget.db"),
                        float(os.getenv("DELIVERYBRIEF_BUDGET_USD", "0")),
                    ),
                    timeout_seconds=settings.anthropic_timeout_seconds,
                )
            )
            with st.spinner("Preparing draft and checking evidence"):
                result, record = generate_and_record(
                    generator,
                    store,
                    settings.project,
                    period,
                    evidence,
                    trace=st.session_state.trace,
                )
            st.session_state.cache[key] = result, record
        st.session_state.result, st.session_state.record = result, record
        st.session_state.trace = list(record.trace)
    except Exception as error:
        st.error(redact(str(error)))
    finally:
        st.session_state.busy = False
result, record = st.session_state.result, st.session_state.record
if result is None or record is None:
    st.stop()
st.header("4 Review and approve")
edited = result.report.model_copy(deep=True)
edited.executive_summary = st.text_area(
    "Client summary", edited.executive_summary, key=f"{record.run_id}-summary", height=120
)
st.caption("Supporting evidence: " + ", ".join(edited.executive_summary_evidence_ids))
for field in ("completed", "in_progress", "blockers", "decisions", "next_priorities"):
    with st.expander(field.replace("_", " ").title(), expanded=bool(getattr(edited, field))):
        for index, item in enumerate(getattr(edited, field)):
            item.text = st.text_area(
                f"{field.replace('_', ' ')} {index + 1}",
                item.text,
                key=f"{record.run_id}-{field}-{index}",
            )
            st.caption("Evidence: " + ", ".join(item.evidence_ids))
with st.expander("Internal actions — excluded from client PDF and Word files"):
    for index, action in enumerate(edited.action_items):
        action.task = st.text_input("Task", action.task, key=f"{record.run_id}-task-{index}")
        owner, due = st.columns(2)
        action.owner = (
            owner.text_input("Owner", action.owner or "", key=f"{record.run_id}-owner-{index}")
            or None
        )
        action.due_date = due.date_input(
            "Due date", action.due_date, key=f"{record.run_id}-due-{index}"
        )
        if not action.owner or not action.due_date:
            st.caption(
                "Needs confirmation: "
                + ("owner " if not action.owner else "")
                + ("due date" if not action.due_date else "")
            )
        st.caption("Evidence: " + ", ".join(action.evidence_ids))
stored = store.get(record.run_id)
if stored and stored[0].status == ApprovalStatus.APPROVED:
    try:
        store.approved_snapshot(record.run_id, edited, evidence)
    except ValueError:
        st.info("Your edit removed approval. Review and approve the new version.")
findings = store.findings(record.run_id, edited)
for finding in findings:
    (st.error if finding.severity == FindingSeverity.BLOCK else st.warning)(finding.message)
    if finding.evidence_ids:
        st.caption("Check: " + ", ".join(finding.evidence_ids))
if any(f.code == "SOURCE_CONFLICT" for f in findings):
    with st.expander("Resolve conflicting evidence"):
        st.write("Compare the sources and correct the draft. Record what you confirmed below.")
        for item in evidence:
            st.text(f"{item.evidence_id}: {item.content}")
        supporting = st.multiselect("Supporting evidence", [i.evidence_id for i in evidence])
        reason = st.text_area("What was confirmed, and why?")
        if st.button("Record resolution"):
            try:
                store.resolve(record.run_id, supporting, redact(reason))
                st.rerun()
            except ValueError as error:
                st.error(str(error))
blocked = any(f.severity == FindingSeverity.BLOCK for f in findings)
reviewed = st.checkbox(
    "I checked every claim against its evidence and reviewed client suitability",
    key=f"review-{record.run_id}",
)
warnings = [f.code for f in findings if f.severity == FindingSeverity.WARNING]
ack = (
    st.checkbox("I reviewed the remaining warnings", key=f"warnings-{record.run_id}")
    if warnings
    else True
)
if st.button("Approve report", type="primary", disabled=blocked or not reviewed or not ack):
    try:
        store.approve(
            record.run_id,
            edited,
            edits_made=edited != result.report,
            client_reviewed=reviewed,
            acknowledged=warnings if ack else [],
        )
        st.rerun()
    except ValueError as error:
        st.error(str(error))
stored = store.get(record.run_id)
if stored and stored[0].status == ApprovalStatus.APPROVED:
    st.header("5 Download approved report")
    try:
        for filename, data in approved_exports(store, record.run_id, edited, evidence).items():
            st.download_button(filename, data, filename.replace(" ", "-"))
        st.success("Approved version ready. Nothing has been sent externally.")
    except ValueError as error:
        st.error(str(error))
with st.expander("Run summary for reviewers"):
    current = store.get(record.run_id)
    st.json(current[0].model_dump(mode="json") if current else {})
    st.caption(
        "Simulation is not a model evaluation. Hosted logs are temporary, "
        "not a production audit archive."
    )
with st.expander("Workflow trace"):
    current = store.get(record.run_id)
    steps = current[0].trace if current else st.session_state.trace
    st.table(trace_rows(steps))
    st.download_button(
        "Workflow trace JSON",
        json.dumps([step.model_dump(mode="json") for step in steps], indent=2, default=str),
        "Workflow-trace.json",
        mime="application/json",
    )
