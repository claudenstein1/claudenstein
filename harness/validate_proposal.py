"""Proposal schema and budget checks (genome rules 2, 13, 16, 17).

Validates the proposal for the current cycle:
  - a proposal file exists for the current cycle (NNN = cycles_completed + 1);
  - it contains all four required predictions (genome rule 13);
  - finance parameters are set (delegated to ledger validation);
  - referenced designs exist;
  - predicted cost <= effective budget cap, OR a funding plan is present
    (genome rule 2);
  - any referenced results/ file exists (genome rule 17);
  - the cycle does not also modify anything under harness/ (spec section 6).

Run with --pre-cycle to skip proposal checks (used before any cycle exists).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from harness.ledger import (
    LedgerError,
    effective_budget_cap,
    load_and_validate,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSALS_DIR = REPO_ROOT / "proposals"

REQUIRED_PREDICTIONS = {
    "predicted capability delta": r"predicted\s+capability\s+delta",
    "predicted independence delta": r"predicted\s+independence\s+delta",
    "predicted cost": r"predicted\s+cost",
    "measurement": r"measurement",
}


def current_cycle(ledger):
    return ledger["resources"].get("cycles_completed", 0) + 1


def find_proposal(cycle):
    nnn = f"{cycle:03d}"
    matches = sorted(PROPOSALS_DIR.glob(f"{nnn}-*.md"))
    return matches[0] if matches else None


def _first_number_after(text, label_regex):
    """First number appearing after a label, e.g. 'Predicted cost: NZD 40' -> 40.0."""
    m = re.search(label_regex + r"[^\n\r]*?(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def check_predictions(text):
    missing = [
        name
        for name, rx in REQUIRED_PREDICTIONS.items()
        if not re.search(rx, text, re.IGNORECASE)
    ]
    return [f"missing required prediction: {m} (genome rule 13)" for m in missing]


def check_designs_exist(text):
    errors = []
    for name in sorted(set(re.findall(r"designs/([A-Za-z0-9_\-]+)", text))):
        if not (REPO_ROOT / "designs" / name).is_dir():
            errors.append(f"referenced design does not exist: designs/{name}")
    return errors


def check_results_exist(text):
    errors = []
    for ref in sorted(set(re.findall(r"results/([A-Za-z0-9_\-]+\.md)", text))):
        if not (REPO_ROOT / "results" / ref).is_file():
            errors.append(
                f"referenced result does not exist: results/{ref} (genome rule 17)"
            )
    return errors


def check_budget(text, ledger):
    cost = _first_number_after(text, REQUIRED_PREDICTIONS["predicted cost"])
    if cost is None:
        return []  # absence is already flagged by check_predictions
    cap = effective_budget_cap(ledger)
    if cost <= cap:
        return []
    if re.search(r"funding\s+plan", text, re.IGNORECASE):
        return []
    return [
        f"predicted cost {cost:.2f} exceeds effective cap {cap:.2f} "
        f"and no funding plan is present (genome rule 2)"
    ]


def check_harness_untouched():
    """Reject a cycle that also modifies harness/ (spec section 6).

    Uses git working-tree status vs HEAD. Silently skips when git or HEAD is
    unavailable (e.g. before the first commit).
    """
    git_dir = REPO_ROOT / ".git"
    if not git_dir.exists():
        return []
    try:
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", "harness"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    if out:
        changed = ", ".join(line[3:] for line in out.splitlines())
        return [
            f"cycle modifies harness/ ({changed}); a proposal may not change the "
            f"validation logic in the same cycle (spec section 6)"
        ]
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the current cycle's proposal.")
    parser.add_argument(
        "--pre-cycle",
        action="store_true",
        help="skip proposal checks (no proposal exists yet)",
    )
    args = parser.parse_args(argv)

    try:
        ledger = load_and_validate()
    except LedgerError as exc:
        print(f"FAIL proposal: ledger invalid: {exc}", file=sys.stderr)
        return 1

    if args.pre_cycle:
        print("OK   proposal: --pre-cycle, skipping proposal checks")
        return 0

    cycle = current_cycle(ledger)
    proposal = find_proposal(cycle)
    if proposal is None:
        print(f"OK   proposal: no proposal for cycle {cycle:03d} (nothing to validate)")
        return 0

    text = proposal.read_text(encoding="utf-8")
    errors = []
    errors.extend(check_predictions(text))
    errors.extend(check_designs_exist(text))
    errors.extend(check_results_exist(text))
    errors.extend(check_budget(text, ledger))
    errors.extend(check_harness_untouched())

    if errors:
        for e in errors:
            print(f"FAIL proposal ({proposal.name}): {e}", file=sys.stderr)
        return 1
    print(f"OK   proposal: {proposal.name} valid for cycle {cycle:03d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
