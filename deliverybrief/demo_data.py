from __future__ import annotations

from datetime import UTC, date, datetime

from deliverybrief.models import EvidenceItem, ReportingPeriod, SourceType

DEMO_PERIOD = ReportingPeriod(start=date(2026, 8, 31), end=date(2026, 9, 4))


def demo_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id="GH-PR-142",
            source=SourceType.GITHUB,
            title="PR 142 Add invoice export filters",
            content=(
                "Merged on 2026-09-02. Adds date and status filters to the invoice export. "
                "Automated tests passed."
            ),
            occurred_at=datetime(2026, 9, 2, 14, 10, tzinfo=UTC),
            source_url="https://github.com/deliverybrief/demo/pull/142",
            author_alias="Engineer A",
            metadata={
                "kind": "pull_request",
                "state": "merged",
                "number": 142,
                "topic": "invoice export filters",
            },
        ),
        EvidenceItem(
            evidence_id="GH-ISSUE-87",
            source=SourceType.GITHUB,
            title="Issue 87 Bulk upload validation",
            content=(
                "Open. Validation work is in progress. The issue is labeled client-priority and "
                "updated on 2026-09-03."
            ),
            occurred_at=datetime(2026, 9, 3, 11, 30, tzinfo=UTC),
            source_url="https://github.com/deliverybrief/demo/issues/87",
            author_alias="Engineer B",
            metadata={
                "kind": "issue",
                "state": "open",
                "labels": ["client-priority"],
                "topic": "bulk upload validation",
            },
        ),
        EvidenceItem(
            evidence_id="GDOC-WEEKLY-0904-INVOICE",
            source=SourceType.GOOGLE_DOC,
            title="Weekly delivery notes 4 September",
            content=("Invoice export filters were demonstrated and accepted."),
            occurred_at=datetime(2026, 9, 4, 9, 0, tzinfo=UTC),
            source_url="https://docs.google.com/document/d/demo-weekly-delivery",
            author_alias="Delivery Manager",
            metadata={"kind": "meeting_notes", "topic": "invoice export filters"},
        ),
        EvidenceItem(
            evidence_id="GDOC-WEEKLY-0904-UPLOAD",
            source=SourceType.GOOGLE_DOC,
            title="Weekly delivery notes 4 September bulk upload",
            content=(
                "Bulk upload validation continues. The client must confirm the final CSV column "
                "names by 2026-09-08. Owner: Client Product Lead."
            ),
            occurred_at=datetime(2026, 9, 4, 9, 5, tzinfo=UTC),
            source_url="https://docs.google.com/document/d/demo-weekly-delivery",
            author_alias="Delivery Manager",
            metadata={"kind": "meeting_notes", "topic": "bulk upload validation"},
        ),
        EvidenceItem(
            evidence_id="GDOC-WEEKLY-0904-RISK",
            source=SourceType.GOOGLE_DOC,
            title="Weekly risk note 4 September",
            content=(
                "The staging test dataset is still missing two invalid-row examples. This blocks "
                "final validation of bulk upload error messages. Owner: QA Lead. Due 2026-09-07."
            ),
            occurred_at=datetime(2026, 9, 4, 9, 15, tzinfo=UTC),
            source_url="https://docs.google.com/document/d/demo-weekly-risk",
            author_alias="Delivery Manager",
            metadata={"kind": "risk_note", "topic": "bulk upload error messages"},
        ),
    ]
