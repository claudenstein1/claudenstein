"""Load, validate, and query ledger.yaml.

This module is the single source of truth for the two scores in the objective
function (genome rule 1) and for the effective budget cap (genome rule 2). The
computations here are deterministic by design: no judgement at scoring time.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

RUNGS = [
    "specify",
    "design",
    "manufacture",
    "assemble",
    "install",
    "order_parts",
    "finance",
]

RUNG_VALUE = {"human": 0.0, "assisted": 0.5, "autonomous": 1.0}

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = REPO_ROOT / "ledger.yaml"


class LedgerError(ValueError):
    """Raised when the ledger fails schema validation."""


def load_ledger(path=DEFAULT_LEDGER):
    """Read and parse ledger.yaml into a dict."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise LedgerError("ledger root must be a mapping")
    return data


def validate(ledger):
    """Validate the ledger structure. Raise LedgerError with a specific message.

    Finance parameters (base_cap, f, cap_ceiling) must be set: null fails
    (genome rule 2). Returns the ledger on success.
    """
    errors = []

    for key in ("meta", "independence", "resources"):
        if key not in ledger:
            errors.append(f"missing top-level key: {key}")
    if errors:
        raise LedgerError("; ".join(errors))

    # Independence: exactly the seven rungs, each a valid state.
    ind = ledger["independence"]
    for rung in RUNGS:
        if rung not in ind:
            errors.append(f"independence missing rung: {rung}")
        elif ind[rung] not in RUNG_VALUE:
            errors.append(
                f"independence.{rung} = {ind[rung]!r}, "
                f"expected one of {sorted(RUNG_VALUE)}"
            )
    extra = set(ind) - set(RUNGS)
    if extra:
        errors.append(f"independence has unknown rungs: {sorted(extra)}")

    # Resources: finance parameters must be set (not null).
    res = ledger["resources"]
    for key in ("base_cap_nzd", "reinvestment_fraction", "cap_ceiling_nzd"):
        if res.get(key) is None:
            errors.append(f"resources.{key} is unset (genome rule 2 requires it)")
        elif not isinstance(res[key], (int, float)):
            errors.append(f"resources.{key} must be numeric, got {type(res[key]).__name__}")

    # capability_weights structure (if present).
    for i, w in enumerate(ledger.get("capability_weights", []) or []):
        for field in ("metric", "ref", "weight"):
            if field not in w:
                errors.append(f"capability_weights[{i}] missing {field}")
        ref = w.get("ref", {})
        if "best" not in ref or "worst" not in ref:
            errors.append(f"capability_weights[{i}].ref needs best and worst")
        elif ref["best"] == ref["worst"]:
            errors.append(f"capability_weights[{i}].ref is degenerate (best == worst)")

    # revenue entries structure (if present).
    for i, e in enumerate(res.get("revenue", []) or []):
        kind = e.get("kind", "cash")
        if kind not in ("cash", "in_kind"):
            errors.append(f"resources.revenue[{i}].kind = {kind!r}, expected cash or in_kind")
        if kind == "cash" and not isinstance(e.get("amount_nzd"), (int, float)):
            errors.append(f"resources.revenue[{i}] (cash) needs numeric amount_nzd")

    if errors:
        raise LedgerError("; ".join(errors))
    return ledger


def independence_score(ledger):
    """Mean over the seven rungs: human=0, assisted=0.5, autonomous=1.0."""
    ind = ledger["independence"]
    return sum(RUNG_VALUE[ind[r]] for r in RUNGS) / len(RUNGS)


def _sub_score(value, weight_entry):
    """Map a raw measurement to a 0..1 sub-score via linear normalisation.

    ref.best is the raw value scoring 1.0; ref.worst scores 0.0. This handles
    both directions: for lower-is-better metrics best < worst, and the formula
    still yields higher sub-scores for better (lower) values.
    """
    ref = weight_entry["ref"]
    best = ref["best"]
    worst = ref["worst"]
    if best == worst:
        raise LedgerError(
            f"degenerate ref for metric {weight_entry.get('metric')!r}: best == worst"
        )
    s = (value - worst) / (best - worst)
    return max(0.0, min(1.0, s))


def capability_score(ledger):
    """Weighted mean of per-metric sub-scores. Empty capabilities -> 0.0."""
    caps = ledger.get("capabilities", []) or []
    if not caps:
        return 0.0
    weights = {w["metric"]: w for w in (ledger.get("capability_weights", []) or [])}
    num = 0.0
    den = 0.0
    for c in caps:
        metric = c["metric"]
        if metric not in weights:
            raise LedgerError(f"no capability_weights entry for metric {metric!r}")
        w = weights[metric]
        num += w["weight"] * _sub_score(c["value"], w)
        den += w["weight"]
    if den == 0:
        return 0.0
    return num / den


def effective_budget_cap(ledger):
    """min(base_cap + f * mean(cash revenue over trailing window), cap_ceiling).

    Only cash revenue enters the formula (genome rule 16). The mean is per cycle
    over the trailing window: total cash in the last N cycles divided by N, so
    cycles with no revenue count as zero.
    """
    res = ledger["resources"]
    base = res["base_cap_nzd"]
    f = res["reinvestment_fraction"]
    ceiling = res["cap_ceiling_nzd"]
    window = res.get("revenue_trailing_window_cycles", 3) or 1
    completed = res.get("cycles_completed", 0)

    lo = completed - window + 1
    cash_in_window = [
        e.get("amount_nzd", 0) or 0
        for e in (res.get("revenue", []) or [])
        if e.get("kind", "cash") == "cash" and lo <= e.get("cycle", 0) <= completed
    ]
    mean_per_cycle = sum(cash_in_window) / window
    return min(base + f * mean_per_cycle, ceiling)


def load_and_validate(path=DEFAULT_LEDGER):
    return validate(load_ledger(path))


def _main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_LEDGER
    try:
        ledger = load_and_validate(path)
    except LedgerError as exc:
        print(f"FAIL ledger validation: {exc}", file=sys.stderr)
        return 1
    print(f"OK   ledger valid: {path}")
    print(f"     independence score = {independence_score(ledger):.4f}")
    print(f"     capability score   = {capability_score(ledger):.4f}")
    print(f"     effective cap NZD  = {effective_budget_cap(ledger):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
