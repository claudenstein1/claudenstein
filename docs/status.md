# Project status and handoff

The repo is the complete state. Anyone - human or agent - picking this up cold on
a fresh machine and account must be able to continue from `genome.md` +
`CLAUDE.md` + this file, with no external memory. Keep this file current: update
it at the end of every cycle.

## Current status (2026-08-02)

- Generation 0 complete: constitution, ledger, objective function, validation
  harness. Built and pushed to claudenstein1/claudenstein.
- `make validate` green: 23 passed, 1 skipped.
- build123d intentionally deferred (not installed, not required yet). The
  geometry validator degrades gracefully and the geometry tests skip. Acceptance
  criterion 2 (envelope-violating fixture) is written as a pytest but skipped
  until build123d is installed.
- No hardware design exists. Cycle 1 (the system's first design proposal) has not
  been run.

## Accounts and isolation

Dedicated, non-shared by design (spec section 12, blast-radius containment):

- GitHub: claudenstein1, repo claudenstein1/claudenstein.
- Email: claudenstein1@gmail.com.
- Planned but not yet provisioned: a dedicated PC and a dedicated Claude Pro
  account. The intent is to pull this repo onto that host and continue there.
- No transaction or posting credentials live on the host. The human performs
  pushes.

Setup on a new host (git identity + credentials do not travel with a clone):
see `docs/setup.md`.

## Decision log

Why the genome and spec read as they do. Append new decisions here as they are
made; do not rewrite history.

- Posting autonomy is governed by the finance rung, not a separate rung
  (genome rule 19).
- Capability score is a deterministic weighted mean of per-metric sub-scores;
  the weights are genome-level (human-merge only) with a documented rationale
  (genome rule 1).
- Agent time is a cost denominated in dollars at the Claude Pro base rate, so
  "per hour" and "per dollar" are one axis (genome rule 16).
- In-kind revenue is recorded but not subject to the cap formula (genome rule 16).
- Prediction error is recorded in results/, not in the ledger (genome rule 15).
- validate_proposal rejects a cycle that also edits anything under harness/
  (spec section 6): the agent cannot weaken its own guardrails in the same cycle.
- No permanent human carve-out from the Independence objective. The objective is
  deliberately allowed to reward removing the human from the loop; the operator
  wants to see where the system goes relatively unhindered and will reintroduce
  human control as and if needed.
- Execution host is a dedicated old x86 PC, not the Jetson (build123d/OCP is
  flaky on ARM and there is no local ML need yet). The Jetson is reserved for a
  later cycle that needs vision or measurement automation.

## Open items

- [ ] Provision the dedicated PC and Claude Pro account; pull the repo; re-apply
      git identity and credential isolation per docs/setup.md.
- [ ] 6061 plate thicknesses (two) are still unset in ledger stock.
- [ ] Confirm the GitHub-added LICENSE is the intended one.
- [ ] Install build123d (`pip install -e .[cad]`) before any cycle that commits a
      design, to bring acceptance criterion 2 and geometry validation live.
- [ ] Run cycle 1.

## How to update this file

At the end of each cycle: refresh Current status and Open items, and append any
new decisions to the Decision log. Keep it ASCII.
