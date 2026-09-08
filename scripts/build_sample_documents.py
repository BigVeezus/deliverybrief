"""Render a saved sanitized sample report using the bundled document runtime."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from deliverybrief.models import WeeklyReport
from deliverybrief.report_documents import client_docx, client_pdf

root = Path(__file__).resolve().parents[1]
with sqlite3.connect(root / "output/browser-check.db") as db:
    row = db.execute("SELECT report_json FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
if row is None:
    raise SystemExit("Generate the public-safe browser sample first.")
report = WeeklyReport.model_validate(json.loads(row[0]))
out = root / "output/qa/sample"
out.mkdir(parents=True, exist_ok=True)
(out / "Client-report.docx").write_bytes(client_docx(report))
(out / "Client-report.pdf").write_bytes(client_pdf(report))
print(out)
