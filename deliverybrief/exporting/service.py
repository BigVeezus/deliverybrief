from __future__ import annotations

from deliverybrief.models import EvidenceItem, WeeklyReport
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

    snapshot = store.approved_snapshot(run_id, report, evidence)
    record = store.get(run_id)
    assert record is not None
    return {
        "Client email.eml": email_bytes(snapshot),
        "Client report.pdf": client_pdf(snapshot),
        "Client report.docx": client_docx(snapshot),
        "Internal actions.csv": action_csv(snapshot).encode(),
        "Report.json": report_json(snapshot).encode(),
        "Run summary.json": record[0].model_dump_json(indent=2).encode(),
    }
