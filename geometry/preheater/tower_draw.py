"""The preheater as a set of 2-D technical drawings.

FIVE SHEETS, and each one answers a question the 3-D solid cannot be
asked by looking at it:

    PH-CAD-01  the cyclone in section, with the eleven named dimensions
    PH-CAD-02  the tower in elevation, with every level marked
    PH-CAD-03  the tower in PLAN -- five places, five azimuths, and the
               calciner envelope they stand around. The sheet the plan
               offset was made for.
    PH-CAD-04  one stage in detail: the meal line in TRUE LENGTH, the
               only view in which its 55 deg is 55 deg, and the stage's
               own frame, the only one in which `mouth_x` is an x
    PH-CAD-05  the two layout patterns side by side, at one scale, with
               the criteria that separate them. It decides nothing; it
               is what a decision would be made on.

NOTHING HERE DECIDES ANYTHING. There is no layout arithmetic in this
module: every level, every dimension and every angle is fetched out of
`CycloneSpec` / `TowerSpec` by name through `drafting.value_of`, and the
drawn geometry is checked against the fetched value at the moment it is
quoted. A view that has drifted from the parameter model raises instead
of printing. What this module does compute is SHAPE -- outlines,
circles, the scroll's spiral -- from those same properties, which is
what drawing something means.

    PYTHONPATH=. python3 -m geometry.preheater.tower_draw

No CAD kernel: matplotlib only, so the drawings come out in the twin's
own environment, next to the layout arithmetic they document.

PROJECTIONS. +x is to the right, +y into the page, +z up. z = 0 is the
stage 5 dipleg discharge, the datum the whole tower is dimensioned
from.

AN ELEVATION HAS A VIEWER, and until it was given one the sheets lied.
Every riser column stands `riser_reach` = 6.604 m clear of the cyclone
it feeds, with `riser_column_clearance` = 2.548 m of air at the
narrowest point. Drawn flat on a FAN layout, as a translucent band over
the body with the body's own outline showing straight through it, the
column read as a duct routed THROUGH the vessel -- and that is how the
defect was reported, three times, correctly.

Three things came out of it, and only the last is cosmetic:

  * `elevation_clearance` MEASURES the complaint -- the worst gap on
    paper between a duct and a cyclone it does not enter. Negative
    means a pipe is drawn through a vessel.
  * `best_elevation_bearing` sweeps the line of sight for the view
    that maximises it. Whether a positive one exists turns out to be
    a property of the LAYOUT, not of the drawing, which is why the
    committed pattern is the zigzag (best view +0.426 m) and not the
    fan (best view -0.556 m: no direction works).
  * the elevations carry depth -- a duct in front of a body is
    painted over it in paper first, so the body's outline stops at
    the duct's edge, and a duct behind one is a hidden line.

The stand-off itself is dimensioned where it is a true horizontal
distance and nowhere else: KESİT D-D on PH-CAD-02, whose cutting plane
contains both axes, and DETAY C-C on PH-CAD-04, the stage's own plan.

A WARNING THE OFFSET MADE NECESSARY. The stages no longer share an
axis or a facing, so a quantity is only true in the frame it was
measured in. `mouth_x` and `riser_approach_y` are the cyclone's own
coordinates and are a world x and y for NO stage; the chute's 55 deg
is true in neither orthographic view. Each of those is dimensioned on
one panel only, and that panel's title says which frame it is. The
sheets cannot catch this for themselves -- `Sheet.quote` compares a
number against what was DRAWN, and a stale panel draws the stale
value quite happily -- so tests/test_preheater_drawing.py asserts it
instead.
"""

import math
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from .. import drafting, plan
from ..drafting import Sheet, save_pdf, format_length, format_level
from ..twin_config import repose_angle_deg
from .cyclone_spec import CycloneSpec
from .tower_spec import CLEARANCES, LAYOUT_PATTERNS, TowerSpec


UNIT = "preheater"
SOURCE_NOTE = "geometry/preheater/cyclone_spec.py + tower_spec.py"
DATUM_NOTE = "±0.000 = kademe 5 dipleg ağzı"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / UNIT


# ==========================================================
# PROJECTIONS
# ==========================================================
def xz(path):
    """Front elevation: looking along +y."""

    return [(p[0], p[2]) for p in path]


def yz(path):
    """Side elevation: looking along -x."""

    return [(p[1], p[2]) for p in path]


def xy(path):
    """Plan: looking down."""

    return [(p[0], p[1]) for p in path]


def looking(bearing_deg):
    """An elevation seen from any compass bearing.

    Returns (project, depth, paper_bearing_deg): the projection onto
    paper, how far a point lies BEHIND the viewer, and the world
    bearing that points to the RIGHT on the paper.

    `looking(90)` is `xz` and `looking(180)` is `yz`, exactly -- those
    two are kept because most of the sheets want them by name.

    THE TOWER DECIDES WHERE IT IS SEEN FROM. A tower whose stages face
    one way has an elevation that shows its ducts standing clear of its
    vessels; a tower whose stages fan round a circle has none, and
    `best_elevation_bearing` is what tells the two apart.
    """

    radians = math.radians(bearing_deg)
    sight = (math.cos(radians), math.sin(radians))
    right = (math.sin(radians), -math.cos(radians))

    def project(path):
        return [(p[0] * right[0] + p[1] * right[1], p[2]) for p in path]

    def depth(point):
        return point[0] * sight[0] + point[1] * sight[1]

    return project, depth, math.degrees(math.atan2(right[1], right[0]))


def depth_xz(point):
    """How far a point lies BEHIND the viewer of the x-z elevation.

    That view looks along +y, so the viewer stands at -y and a larger
    y is further away. Positive means further.
    """

    return point[1]


def depth_yz(point):
    """How far a point lies behind the viewer of the y-z elevation.

    That view looks along -x, so the viewer stands at +x.
    """

    return -point[0]


def developed(path):
    """True-length view of a path that turns in plan.

    The horizontal axis is distance travelled in plan, the vertical axis
    is z. An inclined run laid at 55 deg to the horizontal is at 55 deg
    HERE and at something else in every orthographic view, which is why
    the meal line's angle may only be dimensioned on this one.
    """

    out = [(0.0, path[0][2])]
    run = 0.0

    for a, b in zip(path, path[1:]):
        run += math.hypot(b[0] - a[0], b[1] - a[1])
        out.append((run, b[2]))

    return out


# ==========================================================
# THE CYCLONE, AS SHAPE
# ==========================================================
def roof_z(cyc):
    """Local z of the cyclone roof -- where the barrel ends."""

    return cyc.total_height - cyc.vortex_finder_protrusion


def cyclone_outline(cyc):
    """The body silhouette in a meridional plane, (r, z), closed.

    Dipleg, cone, barrel, roof and the outlet duct that stands above it.
    The volute is drawn separately because it is not axisymmetric.
    """

    R = 0.5 * cyc.D_body
    rd = 0.5 * cyc.dipleg_diameter
    rv = 0.5 * cyc.vortex_finder_diameter

    z_cone = cyc.dipleg_length + cyc.cone_height
    z_roof = roof_z(cyc)
    z_top = cyc.total_height

    return [
        (-rd, 0.0), (-rd, cyc.dipleg_length), (-R, z_cone), (-R, z_roof),
        (-rv, z_roof), (-rv, z_top), (rv, z_top), (rv, z_roof),
        (R, z_roof), (R, z_cone), (rd, cyc.dipleg_length), (rd, 0.0),
    ]


def volute_band(cyc, azimuth_deg):
    """The scroll's section at one azimuth, as (r, z) corners.

    The outer radius is `CycloneSpec.plan_envelope_radius` -- the same
    law the solid is lofted through and the same one the tower layout
    keeps its distance by. The drawing does not own a curve of its own.
    """

    z_hi = roof_z(cyc)
    z_lo = z_hi - cyc.inlet_height

    r_in = cyc.volute_inner_radius
    r_out = cyc.plan_envelope_radius(azimuth_deg)

    return [(r_in, z_lo), (r_out, z_lo), (r_out, z_hi), (r_in, z_hi)]


def volute_spiral(cyc, sections=120):
    """The scroll's outer edge in plan, from the mouth round the wrap."""

    wrap = cyc.volute_wrap_angle_deg

    return [
        (
            cyc.plan_envelope_radius(wrap * i / sections)
            * math.cos(math.radians(wrap * i / sections)),
            cyc.plan_envelope_radius(wrap * i / sections)
            * math.sin(math.radians(wrap * i / sections)),
        )
        for i in range(sections + 1)
    ]


def cyclone_elevation_outlines(cyc, base_z, horizontal=0.0,
                               azimuths=(0.0, 180.0)):
    """What one cyclone covers on an elevation: body first, then scroll.

    The same polygons `draw_cyclone_elevation` inks and the same ones
    `draw_ducts` tests a duct against, so a duct can never be judged
    against an outline different from the one on the paper.
    """

    def place(r, z):
        return (horizontal + r, base_z + z)

    right, left = azimuths

    return [
        [place(r, z) for r, z in cyclone_outline(cyc)],
    ] + [
        [place(sign * r, z) for r, z in volute_band(cyc, azimuth)]
        for azimuth, sign in ((right, 1.0), (left, -1.0))
    ]


