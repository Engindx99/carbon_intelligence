"""
Faz 2 -- ONE cyclone, built as a solid from geometry.preheater.cyclone_spec.

This module carries no dimension of its own. Every length it uses is
read off the spec, so the only way to change the cyclone is to change
the spec, and the five copies of Faz 4 cannot drift apart because
there is only ever one shape object.

WHAT THE SOLID IS
-----------------
The INNER (wetted) envelope: one closed solid whose Volume() is the
gas volume. Vessel walls, refractory, flanges and supports are not
modelled, so every diameter here is an INNER diameter. Two things
follow, and both are deliberate:

  * the volume is directly the quantity a later `V_cell` would be, so
    reusing this for the twin is a read rather than a re-derivation.
    NOT WIRED IN -- that is Faz 6 item 2 and out of scope here.
  * shelling outward by a wall thickness is a single later step if the
    external envelope is ever wanted.

Exactly one wall has to exist anyway: the vortex finder's. A dip tube
of zero thickness is an internal baffle of zero thickness, which is not
a valid B-rep solid -- the envelope could not close around it and the
cyclone would have no vortex finder at all. It is cut out as a void,
not added as material.

DATUM
-----
z = 0 at the dipleg discharge, +Z up, axis on Z. Every part of the
cyclone then has z >= 0 and the whole of Faz 5 is an addition to z, so
a stage's position never touches its shape.

    z = 0                      dipleg discharge      <- datum
    z = L_dip                  dipleg / cone
    z = L_dip + H_cone         cone / barrel
    z = roof - a               volute floor
    z = roof - S               dip tube mouth
    z = roof                   roof
    z = roof + E               gas outlet

WHY THE CONE IS makeCone AND NOT A LOFT
---------------------------------------
Both draw the same frustum, but makeCone leaves an analytic OCCT
conical surface whose half-angle can be read straight back out of the
B-rep. A loft leaves a B-spline, and the cone angle -- the one
INDEPENDENT dimension of the cone -- would then be unverifiable in the
finished solid. Faz 3 reads it back; see geometry/measure.py.

THE VOLUTE IS A RULED LOFT, NOT A SWEEP
---------------------------------------
The scroll narrows: its outer wall spirals in from R + b at the mouth
to the barrel at the end of the wrap, which is what turns all of the
gas into the body. A swept profile is constant by construction and
cannot do that, and `sweep(multisection=True)` self-intersects exactly
in this regime, where the section width (0.30 D) is comparable to the
path's radius of curvature (0.50 D). A ruled loft through k radial
sections is one OCCT call, has no booleans and no Frenet frame, and
its only cost is that the outer wall is chordal -- an O((theta/k)^2)
volume error that Faz 3 drives to zero by refining k.

THE ONE OVERLAP
---------------
Butt joints everywhere the mating faces are exactly coincident: the
dipleg on the cone, the cone on the barrel, the outlet bore on the
roof. OCCT fuses those cleanly.

The volute is the exception. It meets the barrel TANGENTIALLY, and a
tangential fuse with zero overlap leaves a zero-thickness sliver and a
non-manifold result. So the scroll's inner radius is pulled `ov` inside
the barrel wall. That overlap is numerical, and Faz 3 proves it by
halving it and asserting the fused volume does not move.
"""

from math import cos, radians, sin

import cadquery as cq
from cadquery import Vector

from .cyclone_spec import CycloneSpec


# ======================================================
# THE PARTS
#
# Each builder takes the spec and returns one solid in the
# datum above. They are kept separate and handed back by
# name because reading "the height of the cylinder" out of
# a fused B-rep is guesswork, while a component's own
# bounding box and volume are exact and analytic.
# ======================================================
def roof_height(spec):
    """z of the cyclone roof [m]."""

    return spec.dipleg_length + spec.cone_height + spec.cylinder_height


def build_dipleg(spec):
    return cq.Solid.makeCylinder(
        0.5 * spec.dipleg_diameter,
        spec.dipleg_length,
        Vector(0, 0, 0),
        Vector(0, 0, 1),
    )


def build_cone(spec):
    """The frustum, as an analytic cone so its angle stays readable."""

    return cq.Solid.makeCone(
        0.5 * spec.dipleg_diameter,
        0.5 * spec.D_body,
        spec.cone_height,
        Vector(0, 0, spec.dipleg_length),
        Vector(0, 0, 1),
    )


def build_barrel(spec):
    return cq.Solid.makeCylinder(
        0.5 * spec.D_body,
        spec.cylinder_height,
        Vector(0, 0, spec.dipleg_length + spec.cone_height),
        Vector(0, 0, 1),
    )


