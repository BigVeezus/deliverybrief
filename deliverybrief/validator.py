from __future__ import annotations

import re
from collections import Counter

from deliverybrief.models import (
    ApprovalStatus,
    EvidenceItem,
    FindingSeverity,
    ValidationFinding,
    WeeklyReport,
    report_items,
)

SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "api_key": re.compile(r"\b(?:sk-ant-|sk-)[A-Za-z0-9_-]{20,}\b"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{8,}\d)(?!\d)")
ISO_DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
PROMPT_INJECTION_RE = re.compile(
    r"\b(ignore (?:all|any|the) (?:previous|prior) instructions|system prompt|developer message|"
    r"reveal (?:the )?(?:secret|credential|prompt))\b",
    re.IGNORECASE,
)
ACTION_SIGNAL_RE = re.compile(
    r"\b(must|needs? to|should|confirm|confirmation is required|required|owner:|due)\b",
    re.IGNORECASE,
)


def validate_report(
    report: WeeklyReport,
    evidence: list[EvidenceItem],
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    evidence_by_id = {item.evidence_id: item for item in evidence}
    valid_ids = set(evidence_by_id)

    citation_groups: list[tuple[str, list[str]]] = [
        ("executive_summary", report.executive_summary_evidence_ids)
    ]
    citation_groups.extend(
        (f"{section}.{index}", item.evidence_ids) for section, index, item in report_items(report)
    )
    citation_groups.extend(
        (f"action_items.{index}", item.evidence_ids)
        for index, item in enumerate(report.action_items)
    )
    for field_path, citations in citation_groups:
        unknown = sorted(set(citations) - valid_ids)
        if unknown:
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.BLOCK,
                    code="UNKNOWN_EVIDENCE",
                    message=(
                        f"{field_path} cites evidence that was not collected: {', '.join(unknown)}"
                    ),
                    field_path=field_path,
                    evidence_ids=unknown,
                )
            )

    report_text = _report_text(report)
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(report_text):
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.BLOCK,
                    code="SECRET_EXPOSURE",
                    message=f"The draft contains a value matching the {name} secret pattern.",
                )
            )
    if EMAIL_RE.search(report_text):
        findings.append(
            ValidationFinding(
                severity=FindingSeverity.BLOCK,
                code="EMAIL_PII",
                message="The draft contains an email address. Remove or explicitly anonymize it.",
            )
        )
    phone_check_text = ISO_DATE_RE.sub("", report_text)
    if PHONE_RE.search(phone_check_text):
        findings.append(
            ValidationFinding(
                severity=FindingSeverity.BLOCK,
                code="PHONE_PII",
                message="The draft contains a possible phone number.",
            )
        )

    for index, action in enumerate(report.action_items):
        if not action.owner:
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.WARNING,
                    code="MISSING_ACTION_OWNER",
                    message="Action item has no supported owner.",
                    field_path=f"action_items.{index}.owner",
                    evidence_ids=action.evidence_ids,
                )
            )
        if not action.due_date:
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.WARNING,
                    code="MISSING_ACTION_DATE",
                    message="Action item has no supported due date.",
                    field_path=f"action_items.{index}.due_date",
                    evidence_ids=action.evidence_ids,
                )
            )

    action_citations = {
        evidence_id for action in report.action_items for evidence_id in action.evidence_ids
    }
    priority_citations = {
        evidence_id for priority in report.next_priorities for evidence_id in priority.evidence_ids
    }
    for index, priority in enumerate(report.next_priorities):
        if not set(priority.evidence_ids) & action_citations:
            findings.extend(
                [
                    ValidationFinding(
                        severity=FindingSeverity.WARNING,
                        code="MISSING_ACTION_OWNER",
                        message="A next priority has no supported action owner.",
                        field_path=f"next_priorities.{index}",
                        evidence_ids=priority.evidence_ids,
                    ),
                    ValidationFinding(
                        severity=FindingSeverity.WARNING,
                        code="MISSING_ACTION_DATE",
                        message="A next priority has no supported action date.",
                        field_path=f"next_priorities.{index}",
                        evidence_ids=priority.evidence_ids,
                    ),
                ]
            )
    for item in evidence:
        if item.evidence_id in action_citations or item.evidence_id in priority_citations:
            continue
        if ACTION_SIGNAL_RE.search(f"{item.title} {item.content}"):
            findings.extend(
                [
                    ValidationFinding(
                        severity=FindingSeverity.WARNING,
                        code="MISSING_ACTION_OWNER",
                        message=(
                            f"{item.evidence_id} appears to require follow-up but has no "
                            "supported action owner in the draft."
                        ),
                        field_path=f"evidence.{item.evidence_id}",
                        evidence_ids=[item.evidence_id],
                    ),
                    ValidationFinding(
                        severity=FindingSeverity.WARNING,
                        code="MISSING_ACTION_DATE",
                        message=(
                            f"{item.evidence_id} appears to require follow-up but has no "
                            "supported action date in the draft."
                        ),
                        field_path=f"evidence.{item.evidence_id}",
                        evidence_ids=[item.evidence_id],
                    ),
                ]
            )

    source_counts = Counter(item.source.value for item in evidence)
    if len(source_counts) < 2:
        findings.append(
            ValidationFinding(
                severity=FindingSeverity.WARNING,
                code="SINGLE_SOURCE",
                message="Only one source type was available. The report may be incomplete.",
            )
        )

    for item in evidence:
        if not item.content.strip():
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.BLOCK,
                    code="EMPTY_EVIDENCE",
                    message=f"{item.evidence_id} contains no readable evidence.",
                    evidence_ids=[item.evidence_id],
                )
            )
        if PROMPT_INJECTION_RE.search(item.content):
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.WARNING,
                    code="UNTRUSTED_INSTRUCTION",
                    message=(
                        f"{item.evidence_id} contains instruction-like text. "
                        "It was treated only as "
                        "source content and requires review."
                    ),
                    evidence_ids=[item.evidence_id],
                )
            )

    topics: dict[str, list[EvidenceItem]] = {}
    for item in evidence:
        topic = str(item.metadata.get("topic", "")).strip().casefold()
        if topic:
            topics.setdefault(topic, []).append(item)
    for topic, items in topics.items():
        combined = " ".join(f"{item.title} {item.content}" for item in items).casefold()
        completed_signal = any(word in combined for word in ("merged", "completed", "accepted"))
        blocked_signal = any(word in combined for word in ("blocked", "not complete", "reopened"))
        if completed_signal and blocked_signal:
            findings.append(
                ValidationFinding(
                    severity=FindingSeverity.BLOCK,
                    code="SOURCE_CONFLICT",
                    message=f"Sources disagree about the state of {topic}.",
                    evidence_ids=[item.evidence_id for item in items],
                )
            )

    if not evidence:
        findings.append(
            ValidationFinding(
                severity=FindingSeverity.BLOCK,
                code="NO_EVIDENCE",
                message="No evidence is available for this report.",
            )
        )
    return _deduplicate_findings(findings)


def approval_status(findings: list[ValidationFinding], approved: bool = False) -> ApprovalStatus:
    if any(item.severity == FindingSeverity.BLOCK for item in findings):
        return ApprovalStatus.BLOCKED
    if approved:
        return ApprovalStatus.APPROVED
    if findings:
        return ApprovalStatus.REVIEW_REQUIRED
    return ApprovalStatus.DRAFT


def _report_text(report: WeeklyReport) -> str:
    parts = [report.executive_summary]
    parts.extend(item.text for _, _, item in report_items(report))
    for action in report.action_items:
        parts.extend([action.task, action.owner or "", str(action.due_date or "")])
    return "\n".join(parts)


def _deduplicate_findings(findings: list[ValidationFinding]) -> list[ValidationFinding]:
    unique: dict[tuple[str, str | None, tuple[str, ...]], ValidationFinding] = {}
    for finding in findings:
        key = (finding.code, finding.field_path, tuple(finding.evidence_ids))
        unique[key] = finding
    return list(unique.values())