def draw_cyclone_elevation(panel, cyc, base_z, horizontal=0.0,
                           azimuths=(0.0, 180.0), internals=True,
                           fill=drafting.FILL):
    """One cyclone, seen side-on, with its dipleg discharge at `base_z`.

    `azimuths` is which two sides of the scroll the view cuts: (0, 180)
    for the x-z elevation, where the mouth faces the viewer's right, and
    (90, 270) for the y-z one.
    """

    body, *bands = cyclone_elevation_outlines(
        cyc, base_z, horizontal, azimuths
    )

    def place(r, z):
        return (horizontal + r, base_z + z)

    panel.polygon(body, style="outline", fill=fill)

    for band in bands:
        panel.polygon(
            band, style="hidden", fill=fill,
            zorder=drafting.Z_FILL + 0.1,
        )

    if internals:

        rv = 0.5 * cyc.vortex_finder_diameter
        z_hi = roof_z(cyc)
        z_lo = z_hi - cyc.vortex_finder_length

        for sign in (-1.0, 1.0):
            panel.polyline(
                [place(sign * rv, z_hi), place(sign * rv, z_lo)],
                style="hidden", zorder=drafting.Z_OUTLINE,
            )

        panel.polyline(
            [place(-rv, z_lo), place(rv, z_lo)],
            style="hidden", zorder=drafting.Z_OUTLINE,
        )

    panel.centre_line(
        [place(0.0, -0.05 * cyc.total_height),
         place(0.0, 1.05 * cyc.total_height)]
    )


def stage_occluders(tower, horizontal, azimuths_of, depth, stages=None):
    """Each cyclone's elevation silhouette, with the depth of its axis.

    `horizontal` and `azimuths_of` are the same functions of a placement
    the elevation itself draws with, so the silhouette tested against is
    the silhouette on the paper.
    """

    cyc = tower.cyclone

    return [
        (
            cyclone_elevation_outlines(
                cyc, placement.z, horizontal(placement),
                azimuths_of(placement),
            ),
            depth((placement.x, placement.y, placement.z)),
        )
        for placement in tower.placements()
        if stages is None or placement.stage in stages
    ]


# How finely a duct is chopped before each piece is asked which side of
# a cyclone it passes on [m]. Well under the 1.113 m meal-line bore, so
# a crossing is never misplaced by more than a fraction of a duct width.
OCCLUSION_STEP_M = 0.20


def _densify(path, step=OCCLUSION_STEP_M):
    """`path` with no leg longer than `step`, ends kept exactly."""

    out = [path[0]]

    for a, b in zip(path, path[1:]):

        length = math.dist(a, b)
        pieces = max(1, int(math.ceil(length / step)))

        for i in range(1, pieces + 1):
            t = i / pieces
            out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))

    return out


def visibility_of(point, projection, depth, occluders):
    """Where `point` stands relative to the cyclones it projects onto.

        "clear"   over no cyclone at all
        "front"   over one, and nearer the viewer than its axis
        "hidden"  over one, and further from the viewer than its axis

    Only the near/far half of that is about the tower; falling inside a
    silhouette is about the projection, and says nothing at all about
    whether anything touches.
    """

    flat = projection([point])[0]
    behind = depth(point)

    seen = "clear"

    for polygons, axis_depth in occluders:

        if not any(plan.point_in_polygon(flat, poly) for poly in polygons):
            continue

        if behind > axis_depth:
            return "hidden"

        seen = "front"

    return seen


def _visibility_runs(path, projection, depth, occluders):
    """`path` split into (visibility, [points]) runs, in order.

    A node shared by two runs belongs to both, so the drawn duct has no
    gap at the hand-over.
    """

    dense = _densify(path)

    runs = []

    for a, b in zip(dense, dense[1:]):

        middle = tuple(0.5 * (a[k] + b[k]) for k in range(3))
        where = visibility_of(middle, projection, depth, occluders)

        if runs and runs[-1][0] == where:
            runs[-1][1].append(b)
        else:
            runs.append((where, [a, b]))

    return runs


def draw_ducts(panel, tower, projection, names=None, label=False,
               alpha=0.30, depth=None, occluders=()):
    """Every duct the tower carries, in one projection.

    WITHOUT `depth` this is a flat overlay: every duct is drawn at the
    same translucency wherever it runs, which is right for the plan,
    where two things at the same (x, y) really are one above the other.

    WITH `depth` it is an elevation, and an elevation has a viewer. A
    duct that passes in front of a cyclone is painted over it -- bore in
    paper first, so the body's outline stops at the duct's edge the way
    it does on any sectioned drawing -- and a duct that passes behind
    one is drawn as a hidden line. Neither is a change to the tower: the
    riser column beside stage 3 stands `riser_reach` = 6.604 m off its
    cyclone's axis with `riser_column_clearance` = 2.548 m of gap, but
    that offset is almost all in y, and A-A looks along y. Drawn flat,
    the band lay over the body with the body's own outline showing
    through it, and read as a duct routed through the vessel.

    Ducts are hidden BY CYCLONES only, never by each other. Two ducts
    that cross in projection are drawn as they were before, one over the
    other, because the crossings that matter here are duct-on-vessel.
    """

    for name, kind, path, diameter in tower.connections():

        if names is not None and name not in names:
            continue

        if depth is None:
            panel.duct(
                projection(path), diameter, kind,
                label=name if label else None, alpha=alpha,
            )
            continue

        for where, run in _visibility_runs(path, projection, depth,
                                           occluders):

            if where == "hidden":
                panel.polyline(
                    projection(run), style="hidden",
                    color=drafting.DUCT_INK[kind],
                    zorder=drafting.Z_FRONT,
                )
            elif where == "front":
                panel.duct(
                    projection(run), diameter, kind, alpha=alpha,
                    zorder=drafting.Z_FRONT, halo=True,
                )
            else:
                panel.duct(projection(run), diameter, kind, alpha=alpha)

        if label:
            end = projection(path)[-1]
            panel.label(
                end[0], end[1], f" {name}",
                colour=drafting.DUCT_INK[kind], size=drafting.TEXT_DIM,
            )


# ==========================================================
# SHEET 1 -- THE CYCLONE IN SECTION
# ==========================================================
def sheet_cyclone(cyc=None):
    """PH-CAD-01: one cyclone, and the eleven dimensions that set it."""

    cyc = cyc or CycloneSpec()

    sheet = Sheet(
        model=cyc,
        title="SİKLON — KESİT A-A",
        subtitle="Beş kademenin tamamı bu tek geometrinin kopyasıdır",
        unit="PREHEATER / cyclone",
        number="PH-CAD-01",
        source_note="geometry/preheater/cyclone_spec.py",
        size="A3",
        datum="±0.000 = dipleg ağzı (siklon lokal ekseni)",
    )

    panel = sheet.panel((26.0, 64.0, 174.0, 214.0), "KESİT A-A")
    panel.fit((-9.0, 9.0), (-2.5, 21.5))

    R = 0.5 * cyc.D_body
    rd = 0.5 * cyc.dipleg_diameter
    rv = 0.5 * cyc.vortex_finder_diameter
    r_out = cyc.volute_outer_radius

    z_cone = cyc.dipleg_length + cyc.cone_height
    z_roof = roof_z(cyc)
    z_top = cyc.total_height

    draw_cyclone_elevation(panel, cyc, base_z=0.0)

    # ---- vertical chain, left of the body ----
    panel.dim_v(-6.4, 0.0, cyc.dipleg_length, "dipleg_length",
                right=False, extend_to=-rd)
    panel.dim_v(-6.4, cyc.dipleg_length, z_cone, "cone_height",
                right=False, extend_to=-R)
    panel.dim_v(-6.4, z_cone, z_roof, "cylinder_height",
                right=False, extend_to=-R)
    panel.dim_v(-6.4, z_roof, z_top, "vortex_finder_protrusion",
                right=False, extend_to=-rv)
    panel.dim_v(-8.0, 0.0, z_top, "total_height", right=False)

    # ---- the dip tube, which is the reason the roof is not the top ----
    panel.dim_v(5.6, z_roof - cyc.vortex_finder_length, z_roof,
                "vortex_finder_length", right=True)

    # ---- widths ----
    panel.dim_h(-R, R, -1.4, "D_body", above=False, extend_to=0.2)
    panel.dim_h(-rd, rd, -2.1, "dipleg_diameter", above=False,
                extend_to=0.0)
    panel.dim_h(-rv, rv, z_top + 1.1, "vortex_finder_diameter",
                above=True, extend_to=z_top)
    panel.dim_h(R, r_out, z_roof + 1.1, "inlet_width", above=True,
                extend_to=z_roof)
    panel.dim_v(7.4, z_roof - cyc.inlet_height, z_roof, "inlet_height",
                right=True, extend_to=r_out)

    # ---- the cone wall, against the meal's angle of repose ----
    panel.polyline(
        [(rd, cyc.dipleg_length), (rd + 2.6, cyc.dipleg_length)],
        style="construction", zorder=drafting.Z_DIM,
    )
    panel.dim_angle(
        (rd, cyc.dipleg_length), 1.9, 0.0, cyc.cone_wall_inclination_deg,
        "cone_wall_inclination_deg",
    )

    panel.leader(
        (r_out, z_roof - 0.5 * cyc.inlet_height), (1.0, 1.9),
        "volüt ağzı (270° sarım)",
    )
    panel.leader(
        (rv, z_roof - 0.8 * cyc.vortex_finder_length), (2.2, -1.2),
        "vortex finder (dalma borusu)",
    )
    panel.leader(
        (rd, 0.35 * cyc.dipleg_length), (2.4, -0.8), "dipleg",
    )

    top = sheet.text_block(
        (208.0, 278.0, 198.0, None),
        "ÖLÇÜ TABLOSU  —  cyclone_spec.py",
        _cyclone_table(cyc),
    ) - 8.0

    sheet.text_block(
        (208.0, top, 198.0, None),
        "TASARIM TABANI ve TÜRETİLEN BÜYÜKLÜKLER",
        _cyclone_basis(cyc),
    )
    sheet.text_block(
        (26.0, 54.0, 174.0, None),
        "NOTLAR",
        [
            "1  Kesit eksenel; volüt sarımı gizli çizgiyle,",
            "   ağzı sağda (azimut 0°) gösterilmiştir.",
            "2  Koni duvar eğimi malzemenin şev açısını geçmek",
            f"   zorundadır: {repose_angle_deg():.0f}° (motion.repose_angle_deg).",
            "3  Toplam yükseklik türetilmiştir: parçaların toplamı.",
        ],
    )

    return sheet


