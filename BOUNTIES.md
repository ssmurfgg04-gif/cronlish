# 💰 Bounties

cronlish funds small, well-specified work with real money, paid on merge —
no points, no exposure. One ritual, stated once, enforced identically
everywhere.

| Issue | Bounty | Status | Claimed by |
| --- | --- | --- | --- |
| [#4 — `--locale-style` CLI flag with `terse` output](https://github.com/ssmurfgg04-gif/cronlish/issues/4) | **$400** | ⏸ Paused — issue closed & locked; maintainer is re-running the review by hand | — |

Status legend: 🟢 Open · 🟡 Claimed / in progress · ⏸ Paused (no claims accepted) · ✅ Paid & closed

This is the first funded bounty of the program — there is no payout history
yet. The first paid bounty will be recorded here publicly (issue link +
award comment), because receipts are how a bounty program earns trust.

## How it works

1. **Claim it** — comment `/attempt` on the issue with a short plan
   (2–3 sentences on your approach). Claiming is a courtesy signal, not an
   exclusive lock: multiple contributors may attempt, and the first
   **merged** PR that meets the acceptance criteria wins.
2. **Do the work** — read [AGENTS.md](AGENTS.md). `python -m pytest -q`
   must pass. Keep the PR small: one issue per PR, no drive-by refactors.
3. **Open the PR** — title it `Fixes #N: <summary>` (or put `Fixes #N` in
   the body) so GitHub links your PR to the bounty automatically.
4. **Get paid** — the maintainer reviews within 48 hours of your PR being
   ready. When the PR merges, payment is sent within 5 business days via
   PayPal, Wise, or USDC (your choice — you'll be asked for your payout
   details on the merged PR; nothing sensitive goes in public comments
   beyond your PayPal/Wise email or wallet address).

Before starting, ⭐ star the repository — it helps cronlish grow and shows
you're committed to contributing!

## Rules

- Bounties are competitive: multiple PRs may be submitted for the same
  bounty, and review comments are public. The maintainer selects the PR
  that best solves the problem, considering code quality, completeness,
  and contributor behavior. The maintainer's decision is final.
- **Human merge authority.** Automated agents — including the maintainer's
  own review agents — may fetch, build, test, and comment on bounty PRs,
  but are **not** authorized to merge them. Every bounty PR requires final
  approval from the **human maintainer** before merge (`HUMAN_APPROVAL_REQUIRED`),
  and payout is authorized only by the human maintainer after merge.
  A merge performed without that approval does not constitute bounty
  acceptance and may be reverted.
- One bounty claim per contributor at a time.
- If your claim goes 14 days with no visible progress (no commits, no
  comments), the issue may be re-assigned to the next attempter.
- If an issue gains no merged PR within 90 days, the bounty may be
  withdrawn or re-posted. Bounties are pledges from the maintainer, held
  for the contributor whose work merges.
- Bounties are paid per merged PR. There is no invoice and no paperwork:
  the PR is the deliverable. Where legally required, the payout counts as
  miscellaneous income for the recipient.

## AI policy

AI-assisted development is expected and encouraged — this repo exists for
humans and agents equally. The trade is the industry-standard one: you own
every line you open a PR for. You must be able to explain your entire diff,
tests must genuinely exercise the feature, and low-effort AI PRs (template
wording, no real test coverage) will be closed without review.

---

<details>
<summary>📜 Bounty fine print</summary>

**Eligibility.** Open to everyone, anywhere; you need a GitHub account and
a payout method (PayPal, Wise, or USDC). You may not claim a bounty if
doing so conflicts with an employer agreement, and the maintainer may
decline or limit participation at their discretion. Contributions merge
under the project license (MIT) — by opening the PR you confirm the work
is yours to submit.

**Quality bar.** The merged PR must meet every acceptance criterion on the
issue. Tests must genuinely exercise the new behavior; PRs that reformat
unrelated code, pad the diff, or skip CI will be closed without extensive
review. You are expected to understand and be able to defend everything
you submit, regardless of whether AI tools were used.

**Payment.** Exactly one bounty is paid per issue, to the contributor whose
PR merges (or split, pro-rata, if multiple contributors made significant
contributions to the merged result). Payment is sent within 5 business days
of merge to the payout details provided on the merged PR. Do not post full
financial details in public; an email or wallet address is enough.

**Discretion.** Bounties are funded by the maintainer and awarded at the
maintainer's sole discretion. Deadlines, amounts, and availability may
change before a claim is accepted. Only the human maintainer can accept a
claim: AI maintainer agents are not authorized to merge bounty PRs or
approve payouts, and a bot-performed merge is void for bounty purposes.
The maintainer's decision on any bounty question — winners, splits,
forfeits, refunds — is final.

</details>
