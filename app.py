from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import streamlit as st

from deliverybrief.budget import BudgetLedger
from deliverybrief.config import load_settings
from deliverybrief.demo_data import DEMO_PERIOD
from deliverybrief.exports import approved_exports
from deliverybrief.generator import AnthropicReportGenerator, DemoReportGenerator
from deliverybrief.intake import evidence_fingerprint, parse_upload, pasted_note, scoped_evidence
from deliverybrief.integrations.github import GitHubEvidenceClient
from deliverybrief.integrations.google_docs import GoogleDocsEvidenceClient
from deliverybrief.models import ApprovalStatus, EvidenceItem, FindingSeverity, ReportingPeriod
from deliverybrief.privacy import redact, safe_evidence
from deliverybrief.scenarios import SCENARIOS, scenario_evidence
from deliverybrief.storage import RunStore
from deliverybrief.workflow import generate_and_record

st.set_page_config(page_title="DeliveryBrief", page_icon="DB", layout="wide")
st.markdown(
    "<style>.block-container{max-width:1120px;padding-top:2rem}</style>", unsafe_allow_html=True
)
settings = load_settings()
for name, default in {
    "session_id": str(uuid4()),
    "sources": {},
    "result": None,
    "record": None,
    "cache": {},
    "documents": [],
    "busy": False,
    "collection_errors": {},
}.items():
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
        st.session_state.collection_period = str(period)
st.header("1 Collect evidence")
if settings.is_demo:
    selected = st.selectbox("Choose an example", list(SCENARIOS), format_func=SCENARIOS.get)
    if st.button("Load evidence", type="primary"):
        st.session_state.sources = {}
        put_source("sample", scenario_evidence(selected))
else:
    if st.button("Collect GitHub / retry GitHub"):
        try:
            if not settings.github_token:
                raise ValueError("Configure GITHUB_TOKEN for read-only access.")
            with GitHubEvidenceClient(
                settings.github_token,
                settings.project.github_repository,
                timezone=settings.project.timezone,
            ) as client:
                put_source("github", client.collect(period))
        except Exception as error:
            st.session_state.collection_errors["github"] = redact(str(error))
    if st.button("List Google documents"):
        try:
            google = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            st.session_state.documents = google.list_documents()
        except Exception:
            st.error("Cannot list notes. Check the folder and service-account access.")
    docs = st.session_state.documents
    selected_ids = st.multiselect(
        "Select notes",
        [d["id"] for d in docs],
        format_func=lambda key: next(d["name"] for d in docs if d["id"] == key),
    )
    if st.button("Collect selected notes / retry notes", disabled=not selected_ids):
        try:
            google = GoogleDocsEvidenceClient(
                settings.google_service_account_json or "",
                settings.project.google_drive_folder_id or "",
            )
            for doc_id in selected_ids:
                try:
                    put_source(f"google-{doc_id}", google.collect([doc_id]))
                except Exception:
                    st.session_state.collection_errors[f"google-{doc_id}"] = (
                        "Cannot read note. Check access and retry."
                    )
        except Exception:
            st.error("Cannot connect to Google. Check credentials and folder configuration.")
with st.expander("Use your own anonymized evidence"):
    st.caption("Uploads and pasted notes are labeled user supplied, not fetched evidence.")
    st.download_button(
        "Download JSON example",
        json.dumps([i.model_dump(mode="json") for i in scenario_evidence("normal")], indent=2),
        "evidence-example.json",
        mime="application/json",
    )
    upload = st.file_uploader("Evidence JSON — maximum 2 MB and 200 records", type=["json"])
    if st.button("Load uploaded evidence", disabled=upload is None):
        try:
            assert upload is not None
            put_source("upload", parse_upload(upload.getvalue()))
        except ValueError as error:
            st.error(str(error))
    notes = st.text_area("Paste developer notes")
    if st.button("Add developer note", disabled=not notes.strip()):
        try:
            put_source(
                "pasted",
                [
                    pasted_note(
                        notes,
                        settings.project,
                        datetime.combine(period.end, datetime.min.time(), tzinfo=UTC),
                    )
                ],
            )
        except ValueError as error:
            st.error(str(error))
for source, error in st.session_state.collection_errors.items():
    st.warning(f"{source}: {error}. Successfully collected evidence is preserved.")
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
    st.caption("Load a sample, collect sources, or upload evidence to begin.")
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
                )
            )
            with st.spinner("Preparing draft and checking evidence"):
                result, record = generate_and_record(
                    generator, store, settings.project, period, evidence
                )
            st.session_state.cache[key] = result, record
        st.session_state.result, st.session_state.record = result, record
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
