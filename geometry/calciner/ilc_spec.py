"""The in-line calciner's reserved envelope -- NOT the calciner.

WHY THIS EXISTS BEFORE THE VESSEL DOES
--------------------------------------
The preheater tower stands around the calciner. Its column radius, and
therefore the plan offset between one cyclone stage and the next, is
set by how much of the axis the calciner needs. So the tower cannot be
laid out until that radius is known -- and a radius typed in by hand
would be a number with nothing behind it, which is the one thing
`geometry/` does not allow itself.

THE DIAMETER IS DERIVED, AND FROM THE SAME DUTY
-----------------------------------------------
    D = sqrt(4 Qv / (pi u))

the same form as `TowerSpec.riser_diameter` and the same reasoning:
an area follows from a volumetric flow at a stated velocity, and a
free ratio could disagree with the duty the vessel was sized for.

The duty is NOT restated here. `TowerSpec` hands this spec the
cyclone's own `volumetric_flow`, so there is one gas in the model, not
two that have to be kept equal.

    5-8 m/s is the in-line calciner band. Below it the meal drops out
    of suspension; above it the residence time collapses and the
    calcination does not finish.

THIS IS A LOWER BOUND
---------------------
The real ILC carries kiln gas PLUS tertiary air PLUS the combustion
products of 60 % of the fuel, which is more gas than the preheater's
top-stage design duty. When the vessel is actually modelled it
re-derives its diameter from its own duty and the tower's clearances
are re-checked against the bigger number -- they are not relaxed to
suit it. Reserving too little now would be the kind of error that only
shows up as a collision later, so the docstring says it out loud.

WHAT THE HEIGHT IS FOR, AND WHAT IT IS NOT
------------------------------------------
`body_height_m` is a PHYSICAL vessel height. The twin's
`calciner.length = 25.0 m` is not: physics/shell.py:842-848 calls its
D = 4.2 m x L = 25 m "placeholder geometry", and
physics/axial_coordinate.py's z is a distance along the solids path,
not an elevation -- the twin carries no elevation model at all. What
the twin's 25 m buys is GAS PATH LENGTH, i.e. residence time. A 10 m
body plus its connecting ducts gives 2.7-2.8 s, inside the 2-5 s band
an ILC is designed to and close to the twin's own 2.02 s. So the two
numbers are not in conflict and 25 m is not forced on the CAD.

NOTHING HERE IS WIRED INTO THE TWIN.
"""

import math
from dataclasses import dataclass


SCALAR_RANGES = {
    "design_volumetric_flow_m3_s": (10.0, 500.0),
    "gas_velocity_m_s":            (5.0, 8.0),
    "body_height_m":               (5.0, 40.0),
}


@dataclass(frozen=True)
class ILCSpec:
    """The calciner's reserved plan envelope and body height, in SI."""

    # Handed in, never chosen here -- see the module docstring.
    design_volumetric_flow_m3_s: float

    gas_velocity_m_s: float = 6.0     # m/s, the ILC band is 5-8
    body_height_m:    float = 10.0    # m, the cylindrical vessel

    def __post_init__(self):
        self._validate()

    # ======================================================
    # DERIVED
    # ======================================================
    @property
    def D_body(self):
        """Vessel bore [m] -- an area from the duty, nothing else."""

        return math.sqrt(
            4.0 * self.design_volumetric_flow_m3_s
            / (math.pi * self.gas_velocity_m_s)
        )

    @property
    def reserved_radius(self):
        """How much of the tower axis the calciner takes [m].

        The bare vessel radius. Erection clearance is the TOWER's to
        add, because it is the tower that has to stand back -- and it
        is the tower's parameter, so it belongs in one place there
        rather than being half-applied here.
        """

        return 0.5 * self.D_body

    @property
    def cross_sectional_area(self):
        return math.pi * self.reserved_radius ** 2

    @property
    def body_volume(self):
        return self.cross_sectional_area * self.body_height_m

    @property
    def body_residence_time(self):
        """Gas residence in the BODY alone [s].

        Not the calciner's residence time: the connecting ducts carry
        the gas too, and they are most of it. Reported so the body
        height can be argued about with a number attached.
        """

        return self.body_height_m / self.gas_velocity_m_s

    # ======================================================
    # VALIDATION -- reject, never clamp (CLAUDE.md)
    # ======================================================
    def _validate(self):

        for name, (lo, hi) in SCALAR_RANGES.items():

            value = float(getattr(self, name))

            if not (lo <= value <= hi):
                raise ValueError(
                    f"ILCSpec.{name} must be within [{lo}, {hi}], "
                    f"got {value}"
                )


def ilc_report(spec=None, duct_length_m=22.0, duct_velocity_m_s=18.0):
    """The reserved envelope, as text. Makes no geometry."""

    if spec is None:
        from ..preheater.cyclone_spec import CycloneSpec

        spec = ILCSpec(
            design_volumetric_flow_m3_s=CycloneSpec().volumetric_flow
        )

    duct_time = duct_length_m / duct_velocity_m_s
    out = []

    out.append("=" * 66)
    out.append("IN-LINE CALCINER -- reserved envelope (no solid is built)")
    out.append("=" * 66)
    out.append("")
    out.append(
        f"  design duty          {spec.design_volumetric_flow_m3_s:10.2f} m3/s"
        "   (the preheater's own)"
    )
    out.append(f"  gas velocity         {spec.gas_velocity_m_s:10.2f} m/s")
    out.append(f"  DERIVED bore         {spec.D_body:10.3f} m")
    out.append(f"  reserved radius      {spec.reserved_radius:10.3f} m")
    out.append(f"  body height          {spec.body_height_m:10.2f} m")
    out.append(f"  body volume          {spec.body_volume:10.2f} m3")
    out.append("")
    out.append("RESIDENCE TIME  (an ILC is designed to 2-5 s)")
    out.append(f"  body                 {spec.body_residence_time:10.2f} s")
    out.append(
        f"  + {duct_length_m:.0f} m of duct at "
        f"{duct_velocity_m_s:.0f} m/s {duct_time:10.2f} s"
    )
    out.append(
        f"  total                {spec.body_residence_time + duct_time:10.2f} s"
    )
    out.append("")
    out.append(
        "  The twin's calciner.length = 25.0 m is a PROCESS length, not"
    )
    out.append(
        "  an elevation (physics/shell.py:842-848 calls it placeholder"
    )
    out.append(
        "  geometry). It buys 25/12.36 = 2.02 s of gas path. The body"
    )
    out.append(
        "  plus its ducts buys the same thing, so 25 m is not forced"
    )
    out.append("  on the CAD as a height.")
    out.append("")
    out.append("  NOT WIRED INTO THE TWIN. Geometry only -- no solver change.")
    out.append("")

    return "\n".join(out)


if __name__ == "__main__":
    print(ilc_report())
