# DeliveryBrief

DeliveryBrief helps a project or delivery manager turn GitHub activity and project notes into a client email and an internal action list. Every factual item links back to evidence, and the manager must review the result before approval.

[Source repository](https://github.com/BigVeezus/deliverybrief) · [Live demo](https://deliverybrief.streamlit.app/)

The name is deliberately plain. **Delivery** names the manager's responsibility. **Brief** describes the short output. I left AI out of the product name because the user needs a dependable weekly report, not another AI interface.

## Try the sample workflow

1. Install Python 3.12 or newer and run `pip install -e ".[dev]"`.
2. Copy `.env.example` to `.env`; leave `DELIVERYBRIEF_MODE=demo` for the included sample.
3. Run `streamlit run app.py` and open the displayed URL.

The same workflow is available as `make install`, `make check`, and `make run`.

Demo mode requires no private credentials. It uses labeled sample evidence and a deterministic generator so reviewers can exercise collection, validation, editing, approval, and export. Live mode uses the same domain objects and activates GitHub, Drive notes, Google Docs, and Claude through environment variables.

## What the manager does

1. Choose a week and collect evidence.
2. Inspect the GitHub and project-note records.
3. Generate a draft.
4. Review citations and warnings.
5. Edit and approve the report.
6. Download the client PDF, Word document, email, internal action CSV, JSON, run summary, and workflow trace.

The application never sends email or changes GitHub or Google Drive.

## Architecture

![DeliveryBrief architecture and data flow](docs/architecture.svg)

```text
GitHub REST API ----\
                     > Evidence records -> Report generation -> Validation
Google Drive/Docs --/                                      -> Human review
                                                               -> Exports
```

The live adapters are read-only. Claude receives normalized evidence with stable IDs and returns a structured report. Deterministic checks then verify that cited IDs exist, dates are plausible, action fields are complete, and client text does not contain common secret or personal-data patterns.

I kept orchestration explicit in Python instead of adding a workflow framework this late. The app still shows the important AI OS behavior: it selects available tools, records why each tool ran or skipped, tracks attempts and latency, stores validation and approval gates, and exports a redacted workflow trace for review.

The code is split into named runtime layers:

- `deliverybrief/ui/` contains the Streamlit screens.
- `deliverybrief/services/` coordinates the report run, tool selection, and workflow trace.
- `deliverybrief/generation/` contains the Claude adapter, demo adapter, prompt/schema, and cost estimate.
- `deliverybrief/approval/` owns approval, warning acknowledgement, conflict resolution, and edit invalidation.
- `deliverybrief/persistence/` owns SQLite storage and migrations.
- `deliverybrief/exporting/` owns email, CSV, JSON, and approval-gated downloads.

See [Developer architecture](docs/developer-architecture.md) for the change guide.

## Configuration

Set `DELIVERYBRIEF_MODE=live` and provide:

- `ANTHROPIC_API_KEY`
- `DELIVERYBRIEF_BUDGET_USD`
- `GITHUB_TOKEN` with read-only access to the configured repository
- `GITHUB_REPOSITORY` in `owner/repository` form
- `GOOGLE_SERVICE_ACCOUNT_JSON`, either inline JSON or a path to the JSON file
- `GOOGLE_DRIVE_FOLDER_ID` shared with the service account as Viewer
- `DELIVERYBRIEF_REPOSITORY_URL` set to the public source repository before deployment

The Drive adapter reads native Google Docs plus `.txt`, `.md`, `.csv`, and `.docx` notes from the configured folder. Other file types receive a clear unsupported-type message instead of being treated as evidence.

The model names are configuration rather than code constants. This keeps the evaluation reproducible if account access differs from the default model names.

## Evaluation

Run:

```bash
python -m deliverybrief.evaluation --dataset evaluation/cases --model primary --estimate-only
pytest --junitxml=output/reliability-tests.xml
python scripts/summarize_reliability.py
```

The expanded catalog contains 48 named workflow cases (36 development and 12 reserved), plus boundary, integration, structure, trace, CLI, and Streamlit tests. The current local suite has 97 passing tests, and executed results are in `evaluation/results/reliability-v2.json`. These tests measure workflow behavior: intake, validation, approval, exports, privacy patterns, cost-control paths, tool selection, trace redaction, and failure handling. Earlier files preserve a 1/9 direct-prompt result and 9/9 structured-workflow result under different proxy scorers; those pass rates are historical learning evidence, not a controlled factual-quality comparison. Evaluation v2 separates citation validity from human-reviewed factual grounding, expected-fact coverage, and action accuracy.

The private live smoke test collected 26 GitHub records and one Google Drive note, called Claude Haiku once under a `$0.08` cap, approved the validated report, and produced six export files at the time of the run. Current approved runs also export `Workflow trace.json`. The public summary is in `evidence/live-smoke/live-smoke-summary.md`; raw source text remains ignored under `tmp/live-smoke/`.

## Important limits

- Demo evidence is illustrative, not proof of a real user's time savings.
- Secret and PII checks are deliberately conservative patterns, not a data-loss-prevention product.
- Contradiction detection combines explicit source markers and model output; it cannot settle an ambiguous delivery decision.
- SQLite is sufficient for this five-day, single-project scope. It is not a multi-tenant audit store.
- The manager remains responsible for the external message.

## Documentation

- [Decision record](docs/decisions.md)
- [Operator runbook](docs/runbook.md)
- [Evaluation package source](docs/evaluation-package.md)
- [Case study source](docs/case-study.md)
- [AI collaboration note](docs/ai-collaboration-note.md)
- [Developer architecture](docs/developer-architecture.md)
- [User interview guide](docs/user-interview.md)
- [Five-minute demo script](docs/demo-script.md)
- [Quest control sheet](docs/quest-control.md)
- [Deadline confirmation email](docs/deadline-confirmation-email.md)
- [Evaluation Package PDF](output/pdf/DeliveryBrief-Evaluation-Package.pdf)
- [Case Study PDF](output/pdf/DeliveryBrief-Case-Study.pdf)
- [AI Collaboration Note PDF](output/pdf/DeliveryBrief-AI-Collaboration-Note.pdf)

## Reliability revision

Choose among five free examples, paste developer notes, or upload up to 2 MB and 200 evidence records. Uploads are clearly labeled user supplied. Client PDF and Word exports exclude internal actions and source URLs. Approval is enforced against stored evidence and report versions; edits require reapproval.

Live generation additionally requires `DELIVERYBRIEF_BUDGET_USD`. The budget ledger reserves conservative request costs before each attempt. Unknown pricing fails closed. It does not control spending by other applications. Hosted local files can disappear on redeployment; keep the public demo free and use durable storage before a sustained paid pilot.

The “Tool selector” and “Workflow trace” panels are for handoff and debugging. They show selected/skipped sources, generation mode, approval/export availability, step status, output counts, latency, and redacted errors without storing raw note bodies or credentials.

See [Reliability changes and failures](docs/reliability-upgrade.md) and [User timing session](docs/user-observation-session.md).
