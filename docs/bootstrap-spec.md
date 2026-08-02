# Project Bootstrap - Self-Improving Robotics Harness

## Spec for Claude Code - v0.1

---

## 1. Purpose

Build the software harness for a long-horizon project: an agent-driven system that designs, and progressively learns to build, physically capable robotic hardware - starting from zero hardware. The human operator ("Frog") acts as the executor for all physical steps initially; the system's objective is to reduce that dependence over time.

This spec covers **generation 0 only**: a git repo containing the agent's memory, constitution, objective function, and validation tooling. No hardware design work is in scope for this handoff - the first design proposal is produced *by* the system after it exists, not by you now.

The system's standing drive is defined as maximising two ledger-tracked scores:

- **Capability** - measured physical performance of artifacts it has designed (payload, repeatability, print/machining quality, cycle time).
- **Independence** - the fraction of the build pipeline (specify -> design -> manufacture -> assemble -> install -> order parts -> finance) performed without the human.

Both are initially subject to a per-cycle budget cap. Revenue (from documenting the build publicly) never enters the objective function - it relaxes the budget constraint (section 4 rules 16-19). The objective function lives in the genome (section 4) so that changing what the system "wants" is a reviewed edit, never an implicit drift.

## 2. Operating model

The repo *is* the system's persistent memory. Claude Code, pointed at this repo, is the agent engine. One **cycle** looks like:

1. Human triggers a cycle (manual, e.g. `make cycle` or simply invoking Claude Code with the cycle prompt).  Going forward, other external events may trigger new cycles, such as the availability of new parts or compute resources.
2. Agent reads `ledger.yaml`, `genome.md`, and the most recent entries in `results/`.
3. Agent writes exactly **one** proposal into `proposals/`: the highest expected (capability + independence) gain per dollar, where both scores are computed deterministically by `ledger.py` (section 5) and agent time converts to dollars per rule 16. If the highest-value proposal costs more than the current effective budget, it is not discarded: the proposal may include a funding plan to close the gap, and the cycle proceeds with fundraising as part of the work (rule 2, section 6).
4. Agent generates or updates the corresponding design in `designs/` (Build123d code-CAD) plus human-readable build instructions.
5. Validation scripts must pass before the proposal is considered complete (section 6).
6. Human reviews the proposal like a PR, builds/measures, and commits outcomes to `results/`. Initially the results are human-measured, but this may be relaxed as appropriate.
7. Next cycle begins from the updated ledger.

## 3. Repo layout

```
genome.md            # design constitution + objective function (section 4)
ledger.yaml          # capabilities, independence, resources (section 5)
CLAUDE.md            # agent operating instructions (section 7)
Makefile             # cycle trigger, validate, test targets
proposals/           # NNN-short-name.md - one per cycle
designs/             # one dir per artifact: Build123d source, emitted STL/STEP, build notes
results/             # NNN-short-name.md - measurements, photos, human build notes, actual spend
harness/
  validate_geometry.py    # envelope + buildability checks
  validate_proposal.py    # schema + budget checks
  ledger.py               # load/validate/query ledger.yaml
  tests/
```

Python 3.11+, `uv` or plain venv, dependencies: `build123d`, `pyyaml`, `pytest`. Keep the dependency list minimal - this runs on a desktop now and should port to a Jetson Orin later without drama.

## 4. genome.md (write this file with this content, refined for clarity)

Structure it as numbered rules. Content to encode:

**Objective (rules 1-3)**
1. Objective: maximise the Capability and Independence scores as defined in the ledger, weighted equally unless amended, subject to the budget cap. Both scores are computed deterministically by `ledger.py` (section 5), never judged at scoring time. The Capability score is a weighted mean of per-metric sub-scores; the per-metric weights and normalisation references define what the system is optimising for, so they are genome-level and change only by human merge (rule 3), each change carrying a documented, reasoned justification. Initial weights may be arbitrary. A given cycle may additionally impose minimum sub-scores in named capability metrics as gating requirements.
2. Budget cap per cycle = `base_cap + f x trailing_cash_revenue`, hard-limited by `cap_ceiling`. `base_cap` (human out-of-pocket floor), reinvestment fraction `f`, trailing window, and `cap_ceiling` must all be set before cycle 1; validation fails if any is unset. Frog has set them (section 8): `base_cap` NZD 50, `f` 0.9, `cap_ceiling` NZD 1000. Only the human may change `base_cap`, `f`, or `cap_ceiling`. A cycle may begin even when the effective cap is insufficient to complete the proposed build; in that case the proposal must include a funding plan and the shortfall is closed by fundraising within the cycle rather than by exceeding the cap (see rule 3 of section 2 and section 6).
3. Amendments to this genome are proposed as diffs in a proposal file and take effect only after human merge.

