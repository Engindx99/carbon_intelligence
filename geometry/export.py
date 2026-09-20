"""STEP and STL output, for any unit.

STEP is the deliverable: it carries the B-rep, so a solid opens in any
CAD package with its analytic cylinders and cones intact and can be
dimensioned there. STL is a tessellation and is written only as a quick
visual check -- it cannot be measured.

Artefacts land under geometry/output/<unit>/, one directory per unit,
so the preheater's files never sit next to the cooler's.
"""

from pathlib import Path

import cadquery as cq


OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


def unit_output_dir(unit):
    """Where one unit's artefacts go."""

    return OUTPUT_ROOT / unit


def _prepare(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def export_step(shape, path):
    """Write the B-rep. This is the one that can be measured."""

    path = _prepare(path)
    cq.exporters.export(shape, str(path), exportType="STEP")

    return path


def export_stl(shape, path, tolerance=1.0e-3, angular_tolerance=0.1):
    """Write a tessellation, for looking at only."""

    path = _prepare(path)

    cq.exporters.export(
        shape,
        str(path),
        exportType="STL",
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )

    return path


def export_solid(shape, unit, stem, output_dir=None):
    """Both formats, into geometry/output/<unit>/. Returns the paths."""

    directory = Path(output_dir) if output_dir else unit_output_dir(unit)

    return (
        export_step(shape, directory / f"{stem}.step"),
        export_stl(shape, directory / f"{stem}.stl"),
    )
