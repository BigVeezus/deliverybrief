from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import streamlit as st

from deliverybrief.config import load_settings
from deliverybrief.demo_data import DEMO_PERIOD, demo_evidence
from deliverybrief.exports import action_csv, email_bytes, report_json, report_markdown
from deliverybrief.generator import AnthropicReportGenerator, DemoReportGenerator
from deliverybrief.integrations.github import GitHubEvidenceClient, GitHubIntegrationError
from deliverybrief.integrations.google_docs import (
    GoogleDocsEvidenceClient,
    GoogleDocsIntegrationError,
)
from deliverybrief.models import (
    ActionItem,
    ApprovalStatus,
    EvidenceItem,
    FindingSeverity,
    ReportingPeriod,
    ReportItem,
    WeeklyReport,
)
from deliverybrief.storage import RunStore
from deliverybrief.validator import approval_status, validate_report
from deliverybrief.workflow import generate_and_record


def edit_report(report: WeeklyReport) -> WeeklyReport:
    summary = st.text_area("Executive summary", report.executive_summary, height=110)
    updated: dict[str, list[ReportItem]] = {}
    labels = {
        "completed": "Completed",
        "in_progress": "In progress",
        "blockers": "Blockers and risks",
        "decisions": "Decisions",
        "next_priorities": "Next priorities",
    }
    for field, label in labels.items():
        st.subheader(label)
        updated[field] = []
        items: list[ReportItem] = getattr(report, field)
        if not items:
            st.caption("No supported items found.")
        for index, item in enumerate(items):
            text = st.text_area(
                f"{label} item {index + 1}",
                item.text,
                key=f"edit-{field}-{index}",
                label_visibility="collapsed",
            )
            st.caption("Evidence: " + ", ".join(item.evidence_ids))
            updated[field].append(ReportItem(text=text, evidence_ids=item.evidence_ids))

    st.subheader("Internal action list")
    actions: list[ActionItem] = []
    for index, action in enumerate(report.action_items):
        col_task, col_owner, col_due = st.columns([3, 1.3, 1.2])
        task = col_task.text_input("Task", action.task, key=f"action-task-{index}")
        owner = col_owner.text_input("Owner", action.owner or "", key=f"action-owner-{index}")
        due = col_due.date_input(
            "Due date",
            value=action.due_date,
            key=f"action-due-{index}",
        )
        st.caption("Evidence: " + ", ".join(action.evidence_ids))
        actions.append(
            ActionItem(
                task=task,
                owner=owner or None,
                due_date=due,
                evidence_ids=action.evidence_ids,
                review_status="confirmed" if owner and due else "needs_review",
            )
        )

    return report.model_copy(
        update={
            "executive_summary": summary,
            **updated,
            "action_items": actions,
        }
    )