**Manufacturing envelope (rules 4-7)**
4. CNC envelope: 300 x 300 x 160 mm, capable of aluminium. Parts must machine in one setup where feasible; two-setup parts require justification in the proposal.
5. FDM envelope: Rigidbot bed: 250 x 250 x 250mm.
6. Stock inventory: 6061 plate in two thicknesses Frog to specify when required; PETG and ASA filament; one fastener spec: **M3 socket-head cap screws only** (single thread size across the entire system).  Other sizes may be made available if necessary.
7. No part may exceed the envelope of the machine that makes it; larger structures are segmented and joined.  Larger parts could be made available by special request if there is no reasonable alternative.

**Design discipline (rules 8-12)**
8. Every actuated DOF carries an encoder and motor current sensing. Uninstrumented motion is prohibited.
9. Segments and modules must be blind-matable: chamfered leads, self-jigging features, gravity-assisted insertion where orientation allows.
10. Designs are code-CAD (Build123d), parametric, committed as source. Emitted STL/STEP are build artifacts, reproducible from source.
11. Every design ships with a measurement procedure: how the human (or later, the system) scores the artifact against predicted performance.
12. Vitamins (motors, bearings, boards, fasteners) are drawn from a declared list in the ledger's stock section; introducing a new vitamin type requires explicit justification.

**Process (rules 13-15)**
13. One proposal per cycle. Each proposal states: predicted capability delta, predicted independence delta, predicted cost, and the measurement that will verify the prediction.
14. Initially, only the human writes `results/` and the ledger's measured values and spend. The agent should not record an outcome it did not receive from the human unless cleared to do so.
15. Prediction error (predicted vs measured) is itself tracked per cycle and recorded in the cycle's `results/` file; systematically overoptimistic proposals are a defect to be corrected.

**Finance (rules 16-19)**
16. Revenue is instrumental, never terminal: it enters the system only through the budget-cap formula (rule 2) and appears nowhere in the Capability or Independence scores. Revenue-generating activity is proposed and justified like any other work: predicted revenue delta -> predicted budget delta -> resulting capability/independence gain per dollar spent, competing for cycle time on equal footing with building. Agent time is a cost denominated in dollars: elapsed commercial-AI time is valued at the base Claude Pro subscription rate (currently USD 20/month, converted to NZD at the prevailing rate), pro-rated over elapsed time, so "per hour" and "per dollar" are the same axis. Revenue may take the form of materials, components, or services (in-kind), not money alone. In-kind revenue is recorded but is not subject to the cap formula; where a valuation is required it is taken at the market rate for the donated goods or services.
17. All published content must document real, ledger-verifiable build activity. Any claim of a result in content must correspond to an existing file in `results/`. Fabricated, dramatised-beyond-fact, or engagement-farming content is prohibited regardless of predicted revenue.
18. Revenue is recorded in the ledger only by the human, same ground-truth rule as measurements (rule 14). The agent never self-reports earnings.
19. Posting is not a separate independence rung; posting autonomy is governed by the finance/revenue machinery (the `finance` rung and rules 16-18). It starts human (agent drafts, human posts). Movement to assisted or autonomous posting follows the same finance-rung progression and is a genome amendment requiring human merge, and autonomous posting additionally requires compliance with the target platform's automation and AI-disclosure policies. The move to autonomous posting should be made as soon as the system is competent to do it.

## 5. ledger.yaml schema

Define and enforce (via `harness/ledger.py` + a pytest) this structure:

