"""Fluid volumes of single components: one cyclone, the calciner.

A component is built from its catalogue dimensions plus the CFD
boundary parameters (geometry/modelling.py), and from nothing else.
The dimensioning below is pure Python; CadQuery is imported only when
a solid is actually built.

THE CYCLONE. Its own axis is z, the dust outlet at z = 0.

    cone       frustum dust_D -> D over 0 .. cone_h
    barrel     cylinder D over cone_h .. roof
    inlet      a straight rectangular duct, inlet_w wide and inlet_h
               tall, its top flush with the roof and its outer wall
               tangent to the barrel. Gas enters along +x at
               y in [R - inlet_w, R], so the swirl is anticlockwise
               seen from above. The published volute is not modelled;
               a tangential duct of the published section is the
               simplest geometry that feeds it.
    finder     the vortex finder's wall, vortex_finder_wall_m thick,
               from roof - vortex_len up to the roof, is cut out; the
               finder's bore continues above the roof to the outlet
               face.

Where the published inlet is taller than the barrel (C2-C5 on every
line), the duct runs down past the barrel into the cone region. That
is what the catalogue's dimensions describe, and it is built as they
describe it.

Boundary faces: the inlet face, the outlet face above the roof, and
the dust outlet disc (no meal pipe: SOURCES.md, decision 4).

THE CALCINER. A cylinder D x length on z. Its base is the single inlet
face (kiln gas and tertiary air together: SOURCES.md, decision 3),
its top the outlet face.

No riser solid is built: see "Açık belirsizlikler" in SOURCES.md.

These checks refuse a combination that cannot be built; they never
adjust a dimension to make it buildable.

VOLUMES. A solid here is the CFD domain: the equipment plus the inlet
and outlet extensions. Its volume is not the equipment volume and is
not to be used for residence time or hold-up; that is
properties.py's body_volume / vessel volume.
"""

from dataclasses import dataclass
import math

from geometry.properties import CYCLONE_FIELDS, require_fields


@dataclass(frozen=True)
class CycloneLayout:
    """Every coordinate a cyclone solid is built from [m]."""

    stage: int
    D: float
    cone_h: float
    roof: float
    dust_D: float
    vortex_D: float
    vortex_len: float
    wall: float
    inlet_w: float
    inlet_h: float
    inlet_x0: float
    outlet_top: float


def cyclone_layout(stage, cfd):
    """The coordinates of one cyclone of `stage`, or a ValueError
    saying why these dimensions and boundary parameters cannot be built."""

    D, barrel_h, cone_h, vortex_len, vortex_D, dust_D, inlet_w, inlet_h = (
        require_fields(f"cyclone C{stage.stage}", stage, f"C{stage.stage}", CYCLONE_FIELDS)
    )

    name = f"C{stage.stage}"
    R = 0.5 * D
    roof = cone_h + barrel_h
    wall = cfd.vortex_finder_wall_m
    inlet_x0 = -cfd.inlet_extension_over_D * D

    # The inlet face must lie outside the barrel: the barrel reaches
    # x = -sqrt(R^2 - y^2) at the duct's inner wall y = R - w.
    reach = math.sqrt(R * R - (R - inlet_w) ** 2)

    if -inlet_x0 <= reach:
        raise ValueError(
            f"{name}: inlet_extension_over_D = {cfd.inlet_extension_over_D} puts the "
            f"inlet face at x = {inlet_x0:.3f} m, inside the barrel (reaches "
            f"x = {-reach:.3f} m); it must exceed {reach / D:.3f}"
        )

    if inlet_h >= roof:
        raise ValueError(
            f"{name}: inlet_h = {inlet_h:.3f} m reaches below the dust outlet "
            f"(body height {roof:.3f} m)"
        )

    if 0.5 * vortex_D + wall >= R:
        raise ValueError(
            f"{name}: vortex finder wall {wall} m does not fit between the "
            f"finder (D {vortex_D:.3f} m) and the barrel (D {D:.3f} m)"
        )

    if vortex_len >= roof:
        raise ValueError(
            f"{name}: vortex finder ({vortex_len:.3f} m) reaches below the dust outlet"
        )

    return CycloneLayout(
        stage=stage.stage,
        D=D,
        cone_h=cone_h,
        roof=roof,
        dust_D=dust_D,
        vortex_D=vortex_D,
        vortex_len=vortex_len,
        wall=wall,
        inlet_w=inlet_w,
        inlet_h=inlet_h,
        inlet_x0=inlet_x0,
        outlet_top=roof + cfd.outlet_extension_over_vortex_D * vortex_D,
    )


def cyclone_solid(stage, cfd):
    """The fluid volume of ONE cyclone of `stage`."""

    from geometry import solids

    g = cyclone_layout(stage, cfd)
    R = 0.5 * g.D

    body = solids.fuse(
        solids.frustum(g.dust_D, g.D, g.cone_h),
        solids.cylinder(g.D, g.roof - g.cone_h, g.cone_h),
        solids.box(g.inlet_x0, 0.0, R - g.inlet_w, R, g.roof - g.inlet_h, g.roof),
    )

    body = body.cut(
        solids.tube(
            g.vortex_D + 2.0 * g.wall, g.vortex_D, g.vortex_len, g.roof - g.vortex_len
        )
    )

    bore = solids.cylinder(
        g.vortex_D, g.outlet_top - (g.roof - g.vortex_len), g.roof - g.vortex_len
    )

    return solids.fuse(body, bore)


def calciner_solid(line):
    """The calciner's fluid volume: a cylinder D x length on z."""

    from geometry import solids

    D, length = require_fields("calciner", line.calciner, "calciner", ("D", "length"))

    return solids.cylinder(D, length)


def component_names(line):
    """The components of `line` that have a solid builder."""

    return [f"C{c.stage}" for c in line.cyclones] + ["calciner"]


def build_component(line, name, cfd):
    """One named component of `line` as a solid."""

    if name == "calciner":
        return calciner_solid(line)

    for stage in line.cyclones:
        if name == f"C{stage.stage}":
            return cyclone_solid(stage, cfd)

    raise KeyError(f"{line.key}: no component {name!r}; has {component_names(line)}")
