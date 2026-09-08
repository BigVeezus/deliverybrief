# DeliveryBrief Quest control sheet

Use this as the single checklist for the active Quest. Evidence links and result values must be added only after they exist.

## Submission status

| Portal slot | Prepared now | Still required before submission |
|---|---|---|
| Working System | Public repository, tested local demo, deployed Streamlit URL, and phone screenshot showing public access: https://deliverybrief.streamlit.app/ | Repeat one logged-out check before final submission |
| Evaluation Package | Source doc updated with Day 1 baseline, Haiku results, cost controls, regression fixes, and private live smoke | Rebuild final PDF after final review |
| Case Study | Source doc updated with workflow rationale, manual baseline estimates, Haiku results, failure/fix notes, and live smoke | Add final screenshot and review before PDF |
| AI Collaboration Note | Source doc covers planning, implementation, corrections, verification, and live smoke | Rebuild after final document review |
| Demo Video | Five-minute script and shot order | Record and publish a no-login Loom after the live evidence and final metrics are ready |

## Evidence to collect next

- [x] Deadline confirmation requested; Erwin confirmed on 7 September 2026 that the Quest timer is active, but did not provide an exact timestamp deadline in the reply.
- [x] Record the approximate Quest acceptance time: Monday, 7 September 2026 at 3:00 PM WAT.
- [x] Re-test https://deliverybrief.streamlit.app/ while logged out from a phone; screenshot saved in `evidence/day-1/screenshots/mobile-public-url.png`.
- [x] Record my target-user perspective in `evidence/day-1/interview-notes-self-perspective.md`.
- [ ] Complete one external target-user interview using `docs/user-interview.md` if time allows.
- [x] Collect three anonymized reconstructed weekly examples in `evidence/day-1/weekly-examples-index.md`.
- [x] Record manual time estimates for the three examples in `evidence/day-1/baseline-log.csv`.
- [x] Run the Day 1 reconstructed examples through `evaluation/day1/cases.json`; result saved to `evaluation/results/day1-demo.json`.
- [x] Run Anthropic Haiku on the Day 1 reconstructed examples without exposing the API key; result saved to `evaluation/results/day1-haiku.json`.
- [x] Record model cost-control policy in `evidence/day-2/model-cost-control.md`.
- [x] Add local `--estimate-only` and `--max-estimated-cost-usd` protections before paid Anthropic evaluation runs.
- [x] Verify repository-restricted, read-only GitHub access through the private live smoke.
- [x] Share one anonymized Google Drive folder with the service account as Viewer.
- [x] Run the full ten-case Haiku evaluation with a `$0.30` cap; 9 of 9 scored report cases passed and the transient API case is covered by automated test.
- [x] Run direct-prompt Haiku baseline with a `$0.07` cap; result saved to `evaluation/results/direct-prompt-haiku.json`.
- [ ] Run Sonnet only if I explicitly approve the extra cost for a named comparison.
- [x] Record at least three failures, fixes, and regression outcomes in the Evaluation Package and Case Study source docs.
- [ ] Observe one unaided manager run and one follow-up feedback run.
- [x] Capture one public Streamlit app run with approved exports in `evidence/day-2/app-run/`.
- [x] Replace remaining draft evidence-boundary sections after live-source smoke evidence.
- [ ] Add real screenshots and a before/after excerpt to the case study.
- [ ] Review every sentence in my own words and rebuild the PDFs.
- [ ] Rebuild PDFs after Day 1 summary and later measured results are ready.
- [ ] Record the Loom, test it while logged out, and verify the five-minute limit.
- [ ] Attach all five deliverables, open each from the portal, and capture the success screen.

## 8 September reliability checkpoint

- Implemented version-bound approval, source snapshots, scoped sessions, conservative budget reservations, upload/paste intake, five free examples, and client PDF/DOCX exports.
- Free verification: automated tests pass locally, including 48 named scenarios. The split is 36 development / 12 initially held-out cases; these are software checks, not a timed user study.
- Rebuilt submission documents for my final review. Earlier "grounding" scores are legacy citation proxies, not verified factual accuracy. See `docs/evaluation-package.md` for the corrected metric definitions.
- Live source smoke passed privately with GitHub, a Drive text note, Google Docs API access, and Claude Haiku under a `$0.08` cap.
- Still required: human claim review, one consenting timed user observation if time allows, my final review, public deployment check, Loom, and portal submission.

## Daily backup rule

Push an auditable commit and keep a local backup at the end of each day. The portal does not require daily uploads. Upload the final attachments only after they are stable and verified.
