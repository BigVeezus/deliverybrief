# Day 2 model and cost-control note

## Cost rule from this point

Use Haiku for normal evaluation and development runs. Do not run Sonnet again unless Elvis explicitly approves it for a small, named comparison.

## Why

The first clean Haiku run passed all three Day 1 reconstructed cases and cost about 1.6 cents total:

- Week B: $0.005295
- Week C: $0.004583
- Week D: $0.005589

Total recorded Haiku cost: $0.015467.

An earlier Sonnet attempt completed two cases and cost about 6.7 cents for those two completed results before a schema/output issue made the result unsuitable as official evidence. A later Sonnet rerun was stopped after Elvis asked to cap costs.

## Current model evidence

Haiku fixed the action-splitting weakness seen in the deterministic demo generator:

- Demo generator Day 1 pass rate: 0 of 3
- Haiku Day 1 pass rate: 3 of 3
- Haiku grounding: 100% on all three cases
- Haiku coverage: 100% on all three cases
- Haiku action accuracy: 100% on all three cases
- Haiku safety: passed on all three cases

## Remaining model work

Before final submission, run the full ten-case evaluation with a small approved budget. Prefer Haiku first. Only run Sonnet if Haiku fails an important case or if a final benchmark comparison is worth the extra spend.
