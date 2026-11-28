"""The plant's geometry, derived from its one source.

geometry/plant_geometry.yaml holds every primary dimension once; this
module derives everything else from it -- volumes, wall areas, heights,
the throat, the gooseneck -- and nowhere else is any of it computed or
typed (single-source rule, user decision 13-14 Oct 2026). Pure
functions of the loaded file; SI units throughout.

    g = load()
    cyclone(g, "C4")["volume"]      # 283.24 m3, body + cone
    calciner(g)["vessel_volume"]    # 1009.71 m3, cone + cylinder
"""

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

SOURCE = Path(__file__).resolve().parent / "plant_geometry.yaml"

SOURCES = (
    "published",
    "derived_from_reference",
    "literature",
    "cfd_decision",
    "model",
    "schematic",
)

P_ATM = 101325.0           # Pa
R_GAS = 8.314462618        # J/(mol K)
MOLAR_MASS = {             # kg/mol
    "N2": 0.0280134,
    "O2": 0.0319988,
    "H2O": 0.01801528,
    "CO2": 0.0440095,
}

# Grid points per axis for the volume the gooseneck's two bends share
# (calciner.bas GnBendOverlap uses the same).
OVERLAP_N = 300


# ======================================================================
# Loading
# ======================================================================
@lru_cache(maxsize=None)
def _load(path):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load(path=SOURCE):
    """The source file, parsed (cached; do not mutate it)."""
    return _load(str(path))


def entries(node, prefix=""):
    """Every (dotted key, entry) in the source; an entry is a dict
    with 'value'."""
    if isinstance(node, dict) and "value" in node:
        yield prefix, node
        return
    if isinstance(node, dict):
        for key, child in node.items():
            yield from entries(child, f"{prefix}.{key}" if prefix else key)


def v(node):
    """An entry's value."""
    return node["value"]


# ======================================================================
# Cyclones
# ======================================================================
CYCLONE_DIMS = (
    "D_barrel", "H_barrel", "H_cone", "L_vortex", "D_dust",
    "W_inlet", "H_inlet",
)
CYCLONE_FLAGS = (
    "inlet_slope", "volute", "outlet_turn", "outlet_rise_over_Dx",
    "D_vortex_over_D_barrel",
)
# only where they apply: a bend's R and leg (outlet_turn 90 / 180), a
# riser under the inlet (C2-C5, user decision 17 Nov 2026)
CYCLONE_OPTIONAL = {"outlet_bend_R_over_Dx": 0.0, "outlet_run_over_Dx": 0.0, "inlet_riser": False,
                    "outlet_side": 1.0}


def cyclone_scale(g, name):
    """The factor C(name) is of its CFD domain: C5 = C4 x 6.50 / 6.30,
    the rest 1."""
    node = g["cyclones"][name]
    if "scaled_from" not in node:
        return 1.0
    base = g["cyclones"][node["scaled_from"]]
    return v(node["D_barrel_published"]) / v(base["D_barrel"])


def _cyclone_base(g, name):
    node = g["cyclones"][name]
    return node.get("same_as") or node.get("scaled_from") or name


def cyclone(g, name):
    """C(name)'s dimensions, resolved (C2, C3 = C4; C5 = C4 x scale),
    and what follows from them: the body + cone volume, the wetted
    area (barrel + roof ring outside the vortex finder + cone), the
    height (body + cone) and the CFD outlet pipe (rise, bend, run)."""

    node = g["cyclones"][name]
    base = g["cyclones"][_cyclone_base(g, name)]
    k = cyclone_scale(g, name)

    c = {key: k * v(base[key]) for key in CYCLONE_DIMS}
    c.update({key: v(base[key]) for key in CYCLONE_FLAGS})
    c.update({key: v(base[key]) if key in base else dflt for key, dflt in CYCLONE_OPTIONAL.items()})
    if c["outlet_side"] not in (1.0, -1.0) or (c["outlet_side"] < 0.0 and c["outlet_turn"] != 180.0):
        raise ValueError(f"{name}: outlet_side is +1 or -1, and -1 only on a 180 deg bend")
    if c["outlet_turn"] != 0.0 and "outlet_bend_R_over_Dx" not in base:
        raise ValueError(f"{name}: outlet_turn {c['outlet_turn']} needs outlet_bend_R_over_Dx and outlet_run_over_Dx")
    # the level inlet duct: per cyclone where given (C4's, scaled for C5), else the domain's
    c["inlet_duct_length"] = (k * v(base["inlet_duct_length"]) if "inlet_duct_length" in base
                              else v(g["cyclone_domain"]["inlet_duct_length"]))
    c["per_string"] = v(node["per_string"])
    c["boi_radius"] = v(node.get("boi_radius", base["boi_radius"]))
    c["scale"] = k
    # the vortex finder's bore, = the riser rising out of it (user
    # decision, 21 Nov 2026: D / D_x = D / D_riser = 2.0)
    c["D_vortex"] = c["D_vortex_over_D_barrel"] * c["D_barrel"]

    R, r, Dx = 0.5 * c["D_barrel"], 0.5 * c["D_dust"], c["D_vortex"]
    hb, hc = c["H_barrel"], c["H_cone"]
    slant = math.hypot(hc, R - r)

    c["height"] = hb + hc
    c["volume"] = math.pi * R * R * hb + math.pi * hc / 3.0 * (R * R + R * r + r * r)
    c["wet_area"] = (
        2.0 * math.pi * R * hb
        + math.pi * (R * R - 0.25 * Dx * Dx)
        + math.pi * (R + r) * slant
    )
    c["outlet_rise"] = c["outlet_rise_over_Dx"] * Dx
    c["outlet_bend_R"] = c["outlet_bend_R_over_Dx"] * Dx
    c["outlet_run"] = c["outlet_run_over_Dx"] * Dx
    return c


# ======================================================================
# Calciner and gooseneck
# ======================================================================
def throat_radius(g):
    """The throat, sized from a literature kiln-gas flow at a
    literature velocity (ideal gas at one atmosphere), as calciner.bas
    sizes it."""
    c = g["calciner"]
    x = {s: v(c[f"throat_gas_x_{s}"]) for s in MOLAR_MASS}
    m_mol = sum(x[s] * MOLAR_MASS[s] for s in MOLAR_MASS)
    rho = P_ATM * m_mol / (R_GAS * v(c["throat_gas_T"]))
    q = v(c["throat_gas_flow"]) / rho
    return math.sqrt(q / (math.pi * v(c["throat_velocity"])))


def calciner(g):
    """The vessel (cone + cylinder; the throat below it is the kiln
    inlet's side): its radii, heights, elevations (z from the throat's
    foot, as calciner.bas), volume and wall area. The wall is the
    cylinder, the cone frustum and the roof ring outside the
    gooseneck's neck."""

    c = g["calciner"]
    D, H = v(c["D"]), v(c["H"])
    R = 0.5 * D
    r = throat_radius(g)
    h_cone = (R - r) * math.tan(math.radians(v(c["cone_angle"])))
    h_cyl = H - h_cone
    z_throat_top = v(c["throat_length_over_D"]) * 2.0 * r
    r_neck = gooseneck_neck_radius(g)

    v_cone = math.pi * h_cone / 3.0 * (R * R + R * r + r * r)
    v_cyl = math.pi * R * R * h_cyl
    a_cyl = 2.0 * math.pi * R * h_cyl
    a_cone = math.pi * (R + r) * math.hypot(h_cone, R - r)
    a_roof = math.pi * (R * R - r_neck * r_neck)

    return {
        "D": D,
        "R": R,
        "H": H,
        "r_throat": r,
        "D_throat": 2.0 * r,
        "h_cone": h_cone,
        "h_cylinder": h_cyl,
        "z_throat_top": z_throat_top,
        "z_cone_top": z_throat_top + h_cone,
        "z_roof": z_throat_top + H,
        "v_throat": math.pi * r * r * z_throat_top,
        "vessel_volume": v_cone + v_cyl,
        "wall_cylinder": a_cyl,
        "wall_cone": a_cone,
        "wall_roof_ring": a_roof,
        "vessel_wall_area": a_cyl + a_cone + a_roof,
        "D_tertiary_air": v(c["D_tertiary_air"]),
        "D_feed": v(c["D_feed"]),
    }


def chord_integral(r, R, centre=0.0, n=400):
    """2 int sqrt(r^2 - (y - c)^2) sqrt(R^2 - y^2) dy over the disc of
    radius r centred at y = c: a pipe's section times the vessel's
    half chord, integrated across it. Elliptic; with y = c + r sin(phi)
    the integrand is smooth and Simpson's rule on n panels is exact to
    rounding (calciner.bas ChordIntegral, the same)."""
    h = math.pi / n
    total = 0.0
    for k in range(n + 1):
        phi = -0.5 * math.pi + k * h
        y = centre + r * math.sin(phi)
        f = 2.0 * r * r * math.cos(phi) ** 2 * math.sqrt(R * R - y * y)
        w = 1.0 if k in (0, n) else (4.0 if k % 2 else 2.0)
        total += w * f
    return total * h / 3.0


def calciner_pipe(R, r, slope_deg, z_wall, depth):
    """A round pipe through the vessel wall, rising away from it at
    slope_deg: its axis meets the wall at z_wall and runs depth on past
    it; it starts one pipe diameter inside the wall, so its start disc
    lies in the vessel and dissolves in the merge. The volume it adds
    outside the vessel (the part across the section that is odd in the
    section's "up" cancels, as for C1's chute), the hole's lowest
    point, the start's and the end face's centres (radial, z)."""
    c, s = math.cos(math.radians(slope_deg)), math.sin(math.radians(slope_deg))
    rho0 = R - 2.0 * r
    length = (R - rho0) / c + depth
    return {
        "D": 2.0 * r,
        "slope": slope_deg,
        "z_wall": z_wall,
        "start": (rho0, z_wall - (R - rho0) * s / c),
        "end": (R + depth * c, z_wall + depth * s),
        "length": length,
        "hole_bottom": z_wall - r / c - (R - math.sqrt(R * R - r * r)) * s / c,
        "volume": math.pi * r * r * length - (chord_integral(r, R) - rho0 * math.pi * r * r) / c,
        "end_area": math.pi * r * r,
    }


def calciner_inlets(g):
    """The calciner's side inlets, z from the throat's foot as
    calciner(): the tertiary air duct, tangential at the bottom of the
    cylinder, its axis along y on the -x side, coming in from -y (from
    the hood, parallel to the kiln, which runs to -y; user 24 Nov 2026 --
    it was along x on the -y side), a stub of it to its face past the
    vessel's tangent plane y = -R; the swirl as before (clockwise from
    above); the two meal pipes (+-x, from the strings) and the two fuel
    pipes (+-y) just above it, unchanged."""
    c, cal = g["calciner"], calciner(g)
    R = cal["R"]
    r = 0.5 * v(c["D_tertiary_air"])
    x_c = -(R - v(c["tertiary_air_wall_relief"]) - r)    # the axis, x (tangential)
    z_c = cal["z_cone_top"] + v(c["tertiary_air_cone_clearance"]) + r
    y_end = -(R + v(c["tertiary_air_stub_length"]))     # the face, y
    v_ta = math.pi * r * r * (-y_end) - chord_integral(r, R, x_c)

    # the meal: a vertical pipe into a dispersion box on the wall (user 28 Nov
    # 2026), its bottom feed_above_tertiary_air over the duct's top; the fuel
    # pipes' axes meet the wall at the box's mid height (coal and meal at one height)
    box = dispersion_box(g, R, v(c["D_feed"]), z_c + r + v(c["feed_above_tertiary_air"]))
    z_wall = box["z_centre"]
    depth = v(c["feed_depth"])
    meal = dict(box, slope=90.0, z_wall=z_wall, hole_bottom=box["z_bottom"],
                start=(box["rho_pipe"], box["z_top"]), length=box["pipe_rise"])
    return {
        "tertiary_air": {
            "D": 2.0 * r, "x": x_c, "z": z_c, "y_end": y_end, "offset": -x_c,
            "centre": (x_c, y_end, z_c), "direction": (0.0, 1.0, 0.0),
            "top": z_c + r, "volume": v_ta, "end_area": math.pi * r * r,
        },
        "meal": meal,
        "fuel": calciner_pipe(R, 0.5 * v(c["D_fuel"]), v(c["fuel_slope"]), z_wall, depth),
    }


def dispersion_box(g, wall_R, D, z_bottom):
    """The dispersion box on a vessel wall of radius wall_R (yaml
    dispersion_box), for a meal pipe of bore D: a wedge cut flat. Its section
    in the inlet's plane (rho radial out from the vessel axis, z): the open
    face is a flat window in the tangent plane rho = R, H high; the floor
    is level from the chord plane rho_in = sqrt(R^2 - (w/2)^2) (inside the
    wall's thickness, where the cylinder's curve is hidden) to the tangent
    plane, then a ramp at floor_slope_deg up to the back face at rho_out =
    R + depth, back_h under the top, which is level at z_top. Across the wall it
    is w wide, its sides planes: seen from outside, the box ends on the tangent
    plane in straight edges; the flat lead-in meets the cylinder in the sliver
    between the tangent plane and the wall, which the vessel's thickness hides.
    A vertical pipe of bore D stands on the top face at rho_pipe = rho_out -
    depth/2 (D clear of the wall), pipe_rise high; the meal enters at its top
    face (normal +z).

    Volumes outside the vessel, closed form: with S1 = the integral of
    sqrt(R^2 - y^2) over the width, the lead-in's H (w R - S1) plus the ramp
    part (back_h depth + tan depth^2 / 2) w, and the pipe's pi r^2 L."""
    b = g["dispersion_box"]
    w = v(b["width_over_D_feed"]) * D
    depth = v(b["depth_over_D_feed"]) * D
    back_h = v(b["back_height_over_D_feed"]) * D
    tan = math.tan(math.radians(v(b["floor_slope_deg"])))
    rise = v(b["pipe_rise"])
    h = 0.5 * w
    if h >= wall_R:
        raise ValueError(f"dispersion box width {w:.3f} m does not fit a vessel of radius {wall_R:.3f} m")
    rho_in = math.sqrt(wall_R * wall_R - h * h)
    rho_out = wall_R + depth
    H = back_h + depth * tan
    rho_p = rho_out - 0.5 * depth                              # the pipe's axis, over the box's outer half
    r = 0.5 * D
    if rho_p - r <= wall_R:
        raise ValueError("the dispersion box's pipe reaches into the vessel")
    s1 = h * rho_in + wall_R * wall_R * math.asin(h / wall_R)  # integral of sqrt(R^2 - y^2) over -h..h
    v_box = H * (w * wall_R - s1) + w * (back_h * depth + 0.5 * tan * depth * depth)
    v_pipe = math.pi * r * r * rise
    z_top = z_bottom + H
    return {
        "D": D, "width": w, "depth": depth, "back_h": back_h, "slope_deg": v(b["floor_slope_deg"]),
        "height": H, "rho_in": rho_in, "rho_flat": wall_R, "rho_out": rho_out, "rho_pipe": rho_p,
        "z_bottom": z_bottom, "z_top": z_top, "z_centre": z_bottom + 0.5 * H,
        "z_back_foot": z_top - back_h,
        "pipe_rise": rise, "z_pipe_top": z_top + rise,
        "box_volume": v_box, "pipe_volume": v_pipe, "volume": v_box + v_pipe,
        "end": (rho_p, z_top + rise), "end_area": math.pi * r * r,
    }


def calciner_above_feed(g):
    """The vessel the twin's calciner zone starts in: from the meal's
    entry (the meal pipe's axis at the wall) to the roof. Below it the
    kiln gas and the tertiary air only mix; neither meal nor fuel is
    there (the fuel pipes are at the meal's height), and the CFD
    (calciner.md, twin-flow run) carries the meal from that height.
    The wall is the whole vessel's: the gas below the feed loses through
    its wall too, and the zone has nowhere else to put it."""
    cal = calciner(g)
    z = calciner_inlets(g)["meal"]["z_wall"]
    if not cal["z_cone_top"] <= z < cal["z_roof"]:
        raise ValueError(f"meal feed at z {z} m is not in the cylinder")
    return {
        "z_feed": z,
        "volume": math.pi * cal["R"] ** 2 * (cal["z_roof"] - z),
        "wall_area": cal["vessel_wall_area"],
    }


def _gas_stream(c, prefix):
    """A literature gas stream: mass flow, temperature, mole and mass
    fractions, molar mass and density (ideal gas at one atmosphere)."""
    x = {s: v(c[f"{prefix}_x_{s}"]) for s in MOLAR_MASS if f"{prefix}_x_{s}" in c}
    m_mol = sum(x[s] * MOLAR_MASS[s] for s in x)
    T = v(c[f"{prefix}_T"])
    return {
        "flow": v(c[f"{prefix}_flow"]),
        "T": T,
        "x": x,
        "y": {s: x[s] * MOLAR_MASS[s] / m_mol for s in x},
        "M": m_mol,
        "rho": P_ATM * m_mol / (R_GAS * T),
    }


def calciner_boundaries(g):
    """The calciner CFD's two gas inlets, each at its literature flow:
    the kiln gas through the throat, the tertiary air through its duct;
    the hydraulic diameter is the inlet face's own."""
    c, cal = g["calciner"], calciner(g)
    kiln = _gas_stream(c, "throat_gas")
    kiln["D_h"] = cal["D_throat"]
    ta = _gas_stream(c, "tertiary_air")
    ta["D_h"] = v(c["D_tertiary_air"])
    # the duct the flow sizes at its velocity (the yaml's within 0.2 mm)
    ta["D_sized"] = math.sqrt(4.0 * ta["flow"] / (ta["rho"] * math.pi * v(c["tertiary_air_velocity"])))
    return {"kiln_gas_inlet": kiln, "tertiary_air_inlet": ta}


def gooseneck_neck_radius(g):
    """One neck of both legs' area: leg D x sqrt 2, velocity kept."""
    return 0.5 * v(g["gooseneck"]["D_leg"]) * math.sqrt(2.0)


def _cyl(x, y, z, p0, d, length, r):
    """Membership of the points (x, y, z) in the straight cylinder of
    radius r from p0 along the unit vector d, `length` long."""
    dx, dy, dz = x - p0[0], y - p0[1], z - p0[2]
    ax = dx * d[0] + dy * d[1] + dz * d[2]
    perp2 = dx * dx + dy * dy + dz * dz - ax * ax
    return (ax >= 0.0) & (ax <= length) & (perp2 <= r * r)


def _root_forward(r_n, R, beta, setback, margin=0.05):
    """How far in front of the vessel's axis the neck's first piece pierces
    the roof so that its cap (a disc `setback` back along its axis from
    the piercing point, perpendicular to it) lies wholly inside the
    vessel's cylinder, `margin` to spare: an inclined pipe cuts the
    roof plane in an ellipse longer than the vessel is wide, and its
    cap would otherwise stick out of the wall at the roof's edge."""
    phi = np.linspace(0.0, 2.0 * math.pi, 3601)
    cb, sb = math.cos(beta), math.sin(beta)

    def reach(f0):
        y = -f0 + setback * cb + r_n * np.cos(phi) * sb
        x = r_n * np.sin(phi)
        return float(np.max(np.hypot(x, y)))

    # the reach falls as the point moves forward, then rises again when the cap's front
    # leaves the wall: scan for the first f0 that fits, then refine within that step
    step = 1.0e-3
    f0 = 0.0
    while reach(f0) > R - margin:
        f0 += step
        if f0 > R:
            raise ValueError("the neck's cap does not fit inside the vessel at any root position")
    lo, hi = max(0.0, f0 - step), f0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if reach(mid) <= R - margin:
            hi = mid
        else:
            lo = mid
    return hi


