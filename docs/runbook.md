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
10. Download the email, action CSV, JSON report, and run summary.

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

Local runs are stored in the configured SQLite file. Each record contains the model, latency, token use, findings, edits, and approval status. Hosted demo storage is temporary; download the run summary when evidence is needed.

## Secret rotation

Replace the affected credential in the local environment and Streamlit secrets. Revoke the previous credential at its provider. Run one read-only smoke test and check the application logs for unexpected access.

## Model changes

Change the model name through environment configuration. Run the complete evaluation set before making it the default. Update the decision record with the tested version and result.

