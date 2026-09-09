# DeliveryBrief AI Collaboration Note

## Purpose

This note explains how I used AI during the DeliveryBrief Quest.

I used AI to move faster, not to remove my own judgment from the work. My process was simple: I used AI to help plan, build, debug, test, and rewrite, then I reviewed the output, corrected the direction, and decided what was accurate enough to keep.

I did not submit AI output blindly. Several times, I rejected wording, changed the product direction, asked for simpler explanations, corrected technical assumptions, and made the documentation more honest and easier to defend in an interview.

DeliveryBrief is still my work. I owned the problem choice, the scope, the user workflow, the trade-offs, the final claims, and the decision to keep the system safe and testable.

## Why I used AI

The Quest asked for a working AI OS mini-system in a short time. I treated AI as a productivity multiplier across the full workflow:

- turning an ambiguous assessment into a practical delivery plan;
- checking whether the project matched the job description;
- scaffolding code faster than I could type everything manually;
- helping me find edge cases I might miss under time pressure;
- generating first drafts of documentation;
- helping debug errors from Streamlit, Google Drive, GitHub, Claude, tests, and exports;
- helping turn failures into regression tests.

The important point is that I did not treat the first output as final. I kept reviewing and pushing back until the system and documents matched what I actually wanted to submit.

## What I personally owned

I chose the DeliveryBrief problem because I have felt this pain myself as a lead engineer. Weekly delivery updates can become messy when the real status is split between pull requests, commits, developer notes, calls, and people’s memory.

I made the key product decisions:

- The target user is a project or delivery manager preparing weekly updates.
- The first version uses GitHub and developer notes.
- GitHub is a strong V1 source because it contains pull requests, commits, reviews, merge history, issues, and reverts.
- Jira was intentionally left out of V1 because it would add another permission system and another mapping problem before the core workflow was proven.
- The system drafts updates but never sends them.
- A human must review and approve the output before export.
- Public demo data must be safe and anonymized.
- Live Claude calls must use a budget cap.
- Failures should be documented and converted into tests instead of hidden.

AI helped me work through these implementations, but I made the decisions and final calls.

## How AI helped and how I controlled it

| Area | How AI helped | What I checked or changed |
|---|---|---|
| Planning | Helped break the Quest into deliverables, risks, and daily work | I chose the final project and scope |
| Product thinking | Helped compare possible bottlenecks and user workflows | I selected weekly delivery updates from my own experience |
| Engineering | Helped scaffold Python modules, Streamlit screens, validators, exports, and tests | I reviewed the behavior and requested changes when the system felt too shallow or too technical |
| Evaluation | Helped create test cases, baseline comparisons, and failure logs | I corrected weak metrics and made the evaluation more practical |
| Writing | Helped draft README, runbook, case study, evaluation package, and this note | I rejected wording that sounded generic, defensive, or too AI-written |
| Debugging | Helped interpret errors and suggest fixes | I decided which fixes were safe to keep |
| Cost control | Helped add estimate-only and budget-cap checks | I set the cost limits and avoided unnecessary paid calls |

## Examples of where I corrected the AI

### 1. I corrected the voice of the documents

Some early drafts described the work from the outside, using wording like “Elvis supplied...” That sounded wrong because this is my submission. I changed the documents to use first-person ownership where it made sense.

Final approach: I say what I chose, observed, changed, tested, and decided.

### 2. I made the evaluation clearer

The first evaluation package was too long and too technical. It explained too much in a way that could bore the reviewer. I asked for a shorter version that focused on the baseline, test set, important results, failures, and business value.

Final approach: the evaluation now explains what was tested, why it matters, what improved, and what still has limits.

### 3. I pushed the project beyond a prompt demo

The job description is not looking for someone who only writes prompts. It is looking for someone who can build workflow systems. I pushed the project to show tool selection, trace logs, validation, approval gates, retries, exports, and reproducible tests.

Final approach: DeliveryBrief behaves like a small workflow system, not just a Claude prompt wrapped in a web page.

### 4. I asked for messy input handling

Real developer notes are not always clean. They can be pasted, uploaded, written as Google Docs, saved as text files, or sent as rough notes. I asked for the system to handle more note types and fail clearly when something is wrong.

Final approach: the system supports live GitHub, Google Drive notes, pasted notes, uploaded JSON, and several document formats for notes.

### 5. I made approval stricter

I did not want the approval button to be fake. The system now ties approval to the exact report version and evidence snapshot. If the report changes after approval, exports are blocked until the report is reviewed again.

Final approach: approval is a real safety gate, not just a UI step.

### 6. I separated public demo evidence from private live testing

The public app uses safe sample data so reviewers can open it without credentials. I also ran a private local smoke test with GitHub, Google Drive notes, and Claude Haiku under a budget cap.

Final approach: the public demo is safe, and the private live path is verified without exposing raw private source text.

## Final reflection

AI made me faster, but it did not replace the work of thinking.

The most useful part of using AI was not the first draft. It was the iteration: asking better questions, rejecting weak answers, finding edge cases, fixing bugs, simplifying explanations, and making sure the final work matched the problem.

That is also how I would use AI in an operations or workflow automation role. I would not just prompt a model and trust it. I would build the workflow around it: inputs, tools, validation, approval, logs, costs, exceptions, and handoff.

DeliveryBrief is my example of that approach.
