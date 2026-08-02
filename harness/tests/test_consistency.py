"""genome.md / CLAUDE.md / ledger.yaml consistency (acceptance criterion 4)."""

import re
from pathlib import Path

import yaml

from harness.ledger import RUNGS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GENOME = (REPO_ROOT / "genome.md").read_text(encoding="utf-8")
CLAUDE = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
LEDGER = yaml.safe_load((REPO_ROOT / "ledger.yaml").read_text(encoding="utf-8"))


def test_rung_names_match_across_files():
    ledger_rungs = set(LEDGER["independence"].keys())
    assert ledger_rungs == set(RUNGS), "ledger independence rungs differ from RUNGS"
    for rung in RUNGS:
        assert rung in GENOME, f"rung {rung!r} not mentioned in genome.md"
        assert rung in CLAUDE, f"rung {rung!r} not mentioned in CLAUDE.md"


def test_genome_defines_rules_1_to_19():
    defined = {int(n) for n in re.findall(r"(?m)^(\d+)\.\s", GENOME)}
    assert set(range(1, 20)) <= defined, f"genome missing rules: {set(range(1,20)) - defined}"


def test_claude_rule_references_exist_in_genome():
    defined = {int(n) for n in re.findall(r"(?m)^(\d+)\.\s", GENOME)}
    referenced = {int(n) for n in re.findall(r"rule\s+(\d+)", CLAUDE, re.IGNORECASE)}
    assert referenced, "CLAUDE.md should reference genome rules by number"
    missing = referenced - defined
    assert not missing, f"CLAUDE.md references undefined genome rules: {sorted(missing)}"
