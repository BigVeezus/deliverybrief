from __future__ import annotations

import csv
import io
import json
from email.message import EmailMessage

from deliverybrief.models import WeeklyReport


def report_markdown(report: WeeklyReport) -> str:
    lines = [
        f"# Weekly delivery update: {report.project_name}",
        "",
        f"Reporting period: {report.period.start} to {report.period.end}",
        "",
        report.executive_summary,
        "",
    ]
    sections = [
        ("Completed", report.completed),
        ("In progress", report.in_progress),
        ("Blockers and risks", report.blockers),
        ("Decisions", report.decisions),
        ("Next priorities", report.next_priorities),
    ]
    for heading, items in sections:
        lines.extend([f"## {heading}", ""])
        lines.extend(f"- {item.text} [{', '.join(item.evidence_ids)}]" for item in items)
        if not items:
            lines.append("- No supported items found.")
        lines.append("")
    lines.extend(["## Source limitations", ""])
    lines.extend(f"- {item}" for item in report.source_limitations)
    return "\n".join(lines).strip() + "\n"


def email_bytes(report: WeeklyReport) -> bytes:
    message = EmailMessage()
    message["Subject"] = f"Weekly delivery update: {report.project_name}"
    message.set_content(report_markdown(report))
    return message.as_bytes()


def action_csv(report: WeeklyReport) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["task", "owner", "due_date", "review_status", "evidence_ids"],
    )
    writer.writeheader()
    for item in report.action_items:
        writer.writerow(
            {
                "task": item.task,
                "owner": item.owner or "",
                "due_date": item.due_date.isoformat() if item.due_date else "",
                "review_status": item.review_status,
                "evidence_ids": "|".join(item.evidence_ids),
            }
        )
    return output.getvalue()


def report_json(report: WeeklyReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
