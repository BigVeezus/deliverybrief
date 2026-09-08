# DeliveryBrief Developer Architecture

This note explains where to change the system after the maintainability refactor.

## Runtime layers

```text
app.py
  deliverybrief/ui/                 Streamlit screens and session state
  deliverybrief/services/           Workflow orchestration
  deliverybrief/generation/         Claude adapter, demo adapter, prompt/schema, cost estimate
  deliverybrief/intake.py           Evidence validation, normalization, fingerprints
  deliverybrief/validator.py        Deterministic report checks
  deliverybrief/approval/           Approval and export-gating rules
  deliverybrief/persistence/        SQLite storage and migrations
  deliverybrief/exporting/          Email, CSV, JSON and approved export service
  deliverybrief/report_documents.py PDF and DOCX document rendering
  deliverybrief/integrations/       Read-only GitHub and Google Drive/Docs clients
```

The root modules `deliverybrief.generator`, `deliverybrief.exports`, `deliverybrief.workflow`,
and `deliverybrief.storage` remain compatibility wrappers. They keep old imports working while
the implementation lives in named packages.

## Change guide

- Change model prompts, structured-output schema handling, or cost estimates in
  `deliverybrief/generation/`.
- Change source validation, upload limits, duplicate handling, or evidence fingerprints in
  `deliverybrief/intake.py`.
- Change blocking/warning rules in `deliverybrief/validator.py`.
- Change approval, warning acknowledgement, conflict resolution, or edit invalidation in
  `deliverybrief/approval/service.py`.
- Change SQLite tables or migrations in `deliverybrief/persistence/sqlite.py`.
- Change download formats in `deliverybrief/exporting/` or client document layout in
  `deliverybrief/report_documents.py`.
- Change Streamlit labels and step order in `deliverybrief/ui/app.py`.

## Guardrails

Run `pytest`, Ruff, mypy, and the secret scanner after changing shared workflow behavior.
The `tests/test_project_structure.py` checks that the named layers exist and that command-line
scripts do not run work at import time.
