# Day 1 summary

## What was completed

- Quest acceptance time recorded: Monday, 7 September 2026 at 3:00 PM WAT.
- Erwin confirmed that the Quest timer is active.
- Public Streamlit deployment opened on phone: `https://deliverybrief.streamlit.app/`.
- My target-user perspective was recorded.
- Three anonymized reconstructed weekly examples were collected.
- Manual baseline time estimates were recorded for the three examples.
- A separate Day 1 evaluation dataset was created at `evaluation/day1/cases.json`.
- The Day 1 dataset was run through the deterministic demo generator.

## Manual baseline

| Week | Scenario | Manual time estimate |
|---|---:|---:|
| Week B | Payment retry/idempotency risk | 55 minutes |
| Week C | Mobile/backend contract coordination | 75 minutes |
| Week D | Reporting migration/revert context | 40 minutes |

Median manual preparation time: 55 minutes.

## Main problem observed

GitHub activity alone does not explain the delivery state. The manager often has to connect PRs, missing descriptions, cross-repository changes, developer notes, standup context, and hidden blockers before writing a reliable update.

## Day 1 system smoke-test result

Command:

```bash
python -m deliverybrief.evaluation --dataset evaluation/day1 --model demo --output evaluation/results/day1-demo.json
```

Result:

- Scored cases: 3
- Passed cases: 0
- Grounding: 100% on all three cases
- Coverage: 100% on all three cases
- Safety: passed on all three cases
- Main failure: action-item accuracy was 50% on all three cases

## What the failure means

The deterministic demo generator can cite the right evidence and surface blockers, but it does not reliably split one note into multiple action items with different owners. This is a useful baseline finding because the real workflow often contains several actions inside one developer note or standup summary.

## Design implication

DeliveryBrief needs the Claude structured-output path and deterministic validators, not only the simple demo generator. The evaluation should compare:

- direct prompt baseline
- deterministic demo behavior
- Haiku structured-output run
- Sonnet structured-output run
- final validated workflow

## Evidence files

- `evidence/day-1/interview-notes-self-perspective.md`
- `evidence/day-1/weekly-examples-index.md`
- `evidence/day-1/baseline-log.csv`
- `evidence/day-1/screenshots/mobile-public-url.png`
- `evaluation/day1/cases.json`
- `evaluation/results/day1-demo.json`
