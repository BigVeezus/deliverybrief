# DeliveryBrief Case Study

## 1. What I built

I built DeliveryBrief, a small workflow system that helps a project/product manager prepare a weekly delivery update from GitHub activity and developer notes.

The user starts with scattered evidence: pull requests, commits, issues, rough dev notes, missing context, and sometimes conflicting messages. DeliveryBrief helps turn that into a reviewed client-ready update with supporting evidence, action items, and exportable documents.

The product name is intentionally plain. “Delivery” is the work being reported. “Brief” is the concise update the manager needs to send. I left “AI” out of the name because the user is buying a dependable reporting workflow instead of another chatbot surface.

## 2. The real workflow problem

The target user is a project/product manager responsible for weekly updates to an MD or client-facing stakeholder.

In that role, the manager usually has to answer questions like:

- What actually moved this week?
- What looks complete in GitHub but still needs review or deployment?
- What is blocked?
- Who owns the next step?
- What should be said to the client?
- What must stay internal?

The awkward part is that the answer rarely lives in one clean place. GitHub gives activity, but developer notes often explain the real state of the work.

For example, a PR can be merged while the work is still unreleased. A developer can mention a blocker in a note without linking it to an issue. A revert can protect production while looking like failure if the business reason is missing. These are the details a PM has to catch before writing an update.

## 3. Why I chose this project

I chose weekly delivery updates because it is a repeatable operations problem with visible inputs, visible outputs, and real business risk.

I have also felt this problem myself as a lead engineer in the past. When delivery information is split across PRs, notes, calls, and people’s memory, the weekly update can become harder than it should be. I have wanted to solve that gap for a while.

It also fits the Applied AI Engineer role. The task needs API integrations, file handling, structured generation, validation, approval, exports, and workflow logging. It is small enough to finish in five days, but serious enough to show how I think about reliability.

That gave me the product direction: build a system that helps a manager move from messy source material to a decision-ready update.

## 4. The old process

Before DeliveryBrief, the manager’s process was manual.

They would open GitHub, scan PRs and issues, read notes from developers, reconstruct the timeline, decide what mattered to the MD or client, remove sensitive details, write the update, create action items, and review everything again.

The slowest part was not typing the final update. The slowest part was understanding the truth behind the week.

I used three anonymized weekly examples to shape the product:

- Payment retry work where GitHub showed fixes, but notes still warned about old queued jobs.
- Mobile work blocked by a backend contract change that was not clearly documented.
- A reporting migration where a reverted PR looked negative until the notes explained why it protected the nightly production window.

The median manual estimate across those examples was 55 minutes.

## 5. The new workflow

DeliveryBrief changes the workflow into six guided steps:

1. Select the reporting week.
2. Fetch work from the configured GitHub repository.
3. Select one or more developer notes from the configured Drive folder, or paste an extra note.
4. Generate a structured weekly brief.
5. Review the evidence, warnings, and action items.
6. Approve and download the final outputs.

The app exports a client PDF, client DOCX, client email draft, internal action CSV, structured JSON, run summary, and workflow trace.

The email is drafted only. DeliveryBrief never sends it automatically because the final external message should stay under the manager’s control.

## 6. Product decisions I made

I kept the first version focused on one project, one GitHub repository, and one Google Drive folder. That made the product safer, easier to test, and easier to demo under the Quest deadline.

I used GitHub and developer notes together because they answer different questions. GitHub shows activity. Notes explain intent, blockers, deployment status, and client context.

I made evidence visible before generation because the manager should know what the system is using. If the wrong note is selected, the workflow should stop early enough for the manager to correct it.

I kept approval human-controlled because client updates carry judgment. A system can check citations, missing owners, secret-looking values, and conflicts. A person still has to decide whether the message is appropriate for the client.

I added a tool selector and workflow trace because the role is about building repeatable systems, not one-off prompting. The trace shows which tools ran, which ones were skipped, what each step produced, how long it took, and whether approval or export was allowed.

## 7. How the system is built

The application is organized into clear layers:

- Source adapters collect from GitHub and Google Drive.
- Intake code normalizes notes, pasted text, and file content into evidence records.
- The generation layer asks Claude for a structured report in live mode.
- Validators check evidence references, privacy patterns, missing action fields, conflicts, and unsafe states.
- The approval service ties approval to the exact report and evidence snapshot.
- Export code creates the client and internal deliverables from the approved snapshot.
- Persistence stores run records, evidence snapshots, findings, approvals, and workflow traces.

This structure matters because each part can be tested or replaced without rewriting the whole app. For example, adding Slack later should mean adding another source adapter, not changing the approval system.

## 8. What changed after testing

Testing changed the product in practical ways.

One live test showed that developer notes may be uploaded as plain text instead of native Google Docs. I updated the Drive adapter so common note formats like `.txt`, `.md`, `.csv`, and `.docx` can be read from the configured folder.

Another test showed that approval needed to be stricter. I changed approval so it belongs to the exact report and evidence snapshot. If the manager edits the report or changes the evidence, the app requires review again before downloads are available.

I also tightened how the system treats evidence. A real evidence ID proves that the source exists, but the manager still has to confirm that the claim is actually supported. That keeps the workflow honest.

Finally, I added regression tests for wording like “not deployed,” “not confirmed,” and “no completed work.” Those small words change the business meaning of a weekly update.

## 9. What works now

The current system works end to end.

I can open the public Streamlit app, load a safe example, generate a weekly brief, inspect the evidence, approve the report, and export the final files.

I also verified the private live path locally with GitHub, Google Drive, Google Docs access, and Claude Haiku under a budget cap. That live run collected GitHub records and a Drive note, produced a valid structured report, passed validation without blocking findings, and exported from the approved snapshot.

The automated test suite covers normal weeks, messy notes, privacy risks, API failures, approval bypass attempts, unsafe CSV values, session isolation, and workflow traces.

The result is a working product that a non-developer can use and an engineer can inspect.

## 10. What I would show in the demo

In the demo, I would show the product as a manager’s workflow rather than a technical dashboard.

I would start with the reporting week, then fetch GitHub work, add developer notes, generate the draft, inspect the evidence, and approve the final report.

Then I would show one messy case: a note says something is not deployed or not confirmed. The important moment is that DeliveryBrief keeps that uncertainty visible instead of turning it into a confident client promise.

I would also briefly open the workflow trace. That part is for the engineering reviewer. It shows that the app is selecting tools, recording state, and enforcing gates behind the interface.

## 11. What I intentionally left out

I kept multi-repo selection out of the first version. It should come next, but only with a strict allowlist so the app stays inside the right project boundary.

I also left Jira out of V1. Jira tickets can add useful planning context, but GitHub is already a strong engineering source because it contains PRs, commits, reviews, merge history, issues, and reverts. For this first version, GitHub plus developer notes was the cleanest way to prove the workflow without adding another permission system and another mapping problem.

I kept automatic email sending out of scope. The current version exports an email draft because sending a client message should remain a human approval decision.

I skipped a vector database for V1. The manager is working with one weekly evidence set, so a general retrieval layer would add complexity before the workflow needs it.

I also kept LangGraph, CrewAI, and n8n out of the deadline build. The orchestration is explicit in Python, so every step remains easy to explain, test, and modify.

## 12. Next two weeks

The next version would focus on real adoption:

- Add multi-repo project allowlists.
- Add per-user authentication and durable storage.
- Observe more managers using it on live updates.
- Measure time to draft, time to approve, edit rate, and warning frequency.
- Add scheduled collection.
- Add controlled Gmail draft creation after approval.

The long-term version would become a small operating layer for weekly delivery communication: sources come in, risks stay visible, updates are drafted, humans approve, and every run leaves a trace.

## 13. Final reflection

DeliveryBrief taught me that the valuable part of an AI workflow is the system around the model.

The model helps write the draft. The product value comes from the evidence boundaries, validation, approval control, exports, and logs that make the draft safe to use.

That is the kind of AI OS workflow I wanted to build for this Quest.