@lru_cache(maxsize=None)
def _gn_shared(r_n, r_l, R, z_roof, setback, f0, beta, L1, f4, z4, l_ch, gamma, la, nn=OVERLAP_N):
    """What the gooseneck's pieces share, midpoint grids (calciner.bas is
    given these numbers, not the grids): the volume of the neck's first
    piece inside the vessel (its cap `setback` behind the roof point,
    which lies `f0` in front of the axis, along the piece's axis; the
    vessel the cylinder of radius R under z_roof), then where the neck's
    vertical channel (from `l_ch` above its lower end at forward f4, z4,
    down to it) and the two arms (from there, la long, gamma from the
    vertical, +-x) share space: channel x one arm, one arm x the other,
    all three. Model axes: forward is -y."""
    cb, sb = math.cos(beta), math.sin(beta)
    d1 = (0.0, -cb, sb)
    c0 = (0.0, -f0 + setback * cb, z_roof - setback * sb)
    # a box whose top face is the roof plane, so no cell straddles it
    hxy, hz = 2.0 * R / nn, 8.0 / nn
    mid = np.arange(nn) + 0.5
    x = (-R + 0.00131 + mid * hxy)[:, None, None]
    y = (-R + 0.00093 + mid * hxy)[None, :, None]
    z = (z_roof - 8.0 + mid * hz)[None, None, :]
    first = _cyl(x, y, z, c0, d1, setback + L1, r_n)
    inside = x * x + y * y <= R * R
    v_in = float(np.count_nonzero(first & inside)) * hxy * hxy * hz

    d3 = (0.0, 0.0, -1.0)                           # the channel runs down
    n3 = (0.0, -f4, z4)                             # its lower end, where the arms start
    p3 = (n3[0], n3[1], n3[2] + l_ch)
    sg_, cg_ = math.sin(gamma), math.cos(gamma)
    half = 3.2

    def grid_overlaps(n):
        h = 2.0 * half / n
        mid = (np.arange(n) + 0.5) * h - half
        y = (n3[1] + 0.00227 + mid)[None, :, None]
        z = (n3[2] + 0.00173 + mid)[None, None, :]
        count = [0.0, 0.0, 0.0]
        for i0 in range(0, n, 25):                  # x planes at a time, to keep the arrays small
            x = (n3[0] + 0.00311 + mid[i0:i0 + 25])[:, None, None]
            neck = _cyl(x, y, z, p3, d3, l_ch, r_n)
            a_p = _cyl(x, y, z, n3, (sg_, 0.0, -cg_), la, r_l)
            a_m = _cyl(x, y, z, n3, (-sg_, 0.0, -cg_), la, r_l)
            count[0] += float(np.count_nonzero(neck & a_p))
            count[1] += float(np.count_nonzero(a_p & a_m))
            count[2] += float(np.count_nonzero(neck & a_p & a_m))
        return [c * h ** 3 for c in count]

    # the regions are bounded by planes through the grid's middle; the
    # midpoint rule's error there falls as 1 / n, so two grids are
    # extrapolated (Richardson)
    fine, coarse = grid_overlaps(nn), grid_overlaps(nn // 2)
    o_na, o_aa, o_all = (2.0 * f - c for f, c in zip(fine, coarse))
    return (v_in, o_na, o_aa, o_all)


def gooseneck(g):
    """The gooseneck as calciner.bas builds it (user decision, 15 Nov
    2026): the neck is three straight pieces -- one rising from the
    roof's middle at `neck_slope`, one level, one dropping at
    `neck_slope` -- each joined to the next by a mitre, bending forward
    (-y) so it comes down in front of the vessel; then a vertical channel
    of the neck's diameter (`channel_over_D_neck`, a mitre below the third
    piece); from its lower end two arms leave in the plane across it (+-x, `arm_angle` from the
    vertical) down in one straight piece, turn by a mitre to a level run
    (`arm_run_over_D_leg`) whose axis is C5's inlet axis, and end at their outlet faces (vertical planes,
    normal +-x; user's sketch, 15 Nov 2026). A mitre joint between equal pipes adds the pipes'
    axis lengths exactly; the shared parts (the first piece inside the
    vessel, and where the neck and the arms leave one another) are grids.
    Wall area by the axis lengths. z from the throat's foot; forward is
    -y."""

    gn = g["gooseneck"]
    cal = calciner(g)
    r_l = 0.5 * v(gn["D_leg"])
    r_n = gooseneck_neck_radius(g)
    D_n = 2.0 * r_n
    beta = math.radians(v(gn["neck_slope"]))
    L1 = v(gn["neck_piece_over_D_neck"]) * D_n       # the two inclined pieces
    L2 = v(gn["neck_level_over_D_neck"]) * D_n
    l_ch = v(gn["channel_over_D_neck"]) * D_n        # the vertical channel below the neck
    gamma = math.radians(v(gn["arm_angle"]))
    run = v(gn["arm_run_over_D_leg"]) * 2.0 * r_l     # each arm's level run to its outlet face
    z_roof = cal["z_roof"]
    # the arms' level runs end at C5's inlet axis: C5 stands over the tertiary air duct by
    # its clearance, its inlet r_leg under its roof (the same rule layout() places C5 by)
    ta, c5h = calciner_inlets(g)["tertiary_air"], cyclone(g, "C5")["height"]
    z_end = ta["z"] + 0.5 * ta["D"] + v(g["layout"]["c5_over_tertiary_air"]) + c5h - r_l

    cb, sb = math.cos(beta), math.sin(beta)
    # nodes in (forward f = -y, z): N0 on the roof at the axis
    setback = r_n                                   # the first piece's cap, behind N0 along its axis
    f0 = _root_forward(r_n, cal["R"], beta, setback)  # N0 in front of the vessel's axis: the cap stays inside it
    n0 = (f0, z_roof)
    n1 = (n0[0] + L1 * cb, n0[1] + L1 * sb)
    n2 = (n1[0] + L2, n1[1])
    n3 = (n2[0] + L1 * cb, n2[1] - L1 * sb)         # the third piece ends, the channel starts
    n4 = (n3[0], n3[1] - l_ch)                      # the channel ends, the arms start
    cap = (n0[0] - setback * cb, n0[1] - setback * sb)

    # the arms, in the plane across the channel's lower end: forward f = n4[0]
    sg, cg = math.sin(gamma), math.cos(gamma)
    fall = n4[1] - z_end                             # the arms' fall, channel end to the level run's axis
    if fall <= 0.0:
        raise ValueError(f"the gooseneck's level runs at z {z_end} m are not below the channel's end at {n4[1]} m")
    la = fall / cg                                   # the inclined piece, to the mitre
    x_bend = fall * math.tan(gamma)                  # where it turns level
    x_leg = x_bend + run                             # the outlet faces, x

    R = cal["R"]
    v_in, o_na, o_aa, o_all = _gn_shared(
        round(r_n, 12), round(r_l, 12), round(R, 12), round(z_roof, 12), round(setback, 12), round(f0, 12), beta,
        round(L1, 12), round(n4[0], 12), round(n4[1], 12), round(l_ch, 12), gamma, round(la, 12))

    a_n = math.pi * r_n * r_n
    a_l = math.pi * r_l * r_l
    neck_len = setback + 2.0 * L1 + L2 + l_ch
    arm_len = la + run
    volume = (a_n * neck_len - v_in) + 2.0 * a_l * arm_len - 2.0 * o_na - o_aa + o_all

    return {
        "D_leg": 2.0 * r_l,
        "D_neck": D_n,
        "slope": math.degrees(beta),
        "piece": L1,
        "level": L2,
        "setback": setback,
        "nodes": (n0, n1, n2, n3, n4),              # (forward, z)
        "channel": l_ch,
        "root_forward": f0,
        "cap": cap,
        "y_off": n3[0],                             # the channel's lower end, forward of the vessel's axis
        "z_n3": n3[1],                              # where the third piece ends and the channel starts
        "z_split": n4[1],                           # where the arms leave the channel
        "crown": n1[1] + r_n,
        "arm_angle": math.degrees(gamma),
        "arm_piece": la,
        "arm_run": run,
        "x_bend": x_bend,
        "x_leg": x_leg,
        "z_end": z_end,
        "end_over_H": (z_end - cal["z_throat_top"]) / cal["H"],
        "fall": fall,
        "y_front": n3[0] + r_n,                     # the channel's far side, forward (the foremost part)
        "neck_length": neck_len,
        "arm_length": arm_len,
        "inside_vessel": v_in,
        "overlap_neck_arm": o_na,
        "overlap_arms": o_aa,
        "overlap_all": o_all,
        "volume": volume,
        "wall_area": 2.0 * math.pi * r_n * (2.0 * L1 + L2 + l_ch) + 2.0 * 2.0 * math.pi * r_l * arm_len,
    }


# ======================================================================
# Kiln and cooler
# ======================================================================
def kiln(g):
    k = g["kiln"]
    D, L = v(k["D"]), v(k["L"])
    # the kiln inlet chamber's CFD solid carries the tube's first stub
    # (mouth_stub_over_D D along the axis, user decision 22 Nov 2026), so
    # the kiln's own CFD solid starts there; it ends at the transition
    # zone's end, where the flame volume takes over: stub + solid + flame
    # volume's bore = L, no extra length (the twin and the layout keep L)
    z_cfd0 = v(g["kiln_inlet_chamber"]["mouth_stub_over_D"]) * D
    t_sh, t_br = v(k["shell_t"]), v(k["lining_t"])
    L_tr = v(k["transition_L"])
    A_c, L_br = v(k["brick_cold_face"]), v(k["brick_length"])
    # The wall as the twin builds it (burning.py / transition.py:
    # physics.shell geometry(r_inner = D / 2)): D is the flow (gas) bore
    # and the brick's hot face, the brick the innermost layer, no coating
    # (user decisions, 22 Nov 2026); brick and steel outward of it, per
    # zone (transition z in [0, L_tr], burning z in [L_tr, L]): one shell
    # diameter, the zones differing only in the brick grade.
    r_f = 0.5 * D

    def ring(r0, r1, length):
        return math.pi * (r1 * r1 - r0 * r0) * length

    wall = {"r_flow": r_f}
    for zone, length in (("transition", L_tr), ("burning", L - L_tr)):
        r_b = r_f
        r_si = r_b + t_br
        r_so = r_si + t_sh
        wall[f"r_brick_{zone}"] = r_b
        wall[f"r_shell_in_{zone}"] = r_si
        wall[f"r_shell_{zone}"] = r_so
        wall[f"D_brick_{zone}"] = 2.0 * r_b
        wall[f"D_shell_{zone}"] = 2.0 * r_so
        wall[f"V_brick_{zone}"] = ring(r_b, r_si, length)
        wall[f"V_shell_{zone}"] = ring(r_si, r_so, length)
        # the brick ring's bricks (ISO 5417): as many as the cold face A
        # fits round the shell's inside, each a wedge of 2 pi / n; its hot
        # face is the chord there (the ring's two-shape mix, averaged)
        n = round(2.0 * math.pi * r_si / A_c)
        wall[f"brick_n_{zone}"] = n
        wall[f"brick_cold_chord_{zone}"] = 2.0 * r_si * math.sin(math.pi / n)
        wall[f"brick_hot_chord_{zone}"] = 2.0 * r_b * math.sin(math.pi / n)
        wall[f"brick_rings_{zone}"] = math.ceil(length / L_br - 1e-9)
        wall[f"V_brick_ring_{zone}"] = ring(r_b, r_si, L_br)
    return {
        "D": D,
        "L": L,
        # the CFD solid ends where the flame volume (kiln_flame(), the burning
        # zone and the hood) begins: the two meet at the transition zone's end
        # (user, 23 Nov 2026: one gas path, no overlap)
        "z_cfd0": z_cfd0,
        "z_cfd1": L_tr,
        "L_cfd": L_tr - z_cfd0,
        "volume_cfd": 0.25 * math.pi * D * D * (L_tr - z_cfd0),
        "wall_area_cfd": math.pi * D * (L_tr - z_cfd0),
        "slope": v(k["slope"]),
        "transition_L": v(k["transition_L"]),
        # the wall stack's thicknesses, hot face outward (physics.shell)
        "lining": {
            "steel_shell": v(k["shell_t"]),
            "brick": v(k["lining_t"]),
        },
        "wall": wall,
        "burning_L": L - v(k["transition_L"]),
        "volume": 0.25 * math.pi * D * D * L,
        "wall_area": math.pi * D * L,
    }


def kiln_rotax(g):
    """The kiln's mechanical parts after FLS ROTAX-2 (user, 22 Nov 2026:
    these parts are added as simple envelopes; kiln_rotax.bas builds them;
    23 Nov 2026: the kiln is 60 m, L/D 12.5, a two-base kiln's). The kiln's frame as
    kiln_wall.bas: axis z (back end 0, hood end L), y up, x across; the
    slope is not built in, the piers reach the sloped ground.

    Returns the scalars and "bodies": [{name, kind, p, V, box, rgb}], kind
      ring  p = (r0, r1, z0, z1)                     annulus about z
      box   p = (x0, x1, y0, y1, z0, z1)             axis-aligned
      rbox  p = (r0, r1, w, z0, z1, theta)           a box on the +y axis
                                                     (x +-w/2, y r0..r1), turned
                                                     theta about +z (+y towards -x)
      cyl   p = (bx, by, bz, ax, ay, az, r, length)  base centre, unit axis
    V the volume, box the exact extent (x0, y0, z0, x1, y1, z1).
    """
    k, x = g["kiln"], g["kiln_rotax"]
    kk = kiln(g)
    L = kk["L"]
    r_sh = kk["wall"]["r_shell_burning"]
    t_sh = v(k["shell_t"])
    alpha = math.atan(v(k["slope"]) / 100.0)
    axis_z0 = v(g["layout"]["kiln_axis_z"])        # axis over the ground at the back end

    w_t, t_t, gap = v(x["tyre_width"]), v(x["tyre_thickness"]), v(x["tyre_gap"])
    r_tb = r_sh + gap                                # tyre bore
    r_to = r_tb + t_t                                # tyre OD / 2
    r_band = r_sh + v(x["tyre_section_t"]) - t_sh    # the tyre section's extra plate
    L_band = v(x["tyre_section_L"])
    n_br, w_br, oh = int(v(x["bracket_n"])), v(x["bracket_w"]), v(x["bracket_overhang"])
    r_r = 0.5 * v(x["roller_over_tyre"]) * 2.0 * r_to
    w_r = w_t + v(x["roller_extra_width"])
    ang = math.radians(v(x["roller_angle"]))
    d_r = r_to + r_r                                 # tyre centre to roller centre
    x_r, y_r = d_r * math.sin(ang), -d_r * math.cos(ang)
    r_sd = 0.5 * v(x["roller_shaft_D"])
    b_s, b_L = v(x["bearing_size"]), v(x["bearing_length"])
    f_t = v(x["frame_t"])
    y_top = y_r - 0.5 * b_s                          # frame top: under the bearings
    y_pier = y_top - f_t                             # pier top
    p_hw, p_hl = v(x["pier_half_width"]), v(x["pier_half_length"])
    gb_r, gb_L = 0.5 * v(x["gearbox_D"]), v(x["gearbox_L"])
    m_s, m_L, gap_d = v(x["motor_size"]), v(x["motor_L"]), v(x["drive_gap"])
    h_r, h_t = 0.5 * v(x["htd_D"]), v(x["htd_t"])
    z_in, z_out = v(x["tyre_inlet_at"]) * L, v(x["tyre_outlet_at"]) * L

    def ground(z):                                   # the ground's y under z
        return -(axis_z0 - z * math.sin(alpha))

    bodies = []

    def ring(name, r0, r1, z0, z1, rgb):
        bodies.append({"name": name, "kind": "ring", "p": (r0, r1, z0, z1),
                       "V": math.pi * (r1 * r1 - r0 * r0) * (z1 - z0),
                       "box": (-r1, -r1, z0, r1, r1, z1), "rgb": rgb})

    def box(name, x0, x1, y0, y1, z0, z1, rgb):
        bodies.append({"name": name, "kind": "box", "p": (x0, x1, y0, y1, z0, z1),
                       "V": (x1 - x0) * (y1 - y0) * (z1 - z0),
                       "box": (x0, y0, z0, x1, y1, z1), "rgb": rgb})

    def rbox(name, r0, r1, w, z0, z1, th, rgb):
        c, s = math.cos(th), math.sin(th)
        pts = [(-s * yy + c * xx, c * yy + s * xx) for xx in (-0.5 * w, 0.5 * w) for yy in (r0, r1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        bodies.append({"name": name, "kind": "rbox", "p": (r0, r1, w, z0, z1, th),
                       "V": w * (r1 - r0) * (z1 - z0),
                       "box": (min(xs), min(ys), z0, max(xs), max(ys), z1), "rgb": rgb})

    def cyl(name, base, axis, r, length, rgb):
        n = math.sqrt(sum(a * a for a in axis))
        a = tuple(ai / n for ai in axis)
        end = tuple(b + length * ai for b, ai in zip(base, a))
        half = tuple(r * math.sqrt(max(0.0, 1.0 - ai * ai)) for ai in a)
        lo = tuple(min(b, e) - h for b, e, h in zip(base, end, half))
        hi = tuple(max(b, e) + h for b, e, h in zip(base, end, half))
        bodies.append({"name": name, "kind": "cyl", "p": base + a + (r, length),
                       "V": math.pi * r * r * length, "box": lo + hi, "rgb": rgb})

    BLUE, STEEL, GREY, CONCRETE = (0.1, 0.16, 0.72), (0.62, 0.64, 0.66), (0.45, 0.46, 0.48), (0.78, 0.77, 0.74)
    drive_z0 = None
    for st, z in (("inlet", z_in), ("outlet", z_out)):
        ring(f"tyre_{st}", r_tb, r_to, z - 0.5 * w_t, z + 0.5 * w_t, BLUE)
        ring(f"tyre_section_{st}", r_sh, r_band, z - 0.5 * L_band, z + 0.5 * L_band, STEEL)
        for i in range(n_br):
            rbox(f"bracket_{st}_{i:02d}", r_band, r_tb, w_br, z - 0.5 * w_t - oh, z + 0.5 * w_t + oh,
                 (i + 0.5) * 2.0 * math.pi / n_br, STEEL)
        for side, sx in (("L", -1.0), ("R", 1.0)):
            xr = sx * x_r
            cyl(f"roller_{st}_{side}", (xr, y_r, z - 0.5 * w_r), (0.0, 0.0, 1.0), r_r, w_r, BLUE)
            cyl(f"shaft_{st}_{side}", (xr, y_r, z - 0.5 * w_r - b_L), (0.0, 0.0, 1.0), r_sd, w_r + 2.0 * b_L, GREY)
            for end, sz in (("back", -1.0), ("hood", 1.0)):
                za, zb = sorted((z + sz * 0.5 * w_r, z + sz * (0.5 * w_r + b_L)))
                box(f"bearing_{st}_{side}_{end}", xr - 0.5 * b_s, xr + 0.5 * b_s, y_r - 0.5 * b_s, y_r + 0.5 * b_s,
                    za, zb, GREY)
            if st == "inlet":
                # the friction drive: gearbox, then the main motor, back-end side
                zg1 = z - 0.5 * w_r - b_L - gap_d
                cyl(f"gearbox_{side}", (xr, y_r, zg1 - gb_L), (0.0, 0.0, 1.0), gb_r, gb_L, BLUE)
                zm1 = zg1 - gb_L - gap_d
                box(f"motor_{side}", xr - 0.5 * m_s, xr + 0.5 * m_s, y_r - 0.5 * m_s, y_r + 0.5 * m_s,
                    zm1 - m_L, zm1, GREY)
                drive_z0 = zm1 - m_L
        zf = 0.5 * w_r + b_L
        box(f"frame_{st}", -(x_r + 0.5 * b_s), x_r + 0.5 * b_s, y_pier, y_top, z - zf, z + zf, GREY)
        # the inlet pier also carries the drive; the outlet pier reaches
        # the hood end, under the outlet seal and the nose ring fan (images)
        za = min(z - p_hl, drive_z0 - gap_d) if st == "inlet" else z - p_hl
        zb = z + p_hl if st == "inlet" else max(z + p_hl, L)
        box(f"pier_{st}", -p_hw, p_hw, ground(z), y_pier, za, zb, CONCRETE)
    # the hydraulic thrust device: a level roller on the inlet tyre's hood-side face
    zc = z_in + 0.5 * w_t + h_r
    yh = -0.5 * (r_tb + r_to)
    cyl("htd", (0.0, yh - 0.5 * h_t, zc), (0.0, 1.0, 0.0), h_r, h_t, BLUE)
    box("htd_stand", -0.5 * h_r, 0.5 * h_r, y_top, yh - 0.5 * h_t, zc - 0.5 * h_r, zc + 0.5 * h_r, GREY)
    # seals: graphite blocks in ring housings over the shell's ends
    r_is = r_sh + v(x["inlet_seal_depth"])
    L_is = v(x["inlet_seal_L"])
    ring("inlet_seal", r_sh, r_is, -0.5 * L_is, 0.5 * L_is, BLUE)
    r_os = r_sh + v(x["outlet_seal_depth"])
    L_os = v(x["outlet_seal_L"])
    ring("outlet_seal", r_sh, r_os, L - L_os, L, BLUE)
    # the dust chutes: from the seal housing's underside down to the outlet
    # pier (the images' legs to the platform)
    c_r = 0.5 * v(x["chute_D"])
    for i, sx in ((1, -1.0), (2, 1.0)):
        xc = sx * 0.5 * r_sh
        y_c = -math.sqrt(r_os * r_os - xc * xc)
        cyl(f"outlet_chute_{i}", (xc, y_pier, L - 0.5 * L_os), (0.0, 1.0, 0.0), c_r, y_c - y_pier, BLUE)
    # cooling: the nose ring fan aimed at the outlet seal, three shell fans
    f_r, f_L = 0.5 * v(x["fan_D"]), v(x["fan_L"])
    f_c = v(x["fan_clearance"])
    w_w, d_w = v(x["walkway_width"]), v(x["walkway_depth"])
    x_w0, x_w1 = -p_hw, -p_hw + w_w
    xf = 0.5 * (x_w0 + x_w1)
    y_f = y_pier + f_r                               # a fan's base centre, its rim on the deck
    # the nose ring fan: on the outlet pier, square to the kiln (its axis in
    # the plane z = the seal housing's middle, aimed at the kiln's axis; user,
    # 22 Nov 2026), its outlet f_c off the housing, its base on the deck
    r_n = r_os + f_c + f_L                           # base centre's distance from the axis
    base_n = (-math.sqrt(r_n * r_n - y_f * y_f), y_f, L - 0.5 * L_os)
    if base_n[0] < -p_hw:
        raise ValueError(f"kiln_rotax: the nose ring fan at x {base_n[0]:.2f}, off the pier")
    d = (-base_n[0], -base_n[1], 0.0)
    def fan(name, base, axis):
        """A fan and its stand: a post under the fan's base centre, from the
        deck (the pier / walkway top) up to the tilted base face. The face is
        y = y_b - (ax (x - x_b) + az (z - z_b)) / ay; the post's top reaches
        its highest point over the post, so the post meets the face all
        over (and runs a little into the fan where the face is lower)."""
        n_ = math.sqrt(sum(q * q for q in axis))
        a_ = tuple(q / n_ for q in axis)
        if a_[1] <= 0.0:
            raise ValueError(f"kiln_rotax: {name} does not point up; no post under it")
        cyl(name, base, axis, f_r, f_L, STEEL)
        h = 0.35 * f_r                               # the post's half width: its top stays inside the fan
        y_top = base[1] + h * (abs(a_[0]) + abs(a_[2])) / a_[1]
        y_low = base[1] - f_r * math.sqrt(1.0 - a_[1] ** 2)
        if y_low <= y_pier:
            raise ValueError(f"kiln_rotax: {name} reaches below the deck")
        box(f"{name}_stand", base[0] - h, base[0] + h, y_pier, y_top, base[2] - h, base[2] + h, GREY)

    fan("nose_ring_fan", base_n, d)
    box("walkway", x_w0, x_w1, y_pier - d_w, y_pier, z_in + p_hl, z_out - p_hl, GREY)
    # shell fans: on the walkway, aimed at the axis, their outlet f_c off the
    # shell (images: tilted at the shell's side, close to it)
    r_f = r_sh + f_c + f_L                           # base centre's distance from the axis
    xb = -math.sqrt(r_f * r_f - y_f * y_f)
    if not x_w0 <= xb <= x_w1:
        raise ValueError(f"kiln_rotax: shell fans at x {xb:.2f}, off the walkway {x_w0:.2f} .. {x_w1:.2f}")
    for i in range(int(v(x["fan_n"]))):
        zf_i = z_out - v(x["fan_first_before_tyre"]) + i * v(x["fan_pitch"])
        fan(f"shell_fan_{i + 1}", (xb, y_f, zf_i), (-xb, -y_f, 0.0))
    names = [b["name"] for b in bodies]
    assert len(set(names)) == len(names), "kiln_rotax: a body name twice"
    return {
        "z_tyre_inlet": z_in, "z_tyre_outlet": z_out, "tyre_span": z_out - z_in,
        "r_tyre_bore": r_tb, "r_tyre": r_to, "D_tyre": 2.0 * r_to,
        "r_roller": r_r, "D_roller": 2.0 * r_r, "w_roller": w_r, "x_roller": x_r, "y_roller": y_r,
        "y_pier_top": y_pier, "ground_inlet": ground(z_in), "ground_outlet": ground(z_out),
        "bodies": bodies,
    }


def cooler(g):
    c = g["cooler"]
    w, h = v(c["width"]), v(c["casing_height"])
    L = v(c["grate_area"]) / w
    n, nh = int(v(c["segments"])), int(v(c["hood_segments"]))
    hood_L = nh * L / n
    seg = L / n
    # the inlet: a fixed grate falling at cis_angle from the hot end over its
    # segments, the floor flat (z = 0) after it; the roof stays at h
    cis_L = int(v(c["cis_segments"])) * seg
    cis_a = math.radians(v(c["cis_angle"]))
    cis_rise = cis_L * math.tan(cis_a)
    # the clinker bed: the FLS cooler's design depth (a model of the bed
    # the grate speed carries), parallel to the floor
    rho_b = v(c["solid_density"]) * (1.0 - v(c["bed_porosity"]))
    bed_h = v(c["fls_clinker_flow"]) / (rho_b * w * v(c["fls_grate_speed"]))
    if not 0.0 < cis_rise + bed_h < h:
        raise ValueError("cooler: the inlet grate and the bed leave no room under the roof")
    return {
        "width": w,
        "casing_height": h,
        "length": L,
        "grate_area": v(c["grate_area"]),
        "box_volume": w * L * h,
        "segments": n,
        "segment_L": seg,
        "segment_area": w * seg,
        "hood_segments": nh,
        "hood_L": hood_L,
        "hood_area": w * hood_L,
        "cis_L": cis_L, "cis_angle": cis_a, "cis_rise": cis_rise,
        "cis_area": w * cis_L / math.cos(cis_a),      # grate_air_1..: the inclined face
        "bed_h": bed_h, "bed_rho": rho_b,
        "bed_volume": w * L * bed_h,
        # the casing's gas volume (bed + freeboard) without the vent duct
        "casing_volume": w * (L * h - 0.5 * cis_L * cis_rise),
        # the walls of the old box: two sides, two ends, and the roof but for the hood's opening
        "wall_area": 2.0 * L * h + 2.0 * w * h + w * (L - hood_L),
    }


def cooler_air(g):
    """The undergrate air per segment [kg/s], hot end first: the total
    (air_rate x the clinker) in the FLS reference cooler's proportions
    (segment 1, segment 2, the rest alike; user decision, 23 Nov 2026)."""
    c, co = g["cooler"], cooler(g)
    n = co["segments"]
    w = [v(c["fls_air_seg1"]), v(c["fls_air_seg2"])] + [v(c["fls_air_seg_rest"])] * (n - 2)
    total = v(c["air_rate"]) * v(g["kiln"]["clinker_flow"])
    return {"m": [total * wi / sum(w) for wi in w], "total": total,
            "fls_rate": sum(w) / v(c["fls_clinker_flow"])}


AIR_M = 0.028965      # dry air [kg/mol]
VENT_WALL_GAP = 0.10  # [m] the vent duct's edge off the cooler's end wall: a clean roof face between (model)


def cooler_cfd(g):
    """The cooler's CFD volume (user decisions, 23 Nov 2026; cooler.bas):
    the casing on the grate, x along it from the hot end, y across, z up
    from the flat grate. Two bodies: the clinker bed (a porous cell zone,
    bed_h deep over the floor) and the freeboard over it. The floor:
    grate_air_1 the inclined inlet (cis_angle over cis_L), grate_air_2..n
    flat strips. The roof: hood_1 and hood_2 (the hood's opening, one
    segment each: the flame volume's secondary_air_in and
    tertiary_supply_in), and the vent: a round duct off the roof at the
    middle + vent_offset_segments segments (user, 23 Nov 2026), VENT_WALL_GAP
    from the side walls at the least; D from the vent air's flow at vent_T and vent_velocity,
    run vent_L_over_D x D up to its end face vent_out."""
    c, co = g["cooler"], cooler(g)
    if co["hood_segments"] != 2:
        raise ValueError("cooler_cfd: the hood's opening is hood_1 + hood_2, one segment each")
    bal = cooler_boundaries(g, _geometry=False)["balance"]
    rho = 101325.0 * AIR_M / (R_GAS * v(c["vent_T"]))
    q = bal["vent"] / rho
    A = q / v(c["vent_velocity"])
    D = math.sqrt(4.0 * A / math.pi)
    seg, w, L, H = co["segment_L"], co["width"], co["length"], co["casing_height"]
    gap = VENT_WALL_GAP
    x_v = 0.5 * L + v(c["vent_offset_segments"]) * seg
    if D > w - 2.0 * gap or x_v - 0.5 * D < co["hood_L"] + gap or x_v + 0.5 * D > L - gap:
        raise ValueError(f"cooler_cfd: the vent duct (D {D:.2f} m at x {x_v:.2f} m) does not fit on the roof")
    L_v = v(c["vent_L_over_D"]) * D
    V_duct = A * L_v
    # the roof flat at H: hood_1 / hood_2 are its first two segments, split
    # off as faces of their own, and lie on the flame volume's flat hood
    # floor (its secondary_air_in / tertiary_supply_in), so the two volumes
    # meet face to face (user, 23 Nov 2026: one gas path, no gap or overlap;
    # the earlier stubs and the roof's steps under them taken out)
    # the clinker outlet: past the grate's end the HRB deck (cooler: hrb_*,
    # in line with the grate, z = 0) under the freeboard carried on over it;
    # the bed ends at x = L in clinker_out (user, 23 Nov 2026)
    L_h = v(c["hrb_rollers"]) * v(c["hrb_pitch"])
    Lt = L + L_h
    fb = co["casing_volume"] - co["bed_volume"] + V_duct + w * L_h * H
    hb, zc, nh = co["bed_h"], co["cis_rise"], co["hood_segments"]
    side = Lt * H - 0.5 * co["cis_L"] * zc                   # one side wall of the freeboard + bed
    walls = {
        "bed": 2.0 * L * hb + w * hb,                      # its sides and its back end
        "freeboard": (2.0 * (side - L * hb) + w * (H - zc - hb) + w * H
                      + w * (Lt - nh * seg) - A + math.pi * D * L_v),
    }
    return {
        "vent_D": D, "vent_A": A, "vent_q": q, "vent_rho": rho, "vent_x": x_v, "vent_L": L_v,
        "vent_z_out": H + L_v, "hood_z": (H, H), "hrb_L": L_h, "length_total": Lt,
        "bed_volume": co["bed_volume"], "freeboard_volume": fb,
        "volume": co["bed_volume"] + fb,
        "walls": walls,
        "faces": {
            **{f"grate_air_{i + 1}": (co["cis_area"] if i < int(v(c["cis_segments"])) else w * seg)
               for i in range(co["segments"])},
            "hood_1": w * seg, "hood_2": w * seg,
            "vent_out": A,
            # the bed top: the shared face of the two bodies (an interior in the CFD)
            "bed_top": co["cis_area"] + w * (L - co["cis_L"]),
            # the bed's end at the grate's end: the clinker leaves the porous zone
            "clinker_out": w * hb,
            # the HRB deck's top past the grate's end (the rollers, the clinker on them)
            "hrb_deck": w * L_h,
        },
    }


def ergun(eps, d):
    """Fluent's porous-zone coefficients for a packed bed of spheres d
    across at porosity eps (Ergun): viscous 1/alpha [1/m2], inertial C2 [1/m]."""
    return 150.0 * (1.0 - eps) ** 2 / (eps ** 3 * d ** 2), 3.5 * (1.0 - eps) / (eps ** 3 * d)


def cooler_boundaries(g, _geometry=True):
    """The cooler volume's boundary values, one per cooler_cfd() face (CFD
    set-up input). The undergrate air from cooler_air(); the two hood
    outlets take what the flame volume's cooler inlets take from the
    cooler (kiln_flame_boundaries(); one-way through the hood plane, user
    decision 23 Nov 2026): hood_1 the secondary air (the seal's leak joins
    it in the hood, not here), hood_2 the tertiary air; the vent carries
    the rest (a pressure outlet). The bed: a porous zone, Ergun from the
    nodule size, the clinker moving through it at the grate speed.

    Same form as kiln_flame_boundaries()."""
    c, co = g["cooler"], cooler(g)
    air = cooler_air(g)
    split = kiln_air_split(g)
    ta = calciner_boundaries(g)["tertiary_air_inlet"]
    T0 = v(g["kiln_burner"]["primary_air_T"])
    m_h1, m_h2 = split["secondary"], ta["flow"]
    m_vent = air["total"] - m_h1 - m_h2
    if m_vent <= 0.0:
        raise ValueError("cooler_boundaries: the hood takes all the cooling air; no vent air left")
    eps, d = v(c["bed_porosity"]), v(c["particle_d"])
    visc, inert = ergun(eps, d)
    m_cl = v(g["kiln"]["clinker_flow"])
    bc = {f"grate_air_{i + 1}": {"kind": "mass_flow_inlet", "m": m, "T": T0, "gas": "air", "particles": None,
                                 "note": "undergrate air, FLS segment share" + (" (the inclined inlet)" if i == 0 else "")}
          for i, m in enumerate(air["m"])}
    bc.update({
        "hood_1": {"kind": "mass_flow_outlet", "m": m_h1, "T": None, "gas": None, "particles": None,
                   "note": "to the kiln: the secondary air (kiln_flame secondary_air_in less the seal's leak)"},
        "hood_2": {"kind": "mass_flow_outlet", "m": m_h2, "T": None, "gas": None, "particles": None,
                   "note": "to the tertiary air duct (kiln_flame tertiary_supply_in)"},
        "vent_out": {"kind": "pressure_outlet", "m": None, "T": None, "gas": None, "particles": None,
                     "note": "0 Pa gauge (reference); the vent air, the rest"},
        "bed_top": {"kind": "interior", "m": None, "T": None, "gas": None, "particles": None,
                    "note": "the bed's top: shared face of the bed and the freeboard"},
        "clinker_out": {"kind": "interior", "m": None, "T": None, "gas": None, "particles": None,
                        "note": "the bed's end at the grate's end (shared with the freeboard): the clinker "
                                "leaves the porous zone here (its enthalpy out, model); target 65 K over "
                                "ambient (CII manual, IKN)"},
        "hrb_deck": {"kind": "wall", "m": None, "T": None, "gas": None, "particles": None,
                     "note": "the roller breaker's deck past the grate's end; the chute under it is "
                             "closed by the clinker column (no false air, model)"},
    })
    bed = {"porosity": eps, "particle_d": d, "viscous_resistance": visc, "inertial_resistance": inert,
           "solid_density": v(c["solid_density"]), "clinker_flow": m_cl,
           "clinker_velocity": m_cl / (co["bed_rho"] * co["width"] * co["bed_h"]), "depth": co["bed_h"]}
    out = {"bc": bc, "bed": bed,
           "balance": {"in": air["total"], "hood_1": m_h1, "hood_2": m_h2, "vent": m_vent},
           "air": air}
    if _geometry:
        names = set(cooler_cfd(g)["faces"])
        if set(bc) != names:
            raise ValueError(f"cooler_boundaries: faces {sorted(names ^ set(bc))} without a value")
    return out


# ======================================================================
# The preheater ID fan: the duty point and the size that follows
# ======================================================================
R_GAS = 8.314462618


def id_fan(g):
    """One string's ID fan from its duty (the twin's exhaust, a model
    value): gas density and volume flow at the fan's inlet, the shaft
    and motor power, and the size by the fan laws: the tip speed from
    the pressure coefficient psi = 2 dp / (rho u^2), the impeller from
    the tip speed and the speed, the inlet from the inlet velocity."""

    f = g["id_fan"]
    m, T = v(f["exhaust_flow_per_string"]), v(f["exhaust_T"])
    M = v(f["exhaust_molar_mass"]) * 1e-3
    p_in = 101325.0 - v(f["inlet_underpressure"])
    dp, eta = v(f["total_pressure"]), v(f["efficiency"])
    n = v(f["speed"]) / 60.0
    rho = p_in * M / (R_GAS * T)
    q = m / rho
    u = math.sqrt(2.0 * dp / (rho * v(f["pressure_coefficient"])))
    p_shaft = q * dp / eta
    d2 = u / (math.pi * n)
    d1 = v(f["eye_ratio"]) * d2
    out = {
        "per_string": int(v(f["per_string"])),
        "rho": rho,
        "q": q,
        "q_h": q * 3600.0,
        "q_total_h": q * 3600.0 * v(g["plant"]["strings"]),
        "dp": dp,
        "p_shaft": p_shaft,
        "p_motor": p_shaft * v(f["motor_margin"]),
        "u_tip": u,
        "D_impeller": d2,
        "D_inlet": d1,
    }
    out.update(_id_fan_flow_path(f, q, dp, rho, n, d1, d2, u))
    return out


def _id_fan_flow_path(f, q, dp, rho, n, d1, d2, u2):
    """The fan's flow path from its duty and the impeller's diameters.

    Impeller (single-arc plate blades, a flat back plate, a straight
    conical shroud): the eye's axial velocity c0 = 4Q / (pi D1^2) is kept
    into the blade row (c_m1 = c0, so b1 = Q / (pi D1 c0)); the blade
    inlet angle is the flow angle under the blades' blockage plus the
    incidence; z = k sin(beta2) / (1 - D1/D2). The outlet: Euler with
    Wiesner's slip, dp = eta_h rho u2 cu2, cu2 = u2 (sigma - cm2 / (u2
    tan beta2)), gives cm2, and continuity b2 = Q / (pi D2 cm2 tau2).
    Leakage and the disc cavities are not in the flow path.

    Volute: constant width B round the impeller, a free vortex from the
    impeller's rim (c_u r = cu2 r2 = K, angular momentum kept). The
    flow through the section at angle theta from the tongue is
    Q theta / (2 pi) = B K ln(r / r3), so the outer wall is the log
    spiral r = r3 exp(k theta), k = Q / (2 pi B K); the discharge is the
    section at theta = 2 pi, height r_end - r3. Angles are from the
    tangent; lengths in m."""

    z_coef, t = v(f["blade_number_coeff"]), v(f["blade_thickness"])
    b2_ang = math.radians(v(f["blade_outlet_angle"]))
    r1, r2 = 0.5 * d1, 0.5 * d2
    # --- blade count (from the blade angle and the diameter ratio)
    z = round(z_coef * math.sin(b2_ang) / (1.0 - d1 / d2))
    # --- inlet: the eye's velocity carried into the row
    c0 = q / (math.pi * r1 ** 2)
    b1 = q / (math.pi * d1 * c0)
    u1 = math.pi * d1 * n
    # blockage at the inlet depends on beta1 itself: fixed point
    beta1_flow = math.atan(c0 / u1)
    for _ in range(50):
        beta1 = beta1_flow + math.radians(v(f["incidence"]))
        tau1 = 1.0 - z * t / (math.pi * d1 * math.sin(beta1))
        beta1_flow = math.atan(c0 / (tau1 * u1))
    beta1 = beta1_flow + math.radians(v(f["incidence"]))
    tau1 = 1.0 - z * t / (math.pi * d1 * math.sin(beta1))
    # --- outlet: Euler with Wiesner's slip, then continuity
    slip = 1.0 - math.sqrt(math.sin(b2_ang)) / z ** 0.7
    slip_limit = math.exp(-8.16 * math.sin(b2_ang) / z)          # Wiesner's D1/D2 limit
    cu2 = dp / (v(f["hydraulic_efficiency"]) * rho * u2)
    cm2 = (slip * u2 - cu2) * math.tan(b2_ang)
    tau2 = 1.0 - z * t / (math.pi * d2 * math.sin(b2_ang))
    b2 = q / (math.pi * d2 * cm2 * tau2)
    # --- single circular arc from (r1, beta1) to (r2, beta2), angles from the tangent
    rb = (r2 ** 2 - r1 ** 2) / (2.0 * (r2 * math.cos(b2_ang) - r1 * math.cos(beta1)))
    rc = math.sqrt(rb ** 2 + r2 ** 2 - 2.0 * rb * r2 * math.cos(b2_ang))
    # blade centreline: the point at radius r sits phi(r) from the arc
    # centre's ray, on the side where theta falls as r grows (backward
    # against the rotation, which runs +theta: from +x towards +z)
    def phi(r):
        return math.acos((rc ** 2 + r ** 2 - rb ** 2) / (2.0 * rc * r))
    sense = -1.0 if phi(r2) > phi(r1) else 1.0
    # --- volute: a log spiral (constant angle alpha) from the tongue's
    # circle, constant width B round the impeller. Its growth is set by
    # the outlet: the discharge's area B h_stub carries Q at the outlet
    # velocity, h_stub = (r_end - r3) cos(alpha) - 2 rho_t, r_end = r3
    # exp(2 pi k), alpha = atan(k). The casing decelerates the gas from
    # the impeller's cu2 (a free vortex would keep cu r and, at this B,
    # leave far faster).
    big_b = v(f["volute_width_ratio"]) * b2
    gap = v(f["tongue_gap_ratio"]) * d2
    rho_t = v(f["tongue_radius_ratio"]) * d2
    r3 = r2 + gap
    k_vortex = cu2 * r2
    c_out = v(f["volute_outlet_velocity"])
    h_want = q / (big_b * c_out)

    def h_of(k):
        return r3 * (math.exp(2.0 * math.pi * k) - 1.0) * math.cos(math.atan(k)) - 2.0 * rho_t
    lo, hi = 1e-4, 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if h_of(mid) < h_want:
            lo = mid
        else:
            hi = mid
    k_spiral = 0.5 * (lo + hi)
    alpha = math.atan(k_spiral)
    r_end = r3 * math.exp(2.0 * math.pi * k_spiral)
    h_out = r_end - r3
    r_mrf = r2 + v(f["mrf_gap_fraction"]) * gap
    # Placed in the x-z plane (axis y), the impeller turning +theta (from +x
    # towards +z): the discharge leaves at gamma above the horizontal on
    # the -x side, d = (-cos gamma, sin gamma), the spiral's tangent at its
    # start ray psi0 = 90 deg + alpha - gamma. The tongue's nose is a
    # circle of radius rho_t tangent to the spiral's start P0 from outside
    # (centre rho_t along the outward normal n = (sin gamma, cos gamma));
    # the discharge's lower wall leaves the nose's far side T, its outer
    # wall the spiral's end, both along d, to the outlet face normal to d.
    gamma = math.radians(v(f["discharge_angle"]))
    dx, dz = -math.cos(gamma), math.sin(gamma)
    nx, nz = math.sin(gamma), math.cos(gamma)
    psi0 = 0.5 * math.pi + alpha - gamma

    def spiral(th):
        r = r3 * math.exp(k_spiral * th)
        return (r * math.cos(psi0 + th), r * math.sin(psi0 + th))
    p0, pend = spiral(0.0), spiral(2.0 * math.pi)
    tpt = (p0[0] + 2.0 * rho_t * nx, p0[1] + 2.0 * rho_t * nz)
    h_stub = (pend[0] - tpt[0]) * nx + (pend[1] - tpt[1]) * nz      # = h_out cos(alpha) - 2 rho_t
    l_stub = v(f["outlet_stub_ratio"]) * h_stub
    s_exit = pend[0] * dx + pend[1] * dz + l_stub
    e_top = (pend[0] + l_stub * dx, pend[1] + l_stub * dz)
    s_t = s_exit - (tpt[0] * dx + tpt[1] * dz)
    e_low = (tpt[0] + s_t * dx, tpt[1] + s_t * dz)
    a_out = big_b * h_stub
    # the outline's area by the shoelace sum, the spiral finely sampled
    pts = [spiral(2.0 * math.pi * i / 20000) for i in range(20001)]
    pts += [e_top, e_low, tpt]
    cx, cz = p0[0] + rho_t * nx, p0[1] + rho_t * nz
    a0 = 0.5 * math.pi - gamma
    pts += [(cx + rho_t * math.cos(a), cz + rho_t * math.sin(a))
            for a in (a0 - math.pi * i / 2000 for i in range(1, 2000))]
    area = 0.5 * abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts))))
    x_min = min(p[0] for p in pts)
    x_max = max(p[0] for p in pts)
    z_min = min(p[1] for p in pts)
    z_max = max(p[1] for p in pts)
    nose_clear = math.hypot(cx, cz) - rho_t - r_mrf
    # --- inlet cone (from the eye through the volute's front plate) and box
    # on the plate's outside (axis y; the box's inlet face looks along +x)
    d_cone = v(f["cone_inlet_ratio"]) * d1
    y_box = big_b + v(f["side_plate_gap"])
    l_cone = y_box - b1
    a_eye = math.pi * r1 ** 2
    a_box = v(f["inlet_box_area_ratio"]) * a_eye
    h_box = v(f["inlet_box_height_ratio"]) * d_cone
    depth_box = a_box / h_box
    reach_box = 0.5 * d_cone + v(f["inlet_box_reach_ratio"]) * d_cone
    # --- volumes (the macro checks its solids against these)
    # rotor zone: eye cylinder, the shroud's cone r1..r2 (b1 -> b2), the rim ring
    v_frustum = math.pi * (r2 - r1) * (r1 * (2 * b1 + b2) + r2 * (b1 + 2 * b2)) / 3.0
    v_rotor = math.pi * r1 ** 2 * b1 + v_frustum + math.pi * (r_mrf ** 2 - r2 ** 2) * b2
    # the blades, cut hub to shroud: z t times the height along the centreline
    # (from r1 + e to r2 - e: the straight caps then stay off the eye's and
    # the tip's circles, which keep whole edges)
    e = v(f["blade_edge_clearance"])
    ra0, rb0 = r1 + e, r2 - e
    nb = 4000
    v_blade = 0.0
    for i in range(nb):
        ra, rb_ = ra0 + (rb0 - ra0) * i / nb, ra0 + (rb0 - ra0) * (i + 1) / nb
        ds = math.hypot(rb_ - ra, 0.5 * (ra + rb_) * sense * (phi(rb_) - phi(ra)))
        rm = 0.5 * (ra + rb_)
        v_blade += t * (b1 + (b2 - b1) * (rm - r1) / (r2 - r1)) * ds
    v_blades = z * v_blade
    v_volute = big_b * (area - math.pi * r_mrf ** 2)
    v_cone = math.pi * l_cone * (r1 ** 2 + r1 * 0.5 * d_cone + (0.5 * d_cone) ** 2) / 3.0
    v_box = h_box * depth_box * (0.5 * h_box + reach_box)
    return {
        "z": z,
        "c0": c0,
        "b1": b1,
        "u1": u1,
        "beta1": math.degrees(beta1),
        "beta1_flow": math.degrees(beta1_flow),
        "tau1": tau1,
        "beta2": math.degrees(b2_ang),
        "slip": slip,
        "slip_limit": slip_limit,
        "cu2": cu2,
        "cm2": cm2,
        "tau2": tau2,
        "b2": b2,
        "blade_t": t,
        "blade_r_in": ra0,
        "blade_r_out": rb0,
        "blade_arc_R": rb,
        "blade_arc_centre_r": rc,
        "blade_sense": sense,
        "blade_theta_span": math.degrees(abs(phi(r2) - phi(r1))),
        "phi": 4.0 * q / (math.pi ** 2 * d2 ** 3 * n),
        "psi": 2.0 * dp / (rho * u2 ** 2),
        "B": big_b,
        "tongue_gap": gap,
        "tongue_radius": rho_t,
        "r3": r3,
        "K": k_vortex,
        "c_out": c_out,
        "k_spiral": k_spiral,
        "spiral_angle": math.degrees(alpha),
        "psi0": math.degrees(psi0),
        "r_end": r_end,
        "h_out": h_out,
        "u_section": q / (big_b * h_out),
        "h_stub": h_stub,
        "a_out": a_out,
        "u_out": q / a_out,
        "l_stub": l_stub,
        "discharge_dir": (dx, dz),
        "s_exit": s_exit,
        "e_top": e_top,
        "e_low": e_low,
        "p0": p0,
        "pend": pend,
        "nose_top": tpt,
        "nose_clearance": nose_clear,
        "volute_box": (x_min, z_min, x_max, z_max),
        "r_mrf": r_mrf,
        "D_cone": d_cone,
        "L_cone": l_cone,
        "y_box": y_box,
        "a_eye": a_eye,
        "a_box": a_box,
        "u_box": q / a_box,
        "H_box": h_box,
        "depth_box": depth_box,
        "reach_box": reach_box,
        "volute_area": area,
        "V_rotor": v_rotor,
        "V_blades": v_blades,
        "V_rotor_bladed": v_rotor - v_blades,
        "V_volute": v_volute,
        "V_cone": v_cone,
        "V_box": v_box,
    }


