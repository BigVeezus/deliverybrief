"""Run a private live smoke test and publish only a redacted summary."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from deliverybrief.budget import BudgetLedger
from deliverybrief.config import Settings, load_settings
from deliverybrief.exports import approved_exports
from deliverybrief.generator import AnthropicReportGenerator, estimate_generation_cost
from deliverybrief.integrations.github import GitHubEvidenceClient
from deliverybrief.integrations.google_docs import GoogleDocsEvidenceClient
from deliverybrief.models import ApprovalStatus, EvidenceItem, FindingSeverity, ReportingPeriod
from deliverybrief.privacy import redact
from deliverybrief.services.tool_selector import ToolSelectorInput, select_tools
from deliverybrief.services.tracing import fail_step, finish_step, start_step
from deliverybrief.storage import RunStore
from deliverybrief.workflow import generate_and_record

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIR = ROOT / "tmp/live-smoke"
PUBLIC_DIR = ROOT / "evidence/live-smoke"
EXPORT_DIR = PRIVATE_DIR / "exports"


def monday_of_week(today: date) -> date:
    return today - timedelta(days=today.weekday())


def parse_args() -> argparse.Namespace:
    today = datetime.now(UTC).date()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=monday_of_week(today))
    parser.add_argument("--end", type=date.fromisoformat, default=today)
    parser.add_argument("--max-cost-usd", type=float, default=None)
    parser.add_argument("--limit-google-docs", type=int, default=5)
    parser.add_argument("--database", type=Path, default=PRIVATE_DIR / "live-smoke.db")
    parser.add_argument("--budget-db", type=Path, default=PRIVATE_DIR / "budget.db")
    parser.add_argument("--private-output", type=Path, default=PRIVATE_DIR / "raw-live-smoke.json")
    parser.add_argument("--public-summary", type=Path, default=PUBLIC_DIR / "live-smoke-summary.md")
    parser.add_argument("--export-existing-run-id")
    parser.add_argument("--estimate-only", action="store_true")
    return parser.parse_args()


def readiness_errors(settings: Settings, budget: float | None) -> list[str]:
    errors = []
    if settings.mode != "live":
        errors.append("DELIVERYBRIEF_MODE must be live")
    errors.extend(settings.live_readiness_errors())
    if budget is None:
        errors.append("DELIVERYBRIEF_BUDGET_USD or --max-cost-usd is required")
    elif budget <= 0:
        errors.append("Budget must be greater than zero")
    return errors


def selected_budget(args: argparse.Namespace) -> float | None:
    if args.max_cost_usd is not None:
        return float(args.max_cost_usd)
    value = os.getenv("DELIVERYBRIEF_BUDGET_USD")
    return float(value) if value else None


def collect_live(settings: Settings, period: ReportingPeriod, limit_docs: int) -> dict[str, Any]:
    trace = []
    github_step = start_step(
        "collect_github",
        "github_rest_api",
        "Collect pull requests, issues, and commits from the configured repository.",
    )
    try:
        with GitHubEvidenceClient(
            settings.github_token or "",
            settings.project.github_repository,
            timezone=settings.project.timezone,
        ) as github:
            github_evidence = github.collect(period)
        trace.append(finish_step(github_step, output_count=len(github_evidence)))
    except Exception as error:
        trace.append(fail_step(github_step, error))
        raise

    google = GoogleDocsEvidenceClient(
        settings.google_service_account_json or "",
        settings.project.google_drive_folder_id or "",
    )
    list_step = start_step(
        "list_drive_notes",
        "google_drive_notes",
        "List supported project-note files from the configured Drive folder.",
    )
    try:
        documents = google.list_documents()
        trace.append(finish_step(list_step, output_count=len(documents)))
        selected = documents[:limit_docs]
        if not selected:
            raise RuntimeError(
                "Google folder contains no supported note files. Add a Google Doc, .txt, .md, "
                ".csv, or .docx file and share the folder with the service account as Viewer."
            )
    except Exception as error:
        trace.append(fail_step(list_step, error))
        raise

    collect_step = start_step(
        "collect_drive_notes",
        "google_drive_notes",
        "Collect selected Drive project notes.",
        input_count=len(selected),
    )
    try:
        google_evidence = google.collect([item["id"] for item in selected])
        trace.append(finish_step(collect_step, output_count=len(google_evidence)))
    except Exception as error:
        trace.append(fail_step(collect_step, error))
        raise
    return {
        "documents": documents,
        "selected_documents": selected,
        "evidence": [*github_evidence, *google_evidence],
        "trace": trace,
    }


def live_tool_selections(
    settings: Settings,
    budget: float | None,
    approved: bool = False,
) -> list[dict[str, Any]]:
    return [
        selection.model_dump(mode="json")
        for selection in select_tools(
            ToolSelectorInput(
                mode=settings.mode,
                github_repository=settings.project.github_repository,
                github_token=settings.github_token,
                google_service_account_json=settings.google_service_account_json,
                google_drive_folder_id=settings.project.google_drive_folder_id,
                anthropic_api_key=settings.anthropic_api_key,
                budget_usd=budget,
                approved_snapshot_valid=approved,
            )
        )
    ]


def safe_titles(items: list[EvidenceItem], limit: int = 10) -> list[dict[str, str]]:
    selected = items[:limit]
    selected_ids = {id(item) for item in selected}
    for item in items:
        if item.source.value == "google_doc" and id(item) not in selected_ids:
            if len(selected) >= limit:
                selected[-1] = item
            else:
                selected.append(item)
            break
    return [
        {
            "label": f"{item.source.value}-{index + 1}",
            "source": item.source.value,
            "title": redact(item.title)[:160],
            "ingestion": str(item.metadata.get("ingestion", "")),
        }
        for index, item in enumerate(selected)
    ]


def write_private(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def write_public_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DeliveryBrief live smoke summary",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Status: {summary['status']}",
        f"- Repository: {summary['repository']}",
        f"- Google folder ID: {summary['google_folder_id']}",
        f"- Period: {summary['period']}",
        f"- Model: {summary.get('model', 'not run')}",
        f"- Run ID: {summary.get('run_id', 'not run')}",
        f"- Budget cap: ${summary['budget_cap_usd']:.2f}",
        f"- GitHub records collected: {summary.get('github_records', 0)}",
        f"- Drive notes listed: {summary.get('google_docs_listed', 0)}",
        f"- Drive notes collected: {summary.get('google_docs_collected', 0)}",
        f"- Total evidence records: {summary.get('evidence_records', 0)}",
        f"- Estimated request cost: {summary.get('estimated_request_cost_usd')}",
        f"- Actual estimated cost: {summary.get('actual_estimated_cost_usd')}",
        f"- Latency: {summary.get('latency_ms')} ms",
        f"- Attempts: {summary.get('attempts')}",
        f"- Validation findings: {', '.join(summary.get('finding_codes', [])) or 'none'}",
        f"- Approval status: {summary.get('approval_status')}",
        f"- Exported files: {', '.join(summary.get('exports', [])) or 'none'}",
        f"- Workflow trace steps: {summary.get('trace_steps', 0)}",
        "",
        "## Redacted evidence titles",
        "",
    ]
    for item in summary.get("sample_titles", []):
        lines.append(f"- {item['label']} ({item['ingestion']}): {item['title']}")
    lines.extend(["", "## Tool selections", ""])
    for item in summary.get("selected_tools", []):
        missing = ", ".join(item.get("missing_config", []))
        selected = "selected" if item.get("selected") else "skipped"
        suffix = f" Missing: {missing}." if missing else ""
        lines.append(
            f"- {item['tool_name']} ({item['category']}): "
            f"{selected}. {item['reason']}{suffix}"
        )
    lines.extend(
        [
            "",
            "## Privacy note",
            "",
            "Raw PR bodies, Drive note text, private URLs, emails, API keys, and Google key "
            "material were not written to this public summary. Raw smoke details stay under "
            "`tmp/live-smoke/`, which is ignored by Git.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    settings = load_settings()
    budget_cap = selected_budget(args)
    errors = readiness_errors(settings, budget_cap)
    if errors:
        raise SystemExit("Live smoke readiness failed:\n- " + "\n- ".join(errors))
    assert budget_cap is not None

    period = ReportingPeriod(start=args.start, end=args.end)
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    store = RunStore(args.database, session_id="live-smoke")
    if args.export_existing_run_id:
        current = store.get(args.export_existing_run_id)
        if current is None:
            raise SystemExit(f"Run {args.export_existing_run_id} was not found in {args.database}")
        previous_summary: dict[str, Any] = {}
        if args.private_output.exists():
            previous_summary = json.loads(args.private_output.read_text(encoding="utf-8"))
        record, report = current
        stored_evidence = store.evidence(args.export_existing_run_id)
        stored_findings = store.findings(record.run_id, report)
        if any(finding.severity == FindingSeverity.BLOCK for finding in stored_findings):
            raise SystemExit("Stored run has blocking findings and cannot be exported.")
        if record.status != ApprovalStatus.APPROVED:
            record = store.approve(
                record.run_id,
                report,
                edits_made=False,
                client_reviewed=True,
                acknowledged=[
                    finding.code
                    for finding in stored_findings
                    if finding.severity == FindingSeverity.WARNING
                ],
            )
        stored_exports = approved_exports(store, record.run_id, report, stored_evidence)
        estimate = estimate_generation_cost(
            record.model,
            settings.project,
            record.period,
            stored_evidence,
        )
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        for filename, data in stored_exports.items():
            (EXPORT_DIR / filename.replace(" ", "-")).write_bytes(data)
        refreshed = store.get(record.run_id)
        public_summary = {
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "passed",
            "repository": settings.project.github_repository,
            "google_folder_id": settings.project.google_drive_folder_id,
            "period": f"{record.period.start} to {record.period.end}",
            "model": record.model,
            "run_id": record.run_id,
            "budget_cap_usd": budget_cap,
            "github_records": sum(item.source.value == "github" for item in stored_evidence),
            "google_docs_listed": previous_summary.get("google_docs_listed", "not rerun"),
            "google_docs_collected": sum(
                item.source.value == "google_doc" for item in stored_evidence
            ),
            "evidence_records": len(stored_evidence),
            "estimated_request_cost_usd": estimate.estimated_cost_usd,
            "actual_estimated_cost_usd": record.usage.estimated_cost_usd,
            "latency_ms": record.latency_ms,
            "attempts": record.attempts,
            "finding_codes": sorted({finding.code for finding in record.findings}),
            "approval_status": record.status.value,
            "exports": sorted(stored_exports),
            "selected_tools": live_tool_selections(settings, budget_cap, approved=True),
            "trace_steps": len(refreshed[0].trace) if refreshed else 0,
            "sample_titles": safe_titles(stored_evidence),
            "approval_error": None,
        }
        write_public_summary(args.public_summary, public_summary)
        print(json.dumps(public_summary, indent=2, default=str))
        return
    collection = collect_live(settings, period, args.limit_google_docs)
    evidence: list[EvidenceItem] = collection["evidence"]
    estimate = estimate_generation_cost(settings.primary_model, settings.project, period, evidence)
    if estimate.estimated_cost_usd is not None and estimate.estimated_cost_usd > budget_cap:
        raise SystemExit(
            f"Estimated request cost ${estimate.estimated_cost_usd:.6f} exceeds cap "
            f"${budget_cap:.6f}. No Anthropic request was sent."
        )
    if args.estimate_only:
        public_summary = {
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "estimated",
            "repository": settings.project.github_repository,
            "google_folder_id": settings.project.google_drive_folder_id,
            "period": f"{period.start} to {period.end}",
            "model": settings.primary_model,
            "run_id": "not run",
            "budget_cap_usd": budget_cap,
            "github_records": sum(item.source.value == "github" for item in evidence),
            "google_docs_listed": len(collection["documents"]),
            "google_docs_collected": len(collection["selected_documents"]),
            "evidence_records": len(evidence),
            "estimated_request_cost_usd": estimate.estimated_cost_usd,
            "actual_estimated_cost_usd": None,
            "latency_ms": None,
            "attempts": 0,
            "finding_codes": [],
            "approval_status": "not run",
            "exports": [],
            "selected_tools": live_tool_selections(settings, budget_cap),
            "trace_steps": len(collection["trace"]),
            "sample_titles": safe_titles(evidence),
            "approval_error": None,
        }
        print(json.dumps(public_summary, indent=2, default=str))
        return

    generator = AnthropicReportGenerator(
        settings.anthropic_api_key or "",
        settings.primary_model,
        BudgetLedger(args.budget_db, budget_cap),
    )
    result, record = generate_and_record(
        generator,
        store,
        settings.project,
        period,
        evidence,
        trace=collection["trace"],
    )
    finding_codes = [finding.code for finding in record.findings]
    blocked = any(finding.severity == FindingSeverity.BLOCK for finding in record.findings)
    exports: dict[str, bytes] = {}
    approval_error = None
    if not blocked:
        try:
            acknowledged = [
                finding.code
                for finding in record.findings
                if finding.severity == FindingSeverity.WARNING
            ]
            record = store.approve(
                record.run_id,
                result.report,
                edits_made=False,
                client_reviewed=True,
                acknowledged=acknowledged,
            )
            exports = approved_exports(
                store,
                record.run_id,
                result.report,
                store.evidence(record.run_id),
            )
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            for filename, data in exports.items():
                (EXPORT_DIR / filename.replace(" ", "-")).write_bytes(data)
        except Exception as error:  # pragma: no cover - covered by manual smoke behavior
            approval_error = f"{type(error).__name__}: {redact(str(error))}"

    by_source = {source.value: 0 for source in {item.source for item in evidence}}
    for item in evidence:
        by_source[item.source.value] = by_source.get(item.source.value, 0) + 1
    refreshed = store.get(record.run_id)
    public_summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "passed" if exports else "blocked" if blocked else "failed",
        "repository": settings.project.github_repository,
        "google_folder_id": settings.project.google_drive_folder_id,
        "period": f"{period.start} to {period.end}",
        "model": result.model,
        "run_id": record.run_id,
        "budget_cap_usd": budget_cap,
        "github_records": by_source.get("github", 0),
        "google_docs_listed": len(collection["documents"]),
        "google_docs_collected": len(collection["selected_documents"]),
        "evidence_records": len(evidence),
        "estimated_request_cost_usd": estimate.estimated_cost_usd,
        "actual_estimated_cost_usd": result.usage.estimated_cost_usd,
        "latency_ms": result.latency_ms,
        "attempts": result.attempts,
        "finding_codes": sorted(set(finding_codes)),
        "approval_status": record.status.value,
        "exports": sorted(exports),
        "selected_tools": live_tool_selections(settings, budget_cap, approved=bool(exports)),
        "trace_steps": len(refreshed[0].trace) if refreshed else 0,
        "sample_titles": safe_titles(evidence),
        "approval_error": approval_error,
    }
    persisted_trace = refreshed[0].trace if refreshed else record.trace
    private_payload = {
        **public_summary,
        "documents": [
            {
                "id": document.get("id"),
                "name": redact(document.get("name", "")),
                "modifiedTime": document.get("modifiedTime"),
            }
            for document in collection["documents"]
        ],
        "run_record": record.model_dump(mode="json"),
        "report": result.report.model_dump(mode="json"),
        "trace": [step.model_dump(mode="json") for step in persisted_trace],
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    write_private(args.private_output, private_payload)
    write_public_summary(args.public_summary, public_summary)
    print(json.dumps(public_summary, indent=2, default=str))


if __name__ == "__main__":
    main()