def build_outlet(spec):
    """The gas outlet bore standing above the roof."""

    return cq.Solid.makeCylinder(
        0.5 * spec.vortex_finder_diameter,
        spec.vortex_finder_protrusion,
        Vector(0, 0, roof_height(spec)),
        Vector(0, 0, 1),
    )


def build_vortex_finder_wall(spec):
    """The dip tube's wall, as the void to cut from the envelope.

    Runs from the mouth of the dip tube up through the roof to the top
    of the outlet bore, so that after the cut the swirl annulus and the
    outlet bore are separated everywhere they overlap in z.
    """

    r_in = 0.5 * spec.vortex_finder_diameter
    r_out = r_in + spec.vortex_finder_wall_thickness_m

    z_base = roof_height(spec) - spec.vortex_finder_length
    length = spec.vortex_finder_length + spec.vortex_finder_protrusion

    outer = cq.Solid.makeCylinder(r_out, length, Vector(0, 0, z_base), Vector(0, 0, 1))
    inner = cq.Solid.makeCylinder(r_in, length, Vector(0, 0, z_base), Vector(0, 0, 1))

    return outer.cut(inner)


def build_volute(spec, sections=72):
    """The wrap-around inlet scroll, as a ruled loft.

    `sections` is NUMERICAL, not physical: it is how finely the spiral
    is faceted. Faz 3 sweeps it and asserts the volume converges, which
    is what makes it a resolution rather than a dimension.
    """

    if int(sections) != sections or sections < 12:
        raise ValueError(
            f"volute sections must be an integer >= 12, got {sections}"
        )

    sections = int(sections)

    r_in = spec.volute_inner_radius

    z_hi = roof_height(spec)
    z_lo = z_hi - spec.inlet_height

    wrap_deg = spec.volute_wrap_angle_deg

    wires = []

    for j in range(sections + 1):

        # The scroll's outer radius is the cyclone's plan envelope --
        # the same law the tower layout keeps its distance by. It is
        # read from the spec rather than repeated here, because a
        # scroll built to one curve and cleared by another is a
        # collision waiting for someone to widen a ratio.
        azimuth = wrap_deg * j / sections
        theta = radians(azimuth)
        r_out = spec.plan_envelope_radius(azimuth)

        # SAME corner order on every section. ThruSections matches
        # vertices between neighbouring wires, and an inconsistent
        # order is what produces a loft twisted along the spiral.
        corners = (
            (r_in, z_lo),
            (r_out, z_lo),
            (r_out, z_hi),
            (r_in, z_hi),
            (r_in, z_lo),
        )

        wires.append(
            cq.Wire.makePolygon(
                [
                    Vector(r * cos(theta), r * sin(theta), z)
                    for r, z in corners
                ]
            )
        )

    return cq.Solid.makeLoft(wires, ruled=True)


# ======================================================
# THE CYCLONE
# ======================================================
COMPONENT_NAMES = (
    "dipleg",
    "cone",
    "barrel",
    "volute",
    "outlet",
    "vortex_finder_wall",
)


def build_components(spec=None, sections=72):
    """The named parts, before any boolean. Faz 3 asserts on these."""

    spec = spec or CycloneSpec()

    return {
        "dipleg": build_dipleg(spec),
        "cone": build_cone(spec),
        "barrel": build_barrel(spec),
        "volute": build_volute(spec, sections=sections),
        "outlet": build_outlet(spec),
        "vortex_finder_wall": build_vortex_finder_wall(spec),
    }


def build_cyclone(spec=None, sections=72):
    """One closed solid: the cyclone's inner gas envelope.

    Returns (envelope, components). The components are handed back so
    the verification can measure parts whose dimensions are known in
    closed form instead of trying to recover them from the fusion.
    """

    spec = spec or CycloneSpec()
    parts = build_components(spec, sections=sections)

    envelope = (
        parts["dipleg"]
        .fuse(parts["cone"])
        .fuse(parts["barrel"])
        .fuse(parts["volute"])
        .fuse(parts["outlet"])
    )

    envelope = envelope.cut(parts["vortex_finder_wall"]).clean()

    return envelope, parts


if __name__ == "__main__":

    from .. import export

    spec = CycloneSpec()
    envelope, parts = build_cyclone(spec)

    print(f"solids      {len(envelope.Solids())}")
    print(f"shells      {len(envelope.Shells())}")
    print(f"valid       {envelope.isValid()}")
    print(f"volume      {envelope.Volume():.3f} m3")
    print(f"area        {envelope.Area():.3f} m2")

    bb = envelope.BoundingBox()
    print(f"bbox z      {bb.zmin:.3f} .. {bb.zmax:.3f} m")
    print(f"total_height{spec.total_height:10.3f} m (spec)")

    for path in export.export_solid(envelope, "preheater", "cyclone"):
        print(f"wrote       {path}")
