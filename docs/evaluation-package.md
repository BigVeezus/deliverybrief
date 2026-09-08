# DeliveryBrief Evaluation Package

## What this evaluation establishes

DeliveryBrief has an expanded set of 48 named workflow cases, plus regression and interface tests. The current software suite passes 82 automated tests. The 48 named cases pass as 36 development cases and 12 reserved cases. These are free software contract tests, including mocked APIs and deterministic output. They are not a live Anthropic quality benchmark or evidence of user adoption.

The executed results are in `evaluation/results/reliability-v2.json`. The complete test output is reproducible with `pytest --junitxml=output/reliability-tests.xml` followed by `python scripts/summarize_reliability.py`.

## Baselines and provenance

Elvis supplied three anonymized reconstructed operating weeks: payment retries, mobile/backend coordination, and an ingest migration revert. Their manual preparation estimates are 55, 75, and 40 minutes, with a median of 55 minutes. No stopwatch measurement or independent interview is claimed.

The earlier Haiku structured-workflow run returned 9 of 9 under a v1 proxy evaluator, costing an estimated $0.025316 with median generation latency of 6,444 ms. The direct-prompt baseline returned 1 of 9 under a different keyword evaluator and cost an estimated $0.007295. The original JSON files remain unchanged. Because the scorers differed, this is not a controlled model-quality comparison.

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

## Failures and learning

The earlier storage method approved reports without revalidation. Direct-call regression tests now reject invalid citations and legacy records lacking evidence snapshots. Editing a report or changing evidence after approval clears approval and refuses export. This check runs below the interface.

The v1 citation proxy could award full credit to an unsupported statement. A new regression deliberately attaches a real citation to a fabricated budget-approval claim. Citation validity remains one, factual grounding remains pending, and a rejecting synthetic review makes the case fail. The synthetic reviewer is test data, not Elvis's review.

During the revision, the phone detector damaged ISO timestamps. Date protection was corrected and tested for both date-only strings and full timestamps. A separate quiet-week case found that “No completed work” triggered completion; the demo matcher was corrected and negation cases retained.

Earlier Anthropic schema rejection and the missing cross-repository/action findings remain in the historical evidence. Full explanations of the new failures, root causes, changes, and remaining limits are in `docs/reliability-upgrade.md`.

## Costs and remaining evidence

No new paid Anthropic calls were made for this revision. Public scenarios are free simulations. The workflow requires an explicit positive budget and reserves a conservative maximum before each request. Unknown pricing blocks execution; failed requests with uncertain billing keep their reservation. The maximum is three attempts and hidden SDK retries are disabled.

Application reservations do not cap unrelated account spending. Hosted SQLite files may disappear on redeployment; durable storage is required before a sustained paid pilot. Estimates are not provider billing guarantees.

Release evidence still required: a new human-reviewed model run if spending is authorized, a consenting user's complete timed task, Elvis's final claim/code review, and the demo video. Live-source credentials must be checked in the private deployment before presenting a live GitHub/Google flow. Software test passes do not replace these tasks.
