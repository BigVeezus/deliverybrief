# DeliveryBrief Decision Record

This record explains the choices I made while defining and building DeliveryBrief. I record the constraint and the trade-off so I can defend each choice and change it when the evidence changes.

## 1 Weekly delivery updates

**Context and evidence.** A project or delivery manager repeatedly gathers engineering activity and human project notes before writing a client update. The workflow has a stable trigger, identifiable inputs, a human approval point, and an output that can be compared with source evidence.

**Alternatives considered.** Support-request triage and release-readiness reporting.

**Decision.** I chose the weekly delivery update workflow.

**Reason.** It is narrow enough for five days and exposes the central engineering problem: turning incomplete structured and unstructured records into a reviewable result.

**Trade-off.** The first version improves one reporting workflow rather than automating a wider operations process.

**Revisit when.** The target-user interview shows that another recurring task consumes materially more time or creates greater risk.

## 2 Project or delivery manager as the user

**Context and evidence.** This person owns the report but should not need to understand APIs, prompts, or data schemas.

**Alternatives considered.** An engineering lead or company founder.

**Decision.** I designed for a project or delivery manager.

**Reason.** This makes the non-developer usability requirement concrete and keeps external communication under an accountable owner.

**Trade-off.** Technical diagnostic detail remains available as evidence rather than dominating the client output.

**Revisit when.** Observation shows that an engineering lead, rather than the delivery manager, performs and approves the entire workflow.

## 3 DeliveryBrief as the title

**Context and evidence.** The user needs a short delivery report. AI is a mechanism, not the requested outcome.

**Alternatives considered.** DeliveryOS, ProjectPulse AI, and WeeklyOps Agent.

**Decision.** I named the system DeliveryBrief.

**Reason.** Delivery identifies the work domain and Brief describes the output. The name can be understood without explanation or an AI label.

**Trade-off.** The name is less distinctive than a marketing name, but it is clearer in a five-minute assessment.

**Revisit when.** User testing finds the name confusing or the product expands beyond weekly delivery reporting.

## 4 GitHub and Google Docs

**Context and evidence.** GitHub contains delivery activity and status. Google Docs contains meeting context, decisions, risks, and client language. The candidate has confirmed that both are used in the target workflow; the interview must still document the exact sequence.

**Alternatives considered.** Slack, Jira, and manual file upload.

**Decision.** I use GitHub and Google Docs as read-only sources.

**Reason.** Together they test reconciliation between structured system activity and less structured human judgment.

**Trade-off.** Service-account and token setup adds operator work. Slack could add context but would add message-selection and privacy problems.

**Revisit when.** The interview shows that a different source is authoritative or one selected integration is rarely consulted.

## 5 Python and Streamlit

**Context and evidence.** The Quest allows five days and asks for a simple interface that a non-developer can operate.

**Alternatives considered.** A TypeScript application and a no-code automation platform.

**Decision.** I use Python for the domain and integration code and Streamlit for the interface.

**Reason.** This keeps the implementation small enough to test while still exposing typed schemas, adapters, validation, and logs.

**Trade-off.** Streamlit offers less control than a custom frontend and is not the intended long-term multi-tenant architecture.

**Revisit when.** Adoption requires organization authentication, richer navigation, or concurrent editing.

## 6 Anthropic instead of new OpenAI spend

**Context and evidence.** The candidate has funded Anthropic API credits. No dependable free OpenAI API allowance is available for the build.

**Alternatives considered.** Purchasing OpenAI API credit or building a multi-provider abstraction immediately.

**Decision.** I use the Anthropic API and keep model names configurable.

**Reason.** Existing credit removes an avoidable purchasing dependency. Structured Outputs supply the schema guarantee the workflow needs.

**Trade-off.** The Quest does not compare providers. It compares two models from the funded provider.

**Revisit when.** Anthropic account access fails or another provider shows a material quality, cost, or privacy advantage on the same evaluation set.

## 7 Haiku and Sonnet evaluation