def _cyclone_table(cyc):

    rows = [
        ("toplam yükseklik", "total_height", cyc.total_height, "m"),
        ("gövde çapı", "D_body", cyc.D_body, "m"),
        ("silindirik bölüm", "cylinder_height", cyc.cylinder_height, "m"),
        ("konik bölüm", "cone_height", cyc.cone_height, "m"),
        ("koni yarı-açısı", "cone_half_angle_deg",
         cyc.cone_half_angle_deg, "°"),
        ("koni duvar eğimi", "cone_wall_inclination_deg",
         cyc.cone_wall_inclination_deg, "°"),
        ("vortex finder çapı", "vortex_finder_diameter",
         cyc.vortex_finder_diameter, "m"),
        ("vortex finder boyu", "vortex_finder_length",
         cyc.vortex_finder_length, "m"),
        ("çıkış borusu taşması", "vortex_finder_protrusion",
         cyc.vortex_finder_protrusion, "m"),
        ("dipleg çapı", "dipleg_diameter", cyc.dipleg_diameter, "m"),
        ("dipleg boyu", "dipleg_length", cyc.dipleg_length, "m"),
        ("giriş genişliği", "inlet_width", cyc.inlet_width, "m"),
        ("giriş yüksekliği", "inlet_height", cyc.inlet_height, "m"),
        ("volüt dış yarıçapı", "volute_outer_radius",
         cyc.volute_outer_radius, "m"),
        ("volüt iç yarıçapı", "volute_inner_radius",
         cyc.volute_inner_radius, "m"),
        ("volüt sarım açısı", "volute_wrap_angle_deg",
         cyc.volute_wrap_angle_deg, "°"),
    ]

    lines = [f"{'ÖLÇÜ':<24}{'PROPERTY':<28}{'DEĞER':>10}"]

    for label, source, value, unit in rows:
        lines.append(f"{label:<24}{source:<28}{value:>9.3f} {unit}")

    return lines


def _cyclone_basis(cyc):

    return [
        f"{'gaz debisi':<24}{'design_gas_mass_flow_kg_s':<28}"
        f"{cyc.design_gas_mass_flow_kg_s:>9.2f} kg/s",
        f"{'gaz sıcaklığı':<24}{'design_gas_temperature_K':<28}"
        f"{cyc.design_gas_temperature_K:>9.1f} K",
        f"{'giriş hızı':<24}{'design_inlet_velocity_m_s':<28}"
        f"{cyc.design_inlet_velocity_m_s:>9.2f} m/s",
        f"{'gaz yoğunluğu':<24}{'gas_density':<28}"
        f"{cyc.gas_density:>9.4f} kg/m3",
        f"{'hacimsel debi':<24}{'volumetric_flow':<28}"
        f"{cyc.volumetric_flow:>9.2f} m3/s",
        f"{'giriş kesiti':<24}{'inlet_area':<28}"
        f"{cyc.inlet_area:>9.3f} m2",
        f"{'ayrıştırma hacmi':<24}{'separator_volume':<28}"
        f"{cyc.separator_volume:>9.2f} m3",
        "",
        "D_body gaz debisinden türetilir: D = sqrt(Qv/(u·Ka·Kb)).",
        "Diğer bütün boyutlar D_body'nin oranıdır; hiçbiri",
        "bağımsız olarak girilmez.",
    ]


# ==========================================================
# SHEET 2 -- THE TOWER IN ELEVATION
# ==========================================================
def sheet_tower_elevation(tower=None):
    """PH-CAD-02: the stack, its levels and the ducts that join it."""

    tower = tower or TowerSpec()
    cyc = tower.cyclone

    view_bearing, _gap = best_elevation_bearing(tower)

    sheet = Sheet(
        model=tower,
        title=f"KULE — GÖRÜNÜŞ A-A  ({view_bearing:.1f}° yönüne bakış)",
        subtitle="Beş kademeli siklon kulesi, kotlar ve bağlantılar",
        unit="PREHEATER / tower",
        number="PH-CAD-02",
        source_note=SOURCE_NOTE,
        size="A1",
        datum=DATUM_NOTE,
    )

    # A1, and the panel takes nearly the whole height of it. The tower
    # is 117.93 m from the gas inlet to the top of the stack, and that
    # is what decides the sheet: at 1:250 it needs 472 mm of paper, so
    # anything smaller than A1 would have forced 1:500 and halved every
    # cyclone on the sheet.
    panel = sheet.panel((30.0, 44.0, 230.0, 520.0),
                        "GÖRÜNÜŞ A-A")
    panel.fit((-30.0, 24.0), (-6.5, 113.0))

    # WHERE THIS VIEW STANDS IS DERIVED, NOT PICKED. The sheet looks
    # from wherever this layout's ducts are best seen clear of its
    # vessels; for a zigzag that is a view in which every riser column
    # stands its full reach off its own cyclone, and for a fan there is
    # no such view and the notes say so.
    project, depth, paper_bearing = looking(view_bearing)

    def horizontal(placement):
        return project([(placement.x, placement.y, 0.0)])[0][0]

    def azimuths_of(placement):
        # Paper-right is the world bearing `paper_bearing`, which in
        # this stage's own frame is that less its azimuth. The two
        # scroll bands therefore differ from stage to stage, and that
        # asymmetry is the rotation, visible on paper.
        local = paper_bearing - placement.azimuth_deg
        return (local, local + 180.0)

    for placement in tower.placements():
        draw_cyclone_elevation(
            panel, cyc,
            base_z=placement.z,
            horizontal=horizontal(placement),
            azimuths=azimuths_of(placement),
        )

    draw_ducts(
        panel, tower, project, depth=depth,
        occluders=stage_occluders(tower, horizontal, azimuths_of, depth),
    )

    _elevation_levels(panel, tower, cyc, project, horizontal)
    _elevation_dimensions(panel, tower, cyc)
    _elevation_labels(panel, tower, cyc, project, horizontal)

    _stage_section(sheet, tower, cyc, stage=3,
                   rect=(284.0, 60.0, 250.0, 300.0))

    top = sheet.text_block(
        (284.0, 564.0, 252.0, None),
        "KOT TABLOSU  —  tower_spec.py",
        _level_table(tower, cyc),
    ) - 10.0

    sheet.text_block(
        (284.0, top, 252.0, None),
        "DÜŞEY ÖLÇÜLER",
        _vertical_table(tower, cyc),
    )

    top = sheet.text_block(
        (546.0, 564.0, 265.0, None),
        "BAĞLANTILAR  —  connections()",
        _connection_table(tower),
    ) - 10.0

    sheet.text_block(
        (546.0, top, 265.0, None),
        "NOTLAR",
        _elevation_notes(tower),
    )

    return sheet


