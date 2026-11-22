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
CYCLONE_OPTIONAL = {"outlet_bend_R_over_Dx": 0.0, "outlet_run_over_Dx": 0.0, "inlet_riser": False}


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


def _clip_area(poly, x_max):
    """Area of a closed polygon [(x, z), ...] left of x = x_max
    (Sutherland-Hodgman against one half-plane, then the shoelace)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        pin, qin = p[0] <= x_max, q[0] <= x_max
        if pin:
            out.append(p)
        if pin != qin:
            t = (x_max - p[0]) / (q[0] - p[0])
            out.append((x_max, p[1] + t * (q[1] - p[1])))
    a = 0.0
    for i in range(len(out)):
        (x0, z0), (x1, z1) = out[i], out[(i + 1) % len(out)]
        a += x0 * z1 - x1 * z0
    return 0.5 * abs(a)


def calciner_dispersion_plate(g, n_arc=4000, n_y=400):
    """The dispersion plate under each meal pipe's hole (calciner.md):
    a slab of thickness t between two concentric arcs, in the meal
    pipe's vertical plane (rho = radial out along +-x, z), extruded
    +-W/2 across it (y).

    In (rho, z) a plate direction at angle phi to the horizontal,
    inwards, is d = (-cos phi, sin phi); its upper normal n = (sin phi,
    cos phi). The upper (meal) face starts at A = (R, z_A) along the
    meal pipe's slope (phi0 = -slope), turns on radius Rc about
    C = A + Rc n(phi0) to the exit angle phi1, and ends at E, the
    protrusion past the wall: Rc (sin phi1 - sin phi0) = protrusion. The
    lower face is the arc of Rc + t about C. The tail runs back from A
    (and A') by `tail` along -d(phi0), out of the vessel. z_A sits
    lip_clearance under the hole's lowest point.

    Volumes: the slab's own (closed form: the annular sector plus the
    tail's rectangle, times W) and the part of it inside the vessel, the
    fluid the cut removes (rho < sqrt(R^2 - y^2); polygon clip on n_arc
    arc points, Simpson over y)."""
    c, cal = g["calciner"], calciner(g)
    meal = calciner_inlets(g)["meal"]
    R, D = cal["R"], meal["D"]
    phi0 = -math.radians(meal["slope"])
    phi1 = math.radians(v(c["dispersion_plate_exit_angle"]))
    prot = v(c["dispersion_plate_protrusion_over_D_feed"]) * D
    W = v(c["dispersion_plate_width_over_D_feed"]) * D
    t = v(c["dispersion_plate_thickness"])
    tail = v(c["dispersion_plate_tail"])
    z_a = meal["hole_bottom"] - v(c["dispersion_plate_lip_clearance"])
    rc = prot / (math.sin(phi1) - math.sin(phi0))

    def n(phi):
        return (math.sin(phi), math.cos(phi))

    cx, cz = R + rc * n(phi0)[0], z_a + rc * n(phi0)[1]

    def on(rad, phi):
        return (cx - rad * n(phi)[0], cz - rad * n(phi)[1])

    back = (math.cos(phi0), -math.sin(phi0))                  # -d(phi0): out and up
    a, e = on(rc, phi0), on(rc, phi1)
    a2, e2 = on(rc + t, phi0), on(rc + t, phi1)
    tt = (a[0] + tail * back[0], a[1] + tail * back[1])
    tt2 = (a2[0] + tail * back[0], a2[1] + tail * back[1])

    # the profile, closed: tail top -> A -> upper arc -> E -> E' -> lower arc -> A' -> tail bottom
    poly = [tt]
    poly += [on(rc, phi0 + (phi1 - phi0) * k / n_arc) for k in range(n_arc + 1)]
    poly += [on(rc + t, phi1 - (phi1 - phi0) * k / n_arc) for k in range(n_arc + 1)]
    poly.append(tt2)

    dphi = phi1 - phi0
    area = 0.5 * dphi * ((rc + t) ** 2 - rc ** 2) + tail * t
    h = W / n_y
    inside = 0.0
    for k in range(n_y + 1):
        y = -0.5 * W + k * h
        w = 1.0 if k in (0, n_y) else (4.0 if k % 2 else 2.0)
        inside += w * _clip_area(poly, math.sqrt(R * R - y * y))
    inside *= h / 3.0

    z_low = cz - (rc + t)                                      # the lower arc's lowest point (phi = 0 lies on it)
    return {
        "exit_angle": math.degrees(phi1),
        "R_arc": rc,
        "thickness": t,
        "width": W,
        "protrusion": prot,
        "tail": tail,
        "centre": (cx, cz),
        "A": a, "E": e, "A_low": a2, "E_low": e2, "T": tt, "T_low": tt2,
        "z_low": z_low,
        "profile_area": area,
        "volume": area * W,
        "inside_vessel": inside,
        "edge_area": t * W,
        "pipe_clearance": (meal["z_wall"] - 0.5 * D / math.cos(-phi0) - z_a) * math.cos(phi0),
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
    return {
        "D": D,
        "L": L,
        "slope": v(k["slope"]),
        "transition_L": v(k["transition_L"]),
        # the wall stack's thicknesses, hot face outward (physics.shell)
        "lining": {
            "steel_shell": v(k["shell_t"]),
            "brick": v(k["lining_t"]),
            "coating_burning": v(k["burning_coating_t"]),
            "coating_transition": v(k["transition_coating_t"]),
        },
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
# The kiln hood and the kiln inlet chamber: gas velocity checks
# ======================================================================
def kiln_hood(g):
    """The hood is the layout's square round the kiln end (side 2 a). The
    air through it is the secondary air and the tertiary air; at the
    tertiary air's temperature (the hotter secondary air makes it faster:
    checked at 1250 K too) the velocity over the square is held to the
    literature's range."""

    h = g["kiln_hood"]
    bnd = calciner_boundaries(g)["tertiary_air_inlet"]
    m = bnd["flow"] + v(h["secondary_air_flow"])
    side = 2.0 * layout(g)["a_chamber"]
    area = side * side

    def vel(T):
        rho = 101325.0 * bnd["M"] / (R_GAS * T)
        return m / rho / area

    vmax = v(h["air_velocity_max"])
    rho = bnd["rho"]
    return {
        "m": m,
        "rho": rho,
        "q": m / rho,
        "side": side,
        "area": area,
        "u": vel(bnd["T"]),
        "u_hot": vel(1250.0),
        "side_min": math.sqrt(m / rho / vmax),
        "u_min": v(h["air_velocity_min"]),
        "u_max": vmax,
    }


