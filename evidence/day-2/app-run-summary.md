# Streamlit app run summary

## Run details

- Date: Monday, 7 September 2026
- App URL: `https://deliverybrief.streamlit.app/`
- Mode: sample evidence
- Project: Northstar Portal
- Runner: Elvis
- Run ID: `5d79a5da-73cb-4168-b758-fbde44a56b31`
- Reporting period: 2026-08-31 to 2026-09-04

## What was captured

- Approved report JSON: `evidence/day-2/app-run/report.json`
- Run summary JSON: `evidence/day-2/app-run/run-summary.json`
- Client email export: `evidence/day-2/app-run/client-update.eml`
- Action CSV export: `evidence/day-2/app-run/actions.csv`
- Client email preview screenshot: `evidence/day-2/app-run/approved-export-screen.png`

## Result

The app generated a weekly delivery update from five sample evidence records. Elvis reviewed the output, approved the report, and exported the client email, action CSV, report JSON, and run summary.

The run summary records:

- status: approved
- evidence count: 5
- generator: deterministic demo
- model: deterministic-demo-v1
- latency: 1 ms
- edits made: true
- approved at: 2026-09-07T20:28:13Z

## Output observed

The generated client email included:

- one completed item: invoice export filters
- one in-progress item: bulk upload validation
- one blocker/risk: missing invalid-row examples in the staging test dataset
- two next priorities
- a clear source limitation stating that the result came from bundled sample evidence, not live systems

## Why this matters

This run proves the public Streamlit app can be opened, reviewed, approved, and exported without sending anything externally. It is not field evidence of time savings because it used bundled sample evidence. It is product-demo evidence for the Working System and Case Study.
