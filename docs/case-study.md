# DeliveryBrief Case Study

## What I built

I built DeliveryBrief to help a project or delivery manager prepare a weekly client update from GitHub activity and project notes. The system collects evidence, generates a structured draft, checks known failure conditions, and leaves the final external message under the manager's control.

I chose the name because it describes the job. Delivery identifies the work being reported. Brief describes the short output. I did not include AI in the name because the manager's goal is a dependable update, not an AI interaction.

## Why I chose this workflow

Weekly delivery reporting is recurring and bounded. It also exposes a real mismatch between tools. GitHub records pull requests, issues, and commits, while project notes contain decisions, risks, and client context. A manager must reconcile both before writing a message that another person will trust.

The target-user interview and manual baseline must confirm the exact sequence, frequency, time, and observed rework. Until those records exist, the repository describes the proposed workflow and labels the public evidence as sample data.

## Previous process

The workflow map will record the trigger, source order, judgment, approvals, output, and exceptions from the manager's most recent report. Three observed weeks will supply the manual time baseline. I will not substitute an estimate for a measurement.

## Scope

The first version supports one project, one GitHub repository, and one Google Drive folder. It produces an email file and action CSV but never sends a message. It does not provide multi-project administration, historical search, delivery forecasting, or organization-wide authentication.

I kept the scope small so the five-day build includes evaluation, failure handling, documentation, and a real user run.

## Design

GitHub and Google Docs adapters convert source records into a shared `EvidenceItem` schema with stable IDs. Claude receives only these normalized records and must attach evidence IDs to every factual report item. Pydantic checks the response structure. Deterministic validation then checks citations, sensitive patterns, missing action fields, empty evidence, instruction-like source text, and explicit conflicts.

The Streamlit interface exposes the evidence before generation. After generation, the manager can inspect citations and edit each section. Blocking findings disable approval. Warnings require acknowledgement. Approved reports can be downloaded as an email, CSV, JSON file, and run summary.

## Why I made these choices

I used Python and Streamlit because the five-day constraint favored a small, testable application over a custom frontend. I used the candidate's funded Anthropic account rather than adding a new billing dependency. I compare Haiku with Sonnet because cost matters only after the lower-cost model meets the grounding and safety gates.

I did not add a vector database. The user selects one bounded week of evidence, so indexing a historical corpus would introduce another failure surface without serving the first workflow. I also kept both integrations read-only and stopped at an email export because external communication requires human accountability.

## Failures and changes

The final case study will include at least three failures from executed tests, their root causes, code or prompt changes, regression results, and remaining limitations. Each failure must link to a result record or test.

## Results

Time reduction, grounding, coverage, action accuracy, cost, latency, and edit rate will be inserted from frozen result files. Targets are not results. The case study will state clearly if any threshold is missed.

## User response

The target manager will complete one unaided run. The observation will record hesitation, evidence checked, wording changed, approval decision, and requested changes. Only recorded feedback will be quoted.

## Limits and next two weeks

The first version does not establish reliability across organizations. The next iteration would add scheduled collection, controlled Gmail draft creation, per-user OAuth, three additional delivery managers, and at least thirty real cases. Adoption tracking would focus on completed weekly runs, time to approval, edit rate, warning frequency, and abandoned runs.