```yaml
meta:
  schema_version: 1
  created: <date>

capabilities: []
  # each entry:
  # - metric: repeatability_mm | payload_g | backlash_deg | print_dim_error_mm | ...
  #   value:
  #   method:        # reference to the measurement procedure used
  #   artifact:      # designs/<dir> that achieved it
  #   date:
  #   result: results/NNN-...

capability_weights: []             # human-merge-only (genome-level, rule 1); each entry:
  # - metric: repeatability_mm | payload_g | ...
  #   direction: higher_is_better | lower_is_better
  #   ref: <normalisation reference mapping raw value -> 0..1 sub-score>
  #   weight: <float>
  #   rationale: <documented, reasoned justification for this weight>

independence:
  specify:      human   # human | assisted | autonomous
  design:       human
  manufacture:  human
  assemble:     human
  install:      human
  order_parts:  human
  finance:      human   # human = base_cap funds all; assisted = revenue offsets; autonomous = revenue >= cap

resources:
  base_cap_nzd: 50                 # human out-of-pocket floor, Frog-set; validation fails on null
  reinvestment_fraction: 0.9       # f in cap formula, Frog-set; validation fails on null
  cap_ceiling_nzd: 1000            # hard limit, human-set only, Frog-set; validation fails on null
  revenue_trailing_window_cycles: 3
  revenue: []                      # per-cycle entries, human-written only:
                                   #   cash:    {cycle, kind: cash, amount_nzd, source, date}
                                   #   in-kind: {cycle, kind: in_kind, market_value_nzd (optional), source, date}
                                   # only cash entries feed the cap formula (rule 16)
  spend_total_nzd: 0
  cycles_completed: 0
  stock:
    plate_6061: []                 # thicknesses in mm, TBC on request
    filament: [PETG, ASA]
    fasteners: [M3 SHCS]
    vitamins: []                   # declared motors/bearings/boards as acquired
```

Independence score = mean over the seven rungs, each scored `human` = 0, `assisted` = 0.5, `autonomous` = 1.0; implement the calculation in `ledger.py` so it is deterministic, not vibes.

Capability score = weighted mean of per-metric sub-scores. For each entry in `capabilities`, `ledger.py` looks up the matching `capability_weights` entry, maps the raw value to a 0..1 sub-score using that entry's `direction` and `ref`, and combines the sub-scores by `weight`. Weights and normalisation references are genome-level (rule 1): changing them requires human merge with a documented rationale. With an empty `capabilities` list the score is 0.

`ledger.py` also computes the current effective budget cap: `min(base_cap + f x mean(cash revenue over trailing window), cap_ceiling)`. Only cash revenue enters this formula; in-kind revenue does not (rule 16). This cap is the single source of truth the proposal validator checks against.

## 6. Validation scripts

- `validate_proposal.py`: proposal file exists for current cycle, contains all four required predictions (section 4 rule 13), finance parameters are set, referenced designs exist. Budget check: predicted cost <= effective budget cap (as computed by `ledger.py`), OR the proposal includes an explicit funding plan covering the shortfall (rule 2) - a proposal over budget with no funding plan fails. If the proposal includes content/revenue activity, every result it references must exist in `results/` (rule 17 check). A proposal that modifies any file under `harness/` (the validation logic) in the same cycle is rejected.
- `validate_geometry.py`: for each design, imports the Build123d source, builds it, checks every discrete part's bounding box against the declared target machine's envelope, checks fastener spec compliance where fasteners are modelled. Fail loudly and specifically.
- `make validate` runs both plus pytest. A cycle is not complete until green.

## 7. CLAUDE.md

Write the agent operating instructions: the cycle procedure (section 2), the ground-truth rule (agent never writes results/measured values/spend unless authorised), the one-proposal-per-cycle rule, the requirement to read genome + ledger + latest results before proposing, and the instruction that genome changes go through proposal diffs. Keep it short and imperative.

## 8. Open inputs (block cycle 1, not repo construction)

| Item | Owner | Value |
|---|---|---|
| base_cap per cycle (NZD) | Frog | 50 (set) |
| Reinvestment fraction f | Frog | 0.9 (set) |
| cap_ceiling (NZD) | Frog | 1000 (set) |
| 6061 plate thicknesses (x2) | Frog | TBC on request |
| Rigidbot bed dimensions | Frog | 250x250x250 (set) |

The finance parameters and bed dimensions above are set and may be taken as written. Only the 6061 plate thicknesses remain open, and they do not block cycle 1 (Frog supplies them when a design first needs plate).

## 9. Acceptance criteria

1. Fresh clone + `make validate` passes with the empty ledger. The finance parameters ship already set (section 8), so the ledger validates; the proposal validator is a no-op when no proposal exists for the current cycle (or is skipped via an explicit `--pre-cycle` flag). A cycle with an over-budget proposal is still valid provided it carries a funding plan (section 6).
2. A deliberately envelope-violating test fixture design fails `validate_geometry.py` with a specific error (include this as a pytest, not a committed bad design).
3. `ledger.py` computes the independence score correctly for at least three test configurations, the capability score correctly for at least three configurations (empty capabilities list -> 0, single metric, multi-metric weighted mean), and the effective budget cap correctly for at least three revenue scenarios (zero revenue, mid-range, ceiling-limited), confirming in-kind revenue does not move the cap.
4. `CLAUDE.md` and `genome.md` are internally consistent (same rung names, same rule numbering references).
5. No hardware design exists in `designs/` - gen-0 ships empty except for test fixtures under `harness/tests/`.

