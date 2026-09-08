# Reliability verification — 8 September 2026

Implementation commit: trace upgrade pushed on `main`.

## Executed checks

- Current checkout after the trace upgrade: 97 pytest tests passed; Ruff, strict mypy, and the secret scan passed locally and in GitHub Actions run `34221962129`.
- The suite includes Drive text and DOCX note handling, the live-smoke harness, tool selection, trace storage, trace redaction, workflow-trace export, and the estimate-only smoke path.
- Browser: normal free sample reached approval and exposed the approved downloads. Editing the approved summary removed the downloads and required reapproval. The unsafe sample displayed masked-source/instruction warnings and a disabled approval control before review.
- Client PDF and DOCX: generated from the same sample report; rendered and visually inspected.
- Submission PDFs: evaluation 3 pages, case study 5 pages, AI collaboration 7 pages; all final pages inspected. Each file is under 1 MB. They remain drafts for my personal review.
- New Anthropic requests during the first reliability upgrade: zero. The later private live smoke used one Haiku request under a `$0.08` cap. The trace upgrade used no new Anthropic requests.
- GitHub CI verification job passed for the implementation commit on Linux. Public Streamlit showed the revised free workflow without requiring sign-in, and loading the normal sample produced five evidence records. Public screenshot: `evidence/reliability/public-updated.png`.

## Remaining release evidence

The tests use synthetic fixtures and reconstructed examples. The private live smoke separately verified GitHub, Drive note collection, Google Docs access, Claude generation, approval, and exports. Human factual review, a consenting user observation, final document review, Loom recording, and portal submission remain outstanding.

The expanded case names and development/reserved split were fixed before the first expanded execution. Expectations were subsequently made more explicit in the case catalog; reruns are regression checks, not a fresh unseen benchmark.
