# DeliveryBrief Quest control sheet

Use this as the single checklist for the active Quest. Evidence links and result values must be added only after they exist.

## Submission status

| Portal slot | Prepared now | Still required before submission |
|---|---|---|
| Working System | Public repository, tested local demo, deployed Streamlit URL, and phone screenshot showing public access: https://deliverybrief.streamlit.app/ | Repeat one logged-out check before final submission |
| Evaluation Package | Source doc updated with Day 1 baseline, Haiku results, cost controls, and regression fixes | Rebuild final PDF after direct-prompt decision, target-user timing, edit-rate, and final review |
| Case Study | Source doc updated with workflow rationale, manual baseline estimates, Haiku results, and three failure/fix notes | Add observed app-run screenshots, edit-rate, and recorded user reaction before final PDF |
| AI Collaboration Note | Rendered PDF covering planning, implementation, corrections, and verification | Append live-integration, field-test, hardening, document review, and video-review entries |
| Demo Video | Five-minute script and shot order | Record and publish a no-login Loom after the live evidence and final metrics are ready |

## Evidence to collect next

- [x] Deadline confirmation requested; Erwin confirmed on 7 September 2026 that the Quest timer is active, but did not provide an exact timestamp deadline in the reply.
- [x] Record the approximate Quest acceptance time: Monday, 7 September 2026 at 3:00 PM WAT.
- [x] Re-test https://deliverybrief.streamlit.app/ while logged out from a phone; screenshot saved in `evidence/day-1/screenshots/mobile-public-url.png`.
- [x] Record Elvis-provided target-user perspective in `evidence/day-1/interview-notes-elvis-proxy.md`.
- [ ] Complete one external target-user interview using `docs/user-interview.md` if time allows.
- [x] Collect three anonymized reconstructed weekly examples in `evidence/day-1/weekly-examples-index.md`.
- [x] Record manual time estimates for the three examples in `evidence/day-1/baseline-log.csv`.
- [x] Run the Day 1 reconstructed examples through `evaluation/day1/cases.json`; result saved to `evaluation/results/day1-demo.json`.
- [x] Run Anthropic Haiku on the Day 1 reconstructed examples without exposing the API key; result saved to `evaluation/results/day1-haiku.json`.
- [x] Record model cost-control policy in `evidence/day-2/model-cost-control.md`.
- [x] Add local `--estimate-only` and `--max-estimated-cost-usd` protections before paid Anthropic evaluation runs.
- [ ] Verify repository-restricted, read-only GitHub access.
- [ ] Share one anonymized Google Drive folder with the service account as Viewer.
- [x] Run the full ten-case Haiku evaluation with a `$0.30` cap; 9 of 9 scored report cases passed and the transient API case is covered by automated test.
- [x] Run direct-prompt Haiku baseline with a `$0.07` cap; result saved to `evaluation/results/direct-prompt-haiku.json`.
- [ ] Run Sonnet only if Elvis explicitly approves the extra cost for a named comparison.
- [x] Record at least three failures, fixes, and regression outcomes in the Evaluation Package and Case Study source docs.
- [ ] Observe one unaided manager run and one follow-up feedback run.
- [x] Capture one Elvis public Streamlit app run with approved exports in `evidence/day-2/app-run/`.
- [ ] Replace remaining draft evidence-boundary sections after direct-prompt/user-run evidence is ready.
- [ ] Add real screenshots and a before/after excerpt to the case study.
- [ ] Review every sentence in Elvis's own words and rebuild the PDFs.
- [ ] Rebuild PDFs after Day 1 summary and later measured results are ready.
- [ ] Record the Loom, test it while logged out, and verify the five-minute limit.
- [ ] Attach all five deliverables, open each from the portal, and capture the success screen.

## Daily rule

Push an auditable commit and keep a local backup at the end of each day. The portal does not require daily uploads. Upload the final attachments only after they are stable and verified.
