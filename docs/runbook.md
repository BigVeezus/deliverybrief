# DeliveryBrief Operator Runbook

## Purpose

This runbook explains how to configure, operate, and recover DeliveryBrief. The application reads project evidence and produces files for human review. It does not change the source systems or send email.

## Local setup

1. Install Python 3.12 or newer.
2. Run `pip install -e ".[dev]"`.
3. Copy `.env.example` to `.env`.
4. Keep `DELIVERYBRIEF_MODE=demo` for the credential-free sample.
5. Run `streamlit run app.py`.

## Live configuration

Set `DELIVERYBRIEF_MODE=live` and configure:

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_PRIMARY_MODEL`
- `ANTHROPIC_QUALITY_MODEL`
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_DRIVE_FOLDER_ID`
- `DELIVERYBRIEF_TIMEZONE`
- `DELIVERYBRIEF_DB_PATH`

Create a fine-grained GitHub token with read access only to repository metadata, contents, pull requests, and issues for the selected repository. Create a Google service account, enable Drive and Docs APIs, and share only the project-note folder with its email address as Viewer.

Project notes can be native Google Docs, `.txt`, `.md`, `.csv`, or `.docx` files. Unsupported file types should be converted or pasted into a supported format before collection.

## Normal weekly operation

1. Choose the Monday and Friday of the reporting period.
2. List available project notes.
3. Select only documents that belong to the reporting week.
4. Collect evidence and inspect the counts from each source.
5. Generate the draft using the configured default model.
6. Open cited evidence for any delivery claim, blocker, or client action.
7. Correct wording without removing required evidence IDs.
8. Resolve blocking findings. Acknowledge remaining warnings only after review.
9. Approve the report.
10. Download the email, client PDF/DOCX, action CSV, JSON report, run summary, and workflow trace.

## Status meanings

- **Draft:** The report has no current validation finding but still requires approval.
- **Review required:** The system found a non-blocking omission or an instruction-like source passage.
- **Blocked:** The report cites missing evidence, contains possible sensitive data, has empty evidence, or contains a critical source conflict.
- **Approved:** A user reviewed the report and completed the approval action.

## Recovery

### GitHub denied access

Confirm `owner/repository`, token expiry, repository selection, and read permissions. Do not broaden the token beyond the configured repository to bypass an error.

### Google denied access

Confirm the Drive folder ID and share the folder with the service-account email as Viewer. A domain-wide administrator role is not required.

### Transient API failure

The application retries timeouts, rate limits, and server errors up to three times. If all attempts fail, wait for the provider to recover and collect again. Do not repeatedly click Generate because it creates separate model calls.

### Invalid model output

Preserve the error and evidence. Retry once. If the primary model still fails and the evidence is complete, run the quality model. Missing evidence must be corrected at the source rather than hidden with a larger model.

### Blocked report

Read each finding and its evidence IDs. Remove sensitive data, correct the source selection, or return to the manager for a decision. Approval must not be bypassed in the database.

## Logs and records

Local runs are stored in the configured SQLite file. Each record contains the model, latency, token use, findings, edits, approval status, and workflow trace. Hosted demo storage is temporary; download the run summary and workflow trace when evidence is needed.

## Tool selection and trace

Open the “Tool selector” panel before generation when debugging configuration. It shows which sources and generators are selected or skipped:

- demo mode selects bundled sample evidence and the deterministic generator;
- live mode selects GitHub only when `GITHUB_TOKEN` and `GITHUB_REPOSITORY` exist;
- live mode selects Drive notes only when the service-account JSON and folder ID exist;
- pasted notes appear only when the operator provides them;
- Claude is selected only in live mode with an Anthropic key and a positive budget;
- exports are selected only after the stored approved snapshot matches the current report and evidence.

Open the “Workflow trace” panel after generation or approval. It records step name, tool, status, reason, counts, attempts, latency, and redacted errors. Trace data is for monitoring and handoff; it intentionally stores counts and fingerprints instead of raw private source bodies.

