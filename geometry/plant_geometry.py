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
OVERLAP_N = 80


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


def _bend_overlap(r_leg, x_start, r_bend, n=OVERLAP_N):
    """Volume the two 180 deg bends share over the neck (their start
    discs overlap); a midpoint grid, as calciner.bas GnBendOverlap."""
    xa = x_start + r_bend
    hx = 2.0 * (r_leg - x_start) / n
    hy = 2.0 * r_leg / n
    hz = (r_bend + r_leg) / n
    mid = np.arange(n) + 0.5
    x = (-(r_leg - x_start) + mid * hx)[:, None, None]
    y = (-r_leg + mid * hy)[None, :, None]
    z = (mid * hz)[None, None, :]
    ra = np.sqrt((x - xa) ** 2 + z * z) - r_bend
    rb = np.sqrt((x + xa) ** 2 + z * z) - r_bend
    r2 = r_leg * r_leg
    hit = np.count_nonzero((ra * ra + y * y <= r2) & (rb * rb + y * y <= r2))
    return float(hit) * hx * hy * hz


@lru_cache(maxsize=None)
def _overlap_cached(r_leg, x_start, r_bend):
    return _bend_overlap(r_leg, x_start, r_bend)


def gooseneck(g):
    """The Y gooseneck as calciner.bas builds it: the neck on the
    axis, 1.25 neck D up; each leg's disc inside it, a 180 deg bend
    of 1.5 leg D outward and down, and the drop to where the leg ends
    (`end_at_vessel_H` of the vessel above its throat top). Volume
    (the bends' shared part counted once) and wall area (Pappus; the
    shared part's wall is not taken off: no closed form, small)."""

    gn = g["gooseneck"]
    cal = calciner(g)
    r_leg = 0.5 * v(gn["D_leg"])
    r_neck = gooseneck_neck_radius(g)
    x_start = r_neck - r_leg
    r_bend = v(gn["bend_R_over_D_leg"]) * 2.0 * r_leg
    rise = v(gn["rise_over_D_neck"]) * 2.0 * r_neck
    z_top = cal["z_roof"] + rise
    z_end = cal["z_throat_top"] + v(gn["end_at_vessel_H"]) * cal["H"]
    drop = z_top - z_end

    overlap = _overlap_cached(round(r_leg, 12), round(x_start, 12), round(r_bend, 12))
    v_neck = math.pi * r_neck * r_neck * rise
    v_bend = math.pi * r_leg * r_leg * math.pi * r_bend
    v_legs = 2.0 * math.pi * r_leg * r_leg * drop

    a_neck = 2.0 * math.pi * r_neck * rise
    a_bend = 2.0 * math.pi * r_leg * math.pi * r_bend
    a_legs = 2.0 * 2.0 * math.pi * r_leg * drop

    return {
        "D_leg": 2.0 * r_leg,
        "D_neck": 2.0 * r_neck,
        "x_leg_start": x_start,
        "x_leg": x_start + 2.0 * r_bend,
        "bend_R": r_bend,
        "rise": rise,
        "drop": drop,
        "z_top": z_top,
        "z_end": z_end,
        "bend_overlap": overlap,
        "volume": v_neck + 2.0 * v_bend - overlap + v_legs,
        "wall_area": a_neck + 2.0 * a_bend + a_legs,
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
    return {
        "width": w,
        "casing_height": h,
        "length": L,
        "grate_area": v(c["grate_area"]),
        "box_volume": w * L * h,
    }


# ======================================================================
# C1's own riser branch (cyclone.bas Derive, the C1 case)
# ======================================================================
def c1_branch(g):
    """C1's CFD riser branch, heights from its dust outlet and x from
    its axis (the inlet duct towards -x): the branch D (half R1's
    area), its bend radius, the bend's start (top of the straight
    branch), the feed and the domain's floor, and the branch axis's
    distance from the C1 axis."""

    c = cyclone(g, "C1")
    d = g["cyclone_domain"]
    R = 0.5 * c["D_barrel"]
    z_roof = c["height"]
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
        "bend_deg": 90.0 + c["inlet_slope"],
        "x": -(x_axis - r_bend),
        "z_bend": z_bend,
        "z_feed": z_feed,
        "z_floor": z_feed - v(d["c1_riser_below_feed"]),
        "inlet_face_x": -ce_x,
        "transition": trans,
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
    z_gn_top = z0 + gn["z_top"]
    z_gn_end = z0 + gn["z_end"]                   # the CFD's outlet faces
    ta = calciner_inlets(g)["tertiary_air"]
    r_ta = 0.5 * ta["D"]
    z_ta = z0 + ta["z"]

    r_leg = 0.5 * gn["D_leg"]
    x_inner = gn["x_leg"] + r_leg + v(L["gooseneck_to_c5_gap"]) + 0.5 * c[5]["D_barrel"]
    x_outer = x_inner + v(L["column_offset"])
    col = {5: x_inner, 4: x_outer, 3: x_inner, 2: x_outer}

    z_dust = {5: max(z_gn_end - c[5]["height"], z_ta + r_ta + v(L["c5_over_tertiary_air"]))}

    def top(s):        # the outlet pipe's top, where its bend starts
        return z_dust[s] + c[s]["height"] + c[s]["outlet_rise"]

    for s in (4, 3, 2):
        below = s + 1
        z_dust[s] = top(below) + c[below]["outlet_bend_R"] + 0.5 * c[below]["D_vortex"] - c[s]["height"]

    D_r1 = v(g["risers"]["R1"]["D"])
    r, rb = 0.5 * D_r1, 0.5 * br["D"]
    b = v(L["r1_branch_half"])
    y_rise = b - rb + 2.0 * math.sqrt(2.0) * rb - r
    z_leg_top = top(2) + c[2]["outlet_bend_R"] + 0.5 * c[2]["D_vortex"]
    # C1 over C2's outlet pipe by the stage gap, or as high as R1's
    # rise and Y ask before the C1 CFD branch's floor
    z_dust[1] = max(
        top(2) + v(L["stage_gap"]),
        z_leg_top + v(L["r1_up_min"]) + y_rise - br["z_floor"],
    )
    d_r1 = c[2]["outlet_bend_R"] + c[2]["outlet_run"] + v(L["r1_leg_on"]) + r
    d_c1 = br["x"] + b

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
    """The gooseneck as the plant has it (user decision, 14 Oct 2026):
    the neck and bends as the CFD's, each leg on down to its C5's
    inlet, a 45 deg piece and a level run into the barrel (the
    drawing), not to the CFD's outlet faces at half the vessel's
    height. Volume and wall area, both legs."""
    gn, L, c5 = gooseneck(g), layout(g), cyclone(g, "C5")
    D = gn["D_leg"]
    t = v(g["layout"]["gooseneck_turn_leg_over_D"]) * D
    down = L["z_gooseneck_top"] - (L["z_c5_inlet"] + t)
    run = (L["x_inner"] - 0.5 * c5["D_barrel"]) - (gn["x_leg"] + t)
    leg = _pipe(D, down + math.sqrt(2.0) * t + run)

    cfd_legs = 2.0 * 0.25 * math.pi * D * D * gn["drop"]
    cfd_legs_area = 2.0 * math.pi * D * gn["drop"]
    return {
        "leg_length": leg["length"],
        "volume": gn["volume"] - cfd_legs + 2.0 * leg["volume"],
        "wall_area": gn["wall_area"] - cfd_legs_area + 2.0 * leg["wall_area"],
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
    twin branches. calciner.zone_segments: the vessel (the fuel burns
    there), the gooseneck to the C5 inlets, the C5s (all strings)."""

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
    n5 = strings * c5["per_string"]

    return {
        "kiln": {"length": k["L"], "diameter": k["D"]},
        "transition": {"length": k["transition_L"]},
        "motion": {"inclination_pct": k["slope"]},
        "calciner": {
            "length": cal["H"],
            "diameter": cal["D"],
            "zone_segments": [
                {"name": "vessel", "volume": cal["vessel_volume"],
                 "wall_area": cal["vessel_wall_area"], "fuel": True},
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
