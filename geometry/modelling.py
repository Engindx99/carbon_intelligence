"""Modelling parameters: choices of the CFD model, not plant dimensions.

Nothing here comes from a plant source, and nothing here enters the
catalogue. These values say where the model's boundary faces sit,
and they are read from configs/twin_cfg.yaml under
`geometry.cfd_boundary` with no defaults in code. If one is missing
the build refuses and names it.

    inlet_extension_over_D
        How far upstream of the barrel axis the inlet's boundary face
        sits, as a multiple of the cyclone's effective D. It must put
        the face outside the barrel; components.py checks that per
        cyclone.
    outlet_extension_over_vortex_D
        How far above the roof the vortex finder's outlet face sits,
        as a multiple of the vortex finder's diameter.
    vortex_finder_wall_m
        Thickness of the vortex finder's wall [m]. The fluid volume
        needs a wall to separate the gas leaving through the finder
        from the gas swirling around it.
"""

from dataclasses import dataclass, fields
import math

from geometry.config import twin_cfg, TWIN_CFG_PATH


@dataclass(frozen=True)
class CfdBoundaryParams:
    inlet_extension_over_D: float
    outlet_extension_over_vortex_D: float
    vortex_finder_wall_m: float

    def __post_init__(self):

        for f in fields(self):
            value = getattr(self, f.name)

            if not (isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0):
                raise ValueError(
                    f"geometry.cfd_boundary.{f.name} must be a positive number, got {value!r}"
                )


def cfd_boundary_params(path=None):
    """The configured CFD boundary parameters, or a ValueError naming
    what is missing."""

    block = (twin_cfg(path).get("geometry") or {}).get("cfd_boundary")
    names = [f.name for f in fields(CfdBoundaryParams)]

    if not isinstance(block, dict):
        raise ValueError(f"{path or TWIN_CFG_PATH}: geometry.cfd_boundary is missing")

    missing = [n for n in names if n not in block]

    if missing:
        raise ValueError(
            f"{path or TWIN_CFG_PATH}: geometry.cfd_boundary is missing "
            + ", ".join(missing)
        )

    return CfdBoundaryParams(**{n: float(block[n]) for n in names})