# ======================================================================
# The kiln burner (JETFLEX 2.0): duty, primary air, its channels' flow
# volume (kiln_burner.bas builds it)
# ======================================================================
P_ATM = 101325.0           # Pa, the kiln hood (the jets leave into it)
M_AIR = 0.028965           # kg/mol
GAMMA_AIR = 1.4


def nozzle(dp, T0):
    """Isentropic air jet from p_atm + dp, T0 down to p_atm: (u, rho, T)
    at the exit (subsonic: dp under the critical 0.89 bar)."""
    p0 = P_ATM + dp
    if p0 / P_ATM >= ((GAMMA_AIR + 1.0) / 2.0) ** (GAMMA_AIR / (GAMMA_AIR - 1.0)):
        raise ValueError(f"nozzle: {dp} Pa over ambient is choked; the formula is subsonic")
    cp = GAMMA_AIR / (GAMMA_AIR - 1.0) * R_GAS / M_AIR
    T = T0 * (P_ATM / p0) ** ((GAMMA_AIR - 1.0) / GAMMA_AIR)
    u = math.sqrt(2.0 * cp * (T0 - T))
    return u, P_ATM * M_AIR / (R_GAS * T), T


def kiln_burner(g):
    """The JETFLEX 2.0 burner (kiln/kiln_burner.md; user, 22 Nov 2026: a
    flow geometry a CFD can take).

    Duty: the twin's kiln fuel times its LHV. Primary air: the twin's share
    of the kiln air is the axial + swirl air (user); the coal's conveying
    air comes on top, the fuel over a literature solids loading.

    The tip's layout is the brochure's (Fuller JETFLEX 2.0, p. 5, fixed
    nozzles): a straight solid fuel pipe a little above the centre, a ring
    of swirl air holes round it, a ring of rectangular axial air slots
    outside -- their counts, sizes and radii as ratios of the tip's outer
    D (image ratios). The jets leave at the JETFLEX manual's channel
    pressures (isentropic, ambient exit). The open areas' ratio, at those
    velocities, splits the air between axial and swirl; the slots' area
    then gives the scale (the tip's D), and with it the coal pipe -- whose
    velocity is a check against the literature, not an input. The
    momentum (sum of m u) follows and must sit in FLSmidth's 7-11 N/MW.

    The flow volume, frame: the burner's axis z, the tip plane z = 0, the
    flow towards +z (into the kiln), y up, x as seen from the kiln to the
    right. Three bodies, each a channel: coal (the pipe), axial (an annular
    plenum behind the front plate + the slots through it), swirl (a
    plenum + holes inclined swirl_angle towards +theta: the swirl turns
    anticlockwise seen from the kiln; sense not published, model).
    "bodies": [{name, group, kind, p, V, box, rgb}] as kiln_rotax(), kinds
      cyl   p = (bx, by, bz, ax, ay, az, r, length)
      ring  p = (r0, r1, z0, z1)
      slot  p = (cx, cy, z0, z1, l, w, alpha)  a box l x w x (z1 - z0), its
                long side alpha from +x about +z, centred on (cx, cy)
      hole  p = (px, py, pz, e1(3), e2(3), d(3), a, H, z0, z1)  a square
                prism a x a along d through P, H long, cut to z0 .. z1
    "groups": {name: {V, box, n_out, a_out, a_in}} the bodies once joined.
    """
    b = g["kiln_burner"]
    q_th = v(b["fuel_flow"]) * v(b["fuel_LHV"])                 # MW
    m_pa = v(b["kiln_air_flow"]) * v(b["primary_air_fraction"])
    T0 = v(b["primary_air_T"])
    u_ax, rho_ax, T_ax = nozzle(v(b["axial_pressure"]), T0)
    u_sw, rho_sw, T_sw = nozzle(v(b["swirl_pressure"]), T0)
    th = math.radians(v(b["swirl_angle"]))

    # open areas over D_tip^2 (image), the swirl holes' flow area normal to them
    n_ax, n_sw = int(v(b["n_axial"])), int(v(b["n_swirl"]))
    a_ax_img = n_ax * v(b["axial_slot_area_over_D2"])
    a_sw_face_img = n_sw * v(b["swirl_hole_area_over_D2"])
    a_sw_img = a_sw_face_img * math.cos(th)
    # split: m_ax / m_sw = (rho u A)_ax / (rho u A)_sw
    ratio = (rho_ax * u_ax * a_ax_img) / (rho_sw * u_sw * a_sw_img)
    m_ax = m_pa * ratio / (1.0 + ratio)
    m_sw = m_pa - m_ax
    A_ax = m_ax / (rho_ax * u_ax)
    A_sw = m_sw / (rho_sw * u_sw)                                # normal to the holes
    D_tip = math.sqrt(A_ax / a_ax_img)
    force = m_ax * u_ax + m_sw * u_sw
    force_axial = m_ax * u_ax + m_sw * u_sw * math.cos(th)

    # coal pipe: from the scale; its conveying air from the loading
    m_tr = v(b["fuel_flow"]) / v(b["transport_loading"])
    rho_tr = P_ATM * M_AIR / (R_GAS * T0)
    D_c = v(b["coal_pipe_D_over_D"]) * D_tip
    A_c = 0.25 * math.pi * D_c * D_c
    u_c = m_tr / (rho_tr * A_c)
    y_c = v(b["coal_pipe_offset_over_D"]) * D_tip

    # the openings
    A_slot = A_ax / n_ax
    asp = v(b["axial_slot_aspect"])
    w_s = math.sqrt(A_slot / asp)
    l_s = asp * w_s
    r_s = v(b["axial_ring_r_over_D"]) * D_tip
    tilt = math.radians(v(b["axial_slot_tilt"]))
    a_h = math.sqrt(A_sw / n_sw)                                 # hole side, normal to its axis
    r_h = v(b["swirl_ring_r_over_D"]) * D_tip

    t_pl = v(b["plate_t"])
    L_pl = v(b["plenum_L"])
    L_c = v(b["coal_pipe_L_over_D"]) * D_c
    clr = v(b["plenum_clearance"])
    dz = 0.01                                    # the openings reach this far into their plenum
    z_pl0, z_pl1 = -t_pl - L_pl, -t_pl

    bodies = []

    def add(name, group, kind, p, V, pts, rgb):
        xs, ys, zs = zip(*pts)
        bodies.append({"name": name, "group": group, "kind": kind, "p": tuple(p), "V": V,
                       "box": (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)), "rgb": rgb})

    def ring_pts(r0, r1, z0, z1):
        return [(-r1, -r1, z0), (r1, r1, z1)]

    C_COAL, C_AX, C_SW = (0.35, 0.25, 0.15), (0.1, 0.3, 0.8), (0.1, 0.6, 0.3)
    add("coal", "coal", "cyl", (0.0, y_c, -L_c, 0.0, 0.0, 1.0, 0.5 * D_c, L_c), A_c * L_c,
        [(-0.5 * D_c, y_c - 0.5 * D_c, -L_c), (0.5 * D_c, y_c + 0.5 * D_c, 0.0)], C_COAL)

    # axial slots: centres on the ring, the long side tilt off the tangent
    # (brochure: about 13 deg, turned the same way round the ring)
    slot_r = []
    for k in range(n_ax):
        psi = 2.0 * math.pi * k / n_ax + math.pi / 2.0          # one slot on top
        cx, cy = r_s * math.cos(psi), r_s * math.sin(psi)
        alpha = psi + math.pi / 2.0 - tilt
        ca, sa = math.cos(alpha), math.sin(alpha)
        corners = [(cx + ca * u - sa * w, cy + sa * u + ca * w)
                   for u in (-0.5 * l_s, 0.5 * l_s) for w in (-0.5 * w_s, 0.5 * w_s)]
        slot_r += [math.hypot(x, y) for x, y in corners]
        add(f"axial_slot_{k:02d}", "axial", "slot", (cx, cy, z_pl1 - dz, 0.0, l_s, w_s, alpha),
            l_s * w_s * (dz + t_pl), [(x, y, z) for x, y in corners for z in (z_pl1 - dz, 0.0)], C_AX)
    ax_r0, ax_r1 = min(slot_r) - clr, max(slot_r) + clr

    # swirl holes: square, inclined th towards +theta; cut by the planes
    hole_r = []
    for k in range(n_sw):
        psi = 2.0 * math.pi * (k + 0.5) / n_sw + math.pi / 2.0
        er = (math.cos(psi), math.sin(psi), 0.0)
        et = (-math.sin(psi), math.cos(psi), 0.0)
        d = (math.sin(th) * et[0], math.sin(th) * et[1], math.cos(th))
        e2 = (math.cos(th) * et[0], math.cos(th) * et[1], -math.sin(th))
        P = (r_h * er[0], r_h * er[1], 0.0)
        def corners(zc):
            # P + s1 a er + s2 a e2 + s d on the plane z = zc
            out = []
            for s1 in (-0.5, 0.5):
                for s2 in (-0.5, 0.5):
                    s = (zc - s2 * a_h * e2[2]) / d[2]
                    out.append(tuple(P[i] + s1 * a_h * er[i] + s2 * a_h * e2[i] + s * d[i] for i in range(3)))
            return out
        pts = corners(z_pl1 - dz) + corners(0.0)
        # the edges are chords: they dip inwards between their ends
        for j in range(11):
            hole_r += [math.hypot(p[0], p[1]) for p in corners(z_pl1 - dz + (dz + t_pl) * j / 10.0)]
        H = 2.0 * (t_pl + dz + a_h) / math.cos(th)
        add(f"swirl_hole_{k:02d}", "swirl", "hole", P + er + e2 + d + (a_h, H, z_pl1 - dz, 0.0),
            a_h * a_h / math.cos(th) * (dz + t_pl), pts, C_SW)
    sw_r0, sw_r1 = min(hole_r) - clr, max(hole_r) + clr

    for name, r0, r1, rgb in (("axial", ax_r0, ax_r1, C_AX), ("swirl", sw_r0, sw_r1, C_SW)):
        add(f"{name}_plenum", name, "ring", (r0, r1, z_pl0, z_pl1),
            math.pi * (r1 * r1 - r0 * r0) * L_pl, ring_pts(r0, r1, z_pl0, z_pl1), rgb)

    # the channels must not meet: coal pipe | swirl plenum | axial plenum
    r_coal_max = abs(y_c) + 0.5 * D_c
    walls = {"coal pipe to swirl plenum": sw_r0 - r_coal_max, "swirl to axial plenum": ax_r0 - sw_r1}
    for what, gap in walls.items():
        if gap < v(b["wall_min"]):
            raise ValueError(f"kiln_burner: {what} wall {gap * 1e3:.1f} mm, under {v(b['wall_min']) * 1e3:.0f} mm")
    if ax_r1 > 0.5 * D_tip:
        raise ValueError("kiln_burner: the axial plenum runs past the tip's outer D")

    groups = {}
    for grp, a_out, a_in, n_out in (
            ("coal", A_c, A_c, 1),
            ("axial", n_ax * l_s * w_s, math.pi * (ax_r1 ** 2 - ax_r0 ** 2), n_ax),
            ("swirl", n_sw * a_h * a_h / math.cos(th), math.pi * (sw_r1 ** 2 - sw_r0 ** 2), n_sw)):
        mine = [q for q in bodies if q["group"] == grp]
        bx = [q["box"] for q in mine]
        if grp == "coal":
            V = A_c * L_c
        else:   # plenum + each opening above it (the dz inside it counted once)
            V = sum(q["V"] for q in mine if q["kind"] == "ring") + a_out * t_pl
        groups[grp] = {"V": V, "n_out": n_out, "a_out": a_out, "a_in": a_in,
                       "box": tuple(min(q[i] for q in bx) for i in range(3)) + tuple(max(q[i] for q in bx) for i in range(3, 6))}

    return {
        "thermal_MW": q_th,
        "m_pa": m_pa,
        "m_axial": m_ax,
        "m_swirl": m_sw,
        "swirl_share": m_sw / m_pa,
        "m_transport": m_tr,
        "m_primary_total": m_pa + m_tr,
        "primary_total_share": (m_pa + m_tr) / v(b["kiln_air_flow"]),
        "u_axial": u_ax, "rho_axial": rho_ax, "T_axial": T_ax,
        "u_swirl": u_sw, "rho_swirl": rho_sw, "T_swirl": T_sw,
        "A_axial": A_ax, "A_swirl": A_sw, "A_swirl_face": n_sw * a_h * a_h / math.cos(th),
        "momentum_N": force,
        "momentum_per_MW": force / q_th,
        "momentum_axial_N": force_axial,
        "D_tip": D_tip,
        "D_coal": D_c, "y_coal": y_c, "A_coal": A_c, "u_coal": u_c, "rho_transport": rho_tr, "L_coal": L_c,
        "slot_l": l_s, "slot_w": w_s, "r_slots": r_s, "slot_tilt": tilt,
        "hole_a": a_h, "r_holes": r_h, "swirl_angle": th,
        "plate_t": t_pl, "plenum_L": L_pl,
        "axial_plenum": (ax_r0, ax_r1), "swirl_plenum": (sw_r0, sw_r1),
        "walls": walls,
        "bodies": bodies,
        "groups": groups,
    }