def _stage_section(sheet, tower, cyc, stage, rect):
    """KESİT D-D: the plane through a cyclone's axis AND its own riser.

    THE VIEW A-A CANNOT BE, WHATEVER THE LAYOUT. A-A shows only the
    part of the stand-off that lies across its line of sight, so what
    it draws is a projection of the distance and not the distance.
    Even where the sweep finds a view that separates every column from
    its body -- which the zigzag has and the fan does not -- what that
    view shows is still foreshortened. A plane that CONTAINS both axes
    shows the distance itself, and is the only thing that can.

    The cutting plane is vertical, so every level on this panel is a
    true world level, and the horizontal axis is distance along the cut
    from the cyclone's axis -- in which `riser_reach` and
    `riser_column_clearance` are true horizontal distances and may be
    dimensioned. The plane turns with the stage, so this is the stage's
    own frame and the title says so.

    WHAT IS NOT TRUE HERE: the elbow's last leg into the mouth, and the
    chute, both leave the plane. Neither is dimensioned; the chute's
    true length is on PH-CAD-04. Every stage is the same picture --
    the tower is one stage screwed along a helix -- so drawing one is
    drawing all five.
    """

    bearing = tower.riser_bearing_rad
    ux, uy = math.cos(bearing), math.sin(bearing)

    def along(local_xy):
        """Distance from the cyclone's axis, along the cut."""

        return local_xy[0] * ux + local_xy[1] * uy

    base_z = tower.stage_base_z(stage)
    z_low, z_high = tower.riser_vertical_span(stage)
    reach = tower.riser_reach
    flank = tower.riser_local_envelope_radius

    meal = tower.meal_line_path(stage)

    panel = sheet.panel(
        rect,
        f"KESİT D-D — KADEME {stage}, SİKLON EKSENİ + RISER KOLONU DÜZLEMİ",
    )
    panel.fit(
        (-6.0, 11.0),
        (meal[1][2] - 2.5, base_z + cyc.total_height + 5.0),
    )

    cut = math.degrees(bearing)

    draw_cyclone_elevation(
        panel, cyc, base_z=base_z, horizontal=0.0,
        azimuths=(cut, cut + 180.0),
    )

    # The riser column, beside the body over its whole climb, and the
    # elbow that turns into the mouth. The elbow is foreshortened: it
    # runs in the local y this plane looks along.
    panel.duct(
        [(reach, z_low), (reach, z_high),
         (along((tower.mouth_x, 0.0)), z_high)],
        tower.riser_diameter, "gas", alpha=0.30,
    )

    # The dipleg's vertical leg, which drops on the axis and only then
    # turns away -- the leg the offset made possible.
    panel.duct(
        [(0.0, meal[0][2]), (0.0, meal[1][2])],
        tower.meal_line_diameter, "solids", alpha=0.30,
    )

    panel.leader(
        (0.0, meal[1][2]), (-1.6, 2.8),
        "oluk bu düzlemden çıkar\n(gerçek boy PH-CAD-04)",
        colour=drafting.SOLIDS_INK,
    )

    # THE TWO DIMENSIONS THE SHEET WAS MISSING. The clearance is taken
    # across the barrel, the only height at which the flank really is
    # `riser_local_envelope_radius` wide -- measuring it past the cone
    # would put the arrow where the body is not.
    barrel_z = base_z + 0.5 * (
        cyc.dipleg_length + cyc.cone_height + roof_z(cyc)
    )

    panel.dim_h(
        0.0, reach, base_z + cyc.total_height + 2.6, "riser_reach",
        above=True, extend_to=base_z + cyc.total_height,
    )
    panel.dim_h(
        flank, reach - 0.5 * tower.riser_diameter, barrel_z,
        "riser_column_clearance()", above=True,
    )

    panel.level(0.0, base_z, f"stage_base_z({stage})", x_text=-5.4)
    panel.level(
        reach, z_high, f"mouth_point({stage})[2]", x_text=10.3,
    )
    panel.level(
        reach, z_low, f"riser_vertical_span({stage})[0]", x_text=10.3,
    )
    panel.level(
        0.0, meal[1][2], f"meal_line_path({stage})[1][2]", x_text=-5.4,
    )

    panel.label(
        reach + 1.5, 0.5 * (z_low + z_high),
        f"riser_{stage}", colour=drafting.GAS_INK, size=drafting.TEXT_DIM,
    )

    return panel


def _elevation_levels(panel, tower, cyc, project, horizontal):
    """Every level is a z, so the view direction does not touch them.

    Only the leaders move: each one starts at its own stage's place on
    the paper, which is where the chosen view puts it.
    """

    def paper_x(point):
        return project([point])[0][0]

    for placement in tower.placements():

        stage = placement.stage

        panel.level(
            horizontal(placement) - 0.55 * cyc.D_body, placement.z,
            f"stage_base_z({stage})", x_text=-16.0,
        )
        panel.level(
            paper_x(tower.mouth_point(stage)), tower.mouth_point(stage)[2],
            f"mouth_point({stage})[2]", x_text=16.0,
        )

    top = horizontal(tower.placement(1))

    panel.level(
        top, tower.outlet_point(1)[2], "outlet_point(1)[2]", x_text=16.0,
    )
    panel.level(
        top, tower.tower_height, "tower_height", x_text=16.0,
    )

    bottom = tower.riser_path(tower.stage_count)[0]

    panel.level(
        paper_x((*tower.riser_axis(tower.stage_count), 0.0)), bottom[2],
        f"riser_path({tower.stage_count})[0][2]", x_text=16.0,
    )


def _elevation_dimensions(panel, tower, cyc):

    # The pitch, taken where it is easiest to read: two dipleg levels.
    panel.dim_v(
        -18.0, tower.stage_base_z(2), tower.stage_base_z(1), "pitch",
        right=False,
    )

    # The gap is the clearance the whole collision problem turned on.
    panel.dim_v(
        -22.0, tower.outlet_point(2)[2], tower.stage_base_z(1),
        "stage_gap", right=False,
    )

    panel.dim_v(
        -26.0, tower.stage_base_z(tower.stage_count), tower.tower_height,
        "tower_height", right=False,
    )

    # The exhaust stub's own length is not dimensioned here: it is
    # `exit_stack_height_ratio x D`, and the drawing may only quote what
    # the package exposes as a length. Its two ends are marked as
    # levels, which is the same information without the invented number.


def _elevation_labels(panel, tower, cyc, project, horizontal):

    def paper_x(point):
        return project([point])[0][0]

    for placement in tower.placements():

        panel.label(
            horizontal(placement) - 0.70 * cyc.D_body,
            placement.z + 0.62 * cyc.total_height,
            f"KADEME {placement.stage}", size=drafting.TEXT_LABEL,
            ha="right", fontweight="bold",
        )

    panel.label(
        paper_x((*tower.riser_axis(4), 0.0)) + 1.6,
        tower.stage_base_z(4) + 0.5 * cyc.total_height,
        "riser_4", colour=drafting.GAS_INK, size=drafting.TEXT_DIM,
    )
    panel.label(
        paper_x(tower.meal_line_path(3)[1]) + 0.8,
        tower.meal_line_path(3)[1][2] - 2.0,
        "meal_line_3", colour=drafting.SOLIDS_INK, size=drafting.TEXT_DIM,
    )
    panel.label(
        horizontal(tower.placement(1)) + 1.0, tower.tower_height - 2.2,
        "exit_stack", colour=drafting.GAS_INK, size=drafting.TEXT_DIM,
    )
    panel.label(
        paper_x(tower.meal_inlet_path()[0]) - 1.0,
        tower.meal_inlet_path()[0][2] + 1.2, "raw_meal_inlet",
        colour=drafting.SOLIDS_INK, size=drafting.TEXT_DIM, ha="right",
    )
    panel.label(
        paper_x((*tower.riser_axis(tower.stage_count), 0.0)) + 1.6,
        tower.riser_path(tower.stage_count)[0][2] + 6.0,
        "riser_5  (kalsinatörden)", colour=drafting.GAS_INK,
        size=drafting.TEXT_DIM,
    )


def _level_table(tower, cyc):

    lines = [
        f"{'KADEME':<8}{'dipleg':>10}{'çatı':>10}{'ağız':>10}{'çıkış':>10}",
    ]

    for stage in range(1, tower.stage_count + 1):

        base = tower.stage_base_z(stage)

        lines.append(
            f"{stage:<8}{base:>10.3f}"
            f"{base + cyc.total_height - cyc.vortex_finder_protrusion:>10.3f}"
            f"{tower.mouth_point(stage)[2]:>10.3f}"
            f"{tower.outlet_point(stage)[2]:>10.3f}"
        )

    lines += [
        "",
        f"{'baca üstü':<14}{'tower_height':<24}{tower.tower_height:>10.3f}",
        f"{'gaz girişi':<14}{'riser_path(5)[0][2]':<24}"
        f"{tower.riser_path(5)[0][2]:>10.3f}",
        "",
        "MEAL HATTI GİRİŞ KOTLARI  (riser düşey koşusuna düşmeli)",
        f"{'kademe':<10}{'giriş z':>10}{'riser aralığı':>24}{'':>4}",
    ]

    for stage in range(1, tower.stage_count):

        z_low, z_high = tower.riser_vertical_span(stage + 1)
        z_entry = tower.meal_line_path(stage)[-1][2]
        ok = "TAMAM" if z_low <= z_entry <= z_high else "HATA"

        lines.append(
            f"{stage:<10}{z_entry:>10.3f}"
            f"{z_low:>13.3f} ..{z_high:>8.3f}  {ok}"
        )

    return lines


def _vertical_table(tower, cyc):

    return [
        f"{'kademe adımı':<22}{'pitch':<20}{tower.pitch:>9.3f} m",
        f"{'kademe boşluğu':<22}{'stage_gap':<20}"
        f"{tower.stage_gap:>9.3f} m",
        f"{'siklon yüksekliği':<22}{'cyclone.total_height':<20}"
        f"{cyc.total_height:>9.3f} m",
        f"{'kule yüksekliği':<22}{'tower_height':<20}"
        f"{tower.tower_height:>9.3f} m",
        "",
        f"{'riser çapı':<22}{'riser_diameter':<20}"
        f"{tower.riser_diameter:>9.3f} m",
        f"{'meal hattı çapı':<22}{'meal_line_diameter':<20}"
        f"{tower.meal_line_diameter:>9.3f} m",
        "",
        f"{'komşu offset':<22}{'chord_between_stages':<20}"
        f"{tower.chord_between_stages:>9.3f} m",
        f"{'kolon yarıçapı':<22}{'column_radius':<20}"
        f"{tower.column_radius:>9.3f} m",
        "",
        "pitch = cyclone.total_height + stage_gap",
        "",
        "Kademeler artık tek eksende durmuyor: meal hattını",
        "alttaki siklondan uzak tutan şey stage_gap değil,",
        f"{tower.chord_between_stages:.3f} m'lik plan offseti. "
        f"{len(CLEARANCES)} açıklık",
        "kontrolü PH-CAD-03 planındadır.",
    ]


def _connection_table(tower):

    lines = [f"{'AD':<17}{'TİP':<8}{'bore':>7}{'z başı':>9}{'z sonu':>9}"]

    for name, kind, path, diameter in tower.connections():
        lines.append(
            f"{name:<17}{kind:<8}{diameter:>7.3f}"
            f"{path[0][2]:>9.2f}{path[-1][2]:>9.2f}"
        )

    return lines


