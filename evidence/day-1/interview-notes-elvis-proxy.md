# Day 1 target-user perspective

## Interview details

- Date: Monday, 7 September 2026
- Format: Elvis-provided target-user perspective, written in chat
- Target user role: project/product manager handling several projects
- Reader of weekly updates: Managing Director
- Recording used: no
- Consent to quote anonymously: not applicable; this is Elvis's own supplied perspective

## Important boundary

This is not presented as an external user interview. It is a first Day 1 proxy based on Elvis's own understanding of a project/product manager workflow. A separate external user interview is still useful before final submission if time allows.

## Workflow summary

The manager prepares weekly updates for the Managing Director across several projects. The update is meant to explain what changed, what is blocked, what needs attention, and what the MD should understand without reading raw engineering material.

## Sources used

- GitHub pull requests
- GitHub commits
- GitHub issues, when they exist and are linked properly
- Notes from developers

## Main bottleneck

The most annoying part is reading PRs that are not clearly tied to issues, tasks, or useful commit messages. This slows the manager down because they have to infer what actually happened and decide whether the work is complete, blocked, or still unclear.

## Common mistakes and risks

- Completed work can be missed if PR titles are vague.
- A blocker can be hidden inside developer notes and not make it into the MD update.
- Action items can be written without an owner or due date.
- The update can include too much raw technical detail and not enough decision-ready summary.
- The final document can be inconsistent or poorly formatted.

## Information that must never reach the MD or a client

This means information that is private, risky, or not ready to share. Examples:

- API keys, tokens, passwords, or credentials
- Personal emails, phone numbers, or private user data
- Internal blame or sensitive staff comments
- Security weaknesses that should be handled privately first
- Unconfirmed launch dates or promises
- Client names or company names in a public demo
- Private repository links
- Cost, billing, or contract details not meant for that audience

## Trust requirements

The manager would trust the tool if it:

- Handles GitHub and developer-note context correctly
- Produces clean PDF or document exports
- Keeps formatting consistent
- Makes evidence easy to inspect
- Allows the manager to improve the final output
- Does not break during the normal weekly workflow

## Rejection conditions

The manager would reject the tool if it:

- Gives inconsistent summaries
- Breaks often
- Produces poorly formatted documents
- Misses important context
- Creates output that requires too much manual fixing

## Design implications for DeliveryBrief

- Evidence IDs are required because vague PRs and notes need traceability.
- Approval stays human-controlled because the manager owns the update.
- Secret and PII checks matter because private details must not pass into final output.
- Export quality matters because trust depends partly on the final document looking professional.
- The v1 system should stay narrow and reliable instead of trying to handle every possible source.