def kiln_burner_body(g):
    """The whole JETFLEX 2.0 burner as simple envelopes (user, 22 Nov 2026:
    a solid and a sheet of all of it; 23 Nov: the back end as the brochure
    cover's close-up; not a CFD input; kiln_burner_body.bas builds it).
    Frame as kiln_burner(): the tip plane z = 0, the burner back along -z,
    y up, x to the right seen from the kiln. Every length a ratio of the
    tip's outer D (brochure side view; the cover's details schematic)
    times kiln_burner()'s D_tip; the steel burner pipe's bore is the
    channels' axial plenum (the channel solid fits inside it).

    "bodies": [{name, group, kind, p, V, box, rgb}]; the macro joins a
    group's bodies into one body named after the group. Kinds:
      ring  p = (r0, r1, z0, z1)
      box   p = (x0, x1, y0, y1, z0, z1)
      cyl   p = (bx, by, bz, ax, ay, az, r, length)
      fbox  p = (cx, cy, cz, e1(3), e2(3), e3(3), a, b, c)  a box a x b x c
            along e1, e2, e3 centred on (cx, cy, cz)
      tube  p = cyl's + (r_in,)  a pipe, open at both ends
      tor   p = (C(3), u(3), w(3), R, r, r_in, angle)  a smooth pipe bend:
            the bore's centreline round C at R from C + R u, heading w
    A body named cut_* reaches past the rest of its group until the voids
    trim it (the group's extent leaves it out). A body named void_* is cut
    from its group once the group's other parts are joined: the bores through walls, so the pipes, the head and the
    expansion joint are open inside for the flow (user, 23 Nov 2026).
    "groups": {group: {box, V}} V the joined volume where the parts do not
    overlap and nothing is cut, None otherwise (the box: the parts' joint
    one, the cuts left out).
    """
    b = g["kiln_burner"]
    ch = kiln_burner(g)
    D = ch["D_tip"]

    def q(key):
        return v(b[f"body_{key}"]) * D

    r_in = ch["axial_plenum"][1]
    r_p = r_in + v(b["body_pipe_t"])
    R_tip, R_c = 0.5 * D, 0.5 * q("castable_D")
    if not r_p < R_c < R_tip:
        raise ValueError("kiln_burner_body: the steel pipe does not fit inside the castable")
    z_ring = -q("tip_ring_L")
    z_cast = -q("castable_L")
    z_pipe = z_cast - q("collar_L")
    z_fl = z_pipe - q("flange_L")
    z_head = z_fl - q("head_L")
    z_bel = z_head - q("bellows_L")
    z_coal = z_bel - q("coal_L")
    r_head = 0.5 * q("head_D")
    y_c = ch["y_coal"]
    t = q("plate_t")

    pt = v(b["body_pipe_t"])                  # the pipes' and the head's walls
    eps = 0.01                                # a cut's overshoot past the face it opens
    STEEL, CAST, PIPE = (0.45, 0.46, 0.48), (0.72, 0.66, 0.56), (0.55, 0.56, 0.58)
    bodies = []
    overlapping = set()
    hollow = set()

    def add(name, group, kind, p, V, pts, rgb):
        xs, ys, zs = zip(*pts)
        bodies.append({"name": name, "group": group or name, "kind": kind, "p": tuple(p), "V": V,
                       "box": (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)), "rgb": rgb})

    def ring(name, r0, r1, z0, z1, rgb, group=None):
        add(name, group, "ring", (r0, r1, z0, z1), math.pi * (r1 * r1 - r0 * r0) * (z1 - z0),
            [(-r1, -r1, z0), (r1, r1, z1)], rgb)

    def box(name, x0, x1, y0, y1, z0, z1, rgb, group=None):
        add(name, group, "box", (x0, x1, y0, y1, z0, z1), (x1 - x0) * (y1 - y0) * (z1 - z0),
            [(x0, y0, z0), (x1, y1, z1)], rgb)

    def cyl(name, base, axis, r, L, rgb, group=None):
        n = math.sqrt(sum(a * a for a in axis))
        ax = tuple(a / n for a in axis)
        # the extent of a cylinder: its ends' discs, r sqrt(1 - a_i^2) across each axis
        ext = [r * math.sqrt(max(0.0, 1.0 - a * a)) for a in ax]
        top = tuple(base[i] + L * ax[i] for i in range(3))
        pts = [tuple(c[i] + s * ext[i] for i in range(3)) for c in (base, top) for s in (-1, 1)]
        add(name, group, "cyl", tuple(base) + ax + (r, L), math.pi * r * r * L, pts, rgb)

    def fbox(name, c, e1, e2, e3, a, bb, cc, rgb, group=None):
        pts = [tuple(c[i] + s1 * 0.5 * a * e1[i] + s2 * 0.5 * bb * e2[i] + s3 * 0.5 * cc * e3[i] for i in range(3))
               for s1 in (-1, 1) for s2 in (-1, 1) for s3 in (-1, 1)]
        add(name, group, "fbox", tuple(c) + tuple(e1) + tuple(e2) + tuple(e3) + (a, bb, cc), a * bb * cc, pts, rgb)

    def tube(name, base, axis, r, L, r_in, rgb, group=None):
        """A pipe: cylinder r, bore r_in (open at both ends)."""
        n = math.sqrt(sum(a * a for a in axis))
        ax = tuple(a / n for a in axis)
        ext = [r * math.sqrt(max(0.0, 1.0 - a * a)) for a in ax]
        top = tuple(base[i] + L * ax[i] for i in range(3))
        pts = [tuple(c[i] + s * ext[i] for i in range(3)) for c in (base, top) for s in (-1, 1)]
        add(name, group, "tube", tuple(base) + ax + (r, L, r_in), math.pi * (r * r - r_in * r_in) * L, pts, rgb)

    def void(name, base, axis, r, L, group):
        """Cut out of its group once the group's parts are joined (the
        bores through walls: the inside open for the flow)."""
        cyl("void_" + name, base, axis, r, L, (0.0, 0.0, 0.0), group)
        hollow.add(group)

    def bend(name, group, P, d0, d1, R, r, r_in, rgb, th=0.5 * math.pi):
        """A smooth pipe bend (a torus' part, bore r_in) through th from P
        heading d0, turning towards d1 (unit, normal: at 90 deg it heads
        d1), centreline radius R; returns its end point. tor p = (C, u, w,
        R, r, r_in, angle): the bend's centre C, u from C to its start, w
        its heading there."""
        C = tuple(P[i] + R * d1[i] for i in range(3))
        u = tuple(-x for x in d1)
        w = d0
        y = (w[1] * u[2] - w[2] * u[1], w[2] * u[0] - w[0] * u[2], w[0] * u[1] - w[1] * u[0])   # w x u
        lo, hi = [1e30] * 3, [-1e30] * 3
        for k in range(2001):
            tt = th * k / 2000
            for i in range(3):
                gi = math.cos(tt) * u[i] + math.sin(tt) * d0[i]
                s = r * math.sqrt(gi * gi + y[i] * y[i])
                lo[i] = min(lo[i], C[i] + R * gi - s)
                hi[i] = max(hi[i], C[i] + R * gi + s)
        add(name, group, "tor", tuple(C) + u + tuple(d0) + (R, r, r_in, th),
            math.pi * (r * r - r_in * r_in) * R * th, [tuple(lo), tuple(hi)], rgb)
        return tuple(C[i] + R * (math.cos(th) * u[i] + math.sin(th) * d0[i]) for i in range(3))

    # the castable, the steel pipe, the castable's flange
    ring("tip_ring", r_p, R_tip, z_ring, 0.0, CAST)
    ring("castable", r_p, R_c, z_cast, z_ring, CAST)
    ring("burner_pipe", r_in, r_p, z_pipe, 0.0, STEEL)
    # (its bore the steel pipe's: the head opens into the pipe)
    tube("flange", (0.0, 0.0, z_fl), (0.0, 0.0, 1.0), 0.5 * q("flange_D"), z_pipe - z_fl, r_in, STEEL)

    # the tip's other tubes (brochure p. 5, fixed nozzles; seen from the
    # kiln): the fuel lance under the solid fuel channel, the flame scanner
    # (-x) and the igniter (+x) either side; from the tip plane back
    # through the steel pipe, the head and the expansion joint, out through
    # its back wall (p. 4: "the expansion joint for guiding fuel injection
    # pipes"), ending lance_tail behind it (p. 3 side view); on the front
    # plate's solid part (clear of the channels: no CFD effect, no flow in
    # the twin), clear of the coal inlet behind the joint; pipes, open
    tips = (("fuel_lance", 0.0, q("lance_y"), 0.5 * q("lance_D")),
            ("flame_scanner", -q("scanner_x"), q("scanner_y"), 0.5 * q("scanner_D")),
            ("igniter", q("scanner_x"), q("scanner_y"), 0.5 * q("scanner_D")))
    for name, x_t, y_t, r_t in tips:
        if math.hypot(x_t, y_t - y_c) < 0.5 * ch["D_coal"] + r_t or math.hypot(x_t, y_t) + r_t > ch["swirl_plenum"][0]:
            raise ValueError(f"kiln_burner_body: the {name} cuts a channel")
        if math.hypot(x_t, y_t - y_c) < 0.5 * q("coal_D") + r_t:
            raise ValueError(f"kiln_burner_body: the {name} runs into the coal inlet behind the expansion joint")
        z_t0 = z_bel - q("lance_tail")
        tube(name, (x_t, y_t, z_t0), (0.0, 0.0, 1.0), r_t, -z_t0, r_t - min(pt, 0.3 * r_t), PIPE)

    # front support plate: a ring round the bare pipe in front of the
    # flange, a neck up to the beam, down to a foot plate under the pipe
    y_b, h_b, w_b = q("beam_y"), q("beam_H"), 0.5 * q("beam_W")
    R_s, w_s = 0.5 * q("support_D"), 0.5 * q("support_W")
    zs0, zs1 = z_pipe, z_pipe + t
    ring("support_ring", r_p, R_s, zs0, zs1, STEEL, "support")
    box("support_neck", -w_s, w_s, 0.8 * R_s, y_b, zs0, zs1, STEEL, "support")
    y_f = -q("foot_y")
    box("support_leg", -w_s, w_s, y_f, -0.8 * R_s, zs0, zs1, STEEL, "support")
    w_f = 0.5 * q("foot_W")
    box("support_foot", -w_f, w_f, y_f - t, y_f, zs0, zs0 + q("foot_L"), STEEL, "support")

    # the air connection head and its bolting flanges
    r_hf = 0.5 * q("head_flange_D")
    ring("head_flange_front", r_head, r_hf, z_fl - t, z_fl, STEEL)
    ring("head_flange_rear", r_head, r_hf, z_head, z_head + t, STEEL)
    # the expansion joint: a shell open into the head, its back wall
    # through to the coal inlet
    t_cf = q("flange_L")
    r_ci = 0.5 * q("coal_D")
    r_bel = 0.5 * q("bellows_D")
    tube("bellows", (0.0, 0.0, z_bel), (0.0, 0.0, 1.0), r_bel, z_head - z_bel, r_bel - pt, STEEL)
    cyl("bellows_back", (0.0, 0.0, z_bel), (0.0, 0.0, 1.0), r_bel - 0.5 * pt, pt, STEEL, "bellows")
    for name, x_t, y_t, r_t in tips:       # the tip tubes' holes through its back wall (2 mm clear)
        void(f"bellows_{name}", (x_t, y_t, z_bel - eps), (0.0, 0.0, 1.0), r_t + 0.002, pt + 2 * eps, "bellows")
    void("bellows_back", (0.0, y_c, z_bel - eps), (0.0, 0.0, 1.0), r_ci - pt, pt + 2 * eps, "bellows")

    # the coal inlet (the brochure's side view and its alternative-fuel
    # close-up): straight back from the expansion joint, a smooth long
    # radius bend up through coal_tilt_deg coal_kink_at in front of its
    # flange, straight on to the flange, square to it; its cooling air
    # nozzle on the tilted piece; pipes, open. The burner's back end
    # (z_coal, L_total) is the flange's back face at its centre (its lower
    # edge reaches r_cf sin(tilt) further back).
    th_c = math.radians(v(b["body_coal_tilt_deg"]))
    R_k = v(b["body_bend_R_over_OD"]) * 2.0 * r_ci
    r_cf = 0.5 * q("coal_flange_D")
    dc = (0.0, math.sin(th_c), -math.cos(th_c))           # the tilted piece's heading (back, up)
    nc = (0.0, math.cos(th_c), math.sin(th_c))            # square to it, up
    z_E = z_coal                                          # the flange's back face, at its centre
    z_B = z_E + q("coal_kink_at")                         # where the bend starts
    if not z_B < z_bel:
        raise ValueError("kiln_burner_body: the coal pipe's bend lies in the expansion joint")
    tube("coal_inlet", (0.0, y_c, z_B), (0.0, 0.0, 1.0), r_ci, z_bel - z_B, r_ci - pt, PIPE, "coal")
    Pk = bend("coal_bend", "coal", (0.0, y_c, z_B), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0), R_k, r_ci, r_ci - pt, PIPE,
              th_c)
    L2 = (Pk[2] - z_E) / math.cos(th_c)                   # the tilted piece, its flange included
    if L2 <= t_cf + q("nozzle_at") + q("nozzle_D"):
        raise ValueError("kiln_burner_body: the coal pipe's tilted piece is too short for its nozzle")
    E = tuple(Pk[i] + L2 * dc[i] for i in range(3))
    tube("coal_tail", Pk, dc, r_ci, L2 - t_cf, r_ci - pt, PIPE, "coal")
    F0 = tuple(E[i] - t_cf * dc[i] for i in range(3))
    tube("coal_inlet_flange", F0, dc, r_cf, t_cf, r_ci - pt, PIPE, "coal")
    # the nozzle: square to the tilted piece, out to -x like the air
    # elbow's neck, tilted up by nozzle_deg (user)
    r_n = 0.5 * q("nozzle_D")
    a_n = math.radians(v(b["body_nozzle_deg"]))
    A = tuple(F0[i] - q("nozzle_at") * dc[i] for i in range(3))   # its axis on the pipe's
    na = tuple(-math.cos(a_n) * (1.0 if i == 0 else 0.0) + math.sin(a_n) * nc[i] for i in range(3))
    nb = tuple(A[i] + 0.5 * r_ci * na[i] for i in range(3))
    tube("coal_nozzle", nb, na, r_n, q("nozzle_L") + 0.5 * r_ci, r_n - pt, PIPE, "coal")
    void("coal_nozzle", nb, na, r_n - pt, r_ci, "coal")      # out through the coal pipe's wall (0.5 r_ci)
    # the tilted piece's bore again (through the flange), clearing the
    # nozzle's stub inside it
    void("coal_bore", Pk, dc, r_ci - pt, L2 + eps, "coal")

    # air inlet 1, the elbow: a short neck straight out of the head's -x
    # side (at right angles to it), one smooth 90 deg bend up to a flange
    # (user, 23 Nov 2026: out of the main body at right angles, one bend).
    # On the -x side (the brochure's side view: tip right, the elbow in
    # front -- a view from -x). Welded to the head: one body with it.
    r_e = 0.5 * q("inlet1_D")
    R_b = v(b["body_bend_R_over_OD"]) * 2.0 * r_e     # a long radius elbow: the air passes easily
    r_ei = r_e - pt
    y_e = q("elbow_y")
    if abs(y_e) + r_e >= r_head:
        raise ValueError("kiln_burner_body: the elbow is wider than the head")
    z_up = z_fl - q("elbow_up_at")
    x0 = -0.5 * r_head                         # the neck's inner end, inside the head
    x_b = -(r_head + q("elbow_neck_L"))        # the bend's start: the neck's length off the head
    tube("elbow_leg", (x0, y_e, z_up), (-1.0, 0.0, 0.0), r_e, x0 - x_b, r_ei, PIPE, "head")
    P2 = bend("elbow_bend", "head", (x_b, y_e, z_up), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), R_b, r_e, r_ei, PIPE)
    x_leg = P2[0]
    y_fl = P2[1]                               # the flange straight on the bend's end
    y_top = y_fl + t
    tube("elbow_flange", (x_leg, y_fl, z_up), (0.0, 1.0, 0.0), 1.35 * r_e, t, r_ei, PIPE, "head")

    # the head after the elbow in its group (the elbow joined first, then
    # onto it); its shell open at both ends (the flange's bore in front,
    # the expansion joint behind)
    cyl("head", (0.0, 0.0, z_head), (0.0, 0.0, 1.0), r_head, z_fl - z_head, STEEL, "head")
    void("head", (0.0, 0.0, z_head - eps), (0.0, 0.0, 1.0), r_head - pt, z_fl - z_head + 2 * eps, "head")
    # the neck's bore through the head's wall
    void("elbow_leg", (x0, y_e, z_up), (-1.0, 0.0, 0.0), r_ei, x0 - x_b - 0.5 * t, "head")

    # air inlet 2: a flanged stub further back, open into the head
    r2, z2 = 0.5 * q("inlet2_D"), z_fl - q("inlet2_at")
    reach = q("inlet_reach")
    x0 = -0.5 * r_head                         # its inner end, inside the head
    tube("air_inlet_2", (x0, 0.0, z2), (-1.0, 0.0, 0.0), r2, r_head + reach + x0, r2 - pt, PIPE, "head")
    void("air_inlet_2", (x0, 0.0, z2), (-1.0, 0.0, 0.0), r2 - pt, r_head + reach + x0 - 0.5 * t, "head")
    tube("air_inlet_2_flange", (-r_head - reach, 0.0, z2), (-1.0, 0.0, 0.0), 1.3 * r2, t, r2 - pt, PIPE, "head")

    # inside the steel pipe (brochure p. 4: two air systems, axial and
    # swirl; the solid fuel through one straight, uninterrupted pipe): the
    # concentric tubes that carry the head's two compartments to the
    # channel solid's plenums, and the common fuel pipe to its coal pipe.
    #   axial air: air inlet 1 (the elbow) -> the front compartment (head
    #     front .. partition, outside the swirl tube) -> the flange's bore
    #     -> the annulus swirl tube .. steel pipe -> the axial plenum
    #   swirl air: air inlet 2 -> the back compartment (partition ..
    #     expansion joint's back wall, outside the core tube) -> the
    #     annulus core tube .. swirl tube (open at its back end) -> the
    #     swirl plenum
    #   the core (inside the core tube) shut to the air: the fuel pipe and
    #   the tip's tubes run through it
    # Which inlet feeds which: a model assumption (not shown; the outer
    # annulus from the front compartment, the larger inlet for the larger
    # axial share). The tubes' radii are the plenums', so they meet them.
    sw0, sw1 = ch["swirl_plenum"]
    ax0, ax1 = ch["axial_plenum"]
    if abs(ax1 - r_in) > 1e-9:
        raise ValueError("kiln_burner_body: the steel pipe's bore is not the axial plenum's outer wall")
    z_pl = -(ch["plate_t"] + ch["plenum_L"])               # the plenums' back face
    z_c0 = z_bel + pt                                      # the expansion joint's back wall, front face
    r_fo = 0.5 * ch["D_coal"] + pt                         # the fuel pipe's outer radius
    reach_in = max([abs(y_c) + r_fo] + [math.hypot(x_t, y_t) + r_t for _, x_t, y_t, r_t in tips])
    if reach_in >= sw0 - pt:
        raise ValueError("kiln_burner_body: the fuel pipe or the tip's tubes leave the core tube")
    tube("core_tube", (0.0, 0.0, z_c0), (0.0, 0.0, 1.0), sw0, z_pl - z_c0, sw0 - pt, STEEL)
    z_part = z_fl - q("partition_at")
    if not (z2 + 1.3 * r2 < z_part - 0.5 * t and z_part + 0.5 * t < z_up - r_e):
        raise ValueError("kiln_burner_body: the head's partition does not sit between its two inlets")
    tube("swirl_tube", (0.0, 0.0, z_part - 0.5 * t), (0.0, 0.0, 1.0), ax0, z_pl - z_part + 0.5 * t, sw1, STEEL)
    ring("head_partition", ax0, r_head - pt, z_part - 0.5 * t, z_part + 0.5 * t, STEEL)   # touching the shell, not in it
    tube("fuel_pipe", (0.0, y_c, z_c0), (0.0, 0.0, 1.0), r_fo, -ch["L_coal"] - z_c0, 0.5 * ch["D_coal"], PIPE)

    # the carriage beam: two channels back to back (webs inside, open
    # outward), a diagonal stiffener in each, an end plate and pins at the front
    zb0, zb1 = z_pipe - q("beam_L"), z_pipe
    g2 = 0.5 * q("web_gap")
    # (the end plate first: both channels touch it, so the group joins)
    box("beam_end", -w_b, w_b, y_b, y_b + h_b, zb1, zb1 + t, STEEL, "beam")
    for sgn, side in ((1, "R"), (-1, "L")):
        xw0, xw1 = sorted((sgn * g2, sgn * (g2 + t)))
        xf0, xf1 = sorted((sgn * g2, sgn * w_b))
        box(f"beam_web_{side}", xw0, xw1, y_b, y_b + h_b, zb0, zb1, STEEL, "beam")
        box(f"beam_top_{side}", xf0, xf1, y_b + h_b - t, y_b + h_b, zb0, zb1, STEEL, "beam")
        box(f"beam_bot_{side}", xf0, xf1, y_b, y_b + t, zb0, zb1, STEEL, "beam")
        # the diagonal plate joining the two flanges across the channel's
        # open side (welded to their edges), leaning at brace_deg, its ends
        # cut level with the flanges' outer faces: a plate long enough to
        # reach past them (cut_: its own extent is not the beam's), the
        # overshoot cut off by the two boxes over and under the beam
        al = math.radians(v(b["body_brace_deg"]))
        w_p = q("brace_W")
        L_br = (h_b + w_p * math.cos(al)) / math.sin(al) + 2 * t
        e1 = (0.0, math.sin(al), math.cos(al))
        e2 = (0.0, -math.cos(al), math.sin(al))
        xp0, xp1 = sorted((sgn * (w_b - t), sgn * w_b))
        zc = zb1 - q("brace_at")                   # its middle, back from the beam's front end
        fbox(f"cut_beam_brace_{side}", (0.5 * (xp0 + xp1), y_b + 0.5 * h_b, zc), e1, e2, (1.0, 0.0, 0.0),
             L_br, w_p, t, STEEL, "beam")
        zr = 0.5 * L_br
        for k, (y0, y1) in enumerate(((y_b + h_b, y_b + h_b + L_br), (y_b - L_br, y_b))):
            box(f"void_beam_brace_{side}{k}", xp0 - eps, xp1 + eps, y0, y1, zc - zr - eps, zc + zr + eps,
                (0.0, 0.0, 0.0), "beam")
    # at the beam's back end a rectangular plate over each channel's open
    # side, welded to its flanges' edges (user, 23 Nov 2026)
    for sgn, side in ((1, "R"), (-1, "L")):
        xp0, xp1 = sorted((sgn * (w_b - t), sgn * w_b))
        box(f"beam_tail_plate_{side}", xp0, xp1, y_b, y_b + h_b, zb0, zb0 + q("beam_tail_L"), STEEL, "beam")
    r_pin, L_pin = 0.5 * q("pin_D"), q("pin_L")
    for sgn, side in ((1, "R"), (-1, "L")):
        # from the web out through the channel's open side
        cyl(f"beam_pin_{side}", (sgn * (g2 + t), y_b + 0.5 * h_b, zb1 - 0.3 * h_b), (sgn, 0.0, 0.0), r_pin,
            w_b - g2 - t + L_pin, STEEL, "beam")
    overlapping.update(("support", "beam"))      # the neck over the ring; the webs under the flanges
    z1 = z_fl - q("hanger2_at")
    box("hanger", -w_b, w_b, r_head, y_b, z1 - q("hanger2_L"), z1, STEEL)

    groups = {}
    for x in bodies:
        groups.setdefault(x["group"], []).append(x)
    G = {}
    hollow.add("beam")

    def counts(x):       # the cuts lie inside or overshoot a face; a cut_ part is cut back inside the rest
        return not x["name"].startswith(("void_", "cut_"))
    solid = [x for x in bodies if counts(x)]
    for name, xs in groups.items():
        bx = [x["box"] for x in xs if counts(x)]
        G[name] = {"box": tuple(min(q_[i] for q_ in bx) for i in range(3)) + tuple(max(q_[i] for q_ in bx) for i in range(3, 6)),
                   "V": None if name in overlapping | hollow else sum(x["V"] for x in xs), "n": len(xs)}
    lo = [min(x["box"][i] for x in solid) for i in range(3)]
    hi = [max(x["box"][i] for x in solid) for i in range(3, 6)]
    return {
        "D_tip": D, "r_pipe_in": r_in, "r_pipe": r_p, "R_castable": R_c,
        "L_total": -z_coal, "z_ring": z_ring, "z_castable": z_cast, "z_pipe": z_pipe,
        "z_flange": z_fl, "z_head": z_head, "z_bellows": z_bel, "z_coal": z_coal,
        "r_head": r_head, "r_head_flange": r_hf, "x_elbow": x_leg, "z_elbow_up": z_up, "y_elbow_top": y_top,
        "z_inlet2": z2, "y_coal_flange": E[1], "z_partition": z_part, "z_plenums": z_pl, "x_inlet2": -(r_head + reach + t),
        "bodies": bodies, "groups": G, "box": tuple(lo + hi),
    }

# ======================================================================
# The kiln hood and the kiln inlet chamber: gas velocity checks
# ======================================================================
def kiln_air_split(g):
    """The kiln's air (kiln_burner.kiln_air_flow) split as the twin splits
    it (main._update_steady_state_mass_flow): primary (the burner's axial +
    swirl air), the outlet seal's cold leak, the cooler's secondary air
    (the rest). The coal's conveying air is on top (kiln_burner(); not in
    the twin: an open finding)."""
    b, h = g["kiln_burner"], g["kiln_hood"]
    m = v(b["kiln_air_flow"])
    f_pa, f_seal = v(b["primary_air_fraction"]), v(h["seal_air_fraction"])
    if not 0.0 <= f_seal < 1.0 - f_pa:
        raise ValueError("kiln_air_split: the seal leak leaves no secondary air")
    return {"kiln": m, "primary": f_pa * m, "seal": f_seal * m,
            "secondary": (1.0 - f_pa - f_seal) * m}


