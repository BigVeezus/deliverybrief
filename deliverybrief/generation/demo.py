from __future__ import annotations

import re
import time
from datetime import date

from deliverybrief.intake import normalize_evidence
from deliverybrief.models import (
    ActionItem,
    EvidenceItem,
    GenerationResult,
    ProjectConfig,
    ReportingPeriod,
    ReportItem,
    UsageRecord,
    WeeklyReport,
)
from deliverybrief.privacy import safe_evidence

from .base import ReportGenerationError

OWNER_RE = re.compile(r"Owner:\s*([^.;]+)", re.IGNORECASE)
DUE_RE = re.compile(r"(?:Due|by)\s+(20\d{2}-\d{2}-\d{2})", re.IGNORECASE)


class DemoReportGenerator:
    """Deterministic sample generator used only when the app is explicitly in demo mode."""

    model = "deterministic-demo-v1"

    def generate(
        self,
        project: ProjectConfig,
        period: ReportingPeriod,
        evidence: list[EvidenceItem],
    ) -> GenerationResult:
        if not evidence:
            raise ReportGenerationError("No sample evidence was supplied")
        evidence = safe_evidence(normalize_evidence(evidence))
        started = time.perf_counter()
        completed: list[ReportItem] = []
        in_progress: list[ReportItem] = []
        blockers: list[ReportItem] = []
        decisions: list[ReportItem] = []
        next_priorities: list[ReportItem] = []
        actions: list[ActionItem] = []
        seen_topics: dict[str, dict[str, int]] = {
            "completed": {},
            "in_progress": {},
            "blockers": {},
            "next_priorities": {},
        }

        for item in evidence:
            text = f"{item.title}. {item.content}"
            statement = _statement(item)
            lower = text.lower()
            citation = [item.evidence_id]
            topic = str(item.metadata.get("topic", "")).casefold()
            completion = re.search(r"(?<!not )(?<!no )\b(merged|accepted|completed)\b", lower)
            if completion and not re.search(r"\b(reverted|not complete|not completed)\b", lower):
                _upsert_item(completed, seen_topics["completed"], topic, statement, citation)
            if any(term in lower for term in ("in progress", "continues", "open.")):
                _upsert_item(in_progress, seen_topics["in_progress"], topic, statement, citation)
            if any(term in lower for term in ("block", "missing", "risk", "depends")):
                _upsert_item(blockers, seen_topics["blockers"], topic, statement, citation)
            if any(term in lower for term in ("confirm", "must", "due ")):
                _upsert_item(
                    next_priorities,
                    seen_topics["next_priorities"],
                    topic,
                    statement,
                    citation,
                )
            for action_line in item.content.splitlines():
                owner_match = OWNER_RE.search(action_line)
                due_match = DUE_RE.search(action_line)
                if not (owner_match or due_match):
                    continue
                actions.append(
                    ActionItem(
                        task=_action_text(action_line),
                        owner=owner_match.group(1).strip() if owner_match else None,
                        due_date=date.fromisoformat(due_match.group(1)) if due_match else None,
                        evidence_ids=citation,
                        review_status="needs_review",
                    )
                )

        citations = [item.evidence_id for item in evidence]
        summary = (
            f"The {project.display_name} evidence lists "
            f"{len(completed)} merged or accepted item(s); "
            "this does not establish deployment. "
            f"The evidence contains {len(in_progress)} item(s) in progress and "
            f"{len(blockers)} blocker or risk item(s)."
        )
        report = WeeklyReport(
            project_name=project.display_name,
            client_label=project.client_label,
            period=period,
            executive_summary=summary,
            executive_summary_evidence_ids=citations,
            completed=completed,
            in_progress=in_progress,
            blockers=blockers,
            decisions=decisions,
            next_priorities=next_priorities,
            action_items=actions,
            source_limitations=[
                "This result was generated from the bundled sample evidence, not live systems."
            ],
        )
        return GenerationResult(
            report=report,
            model=self.model,
            latency_ms=round((time.perf_counter() - started) * 1000),
            usage=UsageRecord(),
            generator="demo",
        )


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return parts[0].strip()


def _statement(item: EvidenceItem) -> str:
    sentence = _first_sentence(item.content)
    if item.source.value == "github":
        return f"{item.title}: {sentence}"
    return sentence or item.title


def _upsert_item(
    items: list[ReportItem],
    topic_index: dict[str, int],
    topic: str,
    statement: str,
    citations: list[str],
) -> None:
    if topic and topic in topic_index:
        existing = items[topic_index[topic]]
        existing.evidence_ids = list(dict.fromkeys(existing.evidence_ids + citations))
        if len(statement) > len(existing.text):
            existing.text = statement
        return
    items.append(ReportItem(text=statement, evidence_ids=citations))
    if topic:
        topic_index[topic] = len(items) - 1


def _action_text(text: str) -> str:
    cleaned = re.split(r"\bOwner:\s*", text, maxsplit=1, flags=re.IGNORECASE)[0]
    return _first_sentence(cleaned).strip()