## 10. Explicitly out of scope for this handoff

- Any actuator, joint, or arm design (that is cycle 1's proposal, made by the system).
- Cron/scheduled triggering, Jetson deployment, supplier/ordering APIs - all future independence rungs the system should propose itself.
- Vision/measurement automation.

## 11. C style note

Any C code that eventually enters this repo (firmware, later cycles) uses Allman brace style. Not applicable to gen-0 Python, recorded here so it survives into future cycles.

## 12. Execution environment

The eventual home for the harness is a dedicated, treated-as-untrusted host, sandboxed for the system this is designed to become (the objective function rewards removing the human from ordering, payment, posting, and cycle-triggering) rather than for the harmless gen-0 it boots as. This section is a standing constraint, not a gen-0 task; it survives into future cycles like the C style note.

**Phased adoption.** Because the repo is the single source of truth and the harness is fully portable (a git clone plus a Python venv), the location of the box is not itself load-bearing - moving hosts is a clone, not a migration. The early cycles are low-risk: they only read the ledger and write markdown and code-CAD, with no network egress beyond the Anthropic API, no stored credentials, and no actuation. Those cycles may run directly on the operator's workstation for convenience. Migration to the dedicated host must happen before, and is a hard precondition for, the first cycle that introduces any of: outbound network access beyond the Anthropic API and package mirrors; any stored payment, supplier, or posting credential; autonomous ordering, posting, or cycle-triggering; or actuator power. In practice: workstation is fine while the system can only think and draw; move it before it can act on the outside world. The target-host, isolation, and credential rules below define what "the dedicated host" means when that move happens.

**Target host.** A dedicated x86-64 machine (one of the operator's older PCs), headless, running a current Linux LTS. Not the Jetson: gen-0's workload is CPU-bound code-CAD (`build123d` on OCP/OpenCascade) with no local ML, and the OCP/OCCT toolchain is reliable on x86-64 `manylinux` wheels but flaky-to-absent on ARM64. The Jetson is reserved for a later cycle, when local vision/measurement/inference is actually in the loop (see section 10); porting is a future independence rung the system may propose.

**Isolation layers.**
1. Dedicated hardware, physically separate from any trusted machine; wipeable.
2. The harness runs in a container or throwaway VM so a cycle cannot touch the host. The container image is the unit ported to the Jetson later.
3. Network default-deny outbound. The host sits on an isolated VLAN; the firewall allowlists only the Anthropic API endpoints (for Claude Code) and pinned OS/PyPI mirrors, ideally vendored so cycles can run offline between triggers. Every dangerous capability (ordering, posting, paying, self-updating) is network egress; if it is not on the allowlist it cannot happen, regardless of what a cycle decides it wants. This enforces the genome's intent structurally, not by trust.

**Credential policy.** No payment methods, supplier/ordering API keys, or posting/social tokens are ever stored on the host. results, revenue, and spend are human-written ground truth (rules 14, 18), so the machine has no legitimate need to authenticate for a transaction or a post. If it cannot authenticate, it cannot transact - this is the hard stop behind the prohibited-action categories, and it lets "unhindered" mean "free to reason and propose" without meaning "free to spend or publish".

**Git remote.** The repo is the system's memory, and the human-merge gate (genome rule 3; the section 6 rule rejecting proposals that modify `harness/`) only holds if the agent cannot push to the trusted copy. The host keeps a local repo only; merges and pushes to any remote are performed by the human.

**Account isolation.** This project uses its own dedicated GitHub and Anthropic/Claude accounts, not shared with any other project or the operator's personal accounts. The point is blast radius: if the system ever gains autonomy or the host is compromised, the reachable accounts must contain nothing but this project - no other repos or organisations on the GitHub side, no other projects, data, or billing exposure on the Claude side. Corollaries: the dedicated GitHub account has access only to this repo (or its own single-project org); the dedicated Claude account's API credentials, when any are eventually placed on the host, are scoped to this project alone and are subject to the same credential policy above. These accounts are provisioned by the human (account creation is a human-only action).

**Physical interlock (future).** When actuators arrive, their power is not software-switchable without a hardware e-stop / manual power isolation in the loop. Out of scope for gen-0; to be decided before any cycle proposes a motor.