def kiln_hood(g):
    """The hood as a box on the cooler round the kiln's end (user decision,
    23 Nov 2026: sized from the kiln's outlet seal). Its back wall, the
    vertical plane through the kiln's end, closes round the ROTAX outlet
    seal (its outer radius plus seal_clearance either side and over it;
    under the kiln the cooler's back wall closes it); it stands on the
    cooler's roof (cooler_drop under the kiln's bore) and runs over the
    cooler's hood opening (its depth). Beside the cooler's width its floor
    is a hopper (hopper_angle up from the cooler's edges to its side walls;
    Fuller's ABC Inlet). The air through it is the
    secondary air and the tertiary air; at the tertiary air's temperature
    (and at the hotter secondary air's) the velocity over its section
    (width x height) is held to the literature's range. The secondary air
    is the kiln's air less the primary air and the seal's leak (as the
    twin splits it; kiln_air_split())."""

    h = g["kiln_hood"]
    kl, co = kiln(g), cooler(g)
    seal = next(b for b in kiln_rotax(g)["bodies"] if b["name"] == "outlet_seal")
    R_seal = seal["p"][1]
    half_w = R_seal + v(h["seal_clearance"])
    below = 0.5 * kl["D"] + v(g["layout"]["cooler_drop"])      # the kiln's axis over the cooler's roof
    W, H, depth = 2.0 * half_w, below + half_w, co["hood_L"]
    bnd = calciner_boundaries(g)["tertiary_air_inlet"]
    m = bnd["flow"] + kiln_air_split(g)["secondary"]
    # the hopper: the floor beside the cooler's width, each side a wall at
    # hopper_angle from the cooler's edge up to the hood's side wall
    th = math.radians(v(h["hopper_angle"]))
    dw = 0.5 * (W - co["width"])
    rise = dw * math.tan(th)
    if dw < 0.0 or rise >= H:
        raise ValueError("kiln_hood: the hopper does not fit (the hood narrower than the cooler, or too low)")
    R = 0.5 * kl["D"]
    gap = min(below - math.sqrt(max(0.0, R * R - x * x)) - (x - 0.5 * co["width"]) * math.tan(th)
              for x in [0.5 * co["width"] + i * (min(R, 0.5 * W) - 0.5 * co["width"]) / 50 for i in range(51)])
    if gap <= 0.0:
        raise ValueError("kiln_hood: the hopper's wall cuts into the kiln's bore")
    area = W * H - dw * rise                       # less the two triangles under the hopper's walls

    def vel(T):
        rho = 101325.0 * bnd["M"] / (R_GAS * T)
        return m / rho / area

    vmax = v(h["air_velocity_max"])
    rho = bnd["rho"]
    return {
        "m": m,
        "rho": rho,
        "q": m / rho,
        "R_seal": R_seal,
        "W": W, "H": H, "depth": depth,
        "above": half_w, "below": below,     # the roof over, the floor under the kiln's axis
        "area": area, "area_box": W * H,
        "hopper_angle": th, "hopper_dw": dw, "hopper_rise": rise, "hopper_gap": gap,
        "u": vel(bnd["T"]),
        "u_hot": vel(v(h["secondary_air_T"])),
        "area_min": m / rho / vmax,
        "u_min": v(h["air_velocity_min"]),
        "u_max": vmax,
    }


def kiln_bed(g):
    """The clinker bed over the burning zone, as the flame volume's floor
    (user decision, 23 Nov 2026). Fill by continuity: the clinker flow
    times its transit through the zone (Sullivan, as the twin:
    tau = 1.77 L sqrt(theta) / (D N beta_deg) min, the zone's share by
    length) over the bulk density, as a share of the bore. The bed is a
    circular segment; its flat surface lies at the dynamic angle of repose
    to the plant's horizontal, rising to the bed_rise_side (kiln frame, the
    slope not built in, as the kiln's solids).

    n: the surface's normal into the gas; t: along the surface across the
    kiln; d_c: the surface from the axis; c: its half chord; phi: the
    segment's angle; fill: its share of the bore's section."""
    k = g["kiln"]
    kl = kiln(g)
    L, D, R = kl["L"], kl["D"], 0.5 * kl["D"]
    th = math.radians(v(k["repose_angle"]))
    beta = math.degrees(math.atan(0.01 * kl["slope"]))
    tau = 1.77 * L * math.sqrt(math.degrees(th)) / (D * v(k["rpm"]) * beta) * 60.0      # s
    L_bz = kl["burning_L"]
    tau_bz = tau * L_bz / L
    A = math.pi * R * R
    fill = v(k["clinker_flow"]) * tau_bz / v(k["clinker_bulk_density"]) / (L_bz * A)
    if not 0.0 < fill < 0.5:
        raise ValueError(f"kiln_bed: fill {fill:.3f} outside (0, 0.5)")
    lo, hi = 0.0, math.pi                       # (phi - sin phi) / (2 pi) = fill
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if (mid - math.sin(mid)) / (2.0 * math.pi) < fill:
            lo = mid
        else:
            hi = mid
    phi = 0.5 * (lo + hi)
    sd = v(k["bed_rise_side"])
    n = (-sd * math.sin(th), math.cos(th), 0.0)
    t = (math.cos(th), sd * math.sin(th), 0.0)
    return {
        "tau": tau, "tau_bz": tau_bz, "fill": fill, "phi": phi,
        "d_c": R * math.cos(0.5 * phi), "c": R * math.sin(0.5 * phi),
        "A_bed": fill * A, "A_gas": (1.0 - fill) * A, "n": n, "t": t, "theta": th,
        "z0": L - L_bz, "z1": L,
    }


def kiln_burner_placement(g):
    """The burner in the kiln's mouth (literature, kiln_hood.burner_*): its
    tip burner_insertion inside the kiln's end, on (offset from) the
    kiln's axis, parallel to it (tilted down towards the load by
    burner_tilt_deg). Kiln frame (kiln()): axis z, the hood end at z = L,
    y up. The burner's own frame (kiln_burner()): tip at z = 0, the burner
    back along -z, firing towards +z, y up.

    "R" (rows: the burner's x, y, z axes in the kiln frame) and "t" (the
    tip): p_kiln = t + R^T p_burner. It fires up the kiln (-z): the
    burner's +z goes to -z, so its x to -x (a turn about y), then the tilt
    about x.

    Checked: the castable (refractory) covers the burner pipe all through
    the hood, so no bare steel stands in the hot gas (the castable's back
    end past the hood's front wall along the burner's axis)."""
    h = g["kiln_hood"]
    kl, hd, body = kiln(g), kiln_hood(g), kiln_burner_body(g)
    th = math.radians(v(h["burner_tilt_deg"]))
    c, s = math.cos(th), math.sin(th)
    R = ((-1.0, 0.0, 0.0), (0.0, c, -s), (0.0, -s, -c))
    tip = (v(h["burner_offset_x"]), v(h["burner_offset_y"]), kl["L"] - v(h["burner_insertion"]))

    def to_kiln(p):
        return tuple(tip[i] + sum(R[k][i] * p[k] for k in range(3)) for i in range(3))

    alpha = math.atan(0.01 * kl["slope"])
    # the hood's front wall (vertical, depth on from the kiln's end) on the burner's axis
    z_front = kl["L"] + hd["depth"] / math.cos(alpha)
    z_cast_end = to_kiln((0.0, 0.0, body["z_castable"]))[2]
    if z_cast_end <= z_front:
        raise ValueError(f"kiln_burner_placement: the castable ends at z {z_cast_end:.3f}, inside the hood "
                         f"(its front wall at {z_front:.3f}): bare steel in the hot gas")
    if math.hypot(tip[0], tip[1]) + 0.5 * body["D_tip"] >= 0.5 * kl["D"]:
        raise ValueError("kiln_burner_placement: the burner's tip touches the kiln's lining")
    return {"R": R, "tip": tip, "tilt": th, "to_kiln": to_kiln, "z_front": z_front,
            "z_castable_end": z_cast_end, "castable_past_front": z_cast_end - z_front}


def kiln_flame(g):
    """The flame zone's CFD fluid volume (user decision, 23 Nov 2026): the
    hood's inside, the kiln's bore from its end back over the burning zone
    (kiln.burning_L: where the twin releases the fuel's heat, so the
    flame ends inside it; no literature flame length was found), and the
    burner's channels (kiln_burner.SLDPRT, placed by
    kiln_burner_placement; the macro copies them in), less the burner
    itself (its tip ring and castable) in the hood and the kiln.

    Kiln frame (kiln()). The hood is level and the kiln falls at its
    slope towards its end: in the kiln frame the plant's horizontal
    (towards the cooler) is (0, sin a, cos a) and its up (0, cos a, -sin a).
    The bore runs on R tan a past the kiln's end so it meets the hood's
    vertical back wall all round.

    Not modelled (CLAUDE.md rule 10, kiln_flame.md): the clinker bed's
    material (the bore is all gas, user decision 23 Nov 2026; the strip of
    wall under it is a region given the bed's temperature: "bed_strip"), doors,
    refractory detail, the seal's leak air (it enters with the secondary air).

    "bodies" as kiln_burner_body(): kinds cyl/fbox; void_* cut from the
    group once joined. "faces": the boundaries, each a point inside it,
    its outward normal and its area (the macro names and paints them;
    every other face is wall)."""
    kl, hd, co = kiln(g), kiln_hood(g), cooler(g)
    ch, body, pl = kiln_burner(g), kiln_burner_body(g), kiln_burner_placement(g)
    alpha = math.atan(0.01 * kl["slope"])
    sa, ca = math.sin(alpha), math.cos(alpha)
    Hd, U, X = (0.0, sa, ca), (0.0, ca, -sa), (1.0, 0.0, 0.0)
    L, R = kl["L"], 0.5 * kl["D"]
    K = (0.0, 0.0, L)

    def at(h, u, x=0.0):           # the plant's horizontal h, up u, across x from the kiln's end
        return tuple(K[i] + h * Hd[i] + u * U[i] + x * X[i] for i in range(3))

    bodies = []

    def add(name, kind, p, pts, V, rgb=(0.85, 0.35, 0.1)):
        xs, ys, zs = zip(*pts)
        bodies.append({"name": name, "group": "flame", "kind": kind, "p": tuple(p), "V": V,
                       "box": (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)), "rgb": rgb})

    def fbox(name, c, e1, e2, e3, a, b, cc):
        pts = [tuple(c[i] + s1 * 0.5 * a * e1[i] + s2 * 0.5 * b * e2[i] + s3 * 0.5 * cc * e3[i] for i in range(3))
               for s1 in (-1, 1) for s2 in (-1, 1) for s3 in (-1, 1)]
        add(name, "fbox", tuple(c) + tuple(e1) + tuple(e2) + tuple(e3) + (a, b, cc), pts, a * b * cc)

    def cyl(name, base, ax, r, Lc):
        ext = [r * math.sqrt(max(0.0, 1.0 - a * a)) for a in ax]
        top = tuple(base[i] + Lc * ax[i] for i in range(3))
        pts = [tuple(cc[i] + sg * ext[i] for i in range(3)) for cc in (base, top) for sg in (-1, 1)]
        add(name, "cyl", tuple(base) + tuple(ax) + (r, Lc), pts, math.pi * r * r * Lc)

    W, H, depth, above, below = hd["W"], hd["H"], hd["depth"], hd["above"], hd["below"]
    fbox("hood", at(0.5 * depth, 0.5 * (above - below)), Hd, U, X, depth, H, W)
    # the kiln's bore over the burning zone, on past its end to the back wall
    z_cut = L - kl["burning_L"]
    cyl("kiln_bore", (0.0, 0.0, z_cut), (0.0, 0.0, 1.0), R, kl["burning_L"] + R * math.tan(alpha) * 1.001)
    # the cooler's two hood segments: the hood's flat floor between the
    # hopper's feet (cooler width), split across at one segment into two
    # faces (the macro's split line "floor_split"); no stubs (user, 23 Nov 2026)
    seg, cw = co["segment_L"], co["width"]
    if abs(depth - 2.0 * seg) > 1e-6:
        raise ValueError("kiln_flame: the hood's floor is the cooler's two hood segments (depth = 2 segments)")
    faces = []
    for k in (1, 2):
        faces.append((("secondary_air_in", "tertiary_supply_in")[k - 1], at((k - 0.5) * seg, -below), tuple(-u for u in U),
                      seg * cw, ((1.0, 0.55, 0.0), (0.95, 0.8, 0.1))[k - 1]))
    floor_split = (at(seg, -below, -0.5 * cw - 0.5), at(seg, -below, 0.5 * cw + 0.5))
    # the hopper (kiln_hood()): either side a box cut out of the hood's
    # bottom corner, one face in the hopper's wall (from the cooler's edge
    # on the floor up at hopper_angle), the rest outside the hood
    th = hd["hopper_angle"]
    ct, sn = math.cos(th), math.sin(th)
    L_w, T_w = hd["hopper_dw"] / ct + 1.0, hd["hopper_dw"] * sn + 1.5
    for s_, nm in ((1.0, "void_hopper_p"), (-1.0, "void_hopper_m")):
        t = tuple(s_ * ct * X[i] + sn * U[i] for i in range(3))      # up the wall
        n = tuple(s_ * sn * X[i] - ct * U[i] for i in range(3))      # out of the fluid
        foot = at(0.5 * depth, -below, s_ * 0.5 * cw)
        c = tuple(foot[i] + 0.5 * L_w * t[i] + 0.5 * T_w * n[i] for i in range(3))
        fbox(nm, c, Hd, t, n, depth + 2.0, L_w, T_w)
    # the tertiary air duct's mouth on the roof, over segment 2
    r_ta = 0.5 * calciner_inlets(g)["tertiary_air"]["D"]
    h_ta = co["hood_L"] - 0.5 * seg
    if h_ta + r_ta > depth or h_ta - r_ta < 0.0:
        raise ValueError("kiln_flame: the tertiary air mouth does not fit on the hood's roof")
    # its first run straight up, L_ta long (model: the outlet clear of the hood's recirculation)
    L_ta = v(g["kiln_hood"]["tertiary_outlet_L_over_D"]) * 2.0 * r_ta
    cyl("tertiary_air_mouth", at(h_ta, above - 0.001), U, r_ta, L_ta + 0.001)
    faces.append(("tertiary_air_out", at(h_ta, above + L_ta), U, math.pi * r_ta * r_ta, (0.6, 0.2, 0.8)))
    # the clinker bed: no material in the volume (user decision, 23 Nov 2026:
    # the bore whole, as CEMCAP/SINTEF's kiln CFD). The strip of the bore's
    # wall under the bed (its chord, kiln_bed()) is a region the CFD gives
    # the bed's temperature (a position expression on the wall, or the wall
    # separated by a cell mark): SolidWorks merges a split made by cutting
    # and filling back (tried 23 Nov 2026), so it is not a face of the solid.
    bd = kiln_bed(g)
    arc = 2.0 * R * math.asin(bd["c"] / R)
    bed_strip = {"n": bd["n"], "t": bd["t"], "d_c": bd["d_c"], "c": bd["c"], "arc": arc,
                 "z0": z_cut, "z1": L, "area": arc * (L - z_cut),
                 # a wall point is on the strip when its distance along -n from the axis is over d_c
                 "rule": "-(n . p) > d_c, z_cut <= z <= L"}
    faces.append(("kiln_gas_out", (0.0, 0.0, z_cut), (0.0, 0.0, -1.0), math.pi * R * R, (0.2, 0.2, 0.9)))

    # the burner out of it: its tip ring, then its castable on through the front wall
    to_k = pl["to_kiln"]
    tip = pl["tip"]
    back = tuple(-pl["R"][2][i] for i in range(3))     # back along the burner (its -z) in the kiln: toward the hood
    L_ring, L_cast = -body["z_ring"], pl["z_castable_end"] - pl["tip"][2] + 1.0
    # from the tip face itself: the channels' outlets then share it with the flame volume
    cyl("void_burner_tip_ring", tip, back, 0.5 * body["D_tip"], L_ring + 0.001)
    cyl("void_burner_castable", tuple(tip[i] + L_ring * back[i] for i in range(3)), back, body["R_castable"], L_cast)
    # the channels' inlets (kiln_burner.bas's inlet faces), placed
    T, LP = ch["plate_t"], ch["plenum_L"]
    sw0, sw1 = ch["swirl_plenum"]
    ax0, ax1 = ch["axial_plenum"]
    nb = tuple(-pl["R"][2][i] for i in range(3))        # the burner's -z (an inlet's outward normal) in the kiln
    faces.append(("coal_in", to_k((0.0, ch["y_coal"], -ch["L_coal"])), nb, ch["groups"]["coal"]["a_in"], (0.55, 0.0, 0.0)))
    faces.append(("axial_in", to_k((0.0, 0.5 * (ax0 + ax1), -T - LP)), nb, ch["groups"]["axial"]["a_in"], (0.9, 0.0, 0.0)))
    faces.append(("swirl_in", to_k((0.0, 0.5 * (sw0 + sw1), -T - LP)), nb, ch["groups"]["swirl"]["a_in"], (1.0, 0.45, 0.45)))

    # the flame must end well inside the volume (rule 8): the literature's
    # flame length scaled by the kiln's D, times a margin, from the tip
    hk = g["kiln_hood"]
    L_est = v(hk["flame_L_ref"]) * kl["D"] / v(hk["flame_L_ref_D"])
    L_tip = tip[2] - z_cut
    if L_tip < v(hk["flame_domain_margin"]) * L_est:
        raise ValueError(f"kiln_flame: the volume runs {L_tip:.1f} m from the tip, the flame's "
                         f"estimate {L_est:.1f} m needs {v(hk['flame_domain_margin']) * L_est:.1f} m")

    solid = [b for b in bodies if not b["name"].startswith("void_")]
    box = tuple(min(b["box"][i] for b in solid) for i in range(3)) + tuple(max(b["box"][i] for b in solid) for i in range(3, 6))
    return {
        "L_flame_est": L_est, "L_tip_to_cut": L_tip,
        "bodies": bodies, "faces": faces, "box": box, "z_cut": z_cut, "L_flame": kl["burning_L"],
        "alpha": alpha, "Hd": Hd, "U": U, "tip": tip, "h_ta": h_ta, "r_ta": r_ta, "L_ta": L_ta, "bed": bd,
        "bed_strip": bed_strip, "floor_split": floor_split,
        "groups": {"flame": {"box": box, "V": None, "n": len(bodies)}},
    }


def cooler_placement(g):
    """Where the cooler's CFD volume (cooler_cfd(), its own frame: x along
    the grate from the hot end, y across, z up from the grate) sits in the
    kiln frame (kiln_flame()): its x the plant's horizontal towards the
    cooler (Hd), its z the plant's up (U), its y = U x Hd = the kiln's x;
    its hot end under the hood's back wall, its roof (z = H) the hood's
    floor (user, 23 Nov 2026: the cooler, the hood and the kiln one gas
    path). Then hood_1 / hood_2 lie on the flame volume's secondary_air_in
    / tertiary_supply_in. "R": the cooler's axes (rows) in the kiln frame;
    "o": its origin; "box": its extent in the kiln frame."""
    kl, hd, co, f = kiln(g), kiln_hood(g), cooler(g), cooler_cfd(g)
    alpha = math.atan(0.01 * kl["slope"])
    sa, ca = math.sin(alpha), math.cos(alpha)
    Hd, U, X = (0.0, sa, ca), (0.0, ca, -sa), (1.0, 0.0, 0.0)
    u0 = -hd["below"] - co["casing_height"]
    o = tuple((0.0, 0.0, kl["L"])[i] + u0 * U[i] for i in range(3))

    def to_kiln(p):
        return tuple(o[i] + p[0] * Hd[i] + p[1] * X[i] + p[2] * U[i] for i in range(3))

    w2 = 0.5 * co["width"]
    pts = [to_kiln((x, y, z)) for x in (0.0, f["length_total"]) for y in (-w2, w2) for z in (0.0, f["vent_z_out"])]
    box = tuple(min(q[i] for q in pts) for i in range(3)) + tuple(max(q[i] for q in pts) for i in range(3))
    return {"R": (Hd, X, U), "o": o, "to_kiln": to_kiln, "box": box}


def tower_layout(g):
    """The tower in plan, string 1 (+x; string 2 its mirror in x = 0), in
    the plant frame (the calciner's, z up; the kiln and the gooseneck's
    arms towards -y). User, 24 Nov 2026: the C4 and C5 meal pipes have to
    fall at the meal slope, so the tower stands beside the calciner, not
    out past the gooseneck's arms (it had them 26 and 20 m off at ~27 and
    ~30 deg).

    C5 turned so its level inlet duct runs out of the arm along +x with
    the barrel on the calciner's side of it (the mirrored solid, its duct
    on its -y side): its axis yd behind the arm's axis. C4 one column
    offset behind C5 (+y), C3 over C5 and C2 over C4 as before; the C1
    twin turned half round, its two C1 either side of C3's riser. x is
    the furthest in of: C5 and C4 `tower_calciner_gap` clear of the
    calciner (bore to bore); C5's duct then runs from the arm's face
    (x_leg) to its barrel."""
    lay, gn, cal = layout(g), gooseneck(g), calciner(g)
    c5, c4 = cyclone(g, "C5"), cyclone(g, "C4")
    duct5 = cyclone_duct_inlet(g, "C5")
    yd = 0.5 * (duct5["y_inner"] + duct5["y_outer"])
    y_arm = -gn["y_off"]
    y5 = y_arm + yd
    y4 = y5 + lay["column_offset"]
    gap = v(g["layout"]["tower_calciner_gap"])
    R = cal["R"]
    x5 = 0.0
    for r_c, y in ((0.5 * c5["D_barrel"], y5), (0.5 * c4["D_barrel"], y4)):
        d = R + r_c + gap
        if d > abs(y):
            x5 = max(x5, math.sqrt(d * d - y * y))
    L_in = x5 - gn["x_leg"]
    if L_in < 0.5:
        raise ValueError(f"tower_layout: C5's duct from the arm's face would be {L_in:.2f} m")
    if 2.0 * x5 - c5["D_barrel"] < gap:
        raise ValueError("tower_layout: the two strings' C5 stand closer than the gap")
    # user 28 Nov 2026: C3 and C2, each with its riser, turned about its own axis so a dust outlet is not
    # over the elbow of the riser below it. A cyclone's riser stands on the axis of the cyclone below, so the
    # turn swings the cyclone round that axis: C3 about C4's axis by tower_swing_deg (R4's elbow is then not
    # under C3's outlet), C2 about C3's by tower_swing_c2_deg (R3's, which now leans with C3)
    off = lay["column_offset"]
    s3 = math.radians(v(g["layout"]["tower_swing_deg"]))
    s2 = math.radians(v(g["layout"]["tower_swing_c2_deg"]))
    c3 = (x5 + off * math.sin(s3), y4 - off * math.cos(s3))
    c2 = (c3[0] - off * math.sin(s2), c3[1] + off * math.cos(s2))
    cols = {5: (x5, y5), 4: (x5, y4), 3: c3, 2: c2}
    return {"cols": cols, "x": x5, "y_arm": y_arm, "yd": yd, "c5_duct_L": L_in,
            "clear_c5": math.hypot(x5, y5) - R - 0.5 * c5["D_barrel"],
            "clear_c4": math.hypot(x5, y4) - R - 0.5 * c4["D_barrel"]}


def c5_plant_inlet_L(g):
    """C5 as the plant has it (C5_plant.SLDPRT, cyclone.bas c5_plant; user
    23 Nov 2026: the gooseneck arm and C5 must meet): no riser under its
    duct, the level inlet duct run back from the barrel's tangent plane
    to the gooseneck arm's outlet face (tower_layout(): C5's axis x, the
    arm's face x_leg). The arm is round (D_leg), the duct rectangular
    (W x H_inlet): the face is where they meet, no transition piece."""
    return tower_layout(g)["c5_duct_L"]


def tower_placement(g):
    """The tower assembly (user, 23 Nov 2026: the whole pyroprocess in
    one assembly, step by step; option A: the CFD solids as they are):
    each part's axes (rows, in the plant frame) and origin. The plant
    frame is the calciner's (calciner.bas): z up from the ground, the
    two strings at +-x, the gooseneck and the kiln towards -y: the kiln
    inlet chamber turned so its kiln (its +x) runs to -y, across the
    strings' line. The columns where tower_layout() has them (24 Nov
    2026: beside the calciner); each cyclone turned about its axis so its
    CFD riser stands on the axis of the cyclone below; C5 (the mirrored
    solid, turned half round) so its level inlet duct is on the gooseneck
    arm's axis. String 2 is string 1's mirror in x = 0, built from the
    mirrored solids (a file and its mirror swap). C2 = C3 = C4 (one
    solid, C4.SLDPRT).

    Returns {"parts": [{name, file, R, o}], "joints": [...], ...}; the
    joints are what meets and how (face to face, an overlap of two CFD
    domains along one riser)."""
    lay, gn, kl = layout(g), gooseneck(g), kiln(g)
    tl = tower_layout(g)
    c = {n: cyclone(g, f"C{n}") for n in (2, 3, 4, 5)}
    ri = {n: cfd_riser_inlet(g, f"C{n}") for n in (4, 5)}
    tw = c1_twin(g)
    z0 = lay["z_calciner_throat"]
    y_arm = tl["y_arm"]
    z_arm = z0 + gn["z_end"]
    duct5 = cyclone_duct_inlet(g, "C5")

    def rz(th):
        ct, st = math.cos(th), math.sin(th)
        return ((ct, st, 0.0), (-st, ct, 0.0), (0.0, 0.0, 1.0))

    def apply(R, p):
        return tuple(sum(p[i] * R[i][k] for i in range(3)) for k in range(3))

    def mx(v):
        return (-v[0], v[1], v[2])

    def swap(f):        # a solid and its mirror
        return f.replace("_m.SLDPRT", ".SLDPRT") if f.endswith("_m.SLDPRT") else f.replace(".SLDPRT", "_m.SLDPRT")

    parts = [
        {"name": "kiln_inlet_chamber", "file": "kiln_inlet_chamber.SLDPRT",
         "R": ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), "o": (0.0, 0.0, lay["z_chamber_floor"])},
        {"name": "calciner", "file": "calciner.SLDPRT", "R": rz(0.0), "o": (0.0, 0.0, z0)},
    ]
    joints = []
    k = 1
    axis = {n: tl["cols"][n] for n in (5, 4, 3, 2)}
    # C5: the mirrored solid (a point p of C5_plant is (-p_x, p_y, p_z) in it),
    # turned half round: its duct along +x on its -y side
    R5 = rz(math.pi)
    parts.append({"name": f"C5_{k}", "file": "C5_plant_m.SLDPRT", "R": R5, "o": axis[5] + (lay["z_dust"][5],)})
    fc = duct5["face_centre"]
    face = apply(R5, mx((-c5_plant_inlet_L(g), fc[1], fc[2])))
    joints.append({"what": f"gooseneck arm {k} -> C5_{k} inlet duct", "kind": "face",
                   "L": math.hypot(axis[5][0] + face[0] - gn["x_leg"], axis[5][1] + face[1] - y_arm),
                   "z": (z_arm, lay["z_dust"][5] + face[2]),
                   "note": "round arm (D_leg) on the rectangular duct (W x H_inlet), no transition"})
    below = 5
    for n in (4, 3, 2):
        d = (axis[below][0] - axis[n][0], axis[below][1] - axis[n][1])     # the riser: towards the cyclone below
        r = ri[4]
        R = rz(math.atan2(d[1], d[0]) - math.atan2(r["y"], r["x"]))
        parts.append({"name": f"C{n}_{k}", "file": "C4.SLDPRT", "R": R, "o": axis[n] + (lay["z_dust"][n],)})
        rp = apply(R, (r["x"], r["y"], 0.0))
        top_below = lay["z_dust"][below] + c[below]["height"] + c[below]["outlet_rise"]
        foot = lay["z_dust"][n] + c[n]["height"] - r["drop"] - r["stub"]
        joints.append({"what": f"C{below}_{k} outlet pipe -> C{n}_{k} riser", "kind": "overlap",
                       "L": top_below - foot, "riser_at": (axis[n][0] + rp[0], axis[n][1] + rp[1]),
                       "axis_below": axis[below], "D": (c[below]["D_vortex"], r["D"])})
        below = n
    # the C1 twin, turned half round (its C1 either side of C3's riser): R1 on C2's axis
    Rt = rz(math.pi)
    r1 = apply(Rt, (0.0, tw["y_branch"], 0.0))
    o = (axis[2][0] - r1[0], axis[2][1] - r1[1], lay["z_dust"][1])
    parts.append({"name": f"C1_twin_{k}", "file": "C1_twin.SLDPRT", "R": Rt, "o": o})
    # R1's floor (the twin's gas inlet) on C2's outlet face: L the gap (0: face to face)
    joints.append({"what": f"C2_{k} outlet pipe -> R1_{k}", "kind": "face",
                   "L": lay["z_r1_foot"] - (lay["z_dust"][2] + c[2]["height"] + c[2]["outlet_rise"])})
    # string 2: string 1's mirror in the plane x = 0 (user, 24 Nov 2026: the
    # strings mirrored, as plants have them). Its parts are the mirrors of
    # string 1's solids (plant_assembly.bas mirror_parts: x -> -x in the
    # part's frame), so a part point p' = (-p_x, p_y, p_z); the plant point
    # is M (o + p R) with M: x -> -x, so the rows become (-M R0, M R1, M R2)
    # (a proper rotation again) and the origin M o. Its cyclones turn the
    # other way.
    for q in [q for q in parts if q["name"].endswith("_1")]:
        R = q["R"]
        parts.append({"name": q["name"][:-2] + "_2", "file": swap(q["file"]),
                      "R": (tuple(-x for x in mx(R[0])), mx(R[1]), mx(R[2])), "o": mx(q["o"])})
    for j in [j for j in joints if j["what"].count("_1")]:
        m = dict(j)
        m["what"] = j["what"].replace("_1", "_2").replace("arm 1", "arm 2")
        for key in ("riser_at", "axis_below"):
            if key in m:
                m[key] = (-m[key][0], m[key][1])
        joints.append(m)

    # the kiln's end (kiln_outlet_assembly, the kiln frame: z the axis from
    # the back end to the hood, y up across it, x across) out of the
    # chamber's mouth: its back end at the mouth's centre (a, z_axis), its
    # axis falling at the slope towards -y, across the strings' line (user,
    # 24 Nov 2026: the tower stays; the tertiary air duct runs parallel to
    # the kiln into the calciner)
    sec = chamber_section(g)
    al = sec["alpha"]
    sa, ca = math.sin(al), math.cos(al)
    Rk = ((1.0, 0.0, 0.0), (0.0, -sa, ca), (0.0, -ca, -sa))
    ok = (0.0, -sec["a"], lay["z_chamber_floor"] + sec["z_axis"])
    parts.append({"name": "kiln_outlet", "file": "kiln_outlet_assembly.SLDASM", "R": Rk, "o": ok})
    # the meal pipes (meal_pipes.SLDPRT, built in the plant frame; meal_routes())
    parts.append({"name": "meal_pipes", "file": "meal_pipes.SLDPRT",
                  "R": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), "o": (0.0, 0.0, 0.0)})
    # the tertiary air duct (ta_duct.SLDPRT, the plant frame; tertiary_air_duct())
    parts.append({"name": "ta_duct", "file": "ta_duct.SLDPRT",
                  "R": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), "o": (0.0, 0.0, 0.0)})
    # the chamber's stub end (kiln_gas_inlet) is kiln.SLDPRT's back face (kiln_back, z_cfd0)
    se = sec["stub_end"]
    p_ch = (0.0, -se[0], lay["z_chamber_floor"] + se[1])
    p_kl = tuple(ok[i] + kl["z_cfd0"] * Rk[2][i] for i in range(3))
    joints.append({"what": "kiln_inlet_chamber kiln_gas_inlet -> kiln kiln_back", "kind": "face",
                   "L": math.dist(p_ch, p_kl)})
    return {"parts": parts, "joints": joints, "y_arm": y_arm, "z_arm": z_arm}


