# Three anonymized weekly examples

Add one section per weekly example. These do not need to be beautiful. They need to be real enough to score the system against.

Status on 7 September 2026: I supplied three anonymized reconstructed examples from real operating patterns. They are not public production PRs and should not be described that way. They are public-safe examples designed to preserve the workflow shape without exposing private repositories, client names, staff names, or URLs.

## Pattern across the examples

The Git history alone does not show the real state of the work. The missing context is often in developer notes, standups, Slack messages, or someone's head. DeliveryBrief should help the manager connect source activity to decision-ready status without losing blockers, ownership, or evidence.

## Week B

- What happened: Payment retry logic was reworked after duplicate charges appeared in staging. Notification service work was paused.
- GitHub or PR information: `PR 58: retry fix`, `PR 59: add idempotency key to charge handler`, and `PR 60: wip`. PR 58 and PR 60 have no description. PR 59 was merged directly to main without review. PR 60 has been open nine days with no commits since day two.
- Developer notes: Developer 2 said the duplicate charges came from a retry loop with no idempotency key. PR 59 fixes the new path, but old queued jobs may still double-charge on replay. Developer 3 said notifications were deprioritized verbally in standup, with nothing written down.
- What the MD should know: The root cause of duplicate charges is identified and partly fixed. Historic queued jobs are still a risk. Notification work has quietly stopped and no one has told Client A.
- Action items: Developer 2 should confirm whether old queued jobs need a manual drain before release. Developer 3 should close or update PR 60. The PM should tell Client A that notifications slipped.
- Blocker: No one owns the decision on whether to replay or discard the old job queue.
- Manual time estimate: about 55 minutes, mostly reading PR 58 and PR 60 diffs to understand what they actually do.
- Prohibited/private information removed: real client name, repository links, staff names, and staging/payment details that could expose a client or system.

## Week C

- What happened: Mobile app work stalled while waiting on the backend contract. Repo A shipped a schema change that broke the mobile build.
- GitHub or PR information: `Repo A, PR 112: update user response shape` and `Repo B, PR 77: profile screen`. PR 112 was merged Tuesday. PR 77 has had failed CI since Wednesday. Neither PR references the other, and PR 112 has no issue link.
- Developer notes: Developer 1 said the backend change was agreed in a call two weeks ago. Developer 4 said they were never told the field was renamed and found out when CI broke.
- What the MD should know: This is not only a coding issue; it is a coordination issue. Two repositories changed a shared contract without a written agreement. Mobile has lost roughly three days.
- Action items: Developer 1 should document the new response shape and post it where mobile can see it. Developer 4 should unblock PR 77 once the shape is confirmed. The tech lead should decide whether contract changes need a written sign-off step.
- Blocker: Mobile cannot progress until the field naming is confirmed.
- Manual time estimate: about 1 hour 15 minutes, because the manager has to open two repositories and reconstruct the timeline from merge dates.
- Prohibited/private information removed: real repository names, staff names, client/project names, and private CI or commit links.

## Week D

- What happened: Reporting pipeline migration continued. A security patch was applied mid-week and pushed everything else back.
- GitHub or PR information: `PR 203: bump deps`, `PR 204: new ingest job`, and `PR 205: revert new ingest job`. PR 203 merged the same day. PR 204 merged Wednesday and was reverted Thursday in PR 205. The revert has no explanation in the description.
- Developer notes: Developer 2 said the new ingest job doubled the run time on production volumes and was reverted to protect the nightly window. Contractor 1 said they are still waiting on read access to the staging warehouse after raising it twice.
- What the MD should know: Nothing shipped this week that changes the product. The revert is a real finding, not simply a failure. The migration date is now at risk. A contractor has been billing time while partly blocked on access.
- Action items: Developer 2 should write up why the ingest job was slow before attempting it again. Ops should grant Contractor 1 staging access. The PM should re-estimate the migration date.
- Blocker: Contractor access is still outstanding after two requests.
- Manual time estimate: about 40 minutes. The revert reason would probably be missed because it only exists in one Slack message.
- Prohibited/private information removed: real warehouse details, security patch specifics, staff names, contractor identity, private repository links, and client/project names.
