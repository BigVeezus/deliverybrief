"""Input boundaries shared by UI, workflow and tests. No model calls."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from deliverybrief.models import EvidenceItem, ProjectConfig, SourceType

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 200


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def evidence_fingerprint(items: list[EvidenceItem]) -> str:
    return fingerprint(
        sorted([i.model_dump(mode="json") for i in items], key=lambda row: row["evidence_id"])
    )


def normalize_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
    if len(items) > MAX_RECORDS:
        raise ValueError("Select at most 200 evidence records; nothing was truncated.")
    unique: dict[str, EvidenceItem] = {}
    for item in items:
        if not item.evidence_id.strip():
            raise ValueError("Every evidence record needs a non-empty ID.")
        if item.occurred_at.tzinfo is None:
            raise ValueError("Evidence timestamps must include a timezone.")
        cleaned = item.model_copy(
            update={
                "content": "\n".join(
                    re.sub(r"[ \t]+", " ", line).strip()
                    for line in item.content.replace("\r\n", "\n").split("\n")
                ).strip()
            }
        )
        previous = unique.get(item.evidence_id)
        if previous is not None and previous != cleaned:
            raise ValueError("Duplicate evidence ID has conflicting content; correct the input.")
        unique[item.evidence_id] = cleaned
    return sorted(unique.values(), key=lambda item: (item.occurred_at, item.evidence_id))


def parse_upload(raw: bytes) -> list[EvidenceItem]:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload exceeds 2 MB. Split it into smaller reporting weeks.")
    try:
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            raise ValueError("Upload must be a non-empty JSON array of evidence records.")
        items = [EvidenceItem.model_validate(row) for row in data]
    except (ValidationError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(
            "Invalid evidence JSON. Use the downloadable example and ISO dates."
        ) from error
    for item in items:
        item.metadata = {
            **item.metadata,
            "original_source": item.source.value,
            "ingestion": "user_upload",
        }
        item.source = type(item.source).UPLOAD
    return normalize_evidence(items)


def pasted_note(
    text: str, project: ProjectConfig, occurred_at: datetime | None = None
) -> EvidenceItem:
    if not text.strip() or len(text.encode()) > MAX_UPLOAD_BYTES:
        raise ValueError("Paste a non-empty note smaller than 2 MB.")
    return EvidenceItem(
        evidence_id="NOTE-" + fingerprint(text)[:20],
        source=SourceType.NOTE,
        title="Developer note",
        content=text,
        occurred_at=occurred_at or datetime.now(UTC),
        metadata={"project_id": project.project_id, "ingestion": "user_paste"},
    )


def scoped_evidence(
    items: list[EvidenceItem],
    project: ProjectConfig,
) -> tuple[list[EvidenceItem], list[EvidenceItem]]:
    included: list[EvidenceItem] = []
    excluded: list[EvidenceItem] = []
    for item in normalize_evidence(items):
        target = (
            excluded
            if item.metadata.get("project_id", project.project_id) != project.project_id
            else included
        )
        target.append(item)
    by_number = {str(i.metadata["number"]): i for i in included if "number" in i.metadata}
    for item in included:
        references = re.findall(r"(?:\bPR\s+|(?<![\w/])#)(\d+)\b", item.content)
        linked = [by_number[number] for number in references if number in by_number]
        if linked:
            item.metadata["related_evidence_ids"] = [i.evidence_id for i in linked]
            # Only a single explicit reference establishes a shared conflict topic.
            # Multiple references remain inspectable without guessing a relationship.
            if len(linked) == 1:
                topic = str(linked[0].metadata.get("topic") or linked[0].evidence_id)
                item.metadata.setdefault("topic", topic)
                linked[0].metadata.setdefault("topic", topic)
        external = re.findall(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#\d+", item.content)
        if any(repo != project.github_repository for repo in external):
            item.metadata["external_dependency"] = True
    return included, excluded