def _joins(tower, path, stage):
    """Does this duct actually connect to that cyclone?

    Read off the geometry rather than from a list: a duct joins a
    cyclone when one of its ENDS is in it. Every real joint in this
    tower is an end -- a riser leaves an outlet and enters a mouth, a
    meal line leaves a dipleg -- so nothing else should touch, and
    anything else that does is the defect being looked for.
    """

    envelope = tower.stage_envelope(stage)
    base = tower.stage_base_z(stage)
    top = base + tower.cyclone.total_height

    return any(
        plan.point_in_polygon((end[0], end[1]), envelope)
        and base - 1.0e-9 <= end[2] <= top + 1.0e-9
        for end in (path[0], path[-1])
    )


def elevation_clearance(tower, sight_deg):
    """The worst gap ON PAPER between a duct and a cyclone it does not join.

    This is the question the sheet is actually asked -- "does a pipe
    run through a vessel?" -- measured rather than argued. Negative
    means some duct is drawn over a cyclone it has no business
    touching; positive means the view shows every duct outside every
    vessel it does not enter.

    It measures the DRAWING, not the tower. The tower's own clearances
    are `TowerSpec`'s nine checks and they hold whatever this returns;
    what this adds is whether one flat view can be trusted to show
    them, which depends entirely on where the stages face.
    """

    project, _depth, paper_bearing = looking(sight_deg)
    cyc = tower.cyclone

    silhouettes = [
        (
            placement.stage,
            cyclone_elevation_outlines(
                cyc, placement.z,
                project([(placement.x, placement.y, 0.0)])[0][0],
                (paper_bearing - placement.azimuth_deg,
                 paper_bearing - placement.azimuth_deg + 180.0),
            ),
        )
        for placement in tower.placements()
    ]

    worst = math.inf

    for _name, _kind, path, bore in tower.connections():

        drawn = project(path)

        for stage, polygons in silhouettes:

            if _joins(tower, path, stage):
                continue

            gap = min(
                plan.polygon_polyline_distance(polygon, drawn)
                for polygon in polygons
            ) - 0.5 * bore

            worst = min(worst, gap)

    return worst


@lru_cache(maxsize=8)
def best_elevation_bearing(tower, coarse=180, fine=40):
    """Where to stand so the elevation shows the ducts outside the vessels.

    Returns (bearing_deg, clearance) -- the line of sight, and the
    worst gap `elevation_clearance` measures from it. A POSITIVE
    clearance means no duct is drawn over a cyclone it does not enter.

    WHETHER A GOOD VIEW EXISTS IS A PROPERTY OF THE LAYOUT, and it is
    what most separates the two candidate patterns. The zigzag puts
    every riser column on ONE line, so one view sees all five clear.
    The fan turns each stage 27 deg further round a circle, so the
    columns face 108 deg apart and no view can; the sweep finds the
    least bad one and the sheet's notes say what it could not do.
    That is not a drafting problem with a drafting answer -- it is the
    fan's elevation telling the truth about the fan.

    Swept coarsely and then refined, because the measure is a minimum
    over every duct and every cyclone and is not smooth. The sweep is
    a few hundred evaluations, so it is cached on the spec -- which is
    frozen, so the cache cannot go stale.
    """

    def search(centre, half, steps):
        best = max(
            (centre - half + 2.0 * half * i / steps for i in range(steps + 1)),
            key=lambda b: elevation_clearance(tower, b),
        )
        return best

    bearing = search(180.0, 180.0, coarse)
    bearing = search(bearing, 360.0 / coarse, fine)

    return bearing % 360.0, elevation_clearance(tower, bearing)


def _elevation_notes(tower):

    bearing, gap = best_elevation_bearing(tower)

    if gap >= 0.0:
        seen = [
            f"3  KAĞIT ÜZERİNDE HİÇBİR BORU HİÇBİR SİKLONUN",
            "   ÜSTÜNDEN GEÇMEZ. Bakış yönü seçilmedi, tarandı:",
            f"   {bearing:.1f}°'de girmediği gövdeye en yakın kanal bile",
            f"   {gap:.3f} m açıkta kalıyor. Bu yerleşimde bütün riser",
            "   kolonları tek doğrultuda olduğu için böyle bir",
            "   yön var.",
        ]
    else:
        seen = [
            "3  BU GÖRÜNÜŞ ONU GÖSTEREMEZ. Kademeler bir daire",
            "   üzerinde yelpaze gibi açıldığı için riser kolonları",
            f"   108° farklı yöne bakar. 360° tarandı: en iyi yön",
            f"   {bearing:.1f}° ve orada bile bir kanal, girmediği bir",
            f"   gövdenin {-gap:.3f} m üstüne düşüyor. Kağıttaki örtüşme",
            "   bir çakışma değil, izdüşümdür — gerçek açıklıklar",
            "   PH-CAD-03'te ve KESİT D-D'dedir.",
        ]

    return [
        "1  Beş kademe TEK EKSENDE DEĞİLDİR. Her biri kendi",
        f"   plan konumunda ({tower.chord_between_stages:.3f} m komşu offset) ve kendi",
        "   azimutunda durur. Gerçek yerleşim: PH-CAD-03.",
        "2  RISER KOLONU SİKLONUN İÇİNDEN GEÇMEZ, YANINDAN",
        f"   GEÇER: kolon kendi siklonunun ekseninden riser_reach",
        f"   = {tower.riser_reach:.3f} m açıkta durur ve gövdeye en dar yerde",
        f"   riser_column_clearance = {tower.riser_column_clearance():.3f} m kalır.",
        "   Ölçüsü KESİT D-D'de (bu sayfa) ve PH-CAD-04 DETAY",
        "   C-C'dedir; yalnızca orada gerçektir.",
    ] + seen + [
        "4  A-A'da ÖNDEN GEÇEN kanal gövdeyi ÖRTER (gövde",
        "   çizgisi kanalın kenarında kesilir), ARKADAN geçen",
        "   kanal kesikli çizgiyle gösterilir.",
        "5  İki volüt bandının kademeden kademeye farklılaşması",
        "   dönmenin kendisidir: kesit azimutları (-α, 180-α).",
        "6  Meal, siklon n'den siklon n+1'e DEĞİL, onu besleyen",
        "   riser n+1 kanalına verilir: ısı değişimi kanalda olur.",
        "7  Meal hattı iki bacak: alttaki siklonun yanından",
        "   düşey iniş, sonra tek eğimli oluk. Eğim bu",
        "   görünüşte gerçek değildir; gerçek boy PH-CAD-04.",
        "8  riser_5 bir bağlantı borusudur; ILC gövdesi henüz",
        "   modellenmemiştir, yalnızca zarfı ayrılmıştır.",
        "9  Kanal kalınlıkları gerçek çaplandır; dirseklerdeki",
        "   yuvarlak birleşim geometry/pipes.py'nin küre",
        "   dirseğiyle aynıdır.",
    ]


# ==========================================================
# SHEET 3 -- THE TOWER IN PLAN
# ==========================================================
def draw_cyclone_plan(panel, cyc, placement, label=None, fill=drafting.FILL):
    """One cyclone seen from above, standing and facing where it stands.

    The scroll is the spec's own plan envelope carried through the
    placement, so a cyclone drawn here is turned exactly as far as the
    solid will be turned and as far as the clearance checks assumed.
    """

    centre = (placement.x, placement.y)

    panel.circle(centre, cyc.D_body, style="visible", fill=fill)
    panel.polyline(
        [placement.to_world_xy(p) for p in volute_spiral(cyc)],
        style="outline",
    )
    panel.circle(centre, cyc.vortex_finder_diameter, style="hidden")
    panel.circle(centre, cyc.dipleg_diameter, style="hidden")

    reach = 0.75 * cyc.D_body

    for local in (((-reach, 0.0), (reach, 0.0)), ((0.0, -reach), (0.0, reach))):
        panel.centre_line([placement.to_world_xy(p) for p in local])

    if label:
        panel.label(
            centre[0], centre[1], label, size=drafting.TEXT_LABEL,
            ha="center", va="center", fontweight="bold",
        )


