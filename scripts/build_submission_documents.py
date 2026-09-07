from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCX_DIR = ROOT / "output" / "docx"
RESULT_PATH = ROOT / "evaluation" / "results" / "demo-latest.json"
NAVY = "275D7A"
PALE_BLUE = "EFF5F8"
LIGHT_GRAY = "D9D9D9"
TEXT = RGBColor(24, 32, 38)


def set_cell_shading(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), color)


def set_cell_border(cell, color: str = LIGHT_GRAY) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), color)


def set_cell_margins(
    cell, top: int = 100, start: int = 120, bottom: int = 100, end: int = 120
) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("DeliveryBrief  |  ")
    run.font.size = Pt(9)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def base_document(title: str, subtitle: str, document_label: str) -> Document:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.7)
    normal.font.color.rgb = TEXT
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.12

    for name, size, before, after in (
        ("Title", 28, 0, 14),
        ("Subtitle", 13, 0, 20),
        ("Heading 1", 17, 15, 7),
        ("Heading 2", 12.5, 11, 5),
    ):
        style = styles[name]
        style.font.name = "Aptos Display" if name != "Normal" else "Aptos"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    title_paragraph = document.add_paragraph(style="Title")
    title_paragraph.add_run(title)
    subtitle_paragraph = document.add_paragraph(style="Subtitle")
    subtitle_paragraph.add_run(subtitle)

    metadata = document.add_paragraph()
    metadata.add_run(document_label.upper()).bold = True
    metadata.add_run("\nPrepared by Elvis\n7 September 2026")
    metadata.paragraph_format.space_after = Pt(22)

    add_page_number(section.footer.paragraphs[0])
    return document


def add_heading(document: Document, text: str, level: int = 1) -> None:
    document.add_heading(text, level=level)


def add_paragraph(document: Document, text: str, bold_lead: str | None = None) -> None:
    paragraph = document.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        paragraph.add_run(bold_lead).bold = True
        paragraph.add_run(text[len(bold_lead) :])
    else:
        paragraph.add_run(text)


def add_bullets(document: Document, items: Iterable[str]) -> None:
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.add_run(item)
        paragraph.paragraph_format.space_after = Pt(3)


def add_table(
    document: Document, headers: list[str], rows: list[list[str]], widths: list[float]
) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    for index, value in enumerate(headers):
        cell = header.cells[index]
        cell.width = Inches(widths[index])
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_shading(cell, NAVY)
        set_cell_border(cell)
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(value)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(9.2)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            cell.width = Inches(widths[index])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_border(cell)
            set_cell_margins(cell)
            if row_index % 2:
                set_cell_shading(cell, PALE_BLUE)
            paragraph = cell.paragraphs[0]
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            )
            run = paragraph.add_run(str(value))
            run.font.size = Pt(9)
    document.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break(document: Document) -> None:
    document.add_page_break()


def save(document: Document, filename: str) -> None:
    DOCX_DIR.mkdir(parents=True, exist_ok=True)
    document.core_properties.author = "Elvis"
    document.core_properties.title = filename.replace("-", " ").removesuffix(".docx")
    document.core_properties.subject = "DeliveryBrief Quest submission"
    document.save(DOCX_DIR / filename)


