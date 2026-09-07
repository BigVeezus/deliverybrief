# DeliveryBrief Quest control sheet

Use this as the single checklist for the active Quest. Evidence links and result values must be added only after they exist.

## Submission status

| Portal slot | Prepared now | Still required before submission |
|---|---|---|
| Working System | Public repository, tested local demo, deployed Streamlit URL, and screenshot showing public sharing enabled: https://deliverybrief.streamlit.app/ | Re-test while logged out from a separate browser, incognito window, or phone |
| Evaluation Package | Rendered PDF with method, cases, current engineering results, and evidence boundary | Add direct-prompt, Haiku, Sonnet, target-user timing, edit-rate, and failure-regression results |
| Case Study | Rendered PDF with scope, title rationale, architecture, choices, and honest current limit | Add observed workflow, screenshots, measured before/after results, and recorded user reaction |
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
- [ ] Run one small Anthropic API request and retain the timestamp result without exposing the key.
- [ ] Verify repository-restricted, read-only GitHub access.
- [ ] Share one anonymized Google Drive folder with the service account as Viewer.
- [ ] Run the ten-case direct-prompt, Haiku, and Sonnet comparisons.
- [ ] Record at least three failures, fixes, and regression outcomes.
- [ ] Observe one unaided manager run and one follow-up feedback run.
- [ ] Replace draft evidence-boundary sections with measured results.
- [ ] Add real screenshots and a before/after excerpt to the case study.
- [ ] Review every sentence in Elvis's own words and rebuild the PDFs.
- [ ] Record the Loom, test it while logged out, and verify the five-minute limit.
- [ ] Attach all five deliverables, open each from the portal, and capture the success screen.

## Daily rule

Push an auditable commit and keep a local backup at the end of each day. The portal does not require daily uploads. Upload the final attachments only after they are stable and verified.
