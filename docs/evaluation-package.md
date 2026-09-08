# DeliveryBrief Evaluation Package

## What this evaluation establishes

DeliveryBrief has an expanded set of 48 named workflow cases, plus regression, interface, integration, structure, CLI, and trace tests. The current local suite has 97 passing tests. The 48 named cases pass as 36 development cases and 12 reserved cases. These software checks cover intake, validation, approval, exports, privacy patterns, tool selection, trace redaction, cost-control paths, and failure handling. They sit beside the public app run, the private live-source smoke test, earlier capped Haiku runs, and CI evidence.

The executed results are in `evaluation/results/reliability-v2.json`. The complete test output is reproducible with `pytest --junitxml=output/reliability-tests.xml` followed by `python scripts/summarize_reliability.py`. I use GitHub Actions as the remote verification check; the refactored `main` branch passed CI in run `34189560471` after a Linux import-path issue in the structure test was corrected. The trace upgrade was then verified locally before push; it adds tests around tool selection, trace storage, trace redaction, approval invalidation, workflow-trace export, and the estimate-only live-smoke CLI path.

External research helped sanity-check the problem. PMI's communications report links unclear project communication with project risk. DORA's value-stream guidance points teams toward information flow, wait time, and handoffs when looking for delivery bottlenecks. DORA's loosely coupled teams guidance also treats cross-team dependencies as measurable delivery friction. GitHub Projects and Issues connect planning to issues and pull requests, but they do not write the weekly client update for the manager. I used these sources to shape the problem and metrics, not as evidence that DeliveryBrief has adoption. Sources: `https://www.pmi.org/learning/library/en-2013-pulse-high-cost-low-performance-13512`, `https://dora.dev/guides/value-stream-management/`, `https://dora.dev/capabilities/loosely-coupled-teams/`, and `https://github.com/features/issues`.

## Baselines and provenance

I supplied three anonymized reconstructed operating weeks: payment retries, mobile/backend coordination, and an ingest migration revert. Their manual preparation estimates are 55, 75, and 40 minutes, with a median of 55 minutes. No stopwatch measurement or independent interview is claimed.

The private live-source smoke test collected 26 GitHub records and one Google Drive note for 7-8 September 2026. The first run exposed a real file-handling gap: the uploaded note was a `.txt` file, while the adapter only listed native Google Docs. I added Drive note support for `.txt`, `.md`, `.csv`, and `.docx`, kept unsupported files explicit, and reran the smoke. Claude Haiku returned a valid structured report in one attempt. The conservative request estimate was `$0.049441`; the actual estimated cost was `$0.018218`; latency was 22,109 ms. Approval produced six exports from the stored approved snapshot at the time of the run. The later trace upgrade adds a seventh approved export, `Workflow trace.json`, without requiring another paid model call. The public redacted summary is `evidence/live-smoke/live-smoke-summary.md`.

The earlier Haiku structured-workflow run returned 9 of 9 under a v1 proxy evaluator, costing an estimated $0.025316 with median generation latency of 6,444 ms. The direct-prompt baseline returned 1 of 9 under a different keyword evaluator and cost an estimated $0.007295. The original JSON files remain unchanged. Because the scorers differed, this is learning evidence rather than a controlled model-quality comparison.

The old measure named grounding checked citation IDs, coverage counted handled evidence IDs, and action accuracy counted expected owners. These proxies could reward an incorrect statement with a valid citation. The revision corrects the terminology and method. A new paid model comparison was not run; additional spending was not authorized.

## Measures and thresholds

Citation validity is the share of cited IDs present in the supplied evidence. It is reported separately from factual grounding.

Factual grounding is supported claims divided by reviewed claims. Every summary, report item, and action is presented for review against its evidence. A named reviewer and an exact report fingerprint are required. The release target is 95 percent because unsupported client claims create trust risk.

Coverage is expected facts represented divided by all expected facts. A warning about an evidence record does not automatically count as factual coverage. The target is 90 percent because omitted delivery risks can mislead the client even in otherwise accurate prose.