def meal_routes(g):
    """The meal pipes in the tower (user, 24 Nov 2026), string 1 then its
    mirror, in the plant frame: each a polyline from a dust outlet (or
    C1's) to where its meal goes, D from meal_pipes(). The rules of
    plant_topology_2d (14 Oct 2026), laid in 3D on tower_layout():
      C1 (both of the twin) -> R2, C3's CFD outlet pipe, one from each side
         (+-x, across R2's bend towards C2);
      C2 -> R3 (C4's outlet pipe), C3 -> R4 (C5's): each stands over that
         pipe; it leaves at once (drop_over_riser) at the meal slope away
         from the riser's bend, clears the riser's inclined roof, drops
         side_L beside the pipe, and runs in at the slope to its wall
         entry_up over the roof below;
      C4 -> the calciner's meal pipe on its side (its end face), straight
         after c4_drop;
      C5 -> the calciner's throat (user, 24 Nov 2026: "boğaz"), its wall
         at mid height on C5's side, straight after c5_drop.
    Each run's slope from the horizontal; the straight runs have to be
    min_slope or steeper. Points end r past the target (into it)."""
    mr, lay, tl = g["meal_route"], layout(g), tower_layout(g)
    mp = meal_pipes(g)
    tp = tower_placement(g)
    cal_in = calciner_inlets(g)["meal"]
    sec = chamber_section(g)
    slope = math.radians(v(g["cyclone_domain"]["meal_slope"]))
    ts = math.tan(slope)
    cols = tl["cols"]
    c = {n: cyclone(g, f"C{n}") for n in range(1, 6)}
    tw = c1_twin(g)
    twin = next(q for q in tp["parts"] if q["name"] == "C1_twin_1")

    def unit(a, b):
        d = (b[0] - a[0], b[1] - a[1])
        n = math.hypot(*d)
        return (d[0] / n, d[1] / n)

    entry = {}                 # the last into_riser's box (kept on the pipe for the assembly)

    def into_riser(name, p0, drop, below, want_x=None):
        """p0 the dust outlet; below: the cyclone whose outlet pipe takes
        the meal; want_x: the x side (+-1) of the riser the pipe comes down on (None: the side the dust outlet is on).
        The meal ends in a dispersion box on that pipe's wall (dispersion_box():
        a cube, its mid height entry_up over the roof below) through a vertical
        run down onto the box's top face centre."""
        A, rp = cols[below], 0.5 * c[below]["D_vortex"]
        D = mp[int(name[1])]["D"]
        # user 28 Nov 2026: the meal pipe passes the riser's side face (across the elbow's duct direction),
        # neither the elbow's side nor its back: away = that side's unit vector on the x side asked for
        part_el = next(q for q in tp["parts"] if q["name"] == f"C{below - 1}_1")
        e_el = (part_el["R"][0][0], part_el["R"][0][1])
        away = (-e_el[1], e_el[0])
        toward = (away[0] * (p0[0] - A[0]) + away[1] * (p0[1] - A[1])) if want_x is None else away[0] * want_x
        if toward < 0.0:
            away = (-away[0], -away[1])
        z_in = lay["z_roof"][below] + v(mr["entry_up"])
        box = dispersion_box(g, rp, D, 0.0)
        box = dispersion_box(g, rp, D, z_in - 0.5 * box["height"])
        pipe = (A[0] + away[0] * box["rho_pipe"], A[1] + away[1] * box["rho_pipe"])
        # the elbow of the riser R(below-1) above the pipe (its sides D / width0 wide, down to its seam
        # `drop` under the roof of C(below-1)): the meal pipe comes down outboard of it by riser_clear
        # (user 28 Nov 2026: the pipes touched the elbows), then in to the box under the seam
        rs_el = lay["riser"][below - 1]
        z_seam = lay["z_roof"][below - 1] - rs_el["drop"]
        r_p = 0.5 * D
        clr = v(mr["riser_clear"])
        # the elbow's inclined duct in plan: a strip hw wide along the duct's axis (the cyclone C(below-1)'s
        # level-duct direction in the plant frame) from the riser's axis to its barrel; and that barrel
        part = next(q for q in tp["parts"] if q["name"] == f"C{below - 1}_1")
        e_d = (part["R"][0][0], part["R"][0][1])
        hw = 0.5 * max(rs_el["width0"], 2.0 * rp)
        s_len = rs_el["run"] + rs_el["level"] + 0.5 * c[below - 1]["D_barrel"]
        barrel = cols[below - 1]
        Rb = 0.5 * c[below - 1]["D_barrel"]

        def free(t):
            qx, qy = A[0] + away[0] * t, A[1] + away[1] * t
            sd = max(0.0, min(s_len, (qx - A[0]) * e_d[0] + (qy - A[1]) * e_d[1]))
            dd = math.hypot(qx - A[0] - sd * e_d[0], qy - A[1] - sd * e_d[1])
            return dd >= hw + r_p + clr and math.hypot(qx - barrel[0], qy - barrel[1]) >= Rb + r_p + clr

        qx, qy = p0[0] - A[0], p0[1] - A[1]
        sd0 = max(0.0, min(s_len, qx * e_d[0] + qy * e_d[1]))
        if want_x is None and math.hypot(qx - sd0 * e_d[0], qy - sd0 * e_d[1]) < hw + r_p:
            raise ValueError(f"meal_routes {name}: the dust outlet's pipe starts over the riser's elbow duct "
                             f"(turn the cyclones further: layout.tower_swing_deg / tower_swing_c2_deg)")
        far = box["rho_pipe"]
        while not free(far):
            far += 0.01
            if far > rp + 8.0:
                raise ValueError(f"meal_routes {name}: no clear lane past the riser's elbow")
        p1 = (p0[0], p0[1], p0[2] - drop)
        pts_t = []
        # fewest bends (user 28 Nov 2026): the pipe stands on the box's top face where the clear lane is, when
        # that lane is on the face (its outer edge), so one slanted run and one vertical run; only a lane
        # beyond the face needs the way back in
        if far <= box["rho_out"] - r_p + 0.02:                    # (a pipe flush with the face, to 2 cm)
            pipe = (A[0] + away[0] * far, A[1] + away[1] * far)
            far = box["rho_pipe"]
        if far > box["rho_pipe"] + 1e-9:
            far_xy = (A[0] + away[0] * far, A[1] + away[1] * far)
            h_far = math.hypot(far_xy[0] - p1[0], far_xy[1] - p1[1])
            z_a = p1[2] - h_far * ts
            z_b = min(z_a, z_seam - clr)                           # the vertical run ends under the elbow's seam
            z_c = z_b - (far - box["rho_pipe"]) * ts                # then in at the meal slope to the box's pipe
            z_end = box["z_top"] - 0.1
            if z_c <= z_end + 0.2:
                raise ValueError(f"meal_routes {name}: no room to clear the riser's elbow and drop onto the box "
                                 f"(far {far:.2f}, run to it {h_far:.2f} m ends at z {z_a:.2f}, elbow seam clear {z_b:.2f}, "
                                 f"back in to {z_c:.2f}, box top {z_end:.2f})")
            pts_t = [(far_xy[0], far_xy[1], z_a)]
            if z_b < z_a - 1e-9:
                pts_t.append((far_xy[0], far_xy[1], z_b))
            pts_t.append((pipe[0], pipe[1], z_c))
        h = math.hypot(pipe[0] - p1[0], pipe[1] - p1[1])
        p2 = (pipe[0], pipe[1], p1[2] - h * ts)
        p3 = (pipe[0], pipe[1], box["z_top"] - 0.1)          # 0.1 m into the box
        if not pts_t and p3[2] >= p2[2]:
            raise ValueError(f"meal_routes {name}: no room to drop onto the dispersion box ({p2[2]:.2f} <= {p3[2]:.2f})")
        entry.clear()
        entry.update({"box": box, "A": A, "away": away, "R": rp, "z_in": z_in, "toward_bend": away[0] * e_el[0] + away[1] * e_el[1]})
        return [p0, p1] + (pts_t if pts_t else [p2]) + [p3]

    pipes = []
    # C1: the twin's two C1 (its frame turned as tower_placement turned it)
    d_c1 = 0.5 * tw["spacing"]
    for sx in (-1.0, 1.0):
        q = tuple(twin["o"][k] + sx * d_c1 * twin["R"][0][k] for k in range(3))
        side = math.copysign(1.0, q[0] - cols[3][0])
        pipes.append({"name": "C1_out" if side > 0 else "C1_in", "stage": 1, "to": "R2 (C3 outlet pipe)",
                      "pts": into_riser("C1", q, v(mr["drop"]), 3, side), "entry": dict(entry)})
    # C2 -> R3 over C4, C3 -> R4 over C5: away from the bend (towards the cyclone above it)
    for n, below, bend_to in ((2, 4, 3), (3, 5, 4)):
        p0 = cols[n] + (lay["z_dust"][n],)
        pts = into_riser(f"C{n}", p0, v(mr["drop_over_riser"]), below)
        # the dust outlet is off the riser by the swing: its pipe never crosses the riser's roof; the
        # clearance kept is the outlet pipe's wall to the riser's wall, in plan
        rs = lay["riser"][n + 1]
        clear = math.hypot(p0[0] - cols[below][0], p0[1] - cols[below][1]) - 0.5 * rs["D"] - 0.5 * mp[n]["D"]
        if clear < v(mr["riser_clear"]):
            raise ValueError(f"meal_routes C{n}: the dust outlet's pipe is {clear:.2f} m off the riser under it, "
                             f"under riser_clear (turn C{n} further: layout.tower_swing_deg)")
        pipes.append({"name": f"C{n}", "stage": n, "to": f"R{n + 1} (C{below} outlet pipe)",
                      "pts": pts, "riser_clearance": clear, "entry": dict(entry)})
    # C4 -> the calciner's dispersion box on this side (+x): straight down to
    # c4_entry_run over its vertical pipe's top face, then vertically 0.1 m into that pipe
    p0 = cols[4] + (lay["z_dust"][4],)
    p1 = (p0[0], p0[1], p0[2] - v(mr["c4_drop"]))
    z0 = lay["z_calciner_throat"]
    e = (cal_in["end"][0], 0.0, z0 + cal_in["end"][1])
    pipes.append({"name": "C4", "stage": 4, "to": "calciner dispersion box",
                  "pts": [p0, p1, (e[0], e[1], e[2] + v(mr["c4_entry_run"])), (e[0], e[1], e[2] - 0.1)]})
    # C5 -> the calciner's throat: a dispersion box on its wall at mid height, towards C5
    # (user 28 Nov 2026: every meal inlet gets the box); the pipe ends in a vertical run onto it
    cal = calciner(g)
    p0 = cols[5] + (lay["z_dust"][5],)
    p1 = (p0[0], p0[1], p0[2] - v(mr["c5_drop"]))
    u = unit((0.0, 0.0), cols[5])
    r5 = 0.5 * mp[5]["D"]
    z_mid = z0 + 0.5 * cal["z_throat_top"] - v(mr["c5_box_below_mid"])
    box = dispersion_box(g, cal["r_throat"], mp[5]["D"], 0.0)
    box = dispersion_box(g, cal["r_throat"], mp[5]["D"], z_mid - 0.5 * box["height"])
    P = (box["rho_pipe"] * u[0], box["rho_pipe"] * u[1])
    p2 = (P[0], P[1], box["z_top"] + v(mr["c5_box_drop"]))
    p3 = (P[0], P[1], box["z_top"] - 0.1)
    if p2[2] >= p1[2]:
        raise ValueError("meal_routes C5: no room to drop onto the throat's dispersion box")
    pipes.append({"name": "C5", "stage": 5, "to": "calciner throat dispersion box", "pts": [p0, p1, p2, p3],
                  "entry": {"box": box, "A": (0.0, 0.0), "away": u, "R": cal["r_throat"], "z_in": z_mid}})

    lo = v(mr["min_slope"])
    for q in pipes:
        q["D"] = mp[q["stage"]]["D"]
        q["string"] = 1
        sl = []
        for a_, b_ in zip(q["pts"], q["pts"][1:]):
            h = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
            sl.append(math.degrees(math.atan2(a_[2] - b_[2], h)))
        q["slopes"] = sl
        if min(sl) < lo - 1e-9:
            raise ValueError(f"meal_routes {q['name']}: a run at {min(sl):.1f} deg, under {lo:g}")
    out = list(pipes)
    for q in pipes:
        m = dict(q)
        m["string"] = 2
        m["pts"] = [(-p[0], p[1], p[2]) for p in q["pts"]]
        if "entry" in q:
            e_ = q["entry"]
            m["entry"] = dict(e_, A=(-e_["A"][0], e_["A"][1]), away=(-e_["away"][0], e_["away"][1]))
        out.append(m)
    return out


def tertiary_air_duct(g):
    """The tertiary air duct as the plant has it (user, 24 Nov 2026: "TA
    bağlayalım"; route: rise, then one straight run along the kiln), in
    the plant frame: from the hood's tertiary mouth face (kiln_flame's
    tertiary_air_out, on top of its vertical run, carried by the
    kiln_outlet part's placement) through a bend of bend_R_over_D x D in
    the vertical plane towards the calciner, then straight to the
    calciner's tertiary inlet face (its stub's end, calciner_inlets()),
    r on into the stub. The bend's arc drawn as bend_pieces chords. The
    run's slope is whatever the two ends leave (+ rising to the
    calciner); its plan angle off the kiln's axis the inlet's x offset."""
    tp = tower_placement(g)
    k = next(q for q in tp["parts"] if q["name"] == "kiln_outlet")
    face = next(f for f in kiln_flame(g)["faces"] if f[0] == "tertiary_air_out")
    P0 = tuple(k["o"][j] + sum(face[1][i] * k["R"][i][j] for i in range(3)) for j in range(3))
    n0 = tuple(sum(face[2][i] * k["R"][i][j] for i in range(3)) for j in range(3))
    if abs(n0[2] - 1.0) > 1e-9:
        raise ValueError("tertiary_air_duct: the hood's mouth is not vertical")
    ta = calciner_inlets(g)["tertiary_air"]
    z0 = layout(g)["z_calciner_throat"]
    E = (ta["centre"][0], ta["centre"][1], z0 + ta["centre"][2])
    D = ta["D"]
    r = 0.5 * D
    Rb = v(g["tertiary_air_duct"]["bend_R_over_D"]) * D
    n = int(v(g["tertiary_air_duct"]["bend_pieces"]))
    hx, hy = E[0] - P0[0], E[1] - P0[1]
    hn = math.hypot(hx, hy)
    h = (hx / hn, hy / hn, 0.0)
    beta = 0.0
    for _ in range(50):          # the run's slope, from where the bend ends
        phi = 0.5 * math.pi - beta
        S = tuple(P0[i] + Rb * (h[i] * (1.0 - math.cos(phi)) + (math.sin(phi) if i == 2 else 0.0)) for i in range(3))
        beta = math.atan2(E[2] - S[2], math.hypot(E[0] - S[0], E[1] - S[1]))
    pts = [P0]
    for j in range(1, n + 1):
        ps = phi * j / n
        pts.append(tuple(P0[i] + Rb * (h[i] * (1.0 - math.cos(ps)) + (math.sin(ps) if i == 2 else 0.0)) for i in range(3)))
    d = tuple(E[i] - S[i] for i in range(3))
    L = math.sqrt(sum(x * x for x in d))
    pts.append(tuple(E[i] + r * d[i] / L for i in range(3)))
    # the run against the calciner's stub axis (+y): the angle it comes in at
    inc = math.degrees(math.acos(d[1] / L))
    length = Rb * phi + L
    return {"D": D, "pts": pts, "start": P0, "end": E, "run_slope_deg": math.degrees(beta),
            "run_slope_pct": 100.0 * math.tan(beta), "run_L": L, "bend_deg": math.degrees(phi),
            "plan_deg": math.degrees(math.atan2(-hx, hy)), "inlet_angle_deg": inc,
            "length": length, "volume": math.pi * r * r * length}


def _polyline_bodies(prefix, pts, r, rgb):
    """Each run of a polyline a cylinder of radius r, lengthened at a bend
    by r tan(turn / 2) so the two runs close the bend's outside; kinds and
    fields as cooler_body()."""
    bodies = []
    dirs = []
    for a, b in zip(pts, pts[1:]):
        d = [b[k] - a[k] for k in range(3)]
        n = math.sqrt(sum(x * x for x in d))
        dirs.append((tuple(x / n for x in d), n))
    for i, (u, n) in enumerate(dirs):
        e0 = e1 = 0.0
        if i > 0:
            cosT = max(-1.0, min(1.0, sum(x * y for x, y in zip(dirs[i - 1][0], u))))
            e0 = r * math.tan(0.5 * math.acos(cosT))
        if i < len(dirs) - 1:
            cosT = max(-1.0, min(1.0, sum(x * y for x, y in zip(u, dirs[i + 1][0]))))
            e1 = r * math.tan(0.5 * math.acos(cosT))
        base = tuple(pts[i][k] - e0 * u[k] for k in range(3))
        L = n + e0 + e1
        end = tuple(base[k] + L * u[k] for k in range(3))
        half = tuple(r * math.sqrt(max(0.0, 1.0 - x * x)) for x in u)
        lo = tuple(min(p, e) - h for p, e, h in zip(base, end, half))
        hi = tuple(max(p, e) + h for p, e, h in zip(base, end, half))
        bodies.append({"name": f"{prefix}_{i + 1}", "kind": "cyl",
                       "p": base + u + (r, L), "V": math.pi * r * r * L, "box": lo + hi, "rgb": rgb})
    return bodies


def tertiary_air_duct_bodies(g):
    """ta_duct.bas's bodies: tertiary_air_duct()'s polyline as cylinders."""
    t = tertiary_air_duct(g)
    return _polyline_bodies("ta_duct", t["pts"], 0.5 * t["D"], (0.6, 0.2, 0.8))


def meal_dispersion_boxes(g):
    """The dispersion box (dispersion_box(): one design, the pipe's own
    bore) at each meal pipe's entry onto a wall, as meal_routes() lays them
    (C1 -> R2, C2 -> R3, C3 -> R4, C5 -> the calciner's throat, both strings).
    C4's meal goes into the calciner, whose CFD solid carries its boxes.
    Each: the oriented wedge's section frame (centre of its run on the floor,
    the outward unit vector u, width, run, height, slope, level lead-in) and
    the exact extents of its eight corners (the box as a polyhedron)."""
    out = []
    for q in meal_routes(g):
        e = q.get("entry")
        if e is None:
            continue
        b = e["box"]
        ax, ay = e["A"]
        ux, uy = e["away"]
        nx, ny = -uy, ux
        hw = 0.5 * b["width"]
        # the section polygon (s along u, z): floor level to the tangent plane, the ramp up to the back face's foot
        pts = [(b["rho_in"], b["z_bottom"]), (b["rho_flat"], b["z_bottom"]), (b["rho_out"], b["z_back_foot"])]
        if b["back_h"] > 1e-9:
            pts.append((b["rho_out"], b["z_top"]))
        pts.append((b["rho_in"], b["z_top"]))
        if b["back_h"] > 1e-9:
            raise NotImplementedError("a back face on the wedge body")
        corners = [(ax + ux * sr + nx * t, ay + uy * sr + ny * t, z) for sr, z in pts for t in (-hw, hw)]
        lo = tuple(min(c[k] for c in corners) for k in range(3))
        hi = tuple(max(c[k] for c in corners) for k in range(3))
        run = b["rho_out"] - b["rho_in"]
        tan = math.tan(math.radians(b["slope_deg"]))
        out.append({"name": f"dbox_{q['name']}_{q['string']}", "box": lo + hi, "away": (ux, uy), "dims": b,
                    "centre": (ax + ux * (b["rho_in"] + 0.5 * run), ay + uy * (b["rho_in"] + 0.5 * run)),
                    "run": run,
                    # the wedge body: the lead-in (rho_in .. R) at full height, the ramp beyond
                    "V": b["width"] * ((b["rho_flat"] - b["rho_in"]) * b["height"] + 0.5 * tan * b["depth"] ** 2)})
    return out


def meal_pipe_bodies(g):
    """meal_pipes.bas's bodies: each run of meal_routes() a cylinder (the
    pipe's bore, D), lengthened at a bend by r tan(turn / 2) so the two
    runs close the bend's outside; kinds and fields as cooler_body()."""
    bodies = []
    ORANGE = (0.93, 0.55, 0.13)
    for q in meal_routes(g):
        bodies += _polyline_bodies(f"meal_{q['name']}_{q['string']}", q["pts"], 0.5 * q["D"], ORANGE)
    # a dispersion box at each wall entry: the wedge (level top, level lead-in, 60 deg floor ramp), kind "owedge"
    for b in meal_dispersion_boxes(g):
        d = b["dims"]
        cx, cy = b["centre"]
        ux, uy = b["away"]
        bodies.append({"name": b["name"], "kind": "owedge",
                       "p": (cx, cy, d["z_bottom"], ux, uy, d["width"], b["run"], d["height"], d["slope_deg"],
                             d["rho_flat"] - d["rho_in"]),
                       "V": b["V"], "box": b["box"], "rgb": (0.55, 0.55, 0.6)})
    return bodies


def cooler_fans(g):
    """One cooling fan per segment (user, 23 Nov 2026), hot end first: the
    segment's air (cooler_air) at fan_air_T, the pressure linear from
    fan_dp_first to fan_dp_last, sized by the fan laws as id_fan(): tip
    speed u = sqrt(2 dp / (rho psi)), wheel D2 = u / (pi n), eye
    D1 = sqrt(4 Q / (pi c0)); shaft power Q dp / eta."""
    b = g["cooler_body"]
    m = cooler_air(g)["m"]
    T = v(b["fan_air_T"])
    rho = 101325.0 * AIR_M / (R_GAS * T)
    n = v(b["fan_speed"]) / 60.0
    p0, p1 = v(b["fan_dp_first"]), v(b["fan_dp_last"])
    out = []
    for i, mi in enumerate(m):
        dp = p0 + (p1 - p0) * i / max(1, len(m) - 1)
        q = mi / rho
        u = math.sqrt(2.0 * dp / (rho * v(b["fan_pressure_coefficient"])))
        d2 = u / (math.pi * n)
        d1 = math.sqrt(4.0 * q / (math.pi * v(b["fan_eye_velocity"])))
        if d1 >= d2:
            raise ValueError(f"cooler_fans: fan {i + 1}'s eye ({d1:.2f} m) is not inside its wheel ({d2:.2f} m)")
        out.append({"m": mi, "q": q, "dp": dp, "rho": rho, "u_tip": u, "D2": d2, "D1": d1,
                    "b2": d1 * d1 / (4.0 * d2),               # the eye's meridional velocity kept to the tip
                    "P": q * dp / v(b["fan_efficiency"])})
    return out


