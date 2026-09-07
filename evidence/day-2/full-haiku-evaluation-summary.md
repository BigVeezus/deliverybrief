# Full Haiku evaluation summary

## Run

- Date: Monday, 7 September 2026
- Dataset: `evaluation/cases`
- Model: `claude-haiku-4-5`
- Cap used: `$0.30` maximum estimated cost
- Output: `evaluation/results/full-haiku.json`

## Result

- Scored report cases: 9
- Passed report cases: 9
- Pass rate: 100%
- Integration contract case: case 09 covered by `tests/test_integrations.py::test_github_retries_transient_failure`
- Estimated actual model cost for the nine paid cases: `$0.025316`
- Median latency: 6,444 ms

## What changed during the run

The first full run exposed two useful problems:

- Case 03 missed one cross-repository evidence item in the scored report sections.
- Case 06 allowed action-like evidence to disappear when the model did not create an action item.

Both issues were fixed before the final full run:

- The Claude prompt now says important evidence must appear in a substantive report section, not only the executive summary.
- The evaluator now reports used and missing evidence IDs.
- The validator now flags action-like evidence when no action owner or due date is present in the draft.
- Tests were added for strict Anthropic schema behavior, error pass-rate accounting, validator-handled evidence coverage, and missing action-like evidence.

## Why this matters

The result supports using Haiku as the default model for now. It passed the full current suite at low cost, while Sonnet remains gated behind explicit approval.