def sheet_tower_plan(tower=None):
    """PH-CAD-03: where things stand in plan, which the elevation hides.

    This is the sheet the offset was made for. Five bodies at five
    places, each turned its own way, the riser columns between them
    and the calciner's reserved circle on the axis they all stand
    around.
    """

    tower = tower or TowerSpec()
    cyc = tower.cyclone

    sheet = Sheet(
        model=tower,
        title="KULE \u2014 PLAN  (x\u2013y)",
        subtitle=(
            f"{tower.layout_pattern}, "
            f"{tower.stage_azimuth_step_deg:.0f}\u00b0 azimut ad\u0131m\u0131, "
            f"{tower.chord_between_stages:.3f} m kom\u015fu offset"
        ),
        unit="PREHEATER / tower",
        number="PH-CAD-03",
        source_note=SOURCE_NOTE,
        size="A2",
        datum=DATUM_NOTE,
    )

    reach = tower.column_radius + cyc.volute_outer_radius + 4.0

    panel = sheet.panel((26.0, 70.0, 300.0, 320.0), "PLAN")
    panel.fit((-reach, reach), (-reach, reach))

    # ---- the axis everything stands around ----
    panel.circle((0.0, 0.0), 2.0 * tower.calciner.reserved_radius,
                 style="hidden", fill="#f4e6e0")
    panel.circle((0.0, 0.0), 2.0 * tower.column_radius, style="construction")
    panel.centre_line([(-0.35 * reach, 0.0), (0.35 * reach, 0.0)])
    panel.centre_line([(0.0, -0.35 * reach), (0.0, 0.35 * reach)])

    # ---- the ducts, under the bodies so the vessels read on top ----
    draw_ducts(panel, tower, xy, alpha=0.22)

    for placement in tower.placements():

        draw_cyclone_plan(panel, cyc, placement, label=str(placement.stage))

        axis = tower.riser_axis(placement.stage)
        panel.circle(axis, tower.riser_diameter, style="visible")
        panel.label(
            axis[0], axis[1], f"R{placement.stage}",
            size=drafting.TEXT_DIM, ha="center", va="center",
            colour=drafting.GAS_INK,
        )

    # ---- the numbers that place the layout ----
    first = tower.placement(1)
    second = tower.placement(2)

    panel.dim_h(0.0, first.x, 1.6, "column_radius", above=True,
                extend_to=0.8)

    panel.polyline([(0.0, 0.0), (first.x, first.y)], style="construction",
                   zorder=drafting.Z_DIM)
    panel.polyline([(0.0, 0.0), (second.x, second.y)], style="construction",
                   zorder=drafting.Z_DIM)
    panel.dim_angle(
        (0.0, 0.0),
        0.55 * tower.column_radius,
        tower.stage_compass_deg(1),
        tower.stage_compass_deg(2),
        "stage_azimuth_step_deg",
    )

    panel.dim_h(
        -tower.calciner.reserved_radius, tower.calciner.reserved_radius,
        -1.4, "calciner.D_body", above=False, extend_to=-0.8,
    )

    for stage in (2, 4):

        placement = tower.placement(stage)

        panel.dim_h(
            0.0, placement.x, placement.y + 0.9 * cyc.D_body,
            f"placement({stage}).x", above=True, oriented=True,
        )
        panel.dim_v(
            placement.x + 0.9 * cyc.D_body, 0.0, placement.y,
            f"placement({stage}).y", right=True, oriented=True,
        )

    panel.leader(
        (tower.calciner.reserved_radius, 0.0), (2.6, -2.2),
        "ILC i\u00e7in ayr\u0131lm\u0131\u015f zarf (vessel modellenmedi)",
    )

    top = sheet.text_block(
        (338.0, 390.0, 236.0, None),
        "MERKEZ KOORD\u0130NATLARI ve KOM\u015eU OFFSETLER\u0130",
        _placement_table(tower),
    ) - 8.0

    top = sheet.text_block(
        (338.0, top, 236.0, None),
        f"A\u00c7IKLIKLAR  \u2014  {len(CLEARANCES)} k\u0131s\u0131t",
        _clearance_table(tower),
    ) - 8.0

    sheet.text_block(
        (338.0, top, 236.0, None),
        "NOTLAR",
        _plan_notes(tower),
    )

    sheet.text_block(
        (26.0, 60.0, 300.0, None),
        "PLAN ZARFI",
        _plan_envelope(tower, cyc),
    )

    return sheet


def _placement_table(tower):

    lines = [
        f"{'kademe':<7}{'X':>9}{'Y':>9}{'azimut':>8}"
        f"{'dX':>8}{'dY':>8}{'offset':>8}"
    ]

    previous = None

    for placement in tower.placements():

        if previous is None:
            step = " " * 24
        else:
            step = (
                f"{placement.x - previous.x:>8.3f}"
                f"{placement.y - previous.y:>8.3f}"
                f"{math.hypot(placement.x - previous.x, placement.y - previous.y):>8.3f}"
            )

        lines.append(
            f"{placement.stage:<7}{placement.x:>9.3f}{placement.y:>9.3f}"
            f"{placement.azimuth_deg:>8.1f}{step}"
        )

        previous = placement

    lines += [
        "",
        f"{'kolon yarıçapı':<24}{'column_radius':<20}"
        f"{tower.column_radius:>8.3f} m",
        f"{'komşu offset':<24}{'chord_between_stages':<20}"
        f"{tower.chord_between_stages:>8.3f} m",
        f"{'riser kolonu erişimi':<24}{'riser_reach':<20}"
        f"{tower.riser_reach:>8.3f} m",
        f"{'ILC zarf yarıçapı':<24}{'calciner.reserved_radius':<20}"
        f"{tower.calciner.reserved_radius:>8.3f} m",
    ]

    second = [
        math.dist(
            (tower.placement(s).x, tower.placement(s).y),
            (tower.placement(s + 2).x, tower.placement(s + 2).y),
        )
        for s in range(1, tower.stage_count - 1)
    ]

    lines.append(
        f"{'ikinci komşu (n/n+2)':<24}{'':<20}{min(second):>8.3f} m"
    )

    return lines


# The sheets name the checks in Turkish; the spec names them in
# English, because that is the language its docstrings are in. The
# NUMBERS and the order come from `tower_spec.CLEARANCES` either way,
# so a tenth check appears on the sheet whether or not anyone has
# written a Turkish name for it yet.
CLEARANCE_NAMES = {
    1: "dipleg düşeyi / alt gövde",
    2: "meal oluğu / alt gövde",
    3: "riser kolonu / kendi gövdesi",
    4: "siklon / ILC zarfı",
    5: "riser kolonu / ILC zarfı",
    6: "dipleg düşeyi / gaz dirseği",
    7: "oluk başlangıcı / gaz dirseği",
    8: "dipleg düşeyi / alttaki ağız bacağı",
    9: "komşu kademeler arası geçiş",
}


def clearance_name(check):
    """A check's short name for the sheets, or its own if none yet."""

    return CLEARANCE_NAMES.get(check.number, check.label)


def _clearance_table(tower):

    lines = [f"{'kısıt':<38}{'en dar':>9}{'gerekli':>10}{'pay':>8}"]

    for check, have, need in tower.clearances():
        lines.append(
            f"{check.number} {clearance_name(check):<36}"
            f"{have:>9.3f}{need:>10.3f}{have - need:>8.3f}"
        )

    lines += [
        "",
        f"Sayısal açıklık {tower.mesh_clearance_m:.3f} m. Bu paket akış",
        "hacmini modeller; flanş, cıvata ve montaj erişimi kapsam dışı.",
        "Baraj sıfır artı boolean'ı ve yüzey ağını teğetlikten",
        "uzak tutacak kadardır.",
        "",
        "Her kısıt kendi barajını geçmek zorunda; geçmezse",
        "TowerSpec yerleşimi reddeder (clamp yok).",
    ]

    return lines


def _plan_notes(tower):

    return [
        f"1  Be\u015f kademe {tower.column_radius:.3f} m yar\u0131\u00e7apl\u0131 bir daire",
        "   \u00fczerinde durur; merkez ILC i\u00e7in ayr\u0131lm\u0131\u015ft\u0131r.",
        f"2  Her siklon, \u00fcst\u00fcndeki kademe kendi \u00e7er\u00e7evesinde",
        f"   {tower.meal_side_azimuth_deg:.0f}\u00b0'de kalacak \u015fekilde d\u00f6nd\u00fcr\u00fclm\u00fc\u015ft\u00fcr \u2014 volüt",
        "   sar\u0131m\u0131n\u0131n kapand\u0131\u011f\u0131 dar yan. A\u011f\u0131z taraf\u0131 1.669 m",
        "   daha geni\u015f olurdu.",
        "3  Meal hatt\u0131 iki bacak: alttaki siklonun YANINDAN",
        "   d\u00fc\u015fey ini\u015f, sonra tek e\u011fimli oluk.",
        "4  Kanal g\u00fczergahlar\u0131 art\u0131k \u00fcst \u00fcste d\u00fc\u015fm\u00fcyor;",
        "   her kademenin kendi izi var.",
        "5  Kot hi\u00e7 de\u011fi\u015fmedi: kule 112.369 m.",
    ]


def _plan_envelope(tower, cyc):
    """The ground the tower takes up, read off the placements."""

    xs = []
    ys = []

    for stage in range(1, tower.stage_count + 1):

        for x, y in tower.stage_envelope(stage, sections=72):
            xs.append(x)
            ys.append(y)

        axis = tower.riser_axis(stage)
        xs += [axis[0] - 0.5 * tower.riser_diameter,
               axis[0] + 0.5 * tower.riser_diameter]
        ys += [axis[1] - 0.5 * tower.riser_diameter,
               axis[1] + 0.5 * tower.riser_diameter]

    return [
        f"x  {min(xs):+8.3f} .. {max(xs):+8.3f} m      "
        f"toplam {max(xs) - min(xs):7.3f} m",
        f"y  {min(ys):+8.3f} .. {max(ys):+8.3f} m      "
        f"toplam {max(ys) - min(ys):7.3f} m",
        f"kuleyi \u00e7evreleyen daire yar\u0131\u00e7ap\u0131 "
        f"{max(math.hypot(x, y) for x, y in zip(xs, ys)):.3f} m",
        "",
        "Zarf, be\u015f kademenin plan zarflar\u0131 ile riser kolonlar\u0131n\u0131n d\u0131\u015f "
        "y\u00fcz\u00fcnden okunur; ILC i\u00e7in ayr\u0131lan daire merkezdedir.",
    ]


