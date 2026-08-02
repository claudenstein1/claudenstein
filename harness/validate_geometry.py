"""Geometry and buildability checks for designs (genome rules 4-7, 10).

For each design under designs/, import its build123d source, build it, and check
every discrete part's bounding box against the declared target machine's
envelope, plus fastener-spec compliance where fasteners are declared. Fail
loudly and specifically.

Design source contract: designs/<name>/model.py exposes a module-level
    PARTS = [{"name": str, "part": <build123d Part/Solid>, "machine": "cnc"|"fdm"}]
and optionally
    FASTENERS = [<str>, ...]   # each must be the one allowed spec (genome rule 6)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = REPO_ROOT / "designs"

# Machine envelopes in mm (genome rules 4, 5).
ENVELOPES = {
    "cnc": (300.0, 300.0, 160.0),
    "fdm": (250.0, 250.0, 250.0),
}

ALLOWED_FASTENER = "M3 SHCS"
TOL = 1e-6


def part_dimensions(part):
    """Return (dx, dy, dz) of a build123d part's bounding box."""
    bb = part.bounding_box()
    return (bb.size.X, bb.size.Y, bb.size.Z)


def fits(dims, machine):
    """True if dims fit the machine envelope in some axis-aligned orientation."""
    if machine not in ENVELOPES:
        return False
    env = ENVELOPES[machine]
    return all(
        d <= e + TOL
        for d, e in zip(sorted(dims, reverse=True), sorted(env, reverse=True))
    )


def check_part(name, part, machine):
    """Return a list of specific error strings for one part (empty if OK)."""
    errors = []
    if machine not in ENVELOPES:
        errors.append(f"{name}: unknown machine {machine!r} (expected cnc or fdm)")
        return errors
    dims = part_dimensions(part)
    if not fits(dims, machine):
        dims_str = " x ".join(f"{d:.1f}" for d in dims)
        env_str = " x ".join(f"{e:.0f}" for e in ENVELOPES[machine])
        errors.append(
            f"{name}: bounding box {dims_str} mm exceeds {machine} envelope "
            f"{env_str} mm (genome rule 7)"
        )
    return errors


def check_fasteners(design_name, fasteners):
    errors = []
    for f in fasteners:
        if f != ALLOWED_FASTENER:
            errors.append(
                f"{design_name}: fastener {f!r} violates single-spec rule "
                f"(only {ALLOWED_FASTENER!r} allowed, genome rule 6)"
            )
    return errors


def _load_model(model_path):
    spec = importlib.util.spec_from_file_location(
        f"design_{model_path.parent.name}", model_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_design(design_dir):
    """Validate one design directory. Return a list of error strings."""
    errors = []
    model_path = design_dir / "model.py"
    if not model_path.exists():
        return [f"{design_dir.name}: no model.py"]
    module = _load_model(model_path)
    parts = getattr(module, "PARTS", None)
    if not parts:
        return [f"{design_dir.name}: model.py defines no PARTS"]
    for entry in parts:
        errors.extend(check_part(entry["name"], entry["part"], entry["machine"]))
    errors.extend(check_fasteners(design_dir.name, getattr(module, "FASTENERS", [])))
    return errors


def main():
    design_dirs = [d for d in sorted(DESIGNS_DIR.glob("*")) if d.is_dir()]
    if not design_dirs:
        print("OK   geometry: no designs to validate")
        return 0

    try:
        import build123d  # noqa: F401
    except ImportError:
        print(
            "FAIL geometry: build123d not installed but designs exist; "
            "cannot validate geometry",
            file=sys.stderr,
        )
        return 1

    all_errors = []
    for d in design_dirs:
        all_errors.extend(validate_design(d))

    if all_errors:
        for e in all_errors:
            print(f"FAIL geometry: {e}", file=sys.stderr)
        return 1
    print(f"OK   geometry: {len(design_dirs)} design(s) within envelope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
