# Cycle, validate, and test targets for the gen-0 harness.
# PY can be overridden, e.g. `make validate PY=.venv/bin/python`.
PY ?= python

.PHONY: validate test cycle

# A cycle is not complete until `make validate` is green (spec section 6).
# --pre-cycle skips proposal checks when no proposal exists yet.
validate:
	$(PY) -m harness.ledger
	$(PY) -m harness.validate_geometry
	$(PY) -m harness.validate_proposal --pre-cycle
	$(PY) -m pytest -q

test:
	$(PY) -m pytest -q

# Trigger a cycle. gen-0 has no automation here: read the genome and CLAUDE.md,
# then drive the cycle with Claude Code. This target just states that and
# re-runs validation.
cycle:
	@echo "Read genome.md + ledger.yaml + latest results/, then write one proposal."
	@echo "See CLAUDE.md for the cycle procedure. Running validation:"
	$(MAKE) validate