# ==========================================================
# SHEET 4 -- ONE STAGE, IN DETAIL
# ==========================================================
def sheet_stage_detail(tower=None, stage=2):
    """PH-CAD-04: the meal line and the gas elbow that share one axis.

    This is the sheet the collision check produced. Two orthographic
    views show WHERE the three legs go, and a developed view shows the
    one thing neither of them can: that the inclined leg really is laid
    at `meal_entry_angle_deg`, which is derived, not set.
    """

    tower = tower or TowerSpec()
    cyc = tower.cyclone

    sheet = Sheet(
        model=tower,
        title=f"KADEME DETAYI — {stage} → {stage + 1}",
        subtitle="Meal hattının iki bacağı, gaz dirseği ve kademenin kendi çerçevesi",
        unit="PREHEATER / tower",
        number="PH-CAD-04",
        source_note=SOURCE_NOTE,
        size="A3",
        datum=DATUM_NOTE,
    )

    meal = tower.meal_line_path(stage)
    here = tower.placement(stage)
    below = tower.placement(stage + 1)

    z_top = tower.stage_base_z(stage) + 2.5
    z_bot = tower.stage_base_z(stage + 1) + cyc.total_height - 4.0

    names = {
        f"meal_line_{stage}", f"riser_{stage + 1}", f"riser_{stage}",
    }

    # ---- x-z ----
    span = 0.5 * (abs(here.x - below.x) + 16.0)
    middle = 0.5 * (here.x + below.x)

    front = sheet.panel((26.0, 112.0, 120.0, 166.0),
                        "DETAY A-A  (x\u2013z)")
    front.fit((middle - span, middle + span), (z_bot, z_top))

    def front_horizontal(placement):
        return placement.x

    def front_azimuths(placement):
        return (-placement.azimuth_deg, 180.0 - placement.azimuth_deg)

    for placement in (here, below):
        draw_cyclone_elevation(
            front, cyc, base_z=placement.z,
            horizontal=front_horizontal(placement),
            azimuths=front_azimuths(placement),
        )

    draw_ducts(
        front, tower, xz, names=names, alpha=0.30, depth=depth_xz,
        occluders=stage_occluders(
            tower, front_horizontal, front_azimuths, depth_xz,
            stages={stage, stage + 1},
        ),
    )

    front.level(
        here.x - 3.2, meal[0][2], f"stage_base_z({stage})",
        x_text=middle - span + 1.0,
    )
    front.level(
        meal[1][0] + 0.6, meal[1][2],
        f"meal_line_path({stage})[1][2]", x_text=middle + span - 3.0,
    )
    front.level(
        below.x, tower.outlet_point(stage + 1)[2],
        f"outlet_point({stage + 1})[2]", x_text=middle - span + 1.0,
    )

    # ---- y-z ----
    span = 0.5 * (abs(here.y - below.y) + 16.0)
    middle = 0.5 * (here.y + below.y)

    side = sheet.panel((156.0, 112.0, 120.0, 166.0),
                       "DETAY B-B  (y\u2013z)")
    side.fit((middle - span, middle + span), (z_bot, z_top))

    def side_horizontal(placement):
        return placement.y

    def side_azimuths(placement):
        return (90.0 - placement.azimuth_deg, 270.0 - placement.azimuth_deg)

    for placement in (here, below):
        draw_cyclone_elevation(
            side, cyc, base_z=placement.z,
            horizontal=side_horizontal(placement),
            azimuths=side_azimuths(placement),
        )

    draw_ducts(
        side, tower, yz, names=names, alpha=0.30, depth=depth_yz,
        occluders=stage_occluders(
            tower, side_horizontal, side_azimuths, depth_yz,
            stages={stage, stage + 1},
        ),
    )

    side.level(
        tower.riser_axis(stage + 1)[1], meal[-1][2],
        f"meal_line_path({stage})[-1][2]", x_text=middle + span - 3.0,
    )

    # The top of the riser's vertical run -- the upper end of the band
    # the meal line is required to land in. Its lower end is a stage
    # further down and outside this window.
    z_high = tower.riser_vertical_span(stage + 1)[1]
    axis_y = tower.riser_axis(stage + 1)[1]

    side.polyline(
        [(axis_y - 2.4, z_high), (axis_y + 2.4, z_high)],
        style="construction", zorder=drafting.Z_DIM,
    )
    side.label(
        axis_y + 2.6, z_high + 0.7,
        "riser d\u00fc\u015fey ko\u015fusunun \u00fcst ucu",
        size=drafting.TEXT_DIM, colour=drafting.GAS_INK, ha="left",
    )

    # ---- true length ----
    true = sheet.panel((286.0, 112.0, 120.0, 166.0),
                       "MEAL HATTI \u2014 GER\u00c7EK BOY")
    # Pinned to the orthographic views' scale: the whole point of this
    # panel is that it is the same line, so it has to be the same size.
    true.fit((-2.5, 11.5), (z_bot, z_top), scale=front.scale)

    points = developed(meal)

    true.duct(points, tower.meal_line_diameter, "solids")

    true.polyline(
        [points[1], (points[1][0] + 4.6, points[1][1])],
        style="construction", zorder=drafting.Z_DIM,
    )
    true.dim_angle(
        points[1], 2.6, -tower.meal_entry_angle_deg(1), 0.0,
        "meal_entry_angle_deg(1)",
    )

    true.level(points[0][0], points[0][1], f"stage_base_z({stage})",
               x_text=-2.0)
    true.level(points[1][0], points[1][1],
               f"meal_line_path({stage})[1][2]", x_text=-2.0)
    true.level(points[-1][0], points[-1][1],
               f"meal_line_path({stage})[-1][2]", x_text=points[-1][0] + 1.0)

    true.label(
        points[0][0] - 0.5, 0.5 * (points[0][1] + points[1][1]),
        "1  d\u00fc\u015fey bacak", size=drafting.TEXT_DIM, ha="right",
        colour=drafting.SOLIDS_INK,
    )
    true.label(
        0.5 * (points[1][0] + points[2][0]) + 1.2,
        0.5 * (points[1][1] + points[2][1]),
        "2  e\u011fimli oluk", size=drafting.TEXT_DIM,
        colour=drafting.SOLIDS_INK,
    )

    # ---- the stage's own frame, the only view where the cyclone's
    #      own dimensions are true ----
    local = sheet.panel((26.0, 14.0, 120.0, 88.0),
                        "DETAY C-C \u2014 kademe lokal plan\u0131")
    local.fit((-8.0, 8.0), (-8.0, 8.0))

    local.circle((0.0, 0.0), cyc.D_body, style="visible",
                 fill=drafting.FILL)
    local.polyline(volute_spiral(cyc), style="outline")
    local.circle((0.0, 0.0), cyc.vortex_finder_diameter, style="hidden")
    local.circle(tower.riser_offset_local, tower.riser_diameter,
                 style="visible")
    local.centre_line([(-6.0, 0.0), (6.0, 0.0)])
    local.centre_line([(0.0, -6.0), (0.0, 6.0)])

    local.dim_h(0.0, tower.mouth_x, 5.6, "mouth_x", above=True,
                extend_to=5.0)
    local.dim_v(6.6, 0.0, tower.riser_approach_y, "riser_approach_y",
                right=True, oriented=True)

    # THE OFFSET THE ELEVATIONS CANNOT SHOW. No orthographic view of
    # this tower separates all five risers from their own bodies -- the
    # best view axis leaves 3.880 m where 4.056 m is needed -- so this
    # is the panel where the riser column is seen standing BESIDE the
    # cyclone, and the only one where the distance may be quoted.
    local.dim_aligned(
        (0.0, 0.0), tower.riser_offset_local, 0.0, "riser_reach",
        extend=False,
    )

    gap = tower.riser_column_clearance()
    flank = tower.riser_local_envelope_radius
    unit = (tower.mouth_x / tower.riser_reach,
            tower.riser_approach_y / tower.riser_reach)

    local.dim_aligned(
        (flank * unit[0], flank * unit[1]),
        ((flank + gap) * unit[0], (flank + gap) * unit[1]),
        -1.4, "riser_column_clearance()", extend=True,
    )

    local.polyline(
        [(0.0, 0.0),
         (7.0 * math.cos(math.radians(tower.meal_side_azimuth_deg)),
          7.0 * math.sin(math.radians(tower.meal_side_azimuth_deg)))],
        style="construction", zorder=drafting.Z_DIM,
    )
    local.dim_angle(
        (0.0, 0.0), 5.2, 0.0, tower.meal_side_azimuth_deg,
        "meal_side_azimuth_deg",
    )
    local.label(
        7.2 * math.cos(math.radians(tower.meal_side_azimuth_deg)),
        7.2 * math.sin(math.radians(tower.meal_side_azimuth_deg)),
        "\u00fcstteki kademe", size=drafting.TEXT_DIM, ha="center",
    )

    sheet.text_block(
        (156.0, 102.0, 250.0, None),
        "MEAL HATTI — NEDEN İKİ BACAK",
        _detail_notes(tower, stage) + [""] + _clearance_notes(tower, stage),
        size=5.6, leading=3.4,
    )

    return sheet


def _detail_notes(tower, stage):

    return [
        "1  Meal hattı önce YANA açılır, sonra riser'a döner. Doğrudan gitse "
        "yolu neredeyse",
        f"   dikey olurdu: dipleg ile riser kolonu arasında yalnızca "
        f"{tower.chord_between_stages:.3f} m'lik kord var.",
        f"2  Yana açılma {tower.meal_reach_ratio * tower.D:.3f} m "
        "(1.00 x D_body). Radyal dışarı değil YANA, çünkü",
        "   radyal dışarı yaklaşma doğrultusunun tersidir; hat kendi üstünden "
        "geri dönerdi.",
        f"3  Oluk {tower.meal_entry_angle_deg(1):.0f}° ile iner (türetilmiş, "
        f"riser eksenine {tower.meal_riser_angle_deg(1):.0f}°); şev açısı "
        f"{repose_angle_deg():.0f}°'dir, altında kalan bir oluk akmaz tıkanır.",
        "4  Giriş noktası riser'ın DÜŞEY koşusuna düşmek zorundadır; tower_spec._validate "
        "bunu her kademe için reddeder.",
        "5  Açı yalnızca GERÇEK BOY görünüşünde ölçülebilir: hat planda döndüğü için A-A ve "
        "B-B'de eğim göründüğü gibi değildir.",
        "6  C-C, kademenin KENDİ çerçevesidir: mouth_x, riser_approach_y ve "
        "meal_side_azimuth_deg yalnızca orada gerçektir.",
    ]