def chamber_roof(g):
    """The chamber is the layout square (side 2 a, flat roof, the calciner's
    throat in it). Its floor is one ramp across the whole plan, from the
    kiln mouth's lower lip (a clearance under the mouth, so the mouth's
    circle does not touch the ramp's foot) up to the far top corner, so the
    meal slides into the kiln and no meal lies in a pit; the ramp's slope
    follows from that, it is not an input."""

    kl, cal = kiln(g), calciner(g)
    a = 0.5 * kl["D"] + v(g["layout"]["chamber_margin"])
    clear = v(g["kiln_inlet_chamber"]["mouth_clearance"])
    h_lip = a - 0.5 * kl["D"] - clear
    height = 2.0 * a
    run = 2.0 * a
    return {
        "height": height,
        "D_throat": cal["D_throat"],
        "clear": clear,
        "h_lip": h_lip,
        "ramp_run": run,
        "ramp_rise": height - h_lip,
        "ramp_slope": math.degrees(math.atan((height - h_lip) / run)),
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
    roof = chamber_roof(g)
    return {
        **roof,
        "q": q,
        "side": side,
        "u_kiln": q / (0.25 * math.pi * kl["D"] ** 2),
        "u_chamber": q / (side * side),
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
    phi / pi), phi clockwise from +y over a half turn, at 3600 steps.
    x_max on the far side of the duct's tangent plane, y_min where the
    scroll closes behind the barrel."""

    c = cyclone(g, name)
    d = g["cyclone_domain"]
    r_t = 0.5 * c["D_barrel"] + v(d["volute_tongue"])
    W = c["W_inlet"]
    x_max = y_min = 0.0
    for k in range(3601):
        ph = math.pi * k / 3600.0
        r = r_t + W - W * ph / math.pi
        x_max = max(x_max, r * math.sin(ph))
        y_min = min(y_min, r * math.cos(ph))
    return {"x_max": x_max, "y_min": y_min, "r_start": r_t + W, "r_end": r_t}


def riser_inlet(g, name, D_riser=None, offset=None):
    """A riser's top into C(name)'s level inlet duct (R2-R4 into C2-C4,
    and the C4 CFD domain's own inlet; user decisions, 17 Nov and 22 Nov
    2026), in cyclone_duct_inlet's frame (x along the duct towards the
    volute, its face at x = -L_in; y across; z from the roof down as
    "drop").

    The riser (D_riser, the cyclone below's outlet bore; C(name)'s own
    D_x if not given) stands vertical under the duct's axis (y = the
    duct's middle). Its round top is cut obliquely and an elbow starts
    on the cut, turning it into the level duct, tangent to the duct's
    face (riser_elbow). The elbow's centreline radius is
    riser_bend_R_over_H x H at least (the riser axis then that x cos
    riser_cut_deg back from the face), the riser riser_barrel_clearance
    clear of the barrel; `offset` (a column spacing shared by several
    risers) puts it, and so the radius, further out."""

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
    run_min = v(d["riser_bend_R_over_H"]) * H * math.cos(math.radians(v(d["riser_cut_deg"])))
    least = max(R + 0.5 * D + clr, math.hypot(s["length"] + run_min, y_d))
    off = least if offset is None else offset
    if off < least - 1e-9:
        raise ValueError(f"{name}: a riser {off:.3f} m off its axis is closer than its elbow or the barrel allow "
                         f"(needs {least:.3f})")
    x_j = math.sqrt(off * off - y_d * y_d)       # the riser axis back from x = 0
    run = x_j - s["length"]                       # riser axis back from the duct face
    el = riser_elbow(run, D, W, H, v(d["riser_cut_deg"]))
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


def riser_elbow(run, D, W, H, cut_deg):
    """A riser's top turned into a level duct (user decisions, 22 Nov
    2026, from a plant's riser duct + elbow duct). The round riser is
    cut by a plane tilted cut_deg (b) about the horizontal across the
    duct, high on the side away from it -- a mitre: the elbow starts on
    the cut's ellipse itself (D across, D / cos b along the slope; no
    step), and its section goes over linearly (a constant taper) to the
    duct face's W x H while its centreline turns the remaining 90 - b
    deg on a circle of radius bend_R = run / cos b (run: the riser axis
    back from the duct face), tangent to the duct.

    drop_mid: roof down to the cut's centre (H/2 + bend_R (1 - sin b));
    drop: to the cut's low point (the riser's straight part ends there);
    drop_high: to its high point. Volume and wall: the elbow as a ruled
    loft of the centreline's length between the ellipse and the
    rectangle (_vertical_loft; Pappus), and the riser over the cut's
    low point."""
    b = math.radians(cut_deg)
    R_b = run / math.cos(b)
    a = 0.5 * D
    if R_b - 0.5 * H <= 0.0 or R_b - a / math.cos(b) <= 0.0:
        raise ValueError(f"the elbow's radius {R_b:.3f} m leaves no inner radius")
    tilt = a * math.tan(b)
    drop_mid = 0.5 * H + R_b * (1.0 - math.sin(b))
    arc = R_b * (0.5 * math.pi - b)
    w0, h0 = D, D / math.cos(b)
    el = _vertical_loft(D, H, W, arc, h0)
    return {
        "bend_R": R_b,
        "bend_R_inner": R_b - 0.5 * max(H, h0),
        "cut_deg": cut_deg,
        "bend_deg": 90.0 - cut_deg,
        "start_W": w0,
        "start_H": h0,
        "drop_mid": drop_mid,
        "drop": drop_mid + tilt,
        "drop_high": drop_mid - tilt,
        "length": arc,                            # the centreline, the cut's centre to the duct face
        "bend_volume": el["volume"],
        "volume": el["volume"] + math.pi * a * a * tilt,
        "wall_area": el["wall_area"] + 2.0 * math.pi * a * tilt,
    }


@lru_cache(maxsize=None)
def _vertical_loft(D, H, W, L, D_h=None, n=720, phases=128):
    """A ruled loft between a circle (D; an ellipse D x D_h, D_h along
    H, if given) and a rectangle (H x W) in
    parallel planes L apart, centred on one axis, as SolidWorks builds
    it with no guides: each perimeter at equal arc-length steps, of the
    pairings (start, sense) the untwisted one, which encloses the most.
    The section's area is quadratic along the axis, so Simpson's rule
    (ends and the paired mid-curve) is exact; the wall is the ruled
    quads' area."""
    t = np.arange(n) / n
    P = 2.0 * (W + H)
    s = t * P
    x = np.where(s < H, -0.5 * H + s,
        np.where(s < H + W, 0.5 * H,
        np.where(s < 2 * H + W, 0.5 * H - (s - H - W), -0.5 * H)))
    y = np.where(s < H, -0.5 * W,
        np.where(s < H + W, -0.5 * W + (s - H),
        np.where(s < 2 * H + W, 0.5 * W, 0.5 * W - (s - 2 * H - W))))

    def area(px, py):
        return 0.5 * abs(np.dot(px, np.roll(py, -1)) - np.dot(py, np.roll(px, -1)))

    Dh = D if D_h is None else D_h
    a0, a1 = 0.25 * math.pi * D * Dh, W * H
    best = None
    for k in range(phases):
        for sense in (1.0, -1.0):
            ang = 2.0 * math.pi * (k / phases + sense * t)
            cx, cy = 0.5 * Dh * np.cos(ang), 0.5 * D * np.sin(ang)
            am = area(0.5 * (cx + x), 0.5 * (cy + y))
            vol = L / 6.0 * (a0 + 4.0 * am + a1)
            if best is None or vol > best[0]:
                p0 = np.stack([cx, cy, np.zeros(n)], axis=1)
                p1 = np.stack([x, y, np.full(n, L)], axis=1)
                q0, q1 = np.roll(p0, -1, axis=0), np.roll(p1, -1, axis=0)
                wall = 0.5 * (np.linalg.norm(np.cross(q0 - p0, p1 - p0), axis=1)
                              + np.linalg.norm(np.cross(p1 - q0, q1 - q0), axis=1)).sum()
                best = (vol, wall)
    return {"volume": best[0], "wall_area": best[1]}


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
        r.update(riser_elbow(r["run"], r["D"], c["W_inlet"], c["H_inlet"], v(d["riser_cut_deg"])))
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
    along +x (90 deg)."""

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
    z0 = z_ch0 + chamber_roof(g)["height"]        # the calciner's throat foot on the chamber's tapered roof
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
    z_hood = z_kiln_end - a_ch
    # The chamber's section (user sketch, 21 Nov 2026): the throat's walls
    # run down, the ramp from the left one falls at ramp_deg to a foot
    # ramp_foot long at the kiln mouth's lower lip; the foot falls at the
    # kiln's slope towards the kiln (the kiln shell's line carried in)
    kic = g["kiln_inlet_chamber"]
    ramp = math.radians(v(kic["ramp_deg"]))
    z_lip = v(L["kiln_axis_z"]) - 0.5 * kl["D"] / math.cos(alpha)
    x_toe = a_ch - v(kic["ramp_foot"])
    z_toe = z_lip + v(kic["ramp_foot"]) * math.tan(alpha)
    z_ramp_top = z_toe + (x_toe + 0.5 * cal["D_throat"]) * math.tan(ramp)

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
        "chamber_ramp_deg": math.degrees(ramp),
        "chamber_ramp_toe": (x_toe, z_toe),
        "z_chamber_ramp_top": z_ramp_top,
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
