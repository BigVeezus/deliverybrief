# DeliveryBrief — five-minute Loom walkthrough

Rehearsal script for the current app after the maintainability and trace upgrade. Timings include clicks. Use your own voice and rehearse once.

## Before recording

Open the public app on Normal delivery week, the latest client PDF, `evaluation/results/reliability-v2.json`, and `evidence/live-smoke/live-smoke-summary.md` in separate tabs. Use the free public simulation in the browser. Do not show private credential pages or raw live-smoke files.

## 0:00–0:40 — Explain the problem

Show the application title.

“Hi, I'm Elvis. I built DeliveryBrief for a project manager who turns GitHub activity and developer notes into a weekly client update.

“The difficult part isn't typing. It's figuring out what actually happened when PR descriptions are vague and important context lives elsewhere.

“I kept the first version to one configured project, with human approval before download. DeliveryBrief names the outcome: a brief about project delivery.”

## 0:40–1:35 — Show evidence and drafting

Click Load evidence, open Tool selector, open Inspect evidence and context, show a GitHub-labeled record and a developer note, then Generate weekly brief.

“This public walkthrough uses labeled samples and a free, rule-based simulation. It isn't calling Claude. I also ran the private live path with GitHub, a Drive note, Google Docs access, and Claude Haiku under a budget cap.

“This panel is the tool selector. In demo mode it selects sample evidence and the deterministic generator. In live mode it selects GitHub, Drive notes, uploads, pasted notes, or Claude only when the required configuration exists.

“Each record keeps its source, timestamp, and evidence ID. The draft refers back to those records so a manager can investigate a statement.

“An important distinction: merged code doesn't automatically mean deployed code. That stronger claim needs its own evidence.”

## 1:35–2:35 — Review, approve, and export

Compare a report item with its evidence. Review internal actions, tick the review checkbox, acknowledge any warnings, and approve. Download/open the client PDF and workflow trace JSON. Return and edit the summary to an evidence-supported alternative; move focus out of the field.

“I check the wording before approval. The internal action list is separate from the client PDF and Word document.

“All downloads use the stored approved version. Now I'll edit it. The downloads disappear until I review and approve again.

“That check runs below the interface too. Calling the export function directly doesn't bypass approval.”

Open the Workflow trace expander.

“The trace is how I make the workflow inspectable. It records collection, generation, validation, approval, and export steps with counts, timing, attempts, and redacted errors. It stores facts about the run, not raw private note text or credentials.”

## 2:35–3:35 — Show messy input and judgment

Choose Mobile and backend mismatch — Week C, load evidence, and generate. Show the blocked finding, source records, and missing deadlines under Internal actions.

“This example is a user-supplied reconstruction, not a live repository. The backend change was merged, but mobile is still blocked on the contract.

“The validator flags these mixed signals for review. They can coexist, so this is a conservative flag—not proof that one source is false.

“The manager must clarify the situation, correct the draft if needed, and record supporting evidence and an explanation. A checkbox alone can't dismiss the block.

“These three actions have owners but no deadlines. The dates remain unconfirmed instead of being invented.”

Do not invent a confirmation to get an approved result. Showing the blocked state is sufficient.

## 3:35–4:25 — Explain tests and learning

Show the saved reliability result and case breakdown.

“The suite passes 97 automated tests covering 48 named scenarios, messy inputs, API failures, privacy, approval, exports, Drive note formats, tool selection, traces, and the live-smoke estimate path. These are software tests, not 48 live Claude evaluations.

“One important correction was in my evaluator: a valid citation doesn't prove the sentence is true. I separated citation validity from factual grounding, which now requires claim-by-claim review.

“That lets me explain what the results establish without claiming more than I measured.”

## 4:25–5:00 — Costs, limits, and next step

Return to the free-simulation label.

“Public examples make no paid requests. Live generation requires a budget, reserves an estimated maximum before each attempt, and limits retries. It controls this workflow, not other spending on the Anthropic account.

“The private live smoke collected 26 GitHub records and one Drive note, called Claude once, approved the validated report, and exported the approved files. New approved runs also export a workflow trace. I still have not measured the 60 percent time-saving target with another user.

“The next improvement comes from a manager using it, recording corrections, and turning failures into regression tests.”

## Interview preparation

Be ready to explain why there is no vector database, why approval belongs to a report version, why cost reservations remain after uncertain requests, and why valid citations are not factual proof.

“Improving itself” means feedback leads to reviewed code and tests—not automatic production changes. Haiku remains provisional; old proxy scores are not a controlled model comparison. Sensitive-data patterns and conflict detection have limits, and hosted SQLite is not a durable production audit service.