def _clearance_notes(tower, stage):
    """The checks THIS stage pair is measured by, at their own values.

    Every check that is about a stage and the one below it, walked
    from `CLEARANCES` rather than listed here -- the list used to name
    four of them and that is the habit check 8 hid in.
    """

    lines = [f"{'kısıt':<38}{'ölçülen':>9}{'gerekli':>10}"]

    for check in CLEARANCES:

        if not check.about_pairs:
            continue

        lines.append(
            f"{check.number} {clearance_name(check):<36}"
            f"{getattr(tower, check.key)(stage):>9.3f}"
            f"{tower.mesh_clearance_m:>10.3f}"
        )

    lines.append(
        "Kademeler tek eksende dururken 1 ve 6 sağlanamazdı: her dipleg "
        "alttaki siklonun gaz çıkışının tam üstüne boşalıyordu. 8, ağız "
        "bacağının içinden geçen diplegi yakalar: meal hattı riser'ını "
        "iki kez kesiyordu."
    )

    return lines


# ==========================================================
# SHEET 5 -- THE TWO PATTERNS, SIDE BY SIDE
# ==========================================================
def draw_pattern_plan(panel, tower, label):
    """One candidate layout, small, with nothing on it but the shapes."""

    cyc = tower.cyclone

    panel.circle((0.0, 0.0), 2.0 * tower.calciner.reserved_radius,
                 style="hidden", fill="#f4e6e0")
    panel.circle((0.0, 0.0), 2.0 * tower.column_radius, style="construction")

    draw_ducts(panel, tower, xy, alpha=0.20)

    for placement in tower.placements():

        draw_cyclone_plan(panel, cyc, placement, label=str(placement.stage))

        panel.circle(
            tower.riser_axis(placement.stage), tower.riser_diameter,
            style="outline",
        )


def sheet_pattern_comparison(tower=None):
    """PH-CAD-05: fan against zigzag, on the same page.

    Both are laid out from the SAME four parameters and both satisfy
    the same nine clearances -- so everything about a neighbouring
    pair comes out identical, and what differs is what the pattern
    does with the SECOND neighbour. That is the comparison, and it is
    why the two are drawn at the same scale on one sheet rather than
    argued about in prose.

    This sheet decides nothing. It is the evidence the decision is
    made on.
    """

    tower = tower or TowerSpec()

    towers = [
        (name, replace(tower, layout_pattern=name))
        for name in LAYOUT_PATTERNS
    ]

    sheet = Sheet(
        model=tower,
        title="YERLEŞİM KARŞILAŞTIRMASI",
        subtitle=(
            f"aynı {len(CLEARANCES)} kısıt, aynı "
            f"{tower.chord_between_stages:.3f} m komşu offset, iki kalıp"
        ),
        unit="PREHEATER / tower",
        number="PH-CAD-05",
        source_note=SOURCE_NOTE,
        size="A2",
        datum=DATUM_NOTE,
    )

    reach = tower.column_radius + tower.cyclone.volute_outer_radius + 3.0

    for index, (name, candidate) in enumerate(towers):

        panel = sheet.panel(
            (26.0 + index * 190.0, 190.0, 180.0, 190.0),
            f"PLAN — {name.upper()}",
        )
        panel.fit((-reach, reach), (-reach, reach))

        draw_pattern_plan(panel, candidate, name)

        # The one dimension both panels can carry: the column radius
        # is the same in either pattern, so it is quotable against the
        # sheet's single model. Everything else that differs between
        # them is in the table, where it can be read side by side.
        panel.dim_h(
            0.0, candidate.column_radius, -reach + 1.6, "column_radius",
            above=True, extend_to=-reach + 1.0,
        )

    sheet.text_block(
        (26.0, 170.0, 370.0, None),
        "ÖLÇÜTLER",
        _comparison_table(towers),
    )

    sheet.text_block(
        (412.0, 390.0, 162.0, None),
        "NEDEN AYNI",
        [
            "İki kalıp da aynı kolon yarıçapında, aynı",
            "azimut adımında ve aynı meal-side",
            "açısındadır. Bu yüzden KOMŞU iki kademe",
            "arasındaki her şey — meal geometrisi,",
            f"dipleg geçişi, teğetsel giriş, {len(CLEARANCES)} açıklık",
            "— birebir aynı çıkar.",
        ],
    )

    sheet.text_block(
        (412.0, 300.0, 162.0, None),
        "NEDEN FARKLI",
        [
            "Fark ikinci komşudadır: zikzakta kademe",
            "1-3-5 ve 2-4 planda tam üst üste durur.",
            "Yelpazede her kademenin kendi yeri vardır.",
            "",
            "Bunun bedeli gaz yoludur: zikzak riser'ları",
            "kısa tutar, yelpaze zarfı daha dairesel",
            "yapar.",
            "",
            "Bu sayfa seçim yapmaz; seçimin dayanağıdır.",
        ],
    )

    return sheet


def _comparison_table(towers):

    def rows(tower):

        placements = tower.placements()
        second = [
            math.dist(
                (placements[i].x, placements[i].y),
                (placements[i + 2].x, placements[i + 2].y),
            )
            for i in range(len(placements) - 2)
        ]

        risers = [
            sum(math.dist(a, b) for a, b in zip(path, path[1:]))
            for name, _, path, _ in tower.connections()
            if name.startswith("riser")
        ]

        xs = []
        ys = []

        for stage in range(1, tower.stage_count + 1):
            for x, y in tower.stage_envelope(stage, sections=72):
                xs.append(x)
                ys.append(y)
            axis = tower.riser_axis(stage)
            xs += [axis[0] - 0.5 * tower.riser_diameter,
                   axis[0] + 0.5 * tower.riser_diameter]
            ys += [axis[1] - 0.5 * tower.riser_diameter,
                   axis[1] + 0.5 * tower.riser_diameter]

        return {
            "komşu offset": f"{tower.chord_between_stages:.3f} m",
            "ikinci komşu (n/n+2)": f"{min(second):.3f} m",
            **{
                f"{check.number} {clearance_name(check)}": f"{have:.3f} m"
                for check, have, _need in tower.clearances()
            },
            "kanal-kanal girişimi": (
                "yok"
                if not tower.duct_interferences()
                else f"{len(tower.duct_interferences())} çift"
            ),
            "meal yana açılma":
                f"{tower.meal_reach_ratio * tower.D:.3f} m",
            "meal hattı (gerçek boy)": "{:.3f} m".format(
                sum(
                    math.dist(a, b)
                    for a, b in zip(
                        tower.meal_line_path(1), tower.meal_line_path(1)[1:]
                    )
                )
            ),
            "meal → riser açısı":
                f"{tower.meal_riser_angle_deg(1):.1f}°",
            "riser yolu (ortalama)":
                f"{sum(risers) / len(risers):.3f} m",
            "plan zarfı x": f"{max(xs) - min(xs):.3f} m",
            "plan zarfı y": f"{max(ys) - min(ys):.3f} m",
            "çevreleyen daire":
                f"{max(math.hypot(x, y) for x, y in zip(xs, ys)):.3f} m",
            "kule yüksekliği": f"{tower.tower_height:.3f} m",
        }

    tables = [(name, rows(candidate)) for name, candidate in towers]

    lines = [
        f"{'ölçüt':<34}" + "".join(f"{name.upper():>16}" for name, _ in tables)
    ]

    for key in tables[0][1]:
        lines.append(
            f"{key:<34}"
            + "".join(f"{table[key]:>16}" for _, table in tables)
        )

    return lines


# ==========================================================
# THE SET
# ==========================================================
def build_sheets(tower=None):
    """All four sheets, in drawing-set order."""

    tower = tower or TowerSpec()

    return [
        sheet_cyclone(tower.cyclone),
        sheet_tower_elevation(tower),
        sheet_tower_plan(tower),
        sheet_stage_detail(tower),
        sheet_pattern_comparison(tower),
    ]


def write_drawings(tower=None, output_dir=None):
    """The set, as one PDF and one PNG per sheet."""

    directory = Path(output_dir) if output_dir else OUTPUT_DIR
    sheets = build_sheets(tower)

    paths = [save_pdf(sheets, directory / "preheater_layout.pdf")]

    for sheet in sheets:
        paths.append(
            sheet.save(directory / f"{sheet.number.lower()}.png")
        )

    return sheets, paths


def main():

    sheets, paths = write_drawings()

    print("=" * 72)
    print("PREHEATER — 2-D LAYOUT DRAWINGS")
    print("=" * 72)
    print()

    for sheet in sheets:
        scales = ", ".join(
            f"{p.title} 1:{p.scale}" for p in sheet.panels
        )
        print(f"  {sheet.number}  {sheet.title}")
        print(f"            {sheet.size}    {scales}")

    print()
    print("EVERY NUMBER ON EVERY SHEET, AND WHERE IT WAS READ FROM")
    print()

    for sheet in sheets:
        print(sheet.quote_report())
        print()

    print("FILES")

    for path in paths:
        print(f"  {path}")

    print()
    print("  Geometry only. No solver, no physics, no twin module ran.")
    print()

    for sheet in sheets:
        sheet.close()


if __name__ == "__main__":
    main()
