# DeliveryBrief AI Collaboration Note

## Purpose

This log records how I used AI during the Quest and how I checked its work. I remain responsible for the workflow choice, technical decisions, code, evaluation, claims, and submission.

## Collaboration entries

### 7 September 2026 Quest interpretation and scope

**Tool and model.** Codex coding agent.

**Delegated work.** I asked the agent to extract the Quest requirements, compare project directions, and turn the scoring rubric into a build strategy.

**Accepted.** I retained the recommendation to choose one recurring workflow with a measurable baseline, human approval, two integrations, and explicit failure cases.

**Rejected or corrected.** I did not accept the idea that a polished live demo alone would prove value. The plan now separates sample behavior from real-user evidence. I also changed the model-provider recommendation after confirming that I already had Anthropic API credit.

**Verification.** I checked the recommendation against the supplied Quest text and the Applied AI Engineer role description.

**Decision I owned.** I selected weekly delivery updates, a delivery manager as the user, GitHub and Google Docs as sources, a public demo, and Anthropic as the funded provider.

**Artifact.** `docs/decisions.md` and the implementation plan.

### 7 September 2026 System implementation

**Tool and model.** Codex coding agent.

**Delegated work.** I asked the agent to scaffold the Python application, typed schemas, source adapters, validation rules, storage, exports, evaluation fixtures, tests, and document drafts.

**Accepted.** The implementation uses a credential-free demo path and separately configured live adapters. Every factual report item carries evidence IDs. External sending remains outside the system.

**Rejected or corrected.** No field metric, real-user quote, or adoption claim was generated. The documents include an evidence checklist instead of invented results.

**Verification.** Static checks, automated tests, an evaluation run, application smoke testing, and rendered-document inspection must be recorded after execution.

**Decision I owned.** I will personally review the generated code, run the system with my credentials, conduct the user session, and approve every final claim.

**Artifact.** Repository implementation and `docs/evidence-needed.md`.

### 7 September 2026 Deployment and Day 1 evidence planning

**Tool and model.** Codex coding agent.

**Delegated work.** I asked the agent to verify the deployed Streamlit URL and break the Day 1 evidence work into practical next steps.

**Accepted.** The app URL is recorded as `https://deliverybrief.streamlit.app/`. The Quest acceptance time is recorded as Monday, 7 September 2026 at 3:00 PM WAT. Erwin's reply confirmed that the timer is active.

**Rejected or corrected.** The deployed URL was not treated as final because a logged-out check redirected to Streamlit sign-in. I need to make the app public before submitting it as the Working System link.

**Verification.** The deployed URL was checked without an existing logged-in browser session and returned a sign-in redirect instead of the public application.

**Decision I owned.** I will collect real Day 1 evidence manually and only include user feedback, timing numbers, and examples that I can explain and defend.

**Artifact.** `docs/quest-control.md`.

## Daily continuation format

For every later use, add the date, task, tool and model, delegated work, accepted output, rejected or corrected output, verification, personal decision, and artifact reference. Link corrections to commits, tests, or result files where possible.