def build_evaluation() -> None:
    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    document = base_document(
        "DeliveryBrief Evaluation Package",
        "Method, executable checks, current results and evidence still required",
        "Evaluation package",
    )
    add_heading(document, "Current conclusion")
    add_paragraph(
        document,
        "The implementation currently passes twelve automated tests and all nine report cases in the "
        "deterministic demo harness. The tenth case is a mocked retry contract. These results verify "
        "the software paths described here. They do not prove time savings, live model quality or "
        "adoption. I will add those claims only after the same frozen cases run with the configured "
        "models and the delivery manager completes the observed workflow.",
    )
    add_heading(document, "Evaluation question")
    add_paragraph(
        document,
        "Can a delivery manager prepare a weekly client update faster without increasing factual or "
        "privacy risk? I separate report quality, workflow time, reliability and correction effort "
        "because one score would hide the reason a result passed or failed.",
    )
    add_heading(document, "Current verification")
    add_table(
        document,
        ["Check", "Executed result", "What it proves"],
        [
            [
                "Automated tests",
                "12 passed",
                "Core generators, validators, exports, storage and retry behavior",
            ],
            [
                "Static analysis",
                "Ruff and mypy passed",
                "Current Python source meets configured lint and type checks",
            ],
            [
                "Demo report cases",
                f"{results['passed_cases']} of {results['scored_cases']} passed",
                "Deterministic sample behavior against the frozen manifest",
            ],
            [
                "Transient API case",
                "Covered by mocked contract test",
                "GitHub retry stops after the configured successful attempt",
            ],
        ],
        [1.35, 1.45, 3.95],
    )
    add_heading(document, "Evidence boundary")
    add_paragraph(
        document,
        "The public demo uses labeled sample evidence. A perfect deterministic score is not a claim "
        "about Claude or a real manager. The final submission must attach the Haiku, Sonnet, direct-"
        "prompt and field-run result files before reporting the release thresholds as achieved.",
    )

    page_break(document)
    add_heading(document, "Baselines and comparison")
    add_heading(document, "Previous workflow", level=2)
    add_paragraph(
        document,
        "For three anonymized real weeks, the manager follows the existing process while I record "
        "collection, drafting, verification, correction and approval time. I also count source "
        "switches, omissions and changes before sending.",
    )
    add_heading(document, "Direct model baseline", level=2)
    add_paragraph(
        document,
        "All ten frozen cases run through one Claude prompt without stable evidence IDs, source "
        "adapters, deterministic validation or approval controls. This isolates the value supplied "
        "by the workflow around the model.",
    )
    add_heading(document, "Final workflow", level=2)
    add_paragraph(
        document,
        "The same cases run through Haiku, Sonnet and the validated workflow. Each result records the "
        "model ID, prompt version, timestamp, token use, latency and configured token rates.",
    )
    add_heading(document, "Measures and reasons")
    add_table(
        document,
        ["Measure", "Calculation", "Reason"],
        [
            [
                "Grounding",
                "Supported cited facts / cited facts",
                "Unsupported client claims create direct trust risk",
            ],
            [
                "Coverage",
                "Expected facts represented / expected facts",
                "A fluent report can omit important work or risk",
            ],
            [
                "Action accuracy",
                "Supported action fields / expected fields",
                "Wrong ownership creates operational rework",
            ],
            [
                "Exception handling",
                "Expected behaviors observed / expected behaviors",
                "Reliability requires more than a happy path",
            ],
            [
                "Human edit rate",
                "Changed fields / generated fields",
                "Measures correction burden left to the manager",
            ],
            [
                "Workflow time",
                "Minutes from collection through approval",
                "Tests the operational benefit",
            ],
        ],
        [1.25, 2.1, 3.4],
    )

    page_break(document)
    add_heading(document, "Ten frozen cases")
    case_rows = [
        ["01", "Normal week", "Supported completion and action"],
        ["02", "No completed work", "Do not invent completion"],
        ["03", "Multiple repositories", "Preserve evidence across repositories"],
        ["04", "Source conflict", "Block approval and identify both records"],
        ["05", "Duplicate evidence", "Avoid duplicate client bullets"],
        ["06", "Missing action fields", "Warn without inventing owner or date"],
        ["07", "Empty document", "Block empty evidence"],
        ["08", "Long notes", "Preserve supported weekly fact and action"],
        ["09", "Transient API error", "Retry three times and return a useful failure"],
        ["10", "Injection and PII", "Treat instructions as content and prevent a leak"],
    ]
    add_table(document, ["Case", "Condition", "Expected behavior"], case_rows, [0.65, 2.15, 3.95])
    add_heading(document, "Release criteria")
    add_bullets(
        document,
        [
            "At least 9 of 10 total cases pass, and every safety case passes.",
            "Grounding reaches 95 percent and coverage reaches 90 percent.",
            "Action accuracy reaches 85 percent.",
            "Median user workflow time falls by at least 60 percent.",
            "Blocking findings cannot be approved.",
        ],
    )
    add_paragraph(
        document,
        "Grounding and safety receive the strictest thresholds because a wrong client claim matters "
        "more than a missing low-priority detail. Ten cases remain too few for a broad production "
        "reliability claim.",
    )

    page_break(document)
    add_heading(document, "Failure analysis and remaining work")
    add_heading(document, "Required failure record", level=2)
    add_paragraph(
        document,
        "For at least three executed failures I will record the observed behavior, affected case, "
        "root cause, reason the original design allowed it, change made, regression result and "
        "remaining limitation. Each record will link to a test or result file.",
    )
    add_heading(document, "Evidence still required", level=2)
    add_bullets(
        document,
        [
            "Three measured manual workflow runs and the manager's edit record",
            "Ten direct-prompt baseline outputs",
            "Haiku and Sonnet runs over the frozen cases",
            "One unaided user run and Day 4 feedback",
            "Final model decision, cost, latency and regression table",
        ],
    )
    add_heading(document, "Current limits", level=2)
    add_paragraph(
        document,
        "The first evaluation covers one project, one manager and ten cases. Pattern checks can "
        "produce false positives. Read-only access reduces source-system risk but cannot determine "
        "whether client wording represents the manager's judgment. The manager remains the approver.",
    )
    save(document, "DeliveryBrief-Evaluation-Package.docx")


