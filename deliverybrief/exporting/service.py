from __future__ import annotations

import json

from deliverybrief.models import EvidenceItem, WeeklyReport
from deliverybrief.services.tracing import fail_step, finish_step, start_step
from deliverybrief.storage import RunStore

from .serializers import action_csv, email_bytes, report_json


def approved_exports(
    store: RunStore,
    run_id: str,
    report: WeeklyReport,
    evidence: list[EvidenceItem],
) -> dict[str, bytes]:
    """Only public export entrypoint. Serialization helpers do not confer approval."""
    from deliverybrief.report_documents import client_docx, client_pdf

    step = start_step(
        "export_files",
        "export_serializers",
        "Export only from a matching approved report and evidence snapshot.",
        input_count=1,
    )
    try:
        snapshot = store.approved_snapshot(run_id, report, evidence)
    except Exception as error:
        try:
            store.append_trace(run_id, fail_step(step, error, status="blocked"))
        except Exception:
            pass
        raise
    export_map = {
        "Client email.eml": email_bytes(snapshot),
        "Client report.pdf": client_pdf(snapshot),
        "Client report.docx": client_docx(snapshot),
        "Internal actions.csv": action_csv(snapshot).encode(),
        "Report.json": report_json(snapshot).encode(),
    }
    record = store.get(run_id)
    assert record is not None
    run_record = record[0]
    already_recorded = any(
        item.step_name == "export_files"
        and item.status == "success"
        and item.metadata.get("report_fingerprint") == run_record.report_fingerprint
        and item.metadata.get("evidence_fingerprint") == run_record.evidence_fingerprint
        for item in run_record.trace
    )
    if not already_recorded:
        store.append_trace(
            run_id,
            finish_step(
                step,
                output_count=7,
                metadata={
                    "report_fingerprint": run_record.report_fingerprint,
                    "evidence_fingerprint": run_record.evidence_fingerprint,
                },
            ),
        )
        record = store.get(run_id)
        assert record is not None
    trace_json = json.dumps(
        [item.model_dump(mode="json") for item in record[0].trace],
        indent=2,
        sort_keys=True,
    ).encode()
    return {
        **export_map,
        "Run summary.json": record[0].model_dump_json(indent=2).encode(),
        "Workflow trace.json": trace_json,
    }
