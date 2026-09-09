# DeliveryBrief Evaluation Package

## 1. What I evaluated

DeliveryBrief is a workflow tool for a project/product manager who has to prepare weekly delivery updates from messy engineering sources.

The main question I tested was simple:

> Can a manager turn GitHub activity and developer notes into a client-ready weekly update without losing important context, inventing facts, leaking private details, or depending on perfect prompting?

I evaluated DeliveryBrief across four areas:

- Evidence collection from GitHub, Google Drive notes, and pasted developer notes
- Draft generation with required evidence references
- Validation, approval, and export controls
- Reliability across messy notes, missing context, failures, privacy risks, and repeated runs

The current version has:

- 48 named workflow cases
- 97 automated tests
- Five public-safe demo scenarios
- One private live smoke test using GitHub, Google Drive, Google Docs access, and Claude Haiku
- Client PDF, DOCX, email, CSV, JSON, run summary, and workflow trace exports

## 2. Why this problem matters

Weekly delivery updates look simple, but in real project work they are often built from scattered, incomplete information.

External research matched the pain points I observed:

- PMI reports that ineffective project communication creates major delivery risk, especially when teams fail to communicate goals, actions, and business impact clearly.  
  Source: [PMI — Essential Role of Communications](https://www.pmi.org/learning/thought-leadership/pulse/essential-role-communications)

- DORA’s delivery guidance treats handoffs, wait time, and cross-team dependencies as real software-delivery bottlenecks, not just “communication problems.”  
  Source: [DORA — Loosely Coupled Teams](https://dora.dev/capabilities/loosely-coupled-teams/)

- GitHub supports linking issues, pull requests, labels, projects, and dependencies, but those records still do not automatically become a clean weekly update for an MD or client.  
  Sources: [GitHub — Linking PRs to issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue), [GitHub — Planning and tracking with Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)

The product decision was therefore not “summarize GitHub.” The real workflow is:

> collect evidence → detect what is missing or risky → draft the update → let a human review it → export a clean client version.

## 3. Baseline examples

I used three anonymized operating weeks based on the kind of project-management updates I handle:

| Week | Problem pattern | Manual estimate |
|---|---:|---:|
| Payment retry risk | PRs were vague; old queued jobs still created release risk | 55 min |
| Mobile/backend mismatch | Two repos changed a shared contract without clear written coordination | 75 min |
| Migration revert | Git history showed a revert, but the reason was only in notes | 40 min |

Median manual estimate: 55 minutes.

These examples are not random toy prompts. They test the exact problem DeliveryBrief is built for: GitHub shows part of the truth, but the missing business context usually sits in developer notes, calls, or chat.

## 4. Live smoke test

I also ran the private live path locally.

Live setup: GitHub repository activity, one Google Drive developer note, Claude Haiku, a `$0.08` budget cap, no public fallback, and no private raw content committed.

Result:

| Check | Result |
|---|---:|
| GitHub records collected | 26 |
| Google Drive notes collected | 1 |
| Claude structured report | Passed in 1 attempt |
| Estimated request cost before run | `$0.049441` |
| Actual estimated cost after run | `$0.018218` |
| Latency and approval/export | 22.1 sec; passed from stored snapshot |

This test also found a useful real issue: my uploaded developer note was a `.txt` file, not a native Google Doc. I updated the Drive adapter to support common note formats including `.txt`, `.md`, `.csv`, and `.docx`.

That improvement matters because real PM notes do not always arrive in one perfect format.

## 5. Evaluation metrics

I used metrics that connect directly to client risk.

| Metric | What it checks | Why it matters |
|---|---|---|
| Citation validity | Every cited evidence ID exists | Prevents fake references |
| Factual grounding | Claims are supported by the cited evidence | Prevents false client updates |
| Coverage | Expected important facts appear in the update | Prevents missing risks or blockers |
| Action accuracy | Task, owner, and due date are correct | Prevents weak follow-up |
| Exception handling | The workflow blocks or warns correctly | Prevents unsafe approval |
| Privacy safety | Secrets, private links, PII, and internal blame are kept out | Protects client trust |
| Approval control | Exports only come from approved snapshots | Prevents accidental wrong versions |
| Cost control | Paid model calls require an explicit budget | Prevents surprise spend |

Release targets:

- 95% factual grounding after review
- 90% expected-fact coverage
- 85% action accuracy
- 90% scenario pass rate
- 100% pass for privacy, approval, and budget-control gates

## 6. Test set

The test set has 48 named workflow cases.

| Group | Cases | Examples |
|---|---:|---|
| Normal reporting | 6 | Completed work, quiet week, ongoing work |
| Messy notes and PRs | 8 | “wip” PRs, missing descriptions, typos, duplicate notes |
| Context and timelines | 8 | Reverts, merged-but-not-deployed work, stale dates, cross-repo dependencies |
| Privacy and hostile content | 8 | Fake secrets, private emails, prompt injection, unsupported promises |
| API and input failures | 8 | Pagination, timeout, rate limit, denied access, malformed input |
| Approval and exports | 10 | Edit after approval, direct bypass, session isolation, unsafe CSV cells |

The goal was not to make the app pass happy-path examples. The goal was to test the ugly cases a PM actually sees.

## 7. Important failures found and fixed

### Failure 1 — Approval was too easy to trust

Earlier, approval depended too much on the interface state.

Fix:

- Approval now revalidates the stored evidence snapshot
- Editing a report removes approval
- Changing source evidence removes approval
- Exports fail if the approved report version does not match the current report

Why it matters:

A manager should not accidentally export an old or unsafe version.

### Failure 2 — A valid citation did not prove the claim was true

The first evaluator treated “has a real evidence ID” as grounding. That was too weak.

Fix:

- Citation validity is now separate from factual grounding
- Grounding requires claim-by-claim review against evidence
- Unsupported claims remain review failures even if they cite a real record

Why it matters:

A wrong statement with a real citation is still wrong.

### Failure 3 — Notes were not always Google Docs

The first live Google test found that a developer note could be uploaded as plain text.

Fix:

- Added support for native Google Docs, `.txt`, `.md`, `.csv`, and `.docx`
- Unsupported files now fail clearly instead of silently disappearing

Why it matters:

A workflow tool should handle normal messy inputs, not only ideal inputs.

### Failure 4 — Negation changed meaning

A test case with “no completed work” was initially at risk of being treated like completed work.

Fix:

- Added regression coverage for quiet weeks and negated statements
- The app now treats “not deployed,” “not confirmed,” and “no completed work” carefully

Why it matters:

Client updates must not turn uncertainty into progress.

## 8. Cost and model control

DeliveryBrief does not call Claude automatically.

Claude is only used when the manager clicks **Generate weekly brief** in live mode and a positive budget is configured.

The app:

- Estimates request cost before generation
- Reserves budget before each attempt
- Uses at most three attempts
- Disables hidden SDK retries
- Refuses unknown pricing
- Does not fall back to demo output during live runs

This is intentional. A workflow system should make paid model use visible and controlled.

## 9. What the evaluation proves

This evaluation proves that DeliveryBrief is more than a prompt wrapper.

It has:

- Tool selection
- Source-specific evidence collection
- File-processing paths
- Structured generation
- Deterministic validation
- Human approval gates
- Version-bound exports
- Cost controls
- Workflow trace logging
- Regression tests for messy inputs and unsafe outputs

The public demo is safe to run without credentials. The private live path has also been checked with real GitHub, Google Drive, and Claude access.

## 10. Remaining limits

The current version is intentionally scoped.

Known limits:

- V1 supports one configured project repository
- Multi-repo selection should be added with a strict allowlist, not open-ended access
- Hosted Streamlit storage is not a durable production audit database
- Pattern-based privacy checks cannot understand every confidential business situation
- A full timed user adoption study is still the next best evidence to collect

These are acceptable V1 limits because the core workflow already works end-to-end, and the boundaries are clear.

## 11. Final evaluation summary

DeliveryBrief meets the five-day goal: it turns scattered delivery evidence into a reviewed, exportable weekly update while keeping the human in control.

The strongest evidence is not just that the app generates a report. The stronger point is that it knows when not to approve, when not to export, when not to spend money, and when the evidence is not strong enough.

That is the workflow behavior I wanted to demonstrate.
