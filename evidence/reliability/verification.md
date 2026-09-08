# Reliability verification — 8 September 2026

Implementation commit: `eec5fe0`.

## Executed checks

- Original checkout: 82 pytest tests passed; Ruff and strict mypy passed; supported-pattern secret scan passed.
- Clean local Git clone with a newly created Python 3.12 virtual environment: installed using `requirements-lock.txt`; all 82 tests, Ruff, mypy, and secret scan passed again. This is not a production credential smoke test.
- Browser: normal free sample reached approval and exposed six downloads. Editing the approved summary removed the downloads and required reapproval. The unsafe sample displayed masked-source/instruction warnings and a disabled approval control before review.
- Client PDF and DOCX: generated from the same sample report; rendered and visually inspected.
- Submission PDFs: evaluation 3 pages, case study 4 pages, AI collaboration 5 pages; all final pages inspected. Each file is under 1 MB. They remain drafts for Elvis's personal review.
- New Anthropic requests during this upgrade: zero.
- GitHub CI verification job passed for the implementation commit on Linux. Public Streamlit showed the revised free workflow without requiring sign-in, and loading the normal sample produced five evidence records. Public screenshot: `evidence/reliability/public-updated.png`.

## Remaining release evidence

The tests use synthetic fixtures and reconstructed examples. They do not establish live source permissions, production confidentiality detection, Anthropic semantic quality, or measured user time savings. Live source smoke checks, human factual review, a consenting user observation, final document review, Loom recording, and portal submission remain outstanding.

The expanded case names and development/reserved split were fixed before the first expanded execution. Expectations were subsequently made more explicit in the case catalog; reruns are regression checks, not a fresh unseen benchmark.
