# Direct-prompt baseline summary

## Run

- Date: Monday, 7 September 2026
- Dataset: `evaluation/cases`
- Model: `claude-haiku-4-5`
- Cap used: `$0.07` maximum estimated cost
- Output: `evaluation/results/direct-prompt-haiku.json`

## Result

- Scored report cases: 9
- Passed report cases: 1
- Pass rate: 11.11%
- Estimated actual model cost: `$0.007295`
- Conservative cost estimate before the run: `$0.056422`

## Important interpretation

This baseline is not proof that Haiku cannot write useful prose. Several outputs were readable. The failure is that direct prompting does not create a reliably auditable workflow:

- no stable evidence IDs in the final text
- no structured schema enforcement
- no deterministic validation after generation
- no approval gate
- no export/run record

Because of that, the automated evaluator could not consistently prove that all expected evidence was covered or that exceptions were handled.

## Comparison

| Run | Passed | Cost |
|---|---:|---:|
| Direct prompt Haiku | 1 of 9 scored cases | `$0.007295` |
| DeliveryBrief Haiku workflow | 9 of 9 scored cases | `$0.025316` |

The DeliveryBrief workflow costs slightly more because it asks for structured output and performs validation, but it produces an auditable result with evidence IDs and approval controls.
