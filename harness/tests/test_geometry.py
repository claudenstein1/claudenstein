"""Geometry envelope tests (acceptance criterion 2).

The envelope-violating fixture lives here as a pytest, not as a committed bad
design (spec section 9.2, 9.5). Skipped when build123d is not installed.
"""

import pytest

build123d = pytest.importorskip("build123d")

from harness import validate_geometry as G


def _box(x, y, z):
    with build123d.BuildPart() as bp:
        build123d.Box(x, y, z)
    return bp.part


def test_oversize_cnc_part_is_flagged():
    part = _box(400, 50, 50)  # 400 mm exceeds the 300 mm CNC envelope
    errors = G.check_part("bar", part, "cnc")
    assert errors, "expected an envelope violation to be reported"
    assert "exceeds" in errors[0]
    assert "cnc" in errors[0]


def test_in_envelope_cnc_part_passes():
    part = _box(100, 100, 100)
    assert G.check_part("block", part, "cnc") == []


def test_oversize_fdm_part_is_flagged():
    part = _box(300, 100, 100)  # 300 mm exceeds the 250 mm FDM envelope
    errors = G.check_part("plate", part, "fdm")
    assert errors and "fdm" in errors[0]


def test_orientation_is_considered():
    # A tall thin part that fits if reoriented should pass.
    part = _box(160, 100, 300)  # sorted dims fit CNC (300<=... no: 300>300? equal ok)
    # Largest dim 300 == CNC largest 300 -> fits (with tolerance).
    assert G.check_part("post", part, "cnc") == []


def test_unknown_machine_is_flagged():
    part = _box(10, 10, 10)
    errors = G.check_part("widget", part, "laser")
    assert errors and "unknown machine" in errors[0]