st.set_page_config(page_title="DeliveryBrief", page_icon="DB", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1120px; padding-top: 2rem;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .status-ready {color: #176b47; font-weight: 650;}
    .status-review {color: #8a5a00; font-weight: 650;}
    .status-blocked {color: #a32828; font-weight: 650;}
    [data-testid="stMetricValue"] {font-size: 1.35rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def state_default(name: str, value: Any) -> None:
    if name not in st.session_state:
        st.session_state[name] = value


settings = load_settings()
store = RunStore(settings.database_path)
state_default("evidence", [])
state_default("result", None)
state_default("record", None)
state_default("approved", False)
state_default("edited_report", None)
state_default("google_documents", [])

st.title("DeliveryBrief")
st.caption("Evidence-grounded weekly client updates from GitHub and project notes")
st.write(
    "Collect the week's delivery evidence, inspect the draft, and keep the final client message "
    "under human control."
)

with st.sidebar:
    st.subheader("Run context")
    mode_label = "Sample evidence" if settings.is_demo else "Live integrations"
    st.write(f"Mode: **{mode_label}**")
    st.write(f"Project: **{settings.project.display_name}**")
    if settings.repository_url:
        st.markdown(f"[View source repository]({settings.repository_url})")
    else:
        st.caption("Repository link will be added before public deployment.")
    st.divider()
    st.caption(
        "DeliveryBrief reads configured sources. It does not send email or modify GitHub or Drive."
    )

if settings.is_demo:
    period = DEMO_PERIOD
    st.info(
        "This public-safe demo uses labeled sample evidence and a deterministic generator. "
        "Switch to live mode through environment configuration."
    )
else:
    today = date.today()
    default_end = today - timedelta(days=today.weekday()) + timedelta(days=4)
    default_start = default_end - timedelta(days=4)
    col_start, col_end = st.columns(2)
    with col_start:
        start = st.date_input("Week starts", value=default_start)
    with col_end:
        end = st.date_input("Week ends", value=default_end)
    period = ReportingPeriod(start=start, end=end)

st.header("1 Collect evidence")

if settings.is_demo:
    if st.button("Load sample week", type="primary"):
        st.session_state.evidence = demo_evidence()
        st.session_state.result = None
        st.session_state.record = None
        st.session_state.approved = False
else:
    readiness_errors = settings.live_readiness_errors()
    if readiness_errors:
        st.error("Live mode is not ready: " + "; ".join(readiness_errors))
    if st.button("List Google Docs", disabled=bool(readiness_errors)):
        try:
            google_client = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            st.session_state.google_documents = google_client.list_documents()
        except (GoogleDocsIntegrationError, ValueError, json.JSONDecodeError) as error:
            st.error(str(error))
    documents = st.session_state.google_documents
    selected_ids = st.multiselect(
        "Project notes",
        options=[item["id"] for item in documents],
        format_func=lambda item_id: next(
            item["name"] for item in documents if item["id"] == item_id
        ),
    )
    if st.button("Collect selected week", type="primary", disabled=bool(readiness_errors)):
        try:
            with GitHubEvidenceClient(
                settings.github_token or "", settings.project.github_repository
            ) as github_client:
                github_items = github_client.collect(period)
            google_client = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            note_items = google_client.collect(selected_ids)
            st.session_state.evidence = github_items + note_items
            st.session_state.result = None
            st.session_state.record = None
            st.session_state.approved = False
        except (GitHubIntegrationError, GoogleDocsIntegrationError, ValueError) as error:
            st.error(str(error))

evidence: list[EvidenceItem] = st.session_state.evidence
if evidence:
    source_counts = {
        "GitHub": sum(item.source.value == "github" for item in evidence),
        "Google Docs": sum(item.source.value == "google_doc" for item in evidence),
    }
    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Evidence records", len(evidence))
    metric_two.metric("GitHub", source_counts["GitHub"])
    metric_three.metric("Project notes", source_counts["Google Docs"])
    with st.expander("Inspect collected evidence", expanded=True):
        for item in evidence:
            st.markdown(f"**{item.evidence_id} — {item.title}**")
            st.caption(f"{item.source.value} | {item.occurred_at.date()}")
            st.write(item.content)
            if item.source_url:
                st.link_button("Open source", item.source_url)
            st.divider()

st.header("2 Generate draft")
if settings.is_demo:
    selected_model = "deterministic-demo-v1"
else:
    selected_model = st.selectbox(
        "Model",
        options=[settings.primary_model, settings.quality_model],
        help="The evaluation determines which model becomes the default.",
    )

if st.button("Generate weekly brief", disabled=not evidence):
    generator = (
        DemoReportGenerator()
        if settings.is_demo
        else AnthropicReportGenerator(settings.anthropic_api_key or "", selected_model)
    )
    try:
        with st.spinner("Preparing the evidence-grounded draft"):
            result, record = generate_and_record(
                generator, store, settings.project, period, evidence
            )
        st.session_state.result = result
        st.session_state.record = record
        st.session_state.edited_report = result.report
        st.session_state.approved = False
    except Exception as error:
        st.error(str(error))

result = st.session_state.result
record = st.session_state.record
if result and record:
    st.caption(
        f"Generator: {record.generator} | Model: {record.model} | "
        f"Latency: {record.latency_ms} ms | Evidence: {record.evidence_count}"
    )
    report: WeeklyReport = st.session_state.edited_report
    st.header("3 Review and approve")
    edited = edit_report(report)
    findings = validate_report(edited, evidence)
    status = approval_status(findings, st.session_state.approved)
    status_class = {
        ApprovalStatus.DRAFT: "status-ready",
        ApprovalStatus.REVIEW_REQUIRED: "status-review",
        ApprovalStatus.BLOCKED: "status-blocked",
        ApprovalStatus.APPROVED: "status-ready",
    }[status]
    st.markdown(
        f'<p class="{status_class}">Status: {status.value.replace("_", " ").title()}</p>',
        unsafe_allow_html=True,
    )
    for finding in findings:
        message = f"{finding.code}: {finding.message}"
        if finding.severity == FindingSeverity.BLOCK:
            st.error(message)
        elif finding.severity == FindingSeverity.WARNING:
            st.warning(message)
        else:
            st.info(message)

    blocking = any(item.severity == FindingSeverity.BLOCK for item in findings)
    warnings = any(item.severity == FindingSeverity.WARNING for item in findings)
    acknowledge = st.checkbox(
        "I reviewed the evidence and understand the remaining warnings.",
        disabled=blocking,
    )
    if st.button(
        "Approve report",
        type="primary",
        disabled=blocking or (warnings and not acknowledge),
    ):
        original_json = result.report.model_dump_json()
        edited_json = edited.model_dump_json()
        approved_record = store.approve(
            record.run_id, edited, edits_made=original_json != edited_json
        )
        st.session_state.record = approved_record
        st.session_state.edited_report = edited
        st.session_state.approved = True
        st.rerun()

    if st.session_state.approved:
        st.success("Approved. Exports are ready; nothing has been sent externally.")
        export_one, export_two, export_three, export_four = st.columns(4)
        export_one.download_button(
            "Client email",
            data=email_bytes(edited),
            file_name="deliverybrief-client-update.eml",
            mime="message/rfc822",
        )
        export_two.download_button(
            "Action CSV",
            data=action_csv(edited),
            file_name="deliverybrief-actions.csv",
            mime="text/csv",
        )
        export_three.download_button(
            "Report JSON",
            data=report_json(edited),
            file_name="deliverybrief-report.json",
            mime="application/json",
        )
        export_four.download_button(
            "Run summary",
            data=st.session_state.record.model_dump_json(indent=2),
            file_name="deliverybrief-run.json",
            mime="application/json",
        )
        with st.expander("Preview client email"):
            st.markdown(report_markdown(edited))
