# Day 2 model and cost-control note

## Cost rule from this point

Use Haiku for normal evaluation and development runs. Do not run Sonnet again unless I explicitly approve it for a small, named comparison.

Before any paid evaluation run, use `--estimate-only` first. When running a paid evaluation, use `--max-estimated-cost-usd` so the command exits before calling Anthropic if the estimate is above the approved cap.

## Pricing used

Pricing checked on 7 September 2026 from Anthropic's official pricing material:

- Claude Haiku 4.5: $1 per million input tokens and $5 per million output tokens.
- Claude Sonnet 5: $2 per million input tokens and $10 per million output tokens.

The estimator is conservative because it assumes every case uses the full configured output limit.

## Why

The first clean Haiku run passed all three Day 1 reconstructed cases and cost about 1.6 cents total:

- Week B: $0.005295
- Week C: $0.004583
- Week D: $0.005589

Total recorded Haiku cost: $0.015467.

An earlier Sonnet attempt completed two cases before a schema/output issue made the result unsuitable as official evidence. A later Sonnet rerun was stopped after I asked to cap costs.

## Estimate commands

Estimate the Day 1 Haiku run without spending money:

```bash
python -m deliverybrief.evaluation --dataset evaluation/day1 --model primary --estimate-only
```

Latest conservative Day 1 Haiku estimate:

- Report cases: 3
- Estimated input tokens: 4,788
- Maximum output tokens: 18,000
- Estimated cost upper bound: $0.094788

Estimate the full ten-case Haiku evaluation without spending money:

```bash
python -m deliverybrief.evaluation --dataset evaluation/cases --model primary --estimate-only
```

Latest conservative full Haiku estimate:

- Report cases: 9
- Estimated input tokens: 11,882
- Maximum output tokens: 54,000
- Estimated cost upper bound: $0.281882

Run only if the estimate is under a chosen cap:

```bash
python -m deliverybrief.evaluation --dataset evaluation/cases --model primary --max-estimated-cost-usd 0.30
```

A test run with a $0.01 cap correctly stopped before model calls.

## Full Haiku result

The final full Haiku evaluation used the same `$0.30` cap and passed:

- Scored report cases: 9
- Passed report cases: 9
- Integration contract case: 1 covered by automated test
- Actual estimated model cost: $0.025316
- Median latency: 6,444 ms

Result file: `evaluation/results/full-haiku.json`.

## Current model evidence

Haiku fixed the action-splitting weakness seen in the deterministic demo generator:

- Demo generator Day 1 pass rate: 0 of 3
- Haiku Day 1 pass rate: 3 of 3
- Haiku grounding: 100% on all three cases
- Haiku coverage: 100% on all three cases
- Haiku action accuracy: 100% on all three cases
- Haiku safety: passed on all three cases

## Remaining model work

Before final submission, run or document the direct-prompt baseline. Only run Sonnet if I explicitly approve the extra cost for a named comparison.
