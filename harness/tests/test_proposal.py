"""Proposal-validator unit tests (genome rules 2, 13)."""

from harness import validate_proposal as P
from harness.tests.test_ledger import base_ledger

COMPLETE = """
# Proposal 001

Predicted capability delta: +0.10
Predicted independence delta: +0.00
Predicted cost: NZD 40
Measurement: caliper repeatability over 20 runs.
"""


def test_complete_proposal_has_no_missing_predictions():
    assert P.check_predictions(COMPLETE) == []


def test_missing_predictions_are_reported():
    errors = P.check_predictions("# Proposal\n\nJust some prose.\n")
    assert len(errors) == 4


def test_cost_within_cap_passes():
    assert P.check_budget(COMPLETE, base_ledger()) == []


def test_over_budget_without_funding_plan_fails():
    text = "Predicted cost: NZD 5000\n"
    errors = P.check_budget(text, base_ledger())
    assert errors and "exceeds effective cap" in errors[0]


def test_over_budget_with_funding_plan_passes():
    text = "Predicted cost: NZD 5000\n\n## Funding plan\nSell 3 printed brackets.\n"
    assert P.check_budget(text, base_ledger()) == []


def test_missing_design_reference_is_reported():
    text = "See designs/nonexistent_widget for the model.\n"
    errors = P.check_designs_exist(text)
    assert errors and "nonexistent_widget" in errors[0]
