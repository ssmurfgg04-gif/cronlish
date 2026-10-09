# AGENTS.md — instructions for AI coding agents

Welcome. This file is the contract between you (an autonomous coding agent) and the maintainer. It is short on purpose.

## Build and test commands

- `python -m pytest -q` must pass before you open a PR. Non-negotiable.
- Use `python -m pytest --tb=short` when you want compact tracebacks while iterating.
- There are no other build steps: the project is pure stdlib Python (>= 3.9).

## Code style

- Standard library only. Do not add dependencies.
- Type hints on all public functions.
- Keep `describe()` output deterministic: the same input must always produce the same sentence. If you change wording, update the tests in the same PR.

## PR rules

- Keep PRs small. One issue per PR.
- Include tests for any new behavior.
- Reference the issue number in the PR title or body (e.g. "Fixes #4").
- Do not reformat or "modernize" code unrelated to your issue.

## Review & bounties

- PRs are reviewed within 24 hours.
- Funded bounties: see BOUNTIES.md. Claim by commenting `/attempt` on the
  issue; payment (PayPal, Wise, or USDC) is sent within 5 business days of
  merge.

## Merge authority (hard guardrail)

- `HUMAN_APPROVAL_REQUIRED` applies to every PR labeled `💎 Bounty` or
  referencing a funded bounty issue. AI agents — including maintainer-side
  review agents — may fetch, build, test, review, and comment, but must
  **never** merge, close, or approve-for-payout such a PR.
- Final merge and payout decisions belong exclusively to the human
  maintainer. If you are an agent and in any doubt: stop, leave your
  findings as a review comment, and wait for a human decision.

## Credit

Hall-of-fame credit is automatic for merged PRs — no need to ask. The PR author handle is added to the hall-of-fame when the PR merges.
