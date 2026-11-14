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
    "D_barrel", "H_barrel", "H_cone", "L_vortex", "D_vortex", "D_dust",
    "W_inlet", "H_inlet",
)
CYCLONE_FLAGS = (
    "inlet_slope", "volute", "outlet_turn", "outlet_rise_over_Dx",
    "outlet_bend_R_over_Dx", "outlet_run_over_Dx",
)


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
    c["per_string"] = v(node["per_string"])
    c["boi_radius"] = v(node.get("boi_radius", base["boi_radius"]))
    c["scale"] = k

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
    cylinder, coming in along +x on the -y side, a stub of it to its
    face past the vessel's tangent plane; the two meal pipes (+-x) and
    the two fuel pipes (+-y) just above it."""
    c, cal = g["calciner"], calciner(g)
    R = cal["R"]
    r = 0.5 * v(c["D_tertiary_air"])
    y_c = -(R - v(c["tertiary_air_wall_relief"]) - r)
    z_c = cal["z_cone_top"] + v(c["tertiary_air_cone_clearance"]) + r
    x_end = R + v(c["tertiary_air_stub_length"])
    v_ta = math.pi * r * r * x_end - chord_integral(r, R, y_c)

    rf = 0.5 * v(c["D_feed"])
    slope = v(g["cyclone_domain"]["meal_slope"])
    cf, sf = math.cos(math.radians(slope)), math.sin(math.radians(slope))
    z_wall = (z_c + r + v(c["feed_above_tertiary_air"])
              + rf / cf + (R - math.sqrt(R * R - rf * rf)) * sf / cf)
    depth = v(c["feed_depth"])
    return {
        "tertiary_air": {
            "D": 2.0 * r, "y": y_c, "z": z_c, "x_end": x_end,
            "top": z_c + r, "volume": v_ta, "end_area": math.pi * r * r,
        },
        "meal": calciner_pipe(R, rf, slope, z_wall, depth),
        "fuel": calciner_pipe(R, 0.5 * v(c["D_fuel"]), v(c["fuel_slope"]), z_wall, depth),
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


def _grid(centre, half, n):
    """Cell-centre coordinate arrays of a cube around `centre`, and a cell's
    volume. The cube is shifted by a few millimetres, by amounts that
    have no relation to the cells: a plane through the centre (the pipes'
    ends all are) would otherwise run exactly through whole layers of cell
    centres, and which side they fall on would be rounding noise."""
    h = 2.0 * half / n
    mid = (np.arange(n) + 0.5) * h - half
    x = (centre[0] + 0.00311 + mid)[:, None, None]
    y = (centre[1] + 0.00227 + mid)[None, :, None]
    z = (centre[2] + 0.00173 + mid)[None, None, :]
    return x, y, z, h ** 3


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
    return {
        "D": D,
        "L": L,
        "slope": v(k["slope"]),
        "transition_L": v(k["transition_L"]),
        "burning_L": L - v(k["transition_L"]),
        "volume": 0.25 * math.pi * D * D * L,
        "wall_area": math.pi * D * L,
    }


def cooler(g):
    c = g["cooler"]
    w, h = v(c["width"]), v(c["casing_height"])
    L = v(c["grate_area"]) / w
    n, nh = int(v(c["segments"])), int(v(c["hood_segments"]))
    hood_L = nh * L / n
    return {
        "width": w,
        "casing_height": h,
        "length": L,
        "grate_area": v(c["grate_area"]),
        "box_volume": w * L * h,
        "segments": n,
        "segment_L": L / n,
        "segment_area": w * L / n,
        "hood_segments": nh,
        "hood_L": hood_L,
        "hood_area": w * hood_L,
        # the walls: two sides, two ends, and the roof but for the hood's opening
        "wall_area": 2.0 * L * h + 2.0 * w * h + w * (L - hood_L),
    }


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
    return {
        "per_string": int(v(f["per_string"])),
        "rho": rho,
        "q": q,
        "q_h": q * 3600.0,
        "q_total_h": q * 3600.0 * v(g["plant"]["strings"]),
        "dp": dp,
        "p_shaft": p_shaft,
        "p_motor": p_shaft * v(f["motor_margin"]),
        "u_tip": u,
        "D_impeller": u / (math.pi * n),
        "D_inlet": math.sqrt(4.0 * q / (math.pi * v(f["inlet_velocity"]))),
    }


# ======================================================================
# The kiln burner (JETFLEX): thermal input, primary air, jet momentum
# ======================================================================
def kiln_burner(g):
    """The burner's duty and its primary air jet: the thermal input from
    the kiln's fuel, the primary air from its share of the kiln air, the
    momentum from FLSmidth's N/MW; the mean jet velocity is the momentum
    over the air flow, the jet area the air flow over its density (ambient
    pressure, the primary air's temperature) times the velocity."""

    b = g["kiln_burner"]
    q_th = v(b["fuel_flow"]) * v(b["fuel_LHV"])                 # MW
    m_pa = v(b["kiln_air_flow"]) * v(b["primary_air_fraction"])
    force = v(b["momentum_per_MW"]) * q_th                       # N
    u = force / m_pa
    rho = 101325.0 * 0.028965 / (R_GAS * v(b["primary_air_T"]))
    area = m_pa / (rho * u)
    return {
        "thermal_MW": q_th,
        "m_pa": m_pa,
        "momentum_N": force,
        "u_jet": u,
        "rho_pa": rho,
        "jet_area": area,
        "jet_D_eq": math.sqrt(4.0 * area / math.pi),
    }


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


def cyclone_outlet(g, name):
    """The outlet pipe above the roof, in the slot inlet's frame: it
    rises outlet_rise from the roof, bends through outlet_turn about
    an axis outlet_bend_R out along +x, then drops (180 deg, down to
    outlet_run below the bend start) or runs on along +x (90 deg)."""

    c = cyclone(g, name)
    z_roof = c["height"]
    z_bend = z_roof + c["outlet_rise"]
    r_bend = c["outlet_bend_R"]
    out = {
        "D": c["D_vortex"],
        "z_roof": z_roof,
        "z_bend": z_bend,
        "bend_R": r_bend,
        "bend_centre": (r_bend, z_bend),
        "turn_deg": c["outlet_turn"],
    }
    if c["outlet_turn"] == 180.0:
        out["leg_x"] = 2.0 * r_bend
        out["z_end"] = z_bend - c["outlet_run"]
    else:
        out["z_leg"] = z_bend + r_bend
        out["x_end"] = r_bend + c["outlet_run"]
    return out


# ======================================================================
# C1's own riser branch (cyclone.bas Derive, the C1 case)
# ======================================================================
def c1_branch(g):
    """C1's CFD riser branch, heights from its dust outlet and x from
    its axis (the inlet duct towards -x): the branch D (half R1's
    area), its bend radius, the bend's start (top of the straight
    branch), the feed and the domain's floor, and the branch axis's
    distance from the C1 axis."""

    d = g["cyclone_domain"]
    s = cyclone_slot_inlet(g, "C1")
    dx, dz = s["axis"]
    nx, nz = s["normal"]
    ce_x, _, ce_z = s["face_centre"]

    D_r1 = v(g["risers"]["R1"]["D"])
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
    s = cyclone_slot_inlet(g, "C1")
    c = cyclone(g, "C1")
    R = 0.5 * c["D_barrel"]
    r = 0.5 * v(g["risers"]["R1"]["D"])
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
    roof flush with the top of the outlet bend below it, R1 and the
    twin C1 over C2."""

    L = g["layout"]
    cal, gn, kl = calciner(g), gooseneck(g), kiln(g)
    c = {s: cyclone(g, f"C{s}") for s in range(1, 6)}
    br = c1_branch(g)

    a_ch = 0.5 * kl["D"] + v(L["chamber_margin"])
    z_ch0 = v(L["kiln_axis_z"]) - a_ch
    z0 = z_ch0 + 2.0 * a_ch                       # the calciner's throat foot on the chamber
    z_cone_top = z0 + cal["z_cone_top"]
    z_roof_cal = z0 + cal["z_roof"]
    z_gn_top = z0 + gn["crown"]                   # the arch's top
    z_gn_end = z0 + gn["z_end"]                   # the CFD's outlet faces
    ta = calciner_inlets(g)["tertiary_air"]
    r_ta = 0.5 * ta["D"]
    z_ta = z0 + ta["z"]

    r_leg = 0.5 * gn["D_leg"]
    x_inner = gn["x_leg"] + r_leg + v(L["gooseneck_to_c5_gap"]) + 0.5 * c[5]["D_barrel"]
    x_outer = x_inner + v(L["column_offset"])
    col = {5: x_inner, 4: x_outer, 3: x_inner, 2: x_outer}

    # C5's inlet axis is the arms' level runs' axis (the CFD's outlet faces, which gooseneck()
    # puts at the same height by the same rule)
    z_dust = {5: z_ta + r_ta + v(L["c5_over_tertiary_air"])}

    def top(s):        # the outlet pipe's top, where its bend starts
        return z_dust[s] + c[s]["height"] + c[s]["outlet_rise"]

    for s in (4, 3, 2):
        below = s + 1
        z_dust[s] = top(below) + c[below]["outlet_bend_R"] + 0.5 * c[below]["D_vortex"] - c[s]["height"]

    D_r1 = v(g["risers"]["R1"]["D"])
    r = 0.5 * D_r1
    tw = c1_twin(g)
    y_rise = tw["y_rise"]
    z_leg_top = top(2) + c[2]["outlet_bend_R"] + 0.5 * c[2]["D_vortex"]
    # C1 over C2's outlet pipe by the stage gap, or as high as R1's
    # rise and Y ask before the C1 CFD branch's floor
    z_dust[1] = max(
        top(2) + v(L["stage_gap"]),
        z_leg_top + v(L["r1_up_min"]) + y_rise - br["z_floor"],
    )
    d_r1 = c[2]["outlet_bend_R"] + c[2]["outlet_run"] + v(L["r1_leg_on"]) + r
    d_c1 = 0.5 * tw["spacing"]        # the twin's ducts face each other across R1's axis

    # The kiln out of the chamber's +x side, falling at its slope; the
    # cooler under its discharge, the hood (the chamber's mirror) on it
    alpha = math.atan(0.01 * kl["slope"])
    x_kiln_end = a_ch + kl["L"] * math.cos(alpha)
    z_kiln_end = v(L["kiln_axis_z"]) - kl["L"] * math.sin(alpha)
    co = cooler(g)
    z_cooler = z_kiln_end - 0.5 * kl["D"] - v(L["cooler_drop"]) - co["casing_height"]
    z_hood = z_kiln_end - a_ch
    ramp = math.atan(
        (z_ch0 + 2.0 * a_ch - v(L["kiln_axis_z"]) + 0.5 * kl["D"] / math.cos(alpha))
        / (2.0 * a_ch)
    )

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
        "col": col,
        "z_dust": z_dust,
        "z_roof": {s: z_dust[s] + c[s]["height"] for s in z_dust},
        "z_top": {s: top(s) for s in z_dust},
        "z_c5_inlet": z_dust[5] + c[5]["height"] - r_leg,
        "x_r1": x_outer - d_r1,
        "d_r1": d_r1,
        "d_c1": d_c1,
        "x_c1": (x_outer - d_r1 - d_c1, x_outer - d_r1 + d_c1),
        "z_r1_leg_top": z_leg_top,
        "z_r1_split": z_dust[1] + br["z_floor"] - y_rise,
        "z_tower": z_dust[1] + c[1]["height"] + c[1]["outlet_rise"] + c[1]["outlet_bend_R"] + 0.5 * c[1]["D_vortex"],
        "x_gooseneck_leg": gn["x_leg"],
        "chamber_ramp_deg": math.degrees(ramp),
        "kiln_end": (x_kiln_end, z_kiln_end),
        "cooler_x": (x_kiln_end, x_kiln_end + co["length"]),
        "cooler_z": (z_cooler, z_cooler + co["casing_height"]),
        "hood_x": (x_kiln_end, x_kiln_end + 2.0 * a_ch),
        "hood_z": (z_hood, z_hood + 2.0 * a_ch),
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
    """R(k), k = 2..4: the gas from C(k+1) up to C(k) is C(k+1)'s CFD
    outlet pipe itself -- its rise over the roof, its 90 deg bend and
    the leg level on to C(k)'s barrel wall (the drawing; the published
    Ø3.35-3.60 risers are not this plant's). At the pipe's bore all the
    way; the 45 deg taper onto the inlet is left out (simple, small)."""
    s = k + 1
    c, up = cyclone(g, f"C{s}"), cyclone(g, f"C{k}")
    D, R = c["D_vortex"], c["outlet_bend_R"]
    leg = v(g["layout"]["column_offset"]) - R - 0.5 * up["D_barrel"]
    return _sum(
        _pipe(D, c["outlet_rise"]),
        _pipe(D, 0.5 * math.pi * R),
        _pipe(D, leg),
    )


def r1_path(g):
    """R1, the gas from C2 up to the twin C1, per string: C2's CFD
    outlet (rise, 90 deg bend, leg on to R1's axis), R1 straight up to
    its Y, then each twin's branch (half R1's area) up to its bend,
    the 95 deg bend, the transition and the inlet duct to the barrel.
    The Y's own short pieces are taken as the branches' run."""
    c2, br, L = cyclone(g, "C2"), c1_branch(g), layout(g)
    D2, R2 = c2["D_vortex"], c2["outlet_bend_R"]
    D1 = v(g["risers"]["R1"]["D"])
    z_leg = L["z_top"][2] + R2
    up = L["z_r1_split"] - z_leg
    branch_up = (L["z_dust"][1] + br["z_bend"]) - L["z_r1_split"]
    bend = math.radians(br["bend_deg"]) * br["bend_R"]
    duct = br["transition"] + v(g["cyclone_domain"]["inlet_duct_length"])
    n = cyclone(g, "C1")["per_string"]
    branch = _pipe(br["D"], branch_up + bend + duct)
    branches = {"volume": n * branch["volume"], "wall_area": n * branch["wall_area"]}
    out = _sum(
        _pipe(D2, c2["outlet_rise"]),
        _pipe(D2, 0.5 * math.pi * R2),
        _pipe(D2, L["d_r1"] - R2),
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
    "kiln": ("length", "diameter"),
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
            below = cyclone(g, f"C{s + 1}")
            h = below["outlet_rise"] + below["outlet_bend_R"] + 0.5 * below["D_vortex"]
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
        "kiln": {"length": k["L"], "diameter": k["D"]},
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