Action accuracy uses one-to-one reviewed matches of task, owner, and due date. Its F1 score is twice the matched count divided by the number of output actions plus expected actions. Extra invented actions reduce the score. The target is 85 percent.

Exception handling measures whether the expected workflow behavior occurred. Correct blocking and unnecessary blocking are recorded separately. Privacy, approval, session isolation, and budget checks are hard release gates.

Weighted reviewed quality remains 35 percent grounding, 25 percent coverage, 20 percent action accuracy, and 20 percent exception behavior. Reports without completed factual review remain `awaiting_review`; their factual scores are null, not 100 percent.

Time reduction is (manual task time minus app task time) divided by manual task time, reported across comparable paired tasks. Include collection, correction, review, and export. The median 60 percent target remains unmeasured.

## Test set

| Group | Cases | What the tests exercise |
| --- | --- | --- |
| Normal reporting | 6 | Quiet weeks, accepted work, ongoing work, action fields |
| Messy notes and PRs | 8 | Vague descriptions, typos, several owners, duplicates, Unicode |
| Context and timelines | 8 | Reverts, undeployed merges, conflicts, dates, dependencies |
| Privacy and hostile text | 8 | Fake secrets, personal data, instructions, private links, uncertainty |
| API and input failures | 8 | Pagination, timeout, rate limit, denied access, invalid and oversized input |
| Approval and exports | 10 | Direct bypass, edits, evidence changes, sessions, legacy records, documents, CSV, budgets |

Each catalog case identifies synthetic provenance, its input, expected behavior, test reference, executed outcome, and failure explanation. The reconstructed B/C/D examples remain separately labeled in the app. Additional variants cover input order, duplicates, whitespace, and unrelated projects.

The last two cases in each group were reserved before the first expanded execution. All 12 passed their first executed assertions. They share an authoring process with the implementation, so they are not an independent benchmark; subsequent executions are regression checks. Any case used for a later fix loses its unseen status.

The trace tests are intentionally separate from the 48 scenario cases. They check that demo mode selects sample evidence and skips Claude, live mode without a positive budget skips Claude before any paid call, Drive and user-supplied inputs are labeled correctly, trace records survive through generation/validation/approval/export, editing after approval blocks export, sensitive values are redacted, and the live-smoke estimate path does not construct an Anthropic generator.

## Failures and learning

The earlier storage method approved reports without revalidation. Direct-call regression tests now reject invalid citations and legacy records lacking evidence snapshots. Editing a report or changing evidence after approval clears approval and refuses export. This check runs below the interface.

The v1 citation proxy could award full credit to an unsupported statement. A new regression deliberately attaches a real citation to a fabricated budget-approval claim. Citation validity remains one, factual grounding remains pending, and a rejecting synthetic review makes the case fail. The synthetic reviewer is test data, not my human review.

During the revision, the phone detector damaged ISO timestamps. Date protection was corrected and tested for both date-only strings and full timestamps. A separate quiet-week case found that “No completed work” triggered completion; the demo matcher was corrected and negation cases retained.

Earlier Anthropic schema rejection and the missing cross-repository/action findings remain in the historical evidence. Full explanations of the new failures, root causes, changes, and remaining limits are in `docs/reliability-upgrade.md`.

## Costs and remaining evidence

The live smoke used one paid Haiku request under the `$0.08` cap. Public scenarios remain free simulations. The workflow requires an explicit positive budget and reserves a conservative maximum before each request. Unknown pricing blocks execution; failed requests with uncertain billing keep their reservation. The maximum is three attempts and hidden SDK retries are disabled. The CLI has an estimate-only path so I can check configured sources and request cost before constructing the Anthropic generator.

Application reservations do not cap unrelated account spending. Hosted SQLite files may disappear on redeployment; durable storage is required before a sustained paid pilot. Estimates are not provider billing guarantees.

Remaining evidence before stronger adoption claims: a consenting user's complete timed task, my final claim/code review, and the demo video. The live-source path has been checked privately with GitHub, Drive notes, Google Docs API access, and Claude Haiku. Software tests still do not replace a timed user study.
