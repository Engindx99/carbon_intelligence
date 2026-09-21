"""Closed-form fluid-volume properties of catalogue components.

Volumes, cross-sections, wetted areas and hydraulic diameters, from
the dimensions in geometry/catalog.py and nothing else. Each function
names the fields it needs; if any is None, it raises MissingGeometry
listing them. No missing value is filled in here.

Conventions, all SI:

  * D is the effective inner diameter, so every property is of the
    fluid space inside the refractory.
  * A cyclone body is a barrel (cylinder D x barrel_h) on a cone
    (frustum D -> dust_D over cone_h). Its wetted area follows the FLS
    reference model (arXiv 2409.10916, eq. 4): barrel wall, roof
    annulus outside the vortex finder, and cone wall. The vortex
    finder's own surfaces and the inlet duct are not counted.
  * A calciner or kiln is a cylinder D x length. Its wetted area is
    the side wall only: the end faces are inlet and outlet.
  * Ducts (risers, gooseneck) get cross-section properties only. The
    gooseneck and the vendor risers have no published length. The FLS
    risers do, but the paper's end-cone description and its volume
    equations (32)-(34) disagree for the Table 8 values, so no riser
    volume is computed until the source settles it. Neither reading is
    adopted; see "Açık belirsizlikler" in geometry/SOURCES.md.
"""

from dataclasses import dataclass
import math


class MissingGeometry(ValueError):
    """A property needs catalogue fields that no source gives."""

    def __init__(self, what, fields):
        self.fields = tuple(fields)
        super().__init__(f"{what}: missing {', '.join(self.fields)}")


def require_fields(what, part, prefix, names):
    """The values of `names` on `part`, or MissingGeometry."""

    missing = [f"{prefix}.{n}" for n in names if getattr(part, n) is None]

    if missing:
        raise MissingGeometry(what, missing)

    return [getattr(part, n).value for n in names]


# ---------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------

def disc_area(D):
    return 0.25 * math.pi * D * D


def cylinder_volume(D, L):
    return disc_area(D) * L


def cylinder_side_area(D, L):
    return math.pi * D * L


def frustum_volume(D1, D2, L):
    """Truncated cone between end diameters D1 and D2, height L."""

    r1, r2 = 0.5 * D1, 0.5 * D2

    return math.pi * L * (r1 * r1 + r1 * r2 + r2 * r2) / 3.0


def frustum_side_area(D1, D2, L):
    r1, r2 = 0.5 * D1, 0.5 * D2

    return math.pi * (r1 + r2) * math.hypot(r1 - r2, L)


@dataclass(frozen=True)
class Section:
    """A flow cross-section: area [m2], wetted perimeter [m], D_h = 4A/P [m]."""

    area: float
    perimeter: float

    @property
    def hydraulic_D(self):
        return 4.0 * self.area / self.perimeter


def circle(D):
    return Section(disc_area(D), math.pi * D)


def rectangle(w, h):
    return Section(w * h, 2.0 * (w + h))


def annulus(D_outer, D_inner):
    return Section(
        disc_area(D_outer) - disc_area(D_inner),
        math.pi * (D_outer + D_inner),
    )


# ---------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CycloneProperties:
    """One cyclone of a stage; multiply by `count` for the stage."""

    stage: int
    count: int
    barrel_volume: float
    cone_volume: float
    wetted_area: float
    height: float
    cone_half_angle_deg: float
    barrel: Section
    inlet: Section
    vortex_finder: Section
    roof_annulus: Section
    dust_outlet: Section

    @property
    def body_volume(self):
        """Barrel plus cone [m3], vortex finder interior included."""

        return self.barrel_volume + self.cone_volume


CYCLONE_FIELDS = (
    "D", "barrel_h", "cone_h", "vortex_len",
    "vortex_D", "dust_D", "inlet_w", "inlet_h",
)


def cyclone_properties(stage):

    D, barrel_h, cone_h, _vortex_len, vortex_D, dust_D, inlet_w, inlet_h = (
        require_fields(f"cyclone C{stage.stage}", stage, f"C{stage.stage}", CYCLONE_FIELDS)
    )

    return CycloneProperties(
        stage=stage.stage,
        count=stage.count,
        barrel_volume=cylinder_volume(D, barrel_h),
        cone_volume=frustum_volume(D, dust_D, cone_h),
        wetted_area=(
            cylinder_side_area(D, barrel_h)
            + disc_area(D) - disc_area(vortex_D)
            + frustum_side_area(D, dust_D, cone_h)
        ),
        height=barrel_h + cone_h,
        cone_half_angle_deg=math.degrees(math.atan2(0.5 * (D - dust_D), cone_h)),
        barrel=circle(D),
        inlet=rectangle(inlet_w, inlet_h),
        vortex_finder=circle(vortex_D),
        roof_annulus=annulus(D, vortex_D),
        dust_outlet=circle(dust_D),
    )


@dataclass(frozen=True)
class VesselProperties:
    volume: float
    wetted_area: float
    section: Section


def vessel_properties(vessel, name):
    """A cylinder D x length: calciner, or kiln (with `kiln` as name)."""

    D, length = require_fields(name, vessel, name, ("D", "length"))

    return VesselProperties(
        volume=cylinder_volume(D, length),
        wetted_area=cylinder_side_area(D, length),
        section=circle(D),
    )


def duct_section(duct, name):
    """Cross-section of a riser or the gooseneck."""

    (D,) = require_fields(name, duct, name, ("D",))

    return circle(D)