## Secret rotation

Replace the affected credential in the local environment and Streamlit secrets. Revoke the previous credential at its provider. Run one read-only smoke test and check the application logs for unexpected access.

## Model changes

Change the model name through environment configuration. Run the complete evaluation set before making it the default. Update the decision record with the tested version and result.

## Code maintenance

The root `app.py` is only the Streamlit entrypoint. The interface lives in `deliverybrief/ui/`.
Generation code lives in `deliverybrief/generation/`; approval and export gating live in
`deliverybrief/approval/`; SQLite storage lives in `deliverybrief/persistence/`; and download
serializers live in `deliverybrief/exporting/`. The older modules `deliverybrief.generator`,
`deliverybrief.storage`, `deliverybrief.exports`, and `deliverybrief.workflow` remain as
compatibility wrappers so existing commands and tests keep working.

Use `docs/developer-architecture.md` before changing shared behavior. It lists the main package
boundaries and the tests that prove those boundaries still exist.

## Reliability revision operation

Use “Load evidence” to choose a free scenario. The payment, mobile, and migration weeks are reconstructed examples; the unsafe week is synthetic. “Paste an extra developer note” lets a manager add a note from chat, Slack, or email without handling raw JSON. The backend still has a tested JSON intake path for automated fixtures and evaluation, capped at 2 MB and 200 records. Invalid IDs, duplicate-ID conflicts, and timezone-free timestamps require correction before generation.

In live mode, collect GitHub and selected Google notes separately. A failed note leaves other sources intact. Retry the failed source button. Changing the reporting period clears stale selections. Single-source continuation requires acknowledgement.

Resolve a conflict by comparing all cited sources, correcting the report, selecting supporting evidence, and recording an explanation of at least 20 characters. The resolution becomes an acknowledged warning; a secret or invalid citation remains blocking. This is a human decision record, not automated semantic proof.

Approve only after checking each claim and client suitability. Editing an approved report or changing evidence clears approval. Download only the approved snapshot. Internal actions are not in client PDF/Word documents.

Each browser session has an independent run scope. The default local CLI scope can read legacy records, but legacy records without evidence snapshots must be regenerated before approval. Do not use hosted SQLite as a durable audit archive. Back up approved exports; production requires persistent storage and authentication.

## Budget and diagnostics

Set an explicit positive `DELIVERYBRIEF_BUDGET_USD` for live generation. No budget means no model calls. The `workflow-budget.db` ledger reserves a conservative request maximum before each attempt; uncertain failures keep their reservation. There are no hidden Anthropic SDK retries. Do not delete the ledger to retry a request. Raising its limit requires my approval.

For an alternate model, configure its exact identifier in `ANTHROPIC_PRICED_MODEL` and explicit `ANTHROPIC_MODEL_INPUT_PER_MTOK` and `ANTHROPIC_MODEL_OUTPUT_PER_MTOK` rates after checking provider pricing. Unknown or invalid rates block requests. Historical Haiku pricing assumptions remain configuration-dependent estimates. These application controls do not cap unrelated provider-account spending.

Run records contain version fingerprints, attempts, usage, validation, approval information, and workflow traces. SQLite `audit_events` records generation failures by error type without raw provider content. Public app logs are temporary. Rotate a leaked key in its provider console, replace the configured secret, and restart the private live instance.

## Verification and handoff

Run `deliverybrief-live-smoke --estimate-only --max-cost-usd 0.08` or `python scripts/live_smoke.py --estimate-only --max-cost-usd 0.08` first to check source access and cost without constructing the Anthropic generator. Run the full smoke only in a private environment with credentials configured. It writes raw details to ignored `tmp/live-smoke/` and a redacted summary to `evidence/live-smoke/`. Then run `pytest --junitxml=output/reliability-tests.xml`, `python scripts/summarize_reliability.py`, Ruff, mypy, and the secret scanner. Review `docs/user-observation-session.md` with a consenting participant before claiming measured time savings.