def build_case_study() -> None:
    document = base_document(
        "DeliveryBrief Case Study",
        "Evidence-grounded weekly client updates from GitHub and project notes",
        "Case study",
    )
    add_heading(document, "What I built")
    add_paragraph(
        document,
        "I built DeliveryBrief to help a project or delivery manager prepare a weekly client update "
        "from GitHub activity and project notes. It collects evidence, generates a structured draft, "
        "checks known failure conditions and leaves the external message under the manager's control.",
    )
    add_heading(document, "Why I chose the title")
    add_paragraph(
        document,
        "Delivery identifies the work being reported. Brief describes the short output. I left AI "
        "out of the name because the manager needs a dependable report, not an AI interaction. I "
        "rejected DeliveryOS, ProjectPulse AI and WeeklyOps Agent because each name was less specific "
        "about the actual job.",
    )
    add_heading(document, "Why I chose the workflow")
    add_paragraph(
        document,
        "Weekly delivery reporting is recurring and bounded. GitHub records system activity while "
        "project notes contain decisions, risks and client context. The workflow can be observed, its "
        "output can be compared with evidence, and a usable improvement fits within five days.",
    )
    add_heading(document, "Evidence status")
    add_paragraph(
        document,
        "The software and sample workflow are implemented. The target-user interview, three manual "
        "baselines and live model comparison must be completed before the final case study claims an "
        "operational improvement. I separated that missing evidence rather than converting targets "
        "into results.",
    )

    page_break(document)
    add_heading(document, "System design")
    add_paragraph(
        document,
        "GitHub and Google Docs adapters convert source records into a shared evidence schema with "
        "stable IDs. Claude must return a typed report and attach evidence IDs to factual items. "
        "Deterministic validation then checks citations, sensitive patterns, missing action fields, "
        "empty evidence, instruction-like content and explicit source conflicts.",
    )
    flow = document.add_paragraph()
    flow.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = flow.add_run(
        "GitHub and Google Docs  >  Evidence records  >  Claude draft  >  Validation  >  Human approval  >  Exports"
    )
    run.bold = True
    run.font.size = Pt(10)
    add_heading(document, "User control")
    add_paragraph(
        document,
        "The manager sees the source records before generation and the evidence IDs beside each draft "
        "item. Blocking findings disable approval. Warnings require review. Approval unlocks an email "
        "file, action CSV, report JSON and run record. Nothing is sent externally.",
    )
    add_heading(document, "Technical choices and trade-offs")
    add_table(
        document,
        ["Choice", "Reason", "Accepted trade-off"],
        [
            [
                "Python and Streamlit",
                "Small, typed and testable within five days",
                "Less frontend control than a custom web application",
            ],
            [
                "Anthropic",
                "Existing funded API account and structured output support",
                "No cross-provider comparison in version one",
            ],
            [
                "Haiku and Sonnet",
                "Measure cost against the same quality gates",
                "One-time evaluation uses both models",
            ],
            [
                "No vector database",
                "One week is a bounded evidence set",
                "No cross-project historical retrieval",
            ],
            [
                "Read-only integrations",
                "The report should not change its evidence sources",
                "Source corrections happen outside the app",
            ],
            [
                "Email export",
                "Keeps external communication under manager control",
                "One manual step remains",
            ],
        ],
        [1.35, 2.65, 2.75],
    )

    page_break(document)
    add_heading(document, "Scope and reliability")
    add_heading(document, "Version one", level=2)
    add_bullets(
        document,
        [
            "One configured project, GitHub repository and Google Drive folder",
            "One delivery manager workflow",
            "Read-only source access",
            "Evidence-linked report generation, review, approval and export",
            "Run records with model, latency, usage, findings and edits",
        ],
    )
    add_heading(document, "Deliberate exclusions", level=2)
    add_bullets(
        document,
        [
            "Automatic email sending",
            "Delivery-date prediction",
            "Multi-project administration and per-user OAuth",
            "Historical semantic search",
            "A general chatbot or multi-agent framework",
        ],
    )
    add_heading(document, "Current engineering evidence", level=2)
    add_paragraph(
        document,
        "Twelve automated tests pass. Ruff and mypy pass. The deterministic harness passes nine report "
        "cases, while the transient GitHub failure is covered by a mocked retry test. These results "
        "verify implementation behavior only; they do not replace the field evaluation.",
    )
    add_heading(document, "Failure evidence to add", level=2)
    add_paragraph(
        document,
        "The final version will include three executed failures, the reason each occurred, the code "
        "or prompt change, the regression result and the remaining limitation. I will state any "
        "release threshold that the system misses.",
    )

    page_break(document)
    add_heading(document, "Results and adoption")
    add_paragraph(
        document,
        "The final results section will use frozen files for time reduction, grounding, coverage, "
        "action accuracy, cost, latency and edit rate. Only recorded manager feedback will be quoted. "
        "The public sample will remain labeled separately.",
    )
    add_heading(document, "Main current limitation")
    add_paragraph(
        document,
        "The implementation has not yet been exercised with the target manager's anonymized weekly "
        "records. Until that happens, it is a working system with engineering evidence rather than "
        "proof that the manager's workflow improved.",
    )
    add_heading(document, "Next two weeks")
    add_bullets(
        document,
        [
            "Add scheduled collection after the manual pilot establishes the correct source window.",
            "Create Gmail drafts only after recipient controls and approval auditing are tested.",
            "Add per-user OAuth and a second project configuration.",
            "Run the workflow with three more managers and expand the case set to thirty.",
            "Track completion, time to approval, edit rate, warnings and abandoned runs.",
        ],
    )
    save(document, "DeliveryBrief-Case-Study.docx")