def cooler_body(g):
    """The cooler's mechanical parts as simple envelopes (user, 23 Nov
    2026; cooler_body.bas builds them; not a CFD input): the casing round
    the CFD volume (cooler_cfd()), the undergrate housing with one
    compartment per segment, its air distribution plates, the cross bar
    lanes' hydraulic cylinders, a cooling fan per segment (volute, inlet
    cone, motor, duct into its compartment) and the roller crusher's
    housing at the discharge end. The cooler's frame (x along the grate
    from the hot end, y across, z up from the grate); the undergrate's
    floor on the plant's ground under the hood end.

    "bodies" as kiln_rotax(): kinds box (x0, x1, y0, y1, z0, z1) and cyl
    (base, unit axis, r, length)."""
    b, co, f = g["cooler_body"], cooler(g), cooler_cfd(g)
    kl, cp = kiln(g), cooler_placement(g)
    L, w, H, seg, n = co["length"], co["width"], co["casing_height"], co["segment_L"], co["segments"]
    w2 = 0.5 * w
    tc, tu, tp, tg = v(b["casing_wall_t"]), v(b["undergrate_wall_t"]), v(b["partition_t"]), v(b["grate_t"])
    # the ground: the plant's ground under the kiln's hood end (kiln_rotax),
    # its height under the grate along the cooler's up
    alpha = math.atan(v(g["kiln"]["slope"]) / 100.0)
    P_g = (0.0, -(v(g["layout"]["kiln_axis_z"]) - kl["L"] * math.sin(alpha)), kl["L"])
    U = cp["R"][2]
    h_u = sum((cp["o"][i] - P_g[i]) * U[i] for i in range(3))     # grate over the ground
    if h_u < 1.0:
        raise ValueError(f"cooler_body: the grate is {h_u:.2f} m over the ground, no room for the undergrate")
    zg = -h_u
    bodies = []

    def box(name, x0, x1, y0, y1, z0, z1, rgb):
        bodies.append({"name": name, "kind": "box", "p": (x0, x1, y0, y1, z0, z1),
                       "V": (x1 - x0) * (y1 - y0) * (z1 - z0),
                       "box": (x0, y0, z0, x1, y1, z1), "rgb": rgb})

    def cyl(name, base, axis, r, length, rgb):
        end = tuple(bb + length * a for bb, a in zip(base, axis))
        half = tuple(r * math.sqrt(max(0.0, 1.0 - a * a)) for a in axis)
        lo = tuple(min(p, e) - h for p, e, h in zip(base, end, half))
        hi = tuple(max(p, e) + h for p, e, h in zip(base, end, half))
        bodies.append({"name": name, "kind": "cyl", "p": tuple(base) + tuple(axis) + (r, length),
                       "V": math.pi * r * r * length, "box": lo + hi, "rgb": rgb})

    BLUE, STEEL, GREY, BRICK, CONCRETE = ((0.1, 0.16, 0.72), (0.62, 0.64, 0.66), (0.45, 0.46, 0.48),
                                          (0.72, 0.42, 0.30), (0.78, 0.77, 0.74))
    yo = w2 + tc                                   # the casing's outer side
    gc = g["cooler"]
    L_h = f["hrb_L"]
    Lt = L + L_h
    # casing over the grate: side walls, the back wall under the hood, the
    # roof past the hood's opening (round the vent duct)
    for nm, sy in (("m", -1.0), ("p", 1.0)):
        y0, y1 = sorted((sy * w2, sy * yo))
        box(f"casing_side_{nm}", 0.0, Lt, y0, y1, 0.0, H + tc, BRICK)
    box("casing_back", -tc, 0.0, -yo, yo, zg, H + tc, BRICK)
    x_h, x_v, r_v = co["hood_L"], f["vent_x"], 0.5 * f["vent_D"]
    box("casing_roof_1", x_h, x_v - r_v, -w2, w2, H, H + tc, BRICK)
    box("casing_roof_2", x_v + r_v, Lt, -w2, w2, H, H + tc, BRICK)
    box("casing_roof_3", x_v - r_v, x_v + r_v, -w2, -r_v, H, H + tc, BRICK)
    box("casing_roof_4", x_v - r_v, x_v + r_v, r_v, w2, H, H + tc, BRICK)
    # the casing's end wall past the HRB deck, ground to roof
    box("casing_end", Lt, Lt + tc, -yo, yo, zg, H + tc, BRICK)
    # the undergrate: air distribution plates under the grate line, the
    # housing's side walls and the partitions between the compartments
    box("grate_plates", 0.0, L, -w2, w2, -tg, 0.0, GREY)
    for nm, sy in (("m", -1.0), ("p", 1.0)):
        y0, y1 = sorted((sy * (yo - tu), sy * yo))
        box(f"undergrate_side_{nm}", 0.0, Lt, y0, y1, zg, 0.0, STEEL)     # on past the grate: the chute's sides
    for i in range(1, n + 1):                          # the last one: the chute's back wall
        box(f"partition_{i:02d}", i * seg - 0.5 * tp, i * seg + 0.5 * tp, -(yo - tu), yo - tu, zg, -tg, STEEL)
    # cross bar lanes' hydraulic cylinders (the brochure's 2 per line)
    n_l = max(1, round(w / (v(b["lane_unit_width"]) / v(b["frames_per_unit"]))))
    wl = w / n_l
    r_c, L_c, z_c = 0.5 * v(b["cylinder_D"]), v(b["cylinder_L"]), v(b["cylinder_z"])
    chambers = [int(v(b["cylinder_chamber_a"])), int(v(b["cylinder_chamber_b"]))][: int(v(b["cylinders_per_lane"]))]
    for k in range(n_l):
        y = -w2 + (k + 0.5) * wl
        for c in chambers:
            if not 2 <= c <= n:
                raise ValueError(f"cooler_body: a cylinder in chamber {c} (none in the first, {n} in all)")
            cyl(f"cylinder_{k + 1}_{c:02d}", ((c - 0.5) * seg - 0.5 * L_c, y, z_c), (1.0, 0.0, 0.0), r_c, L_c, BLUE)
    # a fan per segment on alternate sides, its axis along x: inlet cone
    # (hot end side), volute, shaft, motor; a duct from the volute across
    # into the compartment
    fans = cooler_fans(g)
    gap = v(b["fan_gap"])
    for i, fn in enumerate(fans):
        sy = -1.0 if i % 2 == 0 else 1.0
        nm = f"{i + 1:02d}"
        r_v_ = v(b["fan_volute_ratio"]) * 0.5 * fn["D2"]
        B = v(g["id_fan"]["volute_width_ratio"]) * fn["b2"]
        xc = (i + 0.5) * seg
        zc = zg + r_v_
        yc = sy * (yo + gap + r_v_)
        cyl(f"fan_volute_{nm}", (xc - 0.5 * B, yc, zc), (1.0, 0.0, 0.0), r_v_, B, BLUE)
        r_in = 0.5 * v(g["id_fan"]["cone_inlet_ratio"]) * fn["D1"]
        L_in = 0.5 * fn["D1"]
        cyl(f"fan_inlet_{nm}", (xc - 0.5 * B - L_in, yc, zc), (1.0, 0.0, 0.0), r_in, L_in, GREY)
        a_m = v(b["motor_side_ref"]) * (fn["P"] / 1.0e5) ** (1.0 / 3.0)
        L_m = v(b["motor_length_ratio"]) * a_m
        x_m = xc + 0.5 * B + 0.3
        cyl(f"fan_shaft_{nm}", (xc + 0.5 * B, yc, zc), (1.0, 0.0, 0.0), 0.06, 0.3, GREY)
        box(f"fan_motor_{nm}", x_m, x_m + L_m, yc - 0.5 * a_m, yc + 0.5 * a_m, zg, zg + a_m, GREY)
        a_d = math.sqrt(fn["q"] / v(b["fan_duct_velocity"]))
        if a_d > min(seg - tp, h_u - tg):
            raise ValueError(f"cooler_body: fan {i + 1}'s duct ({a_d:.2f} m) does not fit its compartment")
        zd = min(max(zc, zg + 0.5 * a_d), -tg - 0.5 * a_d)
        y0, y1 = sorted((sy * yo, yc))
        box(f"fan_duct_{nm}", xc - 0.5 * a_d, xc + 0.5 * a_d, y0, y1, zd - 0.5 * a_d, zd + 0.5 * a_d, STEEL)
        if x_m + L_m > (i + 1.5) * seg or xc - 0.5 * B - L_in < (i - 0.5) * seg:
            raise ValueError(f"cooler_body: fan {i + 1} runs into its neighbour on that side")
    # the clinker outlet: the HRB deck's rollers in line with the grate
    # (tops at z = 0, the last one hrb_drop lower), their geared motors off
    # the +y side; the chute under them between the undergrate's walls
    r_h, p_h, n_h = 0.5 * v(gc["hrb_roller_D"]), v(gc["hrb_pitch"]), int(v(gc["hrb_rollers"]))
    a_hm, L_hm = v(b["hrb_motor_side"]), v(b["hrb_motor_L"])
    for k in range(n_h):
        xr = L + (k + 0.5) * p_h
        zr = -r_h - (v(gc["hrb_drop"]) if k == n_h - 1 else 0.0)
        if zr - r_h < zg + 0.3:
            raise ValueError("cooler_body: the HRB's rollers reach the ground")
        cyl(f"hrb_roller_{k + 1}", (xr, -(yo - tu), zr), (0.0, 1.0, 0.0), r_h, 2.0 * (yo - tu), STEEL)
        cyl(f"hrb_shaft_{k + 1}", (xr, yo - tu, zr), (0.0, 1.0, 0.0), 0.12, tu + 0.4, GREY)
        box(f"hrb_motor_{k + 1}", xr - 0.5 * a_hm, xr + 0.5 * a_hm, yo + 0.4, yo + 0.4 + L_hm,
            zr - 0.5 * a_hm, zr + 0.5 * a_hm, BLUE)
    # the ground slab, open under the chute (the clinker falls through it to
    # the conveyor below; user, 23 Nov 2026)
    ys = yo + gap + 2.0 * max(v(b["fan_volute_ratio"]) * 0.5 * fn["D2"] for fn in fans) + 0.5
    yc_ = yo - tu                                      # the chute's inner sides
    box("ground_slab", -tc, L, -ys, ys, zg - 0.3, zg, CONCRETE)
    box("ground_slab_end", Lt, Lt + tc, -ys, ys, zg - 0.3, zg, CONCRETE)
    box("ground_slab_m", L, Lt, -ys, -yc_, zg - 0.3, zg, CONCRETE)
    box("ground_slab_p", L, Lt, yc_, ys, zg - 0.3, zg, CONCRETE)
    solid = bodies
    box_all = tuple(min(q["box"][i] for q in solid) for i in range(3)) + tuple(max(q["box"][i] for q in solid) for i in range(3, 6))
    return {"bodies": bodies, "box": box_all, "h_undergrate": h_u, "z_ground": zg, "lanes": n_l,
            "lane_w": wl, "fans": fans, "hrb_L": L_h,
            "h_undergrate_holderbank": 0.56 * w}


def _air_h(T, T_ref=298.15):
    """Dry air's sensible enthalpy [J/kg] from T_ref, cp of physics/shell.py
    (cp_air, a polynomial in T) integrated exactly."""
    c = (1034.09, -0.2849, 7.8173e-4, -4.9701e-7, 1.0777e-10)

    def H(t):
        return sum(ci * t ** (i + 1) / (i + 1) for i, ci in enumerate(c))
    return H(T) - H(T_ref)


def _air_T_of_h(h, lo=200.0, hi=2500.0):
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _air_h(mid) < h:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def kiln_flame_boundaries(g):
    """The flame volume's boundary values, one per kiln_flame() face (CFD
    set-up input, kiln frame). Air streams from kiln_air_split() and the
    burner (kiln_burner()), the tertiary air from the calciner's boundary
    (calciner_boundaries()).

    The outlet seal's cold leak has no face of its own (user decision,
    23 Nov 2026): it enters with the secondary air through segment 1, at
    the mixed temperature (an enthalpy balance, dry air); listed apart in
    "streams". The local cold jet at the seal is not modelled.

    Each: {"kind": mass_flow_inlet | mass_flow_outlet | pressure_outlet,
    "m" [kg/s] (None: the solver's), "T" [K] (None: the solver's), "gas":
    air | None, "particles": {...} | None, "note"}. "streams" lists every
    stream in [kg/s]; "balance" in = out (the fuel burns into gas and
    ash, all leaving by the kiln gas outlet)."""
    b, h = g["kiln_burner"], g["kiln_hood"]
    split, ch = kiln_air_split(g), kiln_burner(g)
    ta = calciner_boundaries(g)["tertiary_air_inlet"]
    T0, T_sec = v(b["primary_air_T"]), v(h["secondary_air_T"])
    m_sec, m_seal = split["secondary"], split["seal"]
    m_in1 = m_sec + m_seal
    T_in1 = _air_T_of_h((m_sec * _air_h(T_sec) + m_seal * _air_h(T0)) / m_in1)
    fuel = v(b["fuel_flow"])
    streams = {
        "secondary_air": m_sec, "seal_leak": m_seal, "tertiary_air": ta["flow"],
        "axial_air": ch["m_axial"], "swirl_air": ch["m_swirl"], "conveying_air": ch["m_transport"],
        "coal": fuel,
    }
    m_in = sum(streams.values())
    m_ta_out = ta["flow"]
    bc = {
        "secondary_air_in": {"kind": "mass_flow_inlet", "m": m_in1, "T": T_in1, "gas": "air", "particles": None,
                             "note": "secondary air + the outlet seal's leak (no face of its own), mixed"},
        "tertiary_supply_in": {"kind": "mass_flow_inlet", "m": ta["flow"], "T": ta["T"], "gas": "air",
                               "particles": None, "note": "cooler segment 2: the tertiary air's supply"},
        "tertiary_air_out": {"kind": "mass_flow_outlet", "m": m_ta_out, "T": None, "gas": None, "particles": None,
                             "note": "to the calciner: the calciner's tertiary air inlet flow"},
        "kiln_gas_out": {"kind": "pressure_outlet", "m": None, "T": None, "gas": None, "particles": None,
                         "note": "0 Pa gauge (reference); carries the rest"},
        "coal_in": {"kind": "mass_flow_inlet", "m": ch["m_transport"], "T": T0, "gas": "air",
                    "particles": {"m": fuel, "T": T0, "size": {
                        "dist": "rosin_rammler", "d_mean": v(b["fuel_rr_mean"]), "n": v(b["fuel_rr_n"]),
                        "d_min": v(b["fuel_d_min"]), "d_max": v(b["fuel_d_max"])}},
                    "note": "conveying air (not in the twin) + the petcoke"},
        "axial_in": {"kind": "mass_flow_inlet", "m": ch["m_axial"], "T": T0, "gas": "air", "particles": None,
                     "note": "the twin's primary air, axial share"},
        "swirl_in": {"kind": "mass_flow_inlet", "m": ch["m_swirl"], "T": T0, "gas": "air", "particles": None,
                     "note": "the twin's primary air, swirl share"},
    }
    names = {f[0] for f in kiln_flame(g)["faces"]}
    if set(bc) != names:
        raise ValueError(f"kiln_flame_boundaries: faces {sorted(names ^ set(bc))} without a value")
    return {"bc": bc, "streams": streams,
            "balance": {"in": m_in, "tertiary_out": m_ta_out, "kiln_gas_out": m_in - m_ta_out},
            "T_secondary_mixed": T_in1}


def chamber_section(g):
    """The chamber's x-z section (user sketch, 21 Nov 2026), x from the
    calciner axis (the kiln on +x), z up from the chamber's floor level
    (the kiln axis a over it at x = a, a = kiln D / 2 + the layout
    margin), the plan 2 a across (y):

    - the calciner's throat, D_throat, its walls x = +-r: the left one
      runs down to the ramp's top, the right one to the kiln's roof
      line; the chamber's top (the calciner's throat foot, user decision
      22 Nov 2026: the calciner sits on the roof, no throat extension)
      is the roof's highest point under the throat, at x = -r, so the
      throat in the chamber is only the wedge between the sloping roof
      and that level (0 at x = -r, 2 r tan(alpha) at x = +r);
    - the roof: the kiln tube's top line carried in at kiln.slope, from
      the mouth to x = -r; the left wall x = -r from the roof down to
      the ramp's top;
    - the floor: the ramp, ramp_deg from the throat's left wall to a
      foot ramp_foot long, the foot the kiln's bottom line carried in;
    - the mouth: the kiln's end face, square to its axis at x = a (its
      lips a R sin(alpha) either side of x = a), and on it the kiln
      tube's stub (mouth_stub_over_D D long; the kiln gas inlet is its
      end disc).
    The topology drawing (plant_topology_2d.bas) draws the mouth plumb
    at x = a; the R sin(alpha) = 0.07 m between the two is invisible
    at its scale."""

    kl, cal = kiln(g), calciner(g)
    kic = g["kiln_inlet_chamber"]
    a = 0.5 * kl["D"] + v(g["layout"]["chamber_margin"])
    R = 0.5 * kl["D"]
    r = 0.5 * cal["D_throat"]
    alpha = math.atan(0.01 * kl["slope"])
    ramp = math.radians(v(kic["ramp_deg"]))
    foot = v(kic["ramp_foot"])
    z_ax = a                                         # the kiln axis at x = a
    sa, ca, ta = math.sin(alpha), math.cos(alpha), math.tan(alpha)

    def roof(x):                                     # the kiln's top line
        return z_ax + R / ca + (a - x) * ta

    def bottom(x):                                   # the kiln's bottom line
        return z_ax - R / ca + (a - x) * ta

    lip_low = (a - R * sa, z_ax - R * ca)
    lip_up = (a + R * sa, z_ax + R * ca)
    toe = (a - foot, bottom(a - foot))
    ramp_top = (-r, toe[1] + (toe[0] + r) * math.tan(ramp))
    roof_left = (-r, roof(-r))
    height = roof_left[1]                            # the calciner's throat foot
    profile = [ramp_top, toe, lip_low, lip_up, roof_left]
    area = 0.5 * abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(profile, profile[1:] + profile[:1])))
    L_stub = v(kic["mouth_stub_over_D"]) * kl["D"]
    stub_end = (a + L_stub * ca, z_ax - L_stub * sa)
    v_box = area * 2.0 * a
    v_throat = math.pi * r * r * (height - roof(0.0))   # the wedge: roof linear in x, its mean over the disc
    v_stub = math.pi * R * R * L_stub
    return {
        "a": a,
        "side": 2.0 * a,
        "height": height,
        "D_throat": cal["D_throat"],
        "r_throat": r,
        "R_mouth": R,
        "alpha": alpha,
        "z_axis": z_ax,
        "ramp_deg": math.degrees(ramp),
        "ramp_foot": foot,
        "lip_low": lip_low,
        "lip_up": lip_up,
        "toe": toe,
        "ramp_top": ramp_top,
        "roof_left": roof_left,
        "roof_at_throat": roof(r),
        "profile": profile,
        "profile_area": area,
        "L_stub": L_stub,
        "stub_end": stub_end,
        "V_box": v_box,
        "V_throat": v_throat,
        "V_stub": v_stub,
        "volume": v_box + v_throat + v_stub,
        "plan_area": (a + r) * 2.0 * a,          # the chamber's plan, throat wall to mouth
    }


def kiln_inlet_chamber(g):
    """The chamber is the same square round the kiln end: the kiln gas
    leaves the tube (inner D) into it and rises through its plan area to
    the calciner's throat; its velocity there is held to the literature's
    kiln-inlet limit, as the tube's own is reported."""

    kg = calciner_boundaries(g)["kiln_gas_inlet"]
    kl = kiln(g)
    side = 2.0 * layout(g)["a_chamber"]
    q = kg["flow"] / kg["rho"]
    vmax = v(g["kiln_inlet_chamber"]["gas_velocity_max"])
    sec = chamber_section(g)
    return {
        **sec,
        "q": q,
        "side": side,
        "u_kiln": q / (0.25 * math.pi * kl["D"] ** 2),
        "u_chamber": q / sec["plan_area"],
        "side_min": math.sqrt(q / vmax),
        "u_max": vmax,
    }


# ======================================================================
# The meal pipes C1-C5: scaled from the calciner's feed pipe by mass flux
# ======================================================================
def meal_pipes(g):
    """Each stage's meal pipe at the mass flux of the one literature pipe,
    the calciner's feed pipe (D_feed, one string's C4 meal): C1 has two
    pipes per string (each half the string's meal), C2-C4 one (the string's
    meal), C5 one (the meal leaving the calciner for the kiln). The slope is
    the calciner pipe's (cyclone_domain.meal_slope); length, route and flap
    position are the layout's and unknown.

    flux_dust is the same meal through the cyclone's dust outlet (an FLS
    ratio, cyclone(g).D_dust), dust_over_pipe its ratio to the pipe's
    flux. The two sizes rest on different sources and are kept apart:
    C1's outlet (FLS dust_D/D ~0.092, against ~0.13 for C2-C5) carries
    ~2.25x the pipe's flux. No source gives a design flux for a preheater
    cyclone's outlet; the CFD and the twin see it only as a boundary."""

    m = g["meal_pipe"]
    m_feed = v(m["feed_per_string"])
    d_ref = v(g["calciner"]["D_feed"])
    a_ref = 0.25 * math.pi * d_ref ** 2
    flux = m_feed / a_ref
    slope = v(g["cyclone_domain"]["meal_slope"])
    flows = {1: 0.5 * m_feed, 2: m_feed, 3: m_feed, 4: m_feed, 5: v(m["c5_meal_per_string"])}
    count = {1: 2, 2: 1, 3: 1, 4: 1, 5: 1}
    out = {}
    for s_, mdot in flows.items():
        area = mdot / flux
        d_dust = cyclone(g, f"C{s_}")["D_dust"]
        flux_dust = mdot / (0.25 * math.pi * d_dust ** 2)
        out[s_] = {
            "count_per_string": count[s_],
            "m": mdot,
            "flux": flux,
            "D": math.sqrt(4.0 * area / math.pi),
            "area": area,
            "slope": slope,
            "D_dust": d_dust,
            "flux_dust": flux_dust,
            "dust_over_pipe": flux_dust / flux,
        }
    return out


# ======================================================================
# A cyclone's slot inlet and outlet pipe (cyclone.bas Derive)
# ======================================================================
def cyclone_slot_inlet(g, name):
    """The straight, sloped tangential inlet duct of a cyclone without
    a volute (C1), in the macro's frame: axis z from the dust outlet,
    the gas entering towards +x, the duct's outer wall tangent to the
    barrel at y = R. The top of the opening sits inlet_roof_clearance
    below the roof where the duct's inner wall meets the barrel; the
    face is inlet_duct_length back along the duct axis from where the
    centreline crosses the tangent plane x = 0; the duct stops
    volute_tongue short of the barrel (x = -x_trim, the cut-water)."""

    c = cyclone(g, name)
    if c["volute"]:
        raise ValueError(f"{name} has a volute, not a slot inlet")
    d = g["cyclone_domain"]
    R = 0.5 * c["D_barrel"]
    z_roof = c["height"]
    y_outer = R - v(d["inlet_tangent_relief"])
    y_inner = R - c["W_inlet"]
    th = math.radians(c["inlet_slope"])
    dx, dz = math.cos(th), -math.sin(th)
    nx, nz = math.sin(th), math.cos(th)

    reach = math.sqrt(R * R - y_inner * y_inner)
    z_top0 = z_roof - v(d["inlet_roof_clearance"]) - reach * (nx / nz)
    z_bot0 = z_top0 - c["H_inlet"] / nz
    L_in = v(d["inlet_duct_length"])
    ce_x = -L_in * dx
    ce_z = 0.5 * (z_top0 + z_bot0) - L_in * dz
    t = v(d["volute_tongue"])
    return {
        "y_inner": y_inner,
        "y_outer": y_outer,
        "slope_deg": c["inlet_slope"],
        "axis": (dx, dz),
        "normal": (nx, nz),
        "reach": reach,
        "z_top0": z_top0,
        "z_bot0": z_bot0,
        "face_centre": (ce_x, 0.5 * (y_inner + y_outer), ce_z),
        "x_trim": math.sqrt(t * (2.0 * R - t)),
        "length": L_in,
    }


def cyclone_duct_inlet(g, name):
    """The inlet duct's end face and axis, slot or volute, in the
    macro's frame (gas entering towards +x): what a riser in front of
    the duct joins onto. A slot is cyclone_slot_inlet. A volute's duct
    (cyclone.bas VOLUTE_ON) is horizontal and flush with the roof, its
    inner wall volute_tongue outside the barrel's tangent line, its
    face inlet_duct_length back from the tangent plane x = 0."""

    c = cyclone(g, name)
    if not c["volute"]:
        return cyclone_slot_inlet(g, name)
    if c["inlet_slope"] != 0.0:
        raise ValueError(f"{name}: a volute is built horizontal (inlet_slope 0)")
    d = g["cyclone_domain"]
    R = 0.5 * c["D_barrel"]
    z_roof = c["height"]
    y_inner = R + v(d["volute_tongue"])
    y_outer = y_inner + c["W_inlet"]
    L_in = c["inlet_duct_length"]
    return {
        "y_inner": y_inner,
        "y_outer": y_outer,
        "slope_deg": 0.0,
        "axis": (1.0, 0.0),
        "normal": (0.0, 1.0),
        "z_top0": z_roof,
        "z_bot0": z_roof - c["H_inlet"],
        "face_centre": (-L_in, 0.5 * (y_inner + y_outer), z_roof - 0.5 * c["H_inlet"]),
        "length": L_in,
    }


def cyclone_volute_extent(g, name):
    """How far a volute's scroll reaches outside the barrel, as
    cyclone.bas samples it: the Archimedean spiral r = R + t + W (1 -
    phi / pi), phi clockwise from +y, over a half turn, then easing
    onto the barrel as r = R + t (1 - u)^2 over 2 pi t / W (22 Nov
    2026: tangent to it, no step), at 3600 steps.
    x_max on the far side of the duct's tangent plane, y_min where the
    scroll closes behind the barrel."""

    c = cyclone(g, name)
    d = g["cyclone_domain"]
    r_t = 0.5 * c["D_barrel"] + v(d["volute_tongue"])
    W = c["W_inlet"]
    x_max = y_min = 0.0
    t = v(d["volute_tongue"])
    ph_end = math.pi + 2.0 * math.pi * t / W
    for k in range(3601):
        ph = ph_end * k / 3600.0
        if ph <= math.pi:
            r = r_t + W - W * ph / math.pi
        else:
            u = (ph - math.pi) / (ph_end - math.pi)
            r = r_t - t + t * (1.0 - u) ** 2
        x_max = max(x_max, r * math.sin(ph))
        y_min = min(y_min, r * math.cos(ph))
    return {"x_max": x_max, "y_min": y_min, "r_start": r_t + W, "r_end": r_t - t}


