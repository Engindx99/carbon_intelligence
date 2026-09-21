"""STEP and STL output under geometry/output/<line>/.

STEP carries the B-rep, with its analytic cylinders and cones, and is
the file a mesher reads. STL is a tessellation for a quick look.
"""

from pathlib import Path

import cadquery as cq


OUTPUT_ROOT = Path(__file__).resolve().parent / "output"


def export_solid(solid, line_key, name, output_dir=None):
    """Write `name`.step and `name`.stl; return both paths."""

    directory = Path(output_dir) if output_dir else OUTPUT_ROOT / str(line_key)
    directory.mkdir(parents=True, exist_ok=True)

    step = directory / f"{name}.step"
    stl = directory / f"{name}.stl"

    cq.exporters.export(solid, str(step), exportType="STEP")
    cq.exporters.export(
        solid, str(stl), exportType="STL", tolerance=1.0e-3, angularTolerance=0.1
    )

    return step, stl