**Context and evidence.** Weekly reports should be affordable, but lower cost is useful only if grounding and exception handling remain adequate.

**Alternatives considered.** Always using the largest model or always using the cheapest model.

**Decision.** I evaluate Haiku as the default candidate and Sonnet as the quality benchmark and fallback.

**Reason.** A predefined selection rule turns model choice into a measured engineering decision.

**Trade-off.** Running both models increases evaluation cost once, but prevents an unsupported production choice.

**Revisit when.** Model versions, pricing, or the evaluation distribution changes.

## 8 Human approval

**Context and evidence.** The output is addressed to a client. A wrong completion claim or owner could change expectations.

**Alternatives considered.** Automatic approval after validation.

**Decision.** The delivery manager reviews and explicitly approves every report.

**Reason.** Validators can detect known problems but cannot assume accountability for an external commitment.

**Trade-off.** The system reduces preparation work rather than removing the final human step.

**Revisit when.** A large field study establishes which low-risk messages can be approved by policy.

## 9 Draft but do not send email

**Context and evidence.** Sending is an external side effect and is unnecessary to prove the core workflow.

**Alternatives considered.** Gmail draft creation or automatic email delivery.

**Decision.** The system exports an email file and never sends it.

**Reason.** This keeps the five-day scope on evidence quality and prevents a demo or model failure from contacting a real client.

**Trade-off.** The user completes one manual step in their email client.

**Revisit when.** OAuth, recipient controls, and approval auditing are ready for a controlled pilot.

## 10 Deterministic validation after generation

**Context and evidence.** Schema-valid output can still cite unknown evidence, expose secrets, or omit action owners.

**Alternatives considered.** Prompt-only controls and a second model acting as judge.

**Decision.** I apply deterministic checks after structured generation.

**Reason.** Rules give reproducible approval behavior for conditions that do not require language judgment.

**Trade-off.** Pattern checks can create false positives and do not replace a full privacy system.

**Revisit when.** Evaluation shows repeated failure types that require semantic comparison or organization policy.

## 11 No vector database

**Context and evidence.** The user selects one week's bounded evidence. The first version does not search a large historical corpus.

**Alternatives considered.** Embeddings with a managed vector database.

**Decision.** I pass normalized weekly evidence directly to the generator.

**Reason.** A retrieval layer would add indexing and relevance failure modes without solving a current requirement.

**Trade-off.** The system cannot answer historical questions across many projects.

**Revisit when.** Weekly inputs exceed the model context or the user needs cross-period retrieval.

## 12 Anonymized public demo

**Context and evidence.** Reviewers need an accessible workflow, but client and repository information cannot be published.

**Alternatives considered.** A private local-only demonstration or public real data.

**Decision.** The hosted application uses labeled sample evidence; real-user evaluation uses approved anonymized records.

**Reason.** This gives reviewers a working path without disclosing a client's information.

**Trade-off.** The public example cannot by itself prove adoption or time savings.

**Revisit when.** A client explicitly approves a public case or reviewer authentication becomes available.

## 13 One project in version one

**Context and evidence.** The Quest measures a complete workflow rather than organization-wide configuration.

**Alternatives considered.** Multi-project setup and per-user OAuth.

**Decision.** Version one supports one configured project.

**Reason.** This reserves time for evaluation, failure handling, and handoff.

**Trade-off.** An operator edits configuration before a different team can use the system.

**Revisit when.** A second team begins a pilot.

## 14 Metric thresholds

**Context and evidence.** The email must save time without trading away factual control.

**Alternatives considered.** A single satisfaction score or subjective reviewer rating.

**Decision.** The release gates are 60 percent median time reduction, 95 percent grounding, 90 percent coverage, 85 percent action accuracy, all safety cases, and at least 9 of 10 total cases.

**Reason.** Grounding and safety receive the strictest thresholds because an unsupported client claim creates more risk than a missing low-priority detail.

**Trade-off.** The initial ten-case sample is too small for a broad reliability claim.

**Revisit when.** Real-user results show that these thresholds do not predict acceptable reports.

