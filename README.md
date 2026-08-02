# claudenstein

Software harness for a long-horizon, agent-driven robotics project: a system
that designs, and progressively learns to build, physically capable hardware
starting from zero. This repo **is** the system's persistent memory.

This is **generation 0**: memory, constitution, objective function, and
validation tooling. No hardware design exists yet; the first design proposal is
produced by the system, not committed here.

## Files

- `genome.md` - the constitution and objective function (numbered rules).
- `ledger.yaml` - capabilities, independence rungs, resources, stock.
- `CLAUDE.md` - agent operating instructions (read the genome first).
- `harness/` - `ledger.py` (scores + budget cap), `validate_proposal.py`,
  `validate_geometry.py`, and tests.
- `proposals/`, `designs/`, `results/` - one entry per cycle.
- `docs/bootstrap-spec.md` - the original build specification.
- `docs/status.md` - current state, decision log, open items (read this first
  when picking up the project).
- `docs/setup.md` - how to set up on a fresh host.

## Running

```
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate on POSIX
pip install -e .                                  # core: pyyaml, pytest
make validate
```

`make validate` runs ledger validation, geometry checks, the proposal validator
(`--pre-cycle` when no proposal exists), and the test suite. A cycle is not
complete until it is green.

build123d is an optional extra (`pip install -e .[cad]`), deferred until a cycle
commits a design. Geometry tests are skipped when it is not installed, and
`make validate` is green without it. Full fresh-host setup: `docs/setup.md`.

## Execution environment

See `docs/bootstrap-spec.md` section 12. Early low-risk cycles may run on a
workstation; the harness migrates to a dedicated, network-restricted host before
any cycle can act on the outside world (network egress, credentials, ordering,
posting, or actuator power). Dedicated GitHub and Claude accounts, no
transaction or posting credentials on the host.
