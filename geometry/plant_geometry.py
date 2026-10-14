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
# Risers
# ======================================================================
def riser(g, name):
    """R(name) as a straight cylinder: D, L, volume, wall area."""
    node = g["risers"][name]
    D, L = v(node["D"]), v(node["L"])
    return {
        "D": D,
        "L": L,
        "volume": 0.25 * math.pi * D * D * L,
        "wall_area": math.pi * D * L,
    }


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