def build_collaboration_note() -> None:
    document = base_document(
        "DeliveryBrief AI Collaboration Note",
        "Work delegated to AI, corrections, verification and decisions I owned",
        "AI collaboration note",
    )
    add_heading(document, "My responsibility")
    add_paragraph(
        document,
        "I used AI to accelerate analysis, scaffolding and review. I remain responsible for the "
        "workflow choice, source permissions, code, evaluation, claims and submission. I will not "
        "present an AI suggestion as an observed result.",
    )
    add_heading(document, "7 September Quest interpretation and scope")
    add_paragraph(document, "Tool and model. Codex coding agent.", "Tool and model.")
    add_paragraph(
        document,
        "Delegated work. I asked the agent to extract the Quest requirements, compare project "
        "directions and translate the scoring rubric into a build strategy.",
        "Delegated work.",
    )
    add_paragraph(
        document,
        "Accepted. I retained the recommendation to choose one recurring workflow with a measurable "
        "baseline, two real integrations, human approval and explicit failure cases.",
        "Accepted.",
    )
    add_paragraph(
        document,
        "Rejected or corrected. I did not treat a polished demo as proof of operational value. I "
        "also replaced the original OpenAI recommendation after confirming that I already had "
        "Anthropic API credit.",
        "Rejected or corrected.",
    )
    add_paragraph(
        document,
        "Verification. I checked the recommendations against the supplied Quest and role description.",
        "Verification.",
    )
    add_paragraph(
        document,
        "Decision I owned. I selected the workflow, target user, sources, public demo and funded model "
        "provider.",
        "Decision I owned.",
    )

    page_break(document)
    add_heading(document, "7 September system implementation")
    add_paragraph(document, "Tool and model. Codex coding agent.", "Tool and model.")
    add_paragraph(
        document,
        "Delegated work. I asked the agent to scaffold the Python application, schemas, read-only "
        "source adapters, model integration, validation, storage, exports, cases, tests and document "
        "drafts.",
        "Delegated work.",
    )
    add_paragraph(
        document,
        "Accepted. I retained the separation between a credential-free sample and live integrations. "
        "Every factual item carries evidence IDs, and external sending remains outside the system.",
        "Accepted.",
    )
    add_paragraph(
        document,
        "Rejected or corrected. No field metric, adoption claim or user quote was generated. The "
        "documents identify the evidence still required. During browser testing, I reviewed the "
        "sample output and corrected duplicate topic handling and a phone-pattern false positive.",
        "Rejected or corrected.",
    )
    add_paragraph(
        document,
        "Verification. Twelve automated tests, Ruff, mypy, the deterministic case runner, the Streamlit "
        "health endpoint and the complete browser workflow were executed.",
        "Verification.",
    )
    add_paragraph(
        document,
        "Decision I owned. I will provide credentials, approve the anonymized evidence, conduct the "
        "manager session and review every final statement before submission.",
        "Decision I owned.",
    )
    add_heading(document, "Artifacts")
    add_bullets(
        document,
        [
            "Typed application and integration code",
            "Ten-case evaluation manifest and timestamped demo result",
            "Automated tests and static-analysis configuration",
            "Decision record, runbook and submission-document sources",
        ],
    )

    page_break(document)
    add_heading(document, "Continuation format")
    add_paragraph(
        document,
        "For every later AI-assisted task I will add the date, tool and model, delegated work, "
        "accepted output, rejected or corrected output, verification, decision I owned and artifact "
        "reference. Corrections will link to a commit, test or result file where possible.",
    )
    add_heading(document, "Entries still required")
    add_bullets(
        document,
        [
            "Live credential and integration verification",
            "Prompt revisions after the first Haiku and Sonnet runs",
            "Changes made after the manager's unaided test",
            "Failure analysis and regression work",
            "Final document and demo-video review",
        ],
    )
    add_heading(document, "Disclosure principle")
    add_paragraph(
        document,
        "The purpose of this note is to make the collaboration inspectable. I will describe AI's "
        "contribution accurately and avoid language that implies I completed work I cannot explain "
        "or verify.",
    )
    save(document, "DeliveryBrief-AI-Collaboration-Note.docx")


def main() -> None:
    build_evaluation()
    build_case_study()
    build_collaboration_note()
    print(f"Created submission documents in {DOCX_DIR}")


if __name__ == "__main__":
    main()
