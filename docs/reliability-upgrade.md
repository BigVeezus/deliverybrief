# DeliveryBrief reliability upgrade

This revision strengthens the client-update workflow and corrects how its results are described. It adds automated workflow tests, evidence snapshots, approval checks below the interface, session isolation, source recovery, live-smoke evidence, and client PDF and Word exports.

## What changed and why

The previous score called citation existence “grounding.” That allowed a statement to cite a real PR while saying something the PR did not support. Evaluation v2 reports citation validity separately and leaves factual grounding pending until a named reviewer checks every claim against its evidence.

Approval previously depended on interface checks. The shared store now requires a stored evidence snapshot, current validation, warning acknowledgements, and explicit factual/client review. Exports compare both the report and evidence fingerprints. An edit or source change removes approval.

The public app provides five free simulations and accepts pasted notes or JSON. Every uploaded record is labeled as user supplied. IDs are namespaced for live repositories and documents. Conflicting duplicate IDs stop intake. Records explicitly assigned to other projects are excluded; ambiguous dependencies remain visible for review.

Source collection is separate for GitHub and each selected note. A failed note can be retried without losing a successful GitHub collection. Both connectors paginate; Google Docs tabs, Drive text notes, Markdown, CSV, and DOCX text/table content are supported. Reporting-week GitHub boundaries use the configured timezone. Google modification dates carry a warning because they are not event dates.

The maintainability refactor keeps the same public behavior while separating UI, workflow service,
generation adapters, approval rules, SQLite persistence, and export serializers. Compatibility
wrappers preserve older imports so the refactor does not force unrelated test or documentation
churn. A new structure test checks those package boundaries and confirms helper scripts do not
execute work at import time.

## Failure records

### A valid citation did not prove a true claim

Observed failure: the earlier evaluator awarded its grounding proxy based on evidence IDs. A fabricated budget-approval claim could therefore receive full citation credit. The new regression uses that exact pattern: citation validity remains one, factual grounding is unscored before review, and a rejecting human review produces a failure. Earlier v1 result files remain unchanged and are not comparable to v2 quality scores.

### Approval was bypassable below the interface

Observed failure: the old storage approval method could mark a report approved without revalidation. It also lacked a stored evidence snapshot. Direct-call tests now reject unknown citations, missing acknowledgements, missing client review, and legacy runs without evidence. Editing or changing sources after approval refuses export and clears approval. Semantic factual checking still requires the reviewer.

### Privacy scanning damaged timestamps

Observed failure during implementation: a serialized ISO timestamp was mistaken for a phone number because the date expression did not match before the letter T. This caused evidence validation to fail. Date protection now works for timestamps as well as standalone dates. Privacy and workflow tests exercise both paths.

### Negation changed the demo result

Observed failure in normal-quiet: “No completed work this week” was classified as completed work. The completion matcher now respects that negation. Additional cases cover “not completed” and reverted work. This remains a limited deterministic simulation, not a general language-understanding engine.

### Uploaded notes were not always Google Docs

Observed failure in the first private live smoke: Google Drive listed the uploaded developer note as `text/plain`, so the old adapter did not collect it. I added support for native Google Docs, `.txt`, `.md`, `.csv`, and `.docx` notes while keeping unsupported files explicit. A DOCX extraction test covers paragraphs and table cells.

## Evidence and limitations

The executable catalog contains 48 workflow cases, split into 36 development and 12 reserved cases before the first expanded run. Additional boundary and Streamlit tests exercise state changes, model failures, and repeated generation. The machine-readable result is evaluation/results/reliability-v2.json; its pass counts come from pytest XML.

The reserved cases are not an independently authored benchmark. Their first executed assertions passed; later runs are regression evidence. If any later result influences a fix, that case must no longer be described as unseen.

Secrets and personal data matching supported patterns are masked before model submission and checked again in outputs. This cannot detect every sensitive fact or adversarial instruction. Human client-suitability review remains mandatory. Hosted SQLite files and budget reservations may be lost on redeployment; persistent storage is required before production use.

The private live smoke used one Haiku request under a `$0.08` cap. It collected 26 GitHub records and one Drive note, produced an approved report, and exported six files. Model-quality review, observed time savings, and a consenting user's adoption session remain separate verification tasks.
