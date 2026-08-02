"""Tests for ledger scoring and validation (acceptance criteria 1, 3)."""

import copy

import pytest

from harness import ledger as L


def base_ledger():
    return {
        "meta": {"schema_version": 1, "created": "2026-08-02"},
        "capabilities": [],
        "capability_weights": [],
        "independence": {r: "human" for r in L.RUNGS},
        "resources": {
            "base_cap_nzd": 50,
            "reinvestment_fraction": 0.9,
            "cap_ceiling_nzd": 1000,
            "revenue_trailing_window_cycles": 3,
            "revenue": [],
            "spend_total_nzd": 0,
            "cycles_completed": 0,
            "stock": {},
        },
    }


# --- independence score: three configurations ---

def test_independence_all_human():
    assert L.independence_score(base_ledger()) == 0.0


def test_independence_all_autonomous():
    led = base_ledger()
    led["independence"] = {r: "autonomous" for r in L.RUNGS}
    assert L.independence_score(led) == 1.0


def test_independence_mixed():
    led = base_ledger()
    led["independence"]["specify"] = "assisted"
    led["independence"]["design"] = "assisted"
    led["independence"]["manufacture"] = "autonomous"
    # (0.5 + 0.5 + 1.0) / 7
    assert L.independence_score(led) == pytest.approx(2.0 / 7)


# --- capability score: three configurations ---

def test_capability_empty_is_zero():
    assert L.capability_score(base_ledger()) == 0.0


def test_capability_single_metric():
    led = base_ledger()
    led["capabilities"] = [{"metric": "payload_g", "value": 500}]
    led["capability_weights"] = [
        {
            "metric": "payload_g",
            "direction": "higher_is_better",
            "ref": {"worst": 0, "best": 1000},
            "weight": 1,
        }
    ]
    assert L.capability_score(led) == pytest.approx(0.5)


def test_capability_multi_metric_weighted():
    led = base_ledger()
    led["capabilities"] = [
        {"metric": "payload_g", "value": 500},        # sub 0.5, weight 2
        {"metric": "repeatability_mm", "value": 0.1},  # lower better, sub 0.9, weight 1
    ]
    led["capability_weights"] = [
        {
            "metric": "payload_g",
            "direction": "higher_is_better",
            "ref": {"worst": 0, "best": 1000},
            "weight": 2,
        },
        {
            "metric": "repeatability_mm",
            "direction": "lower_is_better",
            "ref": {"worst": 1.0, "best": 0.0},
            "weight": 1,
        },
    ]
    # (2*0.5 + 1*0.9) / 3
    assert L.capability_score(led) == pytest.approx(1.9 / 3)


def test_capability_missing_weight_raises():
    led = base_ledger()
    led["capabilities"] = [{"metric": "payload_g", "value": 500}]
    with pytest.raises(L.LedgerError):
        L.capability_score(led)


# --- effective budget cap: three revenue scenarios + in-kind ---

def test_cap_zero_revenue():
    assert L.effective_budget_cap(base_ledger()) == pytest.approx(50.0)


def test_cap_mid_range():
    led = base_ledger()
    led["resources"]["cycles_completed"] = 3
    led["resources"]["revenue"] = [
        {"cycle": 1, "kind": "cash", "amount_nzd": 100},
        {"cycle": 2, "kind": "cash", "amount_nzd": 100},
        {"cycle": 3, "kind": "cash", "amount_nzd": 100},
    ]
    # mean per cycle over window 3 = 100; 50 + 0.9*100 = 140
    assert L.effective_budget_cap(led) == pytest.approx(140.0)


def test_cap_ceiling_limited():
    led = base_ledger()
    led["resources"]["cycles_completed"] = 3
    led["resources"]["revenue"] = [
        {"cycle": 1, "kind": "cash", "amount_nzd": 5000},
        {"cycle": 2, "kind": "cash", "amount_nzd": 5000},
        {"cycle": 3, "kind": "cash", "amount_nzd": 5000},
    ]
    # 50 + 0.9*5000 = 4550, clamped to 1000
    assert L.effective_budget_cap(led) == pytest.approx(1000.0)


def test_in_kind_revenue_does_not_move_cap():
    led = base_ledger()
    led["resources"]["cycles_completed"] = 1
    led["resources"]["revenue"] = [
        {"cycle": 1, "kind": "in_kind", "market_value_nzd": 100000, "source": "donor"},
    ]
    assert L.effective_budget_cap(led) == pytest.approx(50.0)


# --- schema validation ---

def test_null_finance_param_fails():
    led = base_ledger()
    led["resources"]["base_cap_nzd"] = None
    with pytest.raises(L.LedgerError):
        L.validate(led)


def test_unknown_rung_state_fails():
    led = base_ledger()
    led["independence"]["specify"] = "sometimes"
    with pytest.raises(L.LedgerError):
        L.validate(led)


def test_shipped_ledger_is_valid():
    led = L.load_and_validate()
    assert L.independence_score(led) == 0.0
    assert L.capability_score(led) == 0.0
    assert L.effective_budget_cap(led) == pytest.approx(50.0)