def riser_inlet(g, name, D_riser=None, offset=None):
    """A riser's top into C(name)'s level inlet duct (R2-R4 into C2-C4,
    and the C4 CFD domain's own inlet; user decisions, 17 Nov and 22 Nov
    2026), in cyclone_duct_inlet's frame (x along the duct towards the
    volute, its face at x = -L_in; y across; z from the roof down as
    "drop").

    The riser (D_riser, the cyclone below's outlet bore; C(name)'s own
    D_x if not given) stands vertical under the duct's axis (y = the
    duct's middle) and an inclined flat-faced duct climbs from it into
    the level duct (riser_elbow). Its axis is riser_duct_run_min back
    from the face at least, the riser riser_barrel_clearance clear of
    the barrel; `offset` (a column spacing shared by several risers)
    puts it further out (the inclined duct then longer)."""

    c = cyclone(g, name)
    if not c["inlet_riser"]:
        raise ValueError(f"{name} has no riser inlet")
    s = cyclone_duct_inlet(g, name)
    d = g["cyclone_domain"]
    D = c["D_vortex"] if D_riser is None else D_riser
    R = 0.5 * c["D_barrel"]
    H, W = c["H_inlet"], c["W_inlet"]
    y_d = 0.5 * (s["y_inner"] + s["y_outer"])
    clr = v(d["riser_barrel_clearance"])
    slope, taper = v(d["riser_duct_slope_deg"]), v(d["riser_taper_deg"])
    run_min = riser_duct_run_min(D, W, H, slope, taper)
    least = max(R + 0.5 * D + clr, math.hypot(s["length"] + run_min, y_d))
    off = least if offset is None else offset
    if off < least - 1e-9:
        raise ValueError(f"{name}: a riser {off:.3f} m off its axis is closer than its elbow or the barrel allow "
                         f"(needs {least:.3f})")
    x_j = math.sqrt(off * off - y_d * y_d)       # the riser axis back from x = 0
    run = x_j - s["length"]                       # riser axis back from the duct face
    el = riser_elbow(run, D, W, H, slope, taper)
    w = 0.5 * W
    dots = (s["length"] * x_j + (y_d + w) * y_d, s["length"] * x_j + (y_d - w) * y_d)
    out = {
        "D": D,
        "offset": off,
        "clearance": off - R - 0.5 * D,
        "x": -x_j,
        "y": y_d,
        "run": run,
        "level": s["length"],
        # the duct face's outer / inner corners in the plant section
        # (the vertical plane of both axes; t from the riser's axis
        # towards the cyclone's), for plant_topology_2d.bas
        "t_out": off - max(dots) / off,
        "t_in": off - min(dots) / off,
        "duct_volume": W * H * s["length"],
        "duct_wall_area": 2.0 * (W + H) * s["length"],
    }
    out.update(el)
    return out


def riser_duct_run_min(D, W, H, slope_deg, taper_deg):
    """The least run (riser axis back from the level duct's face) of
    riser_elbow: the mitre's roof corner (H/2) tan(slope/2) behind the
    face, the side walls' taper from the riser's D to W at taper_deg
    each, and the riser's radius."""
    taper = max(0.0, 0.5 * (D - W)) / math.tan(math.radians(taper_deg))
    return 0.5 * H * math.tan(0.5 * math.radians(slope_deg)) + taper + 0.5 * D


def riser_elbow(run, D, W, H, slope_deg, taper_deg, n=4000):
    """A riser's top into C(k)'s level duct (user decision, 22 Nov 2026,
    "aynısını yapalım", from a plant image: the riser goes straight up
    and a flat-faced rectangular duct climbs from it to the cyclone's
    inlet). In the level duct's frame (x along it, its face at x = 0
    here; z from its centreline, H high): the inclined duct's centreline
    rises at slope_deg (a) through the face's centre, its section H
    (normal to it) by w(x); the union with the level duct mitres them --
    the roof lines meet (H/2) tan(a/2) behind the face, the floors as far
    in front. The riser (D, axis `run` behind the face) stands up into
    it and is cut by the inclined roof; the inclined floor -- one plane,
    constant slope -- meets the riser's front half along half an ellipse
    (the "parabolic" seam). The duct is D wide back to the riser's axis
    (its sides tangent to the riser, its back the riser itself) and
    narrows to W at taper_deg at most, from the riser's front to the
    roof's mitre. No step anywhere.

    drop: the level duct's roof down to the seam's lowest points (the
    riser's sides, where its straight part ends); drop_top: down to the
    riser's top on its axis (the inclined roof). Volume and wall (exact,
    the union above the seam's foot, the level duct x > -0 not counted
    but for the mitre's floor wedge under it): the riser's back half,
    the inclined duct, the mitre's wedge."""
    a = math.radians(slope_deg)
    if run < riser_duct_run_min(D, W, H, slope_deg, taper_deg) - 1e-9:
        raise ValueError(f"a riser {run:.3f} m behind the duct face leaves no room for the inclined duct")
    r = 0.5 * D
    w0 = max(D, W)
    ta, ca = math.tan(a), math.cos(a)
    hv = H / ca                                     # the inclined duct's vertical depth
    x_r = -run                                      # riser axis
    x_rm = -0.5 * H * math.tan(0.5 * a)             # roofs meet
    x_fm = -x_rm                                    # floors meet
    x_t0, x_t1 = x_r + r, x_rm                      # the sides narrow, w0 -> W

    def floor(x):
        return x * ta - 0.5 * hv                    # z from the level duct's centreline

    def roof(x):
        return x * ta + 0.5 * hv

    def width(x):
        if x <= x_t0:
            return w0
        if x >= x_t1:
            return W
        return w0 + (W - w0) * (x - x_t0) / (x_t1 - x_t0)

    def h_side(x):                                  # the side walls' depth outside the level duct
        if x <= x_rm:
            return hv
        if x <= 0.0:
            return 0.5 * H - floor(x)
        return max(0.0, -0.5 * H - floor(x))

    xs = np.linspace(x_r, x_fm, n + 1)
    ws = np.array([width(x) for x in xs])
    hs = np.array([h_side(x) for x in xs])
    slope_w = np.gradient(ws, xs)
    vol = np.trapz(ws * hs, xs) + 0.5 * math.pi * r * r * hv
    taper_len = x_t1 - x_t0
    ang = math.degrees(math.atan(0.5 * (w0 - W) / taper_len)) if taper_len > 0 else 0.0
    a_floor = np.trapz(ws, xs) / ca - 0.5 * math.pi * r * r / ca
    m_roof = xs <= x_rm
    a_roof = np.trapz(ws[m_roof], xs[m_roof]) / ca
    a_side = 2.0 * np.trapz(hs * np.sqrt(1.0 + (0.5 * slope_w) ** 2), xs)
    a_riser = math.pi * r * hv + 0.5 * math.pi * r * r / ca
    # the level roof gains W x (-x_rm) behind the face, its floor loses
    # as much in front of it (x_fm = -x_rm): they cancel
    drop = 0.5 * H - floor(x_r)
    return {
        "slope_deg": slope_deg,
        "taper_deg": ang,
        "taper_L": taper_len,
        "width0": w0,
        "mitre_back": -x_rm,                        # the roofs' corner behind the face
        "mitre_front": x_fm,                        # the floors' corner in front of it
        "drop": drop,
        "drop_top": 0.5 * H - roof(x_r),
        "length": 0.5 * hv + run / ca,              # riser axis from the seam's foot, then the duct's centreline
        "volume": vol,
        "wall_area": a_floor + a_roof + a_side + a_riser,
    }


def cfd_riser_inlet(g, name):
    """The riser inlet of the C4 CFD domain (C2-C4 are C4; C5 is it x
    its scale): R2 / R3 as the plant has them -- C4's own D_x, the
    columns' shared offset -- and riser_cfd_stub_over_D of vertical
    riser under the transition, where the domain's gas inlet is."""
    base = "C4"
    r = dict(riser_inlet(g, base, None, layout(g)["column_offset"]))
    r["stub"] = v(g["cyclone_domain"]["riser_cfd_stub_over_D"]) * r["D"]
    k = cyclone_scale(g, name) if name != base else 1.0
    if k != 1.0:
        for key in ("D", "offset", "clearance", "x", "y", "run", "level", "stub"):
            r[key] *= k
        for key in ("duct_volume",):
            r[key] *= k ** 3
        for key in ("duct_wall_area",):
            r[key] *= k ** 2
        # the volute's tongue is not scaled (cyclone.bas, C5_TONGUE), so
        # the duct's middle -- the riser's y -- is C(name)'s own, and the
        # riser's x and run (and so the elbow's radius) follow from it at
        # the scaled offset (the solid's frame)
        c = cyclone(g, name)
        d = g["cyclone_domain"]
        r["y"] = 0.5 * c["D_barrel"] + v(d["volute_tongue"]) + 0.5 * c["W_inlet"]
        x_j = math.sqrt(r["offset"] ** 2 - r["y"] ** 2)
        r["x"] = -x_j
        r["run"] = x_j - r["level"]
        r.update(riser_elbow(r["run"], r["D"], c["W_inlet"], c["H_inlet"], v(d["riser_duct_slope_deg"]),
                             v(d["riser_taper_deg"])))
        w = 0.5 * c["W_inlet"]
        dots = (r["level"] * x_j + (r["y"] + w) * r["y"], r["level"] * x_j + (r["y"] - w) * r["y"])
        r["t_out"] = r["offset"] - max(dots) / r["offset"]
        r["t_in"] = r["offset"] - min(dots) / r["offset"]
    return r


def cyclone_outlet(g, name):
    """The outlet pipe above the roof, in the slot inlet's frame: it
    rises outlet_rise from the roof, then ends there (0 deg), or bends
    through outlet_turn about an axis outlet_bend_R out along +x and
    drops (180 deg, down to outlet_run below the bend start) or runs on
    along +x (90 deg). outlet_side -1 (C1 since 24 Nov 2026): the 180
    deg bend goes along -x, back over the inlet duct; leg_x stays the
    distance, "side" the sign."""

    c = cyclone(g, name)
    z_roof = c["height"]
    z_bend = z_roof + c["outlet_rise"]
    r_bend = c["outlet_bend_R"]
    out = {
        "D": c["D_vortex"],
        "z_roof": z_roof,
        "z_bend": z_bend,
        "bend_R": r_bend,
        "bend_centre": (c["outlet_side"] * r_bend, z_bend),
        "turn_deg": c["outlet_turn"],
        "side": c["outlet_side"],
    }
    if c["outlet_turn"] == 0.0:
        # straight up (C2-C5 since 17 Nov 2026): the CFD domain ends in
        # a level disc outlet_rise over the roof, on the axis
        out["z_end"] = z_bend
        out["z_top"] = z_bend
    elif c["outlet_turn"] == 180.0:
        out["leg_x"] = 2.0 * r_bend
        out["z_end"] = z_bend - c["outlet_run"]
    else:
        out["z_leg"] = z_bend + r_bend
        out["x_end"] = r_bend + c["outlet_run"]
    return out


# ======================================================================
# C1's own riser branch (cyclone.bas Derive, the C1 case)
# ======================================================================
def r1_D(g):
    """R1's bore: C2's outlet pipe (its vortex finder) straight up, no
    reducer (user decision, 21 Nov 2026; it was the published 3.07)."""
    return cyclone(g, "C2")["D_vortex"]


def c1_branch(g):
    """C1's CFD riser branch, heights from its dust outlet and x from
    its axis (the inlet duct towards -x): the branch D (half R1's
    area), its bend radius, the bend's start (top of the straight
    branch), the feed and the domain's floor, and the branch axis's
    distance from the C1 axis."""

    d = g["cyclone_domain"]
    s = cyclone_duct_inlet(g, "C1")
    dx, dz = s["axis"]
    nx, nz = s["normal"]
    ce_x, _, ce_z = s["face_centre"]

    D_r1 = r1_D(g)
    r = math.sqrt(v(d["c1_riser_area_share"]) * 0.25 * D_r1 * D_r1)
    r_bend = v(d["c1_riser_bend_R_over_D"]) * 2.0 * r
    trans = v(d["c1_riser_transition"])
    g_x, g_z = ce_x - trans * dx, ce_z - trans * dz
    x_axis = g_x - r_bend * nx
    z_bend = g_z - r_bend * nz
    z_feed = z_bend - v(d["c1_riser_above_feed"])
    return {
        "D": 2.0 * r,
        "bend_R": r_bend,
        "bend_deg": 90.0 + s["slope_deg"],
        "x": -(x_axis - r_bend),
        "z_bend": z_bend,
        "z_feed": z_feed,
        "z_floor": z_feed - v(d["c1_riser_below_feed"]),
        "inlet_face_x": -ce_x,
        "transition": trans,
    }


# ======================================================================
# The twin C1 and R1's Y (c1_twin.bas; user decision, 13 Nov 2026)
# ======================================================================
def c1_twin(g):
    """The twin C1 as a mirror pair over one R1, in the pair's frame:
    z from the C1 dust outlets, x across the pair (mirror plane x = 0),
    y the inlet ducts' direction. Each C1 is its CFD domain (with its
    riser branch, c1_branch) turned 90 deg so its duct runs along +y on
    the barrel's side facing the other; the second is the first's
    mirror. The branches then rise side by side at x = +-b, c1_branch's
    x in front of the barrels, and R1 between them on the mirror plane.

    The spacing is the tightest the branches allow: their walls (the
    widest part: the branch circle, its bend and transition) c1_twin_gap
    apart. R1's Y is plant_topology_2d.bas's: R1's walls open at 45 deg
    to the branches' outer walls, the branches' inner walls rise 45 deg
    from the crotch on R1's axis, each branch keeping its width; the
    branches' straight run starts at the CFD domain's floor."""

    br = c1_branch(g)
    s = cyclone_duct_inlet(g, "C1")
    c = cyclone(g, "C1")
    R = 0.5 * c["D_barrel"]
    r = 0.5 * r1_D(g)
    rb = 0.5 * br["D"]
    gap = v(g["layout"]["c1_twin_gap"])
    y_duct = 0.5 * (s["y_inner"] + s["y_outer"])   # the duct's (and branch's) axis from the C1 axis
    spacing = 2.0 * (y_duct + rb) + gap
    b = 0.5 * spacing - y_duct
    y_rise = b - rb + 2.0 * math.sqrt(2.0) * rb - r
    return {
        "spacing": spacing,
        "barrel_gap": spacing - 2.0 * R,
        "branch_half": b,
        "branch_gap": 2.0 * (b - rb),
        "y_duct": y_duct,
        "y_branch": -br["x"],
        "y_rise": y_rise,
        "z_split": br["z_floor"] - y_rise,
        "z_branch": br["z_floor"],
        "gap": gap,
    }


# ======================================================================
# Layout (plant_topology_2d.bas Derive): one string, x > 0 outboard
# ======================================================================
def layout(g):
    """Where everything stands, z above ground, x from the calciner
    axis on one string's side: the kiln inlet chamber, the calciner on
    it, the tertiary air duct, C5 by the gooseneck leg, C4..C2 each
    roof flush with the top of the outlet bend below it, R1 straight up
    on C2's axis and the twin C1 over it. C4..C2 each over the outlet
    pipe of the one below, which rises beside it into its inlet."""

    L = g["layout"]
    cal, gn, kl = calciner(g), gooseneck(g), kiln(g)
    c = {s: cyclone(g, f"C{s}") for s in range(1, 6)}
    br = c1_branch(g)

    a_ch = 0.5 * kl["D"] + v(L["chamber_margin"])
    z_ch0 = v(L["kiln_axis_z"]) - a_ch
    sec = chamber_section(g)
    z0 = z_ch0 + sec["height"]                    # the calciner's throat foot, the top of the chamber's throat
    z_cone_top = z0 + cal["z_cone_top"]
    z_roof_cal = z0 + cal["z_roof"]
    z_gn_top = z0 + gn["crown"]                   # the arch's top
    z_gn_end = z0 + gn["z_end"]                   # the CFD's outlet faces
    ta = calciner_inlets(g)["tertiary_air"]
    r_ta = 0.5 * ta["D"]
    z_ta = z0 + ta["z"]

    r_leg = 0.5 * gn["D_leg"]
    x_inner = gn["x_leg"] + r_leg + v(L["gooseneck_to_c5_gap"]) + 0.5 * c[5]["D_barrel"]
    # R4..R2 (user decision, 17 Nov 2026): each the outlet pipe of the
    # cyclone below, straight up under the inlet of the one above and
    # turning in at its top; the two columns as far apart as the widest
    # riser asks, every riser then set at that spacing
    rs = {s: riser_inlet(g, f"C{s}", c[s + 1]["D_vortex"]) for s in (4, 3, 2)}
    offset = max(r["offset"] for r in rs.values())
    rs = {s: riser_inlet(g, f"C{s}", c[s + 1]["D_vortex"], offset) for s in (4, 3, 2)}
    x_outer = x_inner + offset
    col = {5: x_inner, 4: x_outer, 3: x_inner, 2: x_outer}

    # C5's inlet axis is the arms' level runs' axis (the CFD's outlet faces, which gooseneck()
    # puts at the same height by the same rule)
    z_dust = {5: z_ta + r_ta + v(L["c5_over_tertiary_air"])}

    def top(s):        # the outlet pipe's top, where its bend starts
        return z_dust[s] + c[s]["height"] + c[s]["outlet_rise"]

    # each C4..C2 stands with its dust outlet dust_over_roof over the roof
    # under it (the cyclone two below shares its column, its riser's top
    # just under this one's roof), or as high as the CFD outlet pipe
    # below and the riser's turn ask
    gap = v(L["dust_over_roof"])
    riser_vertical = {}
    for s in (4, 3, 2):
        below = s + 1
        roof_below = z_dust[below] + c[below]["height"]
        step = max(c[s]["height"] + gap, c[below]["outlet_rise"] + rs[s]["drop"])
        z_dust[s] = roof_below + step - c[s]["height"]
        riser_vertical[s] = step - rs[s]["drop"]

    tw = c1_twin(g)
    y_rise = tw["y_rise"]
    # R1 straight up on C2's axis (user decision, 17 Nov 2026): C2's
    # outlet pipe, its bore unchanged (21 Nov 2026), up to the Y
    z_foot = top(2)
    # C1 over C2's outlet pipe by the stage gap (its meal reaching R2),
    # or as high as R1's rise and Y ask before the C1 CFD branch's floor
    z_dust[1] = max(
        top(2) + v(L["stage_gap"]),
        z_foot + v(L["r1_up_min"]) + y_rise - br["z_floor"],
    )
    d_c1 = 0.5 * tw["spacing"]        # the twin's ducts face each other across R1's axis

    # The kiln out of the chamber's +x side, falling at its slope; the
    # cooler under its discharge, the hood (the chamber's mirror) on it
    alpha = math.atan(0.01 * kl["slope"])
    x_kiln_end = a_ch + kl["L"] * math.cos(alpha)
    z_kiln_end = v(L["kiln_axis_z"]) - kl["L"] * math.sin(alpha)
    co = cooler(g)
    z_cooler = z_kiln_end - 0.5 * kl["D"] - v(L["cooler_drop"]) - co["casing_height"]
    hd = kiln_hood(g)
    z_hood = z_kiln_end - hd["below"]               # on the cooler's roof
    # The chamber's section (user sketch, 21 Nov 2026): chamber_section
    x_toe, z_toe = sec["toe"][0], z_ch0 + sec["toe"][1]
    z_ramp_top = z_ch0 + sec["ramp_top"][1]

    return {
        "a_chamber": a_ch,
        "z_chamber_floor": z_ch0,
        "z_calciner_throat": z0,
        "z_calciner_cone_top": z_cone_top,
        "z_calciner_roof": z_roof_cal,
        "z_gooseneck_top": z_gn_top,
        "y_gooseneck": gn["y_off"],
        "z_gooseneck_cfd_end": z_gn_end,
        "z_tertiary_air": z_ta,
        "x_inner": x_inner,
        "x_outer": x_outer,
        "column_offset": offset,
        "col": col,
        "riser": rs,
        "riser_vertical": riser_vertical,
        "z_dust": z_dust,
        "z_roof": {s: z_dust[s] + c[s]["height"] for s in z_dust},
        "z_top": {s: top(s) for s in z_dust},
        "z_c5_inlet": z_dust[5] + c[5]["height"] - r_leg,
        "x_r1": x_outer,
        "d_c1": d_c1,
        "x_c1": (x_outer - d_c1, x_outer + d_c1),
        "z_r1_foot": z_foot,
        "z_r1_split": z_dust[1] + br["z_floor"] - y_rise,
        "z_tower": z_dust[1] + c[1]["height"] + c[1]["outlet_rise"] + c[1]["outlet_bend_R"] + 0.5 * c[1]["D_vortex"],
        "x_gooseneck_leg": gn["x_leg"],
        "chamber_ramp_deg": sec["ramp_deg"],
        "chamber_ramp_toe": (x_toe, z_toe),
        "z_chamber_ramp_top": z_ramp_top,
        "kiln_end": (x_kiln_end, z_kiln_end),
        "cooler_x": (x_kiln_end, x_kiln_end + co["length"]),
        "cooler_z": (z_cooler, z_cooler + co["casing_height"]),
        "hood_x": (x_kiln_end, x_kiln_end + hd["depth"]),
        "hood_z": (z_hood, z_hood + hd["H"]),
    }


# ======================================================================
# The gas paths between the stages (user decisions, 14 Oct 2026)
# ======================================================================
def _pipe(D, length):
    return {
        "D": D,
        "length": length,
        "volume": 0.25 * math.pi * D * D * length,
        "wall_area": math.pi * D * length,
    }


def _sum(*parts):
    return {
        "volume": sum(p["volume"] for p in parts),
        "wall_area": sum(p["wall_area"] for p in parts),
        "parts": parts,
    }


def stage_riser(g, k):
    """R(k), k = 2..4: the gas from C(k+1) up to C(k) (user decision,
    17 Nov 2026): C(k+1)'s outlet pipe straight up from its roof beside
    C(k) (its first outlet_rise the CFD domain's), the transition whose
    walls turn in at riser_slope_deg (circle -> the volute inlet) and
    the level duct into C(k)'s volute. Before, it was C(k+1)'s CFD
    outlet pipe, its 90 deg bend and a level leg 15 m over to C(k)."""
    s = k + 1
    c = cyclone(g, f"C{s}")
    L = layout(g)
    r = L["riser"][k]
    trans = {"D": r["D"], "length": r["length"], "volume": r["volume"], "wall_area": r["wall_area"]}
    duct = {"length": r["level"], "volume": r["duct_volume"], "wall_area": r["duct_wall_area"]}
    out = _sum(_pipe(c["D_vortex"], L["riser_vertical"][k]), trans, duct)
    out["riser"] = r
    return out


def r1_path(g):
    """R1, the gas from C2 up to the twin C1, per string: C2's CFD
    outlet pipe (its rise over the roof), then the same bore straight
    up on C2's axis to its Y (user decisions, 17 Nov 2026; 21 Nov 2026
    no reducer: R1 = C2's D_x), then each twin's branch (half R1's
    area) up to its bend, the bend, the transition and the inlet duct
    to the barrel. The Y's own short pieces are taken as the branches'
    run."""
    c2, br, L = cyclone(g, "C2"), c1_branch(g), layout(g)
    D2 = c2["D_vortex"]
    D1 = r1_D(g)
    up = L["z_r1_split"] - L["z_r1_foot"]
    branch_up = (L["z_dust"][1] + br["z_bend"]) - L["z_r1_split"]
    bend = math.radians(br["bend_deg"]) * br["bend_R"]
    duct = br["transition"] + v(g["cyclone_domain"]["inlet_duct_length"])
    n = cyclone(g, "C1")["per_string"]
    branch = _pipe(br["D"], branch_up + bend + duct)
    branches = {"volume": n * branch["volume"], "wall_area": n * branch["wall_area"]}
    out = _sum(
        _pipe(D2, c2["outlet_rise"]),
        _pipe(D1, up),
        branches,
    )
    out["branch"] = branch
    out["branches"] = n
    return out


def gooseneck_plant(g):
    """The gooseneck as the plant has it (user decisions, 14 Oct and
    15 Nov 2026): the neck, channel and arms as the CFD's (each arm an
    inclined piece and a level run), the level run going on from the CFD's
    outlet face to the C5's barrel at the same height (C5's inlet axis is
    the arms' axis). The arms stand in front of the vessel (y = -y_off):
    the C5s stand in their plane (no source places them in y), so no
    sideways run is added. Volume and wall area, both legs."""
    gn, L, c5 = gooseneck(g), layout(g), cyclone(g, "C5")
    D = gn["D_leg"]
    run = (L["x_inner"] - 0.5 * c5["D_barrel"]) - gn["x_leg"]
    leg = _pipe(D, run)
    return {
        "leg_length": leg["length"],
        "volume": gn["volume"] + 2.0 * leg["volume"],
        "wall_area": gn["wall_area"] + 2.0 * leg["wall_area"],
    }


# ======================================================================
# The twin's geometry (main.load_cfg puts it into the config)
# ======================================================================
# The config keys that are geometry: they come from here and must not
# be written in configs/twin_cfg.yaml.
TWIN_KEYS = {
    "kiln": ("length", "diameter", "lining"),
    "transition": ("length",),
    "motion": ("inclination_pct",),
    "calciner": ("length", "diameter", "zone_segments"),
    "preheater": ("strings", "stages"),
    "cooler": ("length", "width", "casing_height"),
}


def twin_sections(g=None):
    """The config keys of TWIN_KEYS, derived from the source.

    preheater.stages, in the twin's gas order (Stage 1 = C4 ... C1):
    each the riser below the cyclone plus the cyclone, per string --
    R4..R2 the CFD outlet pipes of C5..C3, R1 C2's outlet, R1 and the
    twin branches. calciner.zone_segments: the vessel above the meal's
    entry (calciner_above_feed; the fuel burns there), the gooseneck to
    the C5 inlets, the C5s (all strings)."""

    g = g or load()
    k, cal, coo, L = kiln(g), calciner(g), cooler(g), layout(g)
    strings = v(g["plant"]["strings"])

    stages = []
    for s in (4, 3, 2, 1):
        c = cyclone(g, f"C{s}")
        if s == 1:
            r = r1_path(g)
            br = c1_branch(g)
            h = L["z_dust"][1] + br["z_bend"] - L["z_roof"][2]
        else:
            r = stage_riser(g, s)
            h = L["z_roof"][s] - L["z_roof"][s + 1]          # the riser, roof below to roof
        stages.append({
            "cyclone": f"C{s}",
            "cyclones_per_string": c["per_string"],
            "cyclone_volume": c["volume"],
            "cyclone_wall_area": c["wet_area"],
            "cyclone_height": c["height"],
            "riser_volume": r["volume"],
            "riser_wall_area": r["wall_area"],
            "riser_height": h,
        })

    c5 = cyclone(g, "C5")
    gp = gooseneck_plant(g)
    vf = calciner_above_feed(g)
    n5 = strings * c5["per_string"]

    return {
        "kiln": {"length": k["L"], "diameter": k["D"], "lining": dict(k["lining"])},
        "transition": {"length": k["transition_L"]},
        "motion": {"inclination_pct": k["slope"]},
        "calciner": {
            "length": cal["H"],
            "diameter": cal["D"],
            "zone_segments": [
                {"name": "vessel", "volume": vf["volume"],
                 "wall_area": vf["wall_area"], "fuel": True},
                {"name": "gooseneck", "volume": gp["volume"], "wall_area": gp["wall_area"]},
                {"name": "C5", "volume": n5 * c5["volume"], "wall_area": n5 * c5["wet_area"]},
            ],
        },
        "preheater": {"strings": strings, "stages": stages},
        "cooler": {"length": coo["length"], "width": coo["width"],
                   "casing_height": coo["casing_height"]},
    }


def apply_to_config(cfg, g=None):
    """Put the twin's geometry into a loaded config, in place. A
    geometry key already written in the config is an error: the
    single source would have two values."""
    for section, keys in TWIN_KEYS.items():
        for key in keys:
            if key in (cfg.get(section) or {}):
                raise ValueError(
                    f"configs: {section}.{key} is geometry; it comes from "
                    "geometry/plant_geometry.yaml and must not be written in the config"
                )
    for section, values in twin_sections(g).items():
        if cfg.get(section) is None:
            cfg[section] = {}
        cfg[section].update(values)
    return cfg


def load_config(path):
    """A twin config file with the plant's geometry put in."""
    with open(path, encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    return apply_to_config(cfg)
