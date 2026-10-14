"""Write the plant's geometry into the macros, from its one source.

Every dimension is in geometry/plant_geometry.yaml once (single-source
rule, user decision 13-14 Oct 2026). The SolidWorks macros cannot read
it, so each holds a copy in a generated Const block between

    ' BEGIN GENERATED (tools/gen_geometry.py) ...
    ' END GENERATED

which this script writes; nothing between the markers is edited by
hand. Values the source gives are written as given (the CFD domains
are rebuilt bit for bit); values it derives (geometry/plant_geometry.py)
at 1 um.

    python3 tools/gen_geometry.py           # rewrite the blocks
    python3 tools/gen_geometry.py --check   # exit 1 if any is stale
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geometry import plant_geometry as pg  # noqa: E402

MACROS = ROOT / "geometry" / "macros"
BEGIN = "' BEGIN GENERATED (tools/gen_geometry.py)"
END = "' END GENERATED"
HEADER = (
    BEGIN + " -- do not edit by hand.\n"
    "' From geometry/plant_geometry.yaml through geometry/plant_geometry.py;\n"
    "' change the source and run: python3 tools/gen_geometry.py\n"
)
DERIVED_DIGITS = 6  # m: 1 um


class Const:
    """One generated Const: a source entry, or a derived value."""

    def __init__(self, name, value, note, kind="Double", derived=False):
        self.name, self.value, self.note = name, value, note
        self.kind, self.derived = kind, derived

    def line(self):
        if self.kind == "Boolean":
            text = "True" if self.value else "False"
        elif self.kind == "Long":
            text = str(int(self.value))
        else:
            x = round(self.value, DERIVED_DIGITS) if self.derived else float(self.value)
            text = repr(x)
            if text.endswith(".0"):
                text = text[:-2] + "#"
        return f"Const {self.name:<28} As {self.kind:<7} = {text:<12} ' {self.note}"


def src(name, node, what="", kind="Double", scale=1.0):
    """A Const from a source entry: its value (x scale), tagged with
    its source and document."""
    tag = f"{node['source']}, {node['doc']}"
    return Const(name, scale * pg.v(node), f"{what} [{tag}]" if what else f"[{tag}]", kind)


def der(name, value, what):
    return Const(name, value, f"{what} [derived]", derived=True)


# ======================================================================
# cyclone.bas
# ======================================================================
CASE_KEYS = (  # source key -> SelectCyclone variable
    ("D_barrel", "D_BARREL"), ("H_barrel", "H_BARREL"), ("H_cone", "H_CONE"),
    ("L_vortex", "L_VORTEX"), ("D_vortex", "D_VORTEX"), ("D_dust", "D_DUST"),
    ("W_inlet", "W_INLET"), ("H_inlet", "H_INLET"),
    ("inlet_slope", "INLET_SLOPE_DEG"), ("volute", "VOLUTE_ON"),
    ("outlet_turn", "OUTLET_TURN_DEG"),
    ("outlet_rise_over_Dx", "OUTLET_EXT_OVER_VORTEX_D"),
    ("outlet_bend_R_over_Dx", "ELBOW_R_OVER_VORTEX_D"),
    ("outlet_run_over_Dx", "OUTLET_DOWN_OVER_VORTEX_D"),
    ("boi_radius", "BOI_RADIUS"),
)

DOMAIN_KEYS = (  # cyclone_domain key -> module Const
    ("vortex_wall", "VORTEX_WALL"), ("inlet_duct_length", "L_INLET"),
    ("inlet_roof_clearance", "INLET_ROOF_CLEARANCE"),
    ("inlet_tangent_relief", "INLET_TANGENT_RELIEF"),
    ("volute_tongue", "INLET_TONGUE"), ("volute_overlap", "VOLUTE_OVERLAP"),
    ("c1_riser_area_share", "RISER_AREA_SHARE"),
    ("c1_riser_transition", "RISER_TRANS_LEN"),
    ("c1_riser_bend_R_over_D", "RISER_BEND_R_OVER_D"),
    ("c1_riser_above_feed", "RISER_ABOVE_FEED"),
    ("c1_riser_below_feed", "RISER_BELOW_FEED"),
    ("c1_feed_width", "FEED_W"), ("c1_feed_height", "FEED_H"),
    ("c1_feed_depth", "FEED_DEPTH"), ("meal_slope", "FEED_SLOPE_DEG"),
)


def cyclone_case(g, name):
    """C(name)'s SelectCyclone values: C1, C4 from the source; C5 the
    C4 domain x its scale, derived."""
    node = g["cyclones"][name]
    out = []
    if "scaled_from" in node:
        c = pg.cyclone(g, name)
        base = node["scaled_from"]
        for key, var in CASE_KEYS:
            if key == "boi_radius":
                out.append(src(f"{name}_{var}", node[key]))
            elif key == "D_barrel":
                out.append(src(f"{name}_{var}", node["D_barrel_published"]))
            elif key in pg.CYCLONE_DIMS:
                out.append(der(f"{name}_{var}", c[key], f"{base} x {c['scale']:.6f}"))
            else:
                kind = "Boolean" if key == "volute" else "Double"
                out.append(Const(f"{name}_{var}", c[key], f"as {base}", kind))
        return out
    for key, var in CASE_KEYS:
        kind = "Boolean" if key == "volute" else "Double"
        out.append(src(f"{name}_{var}", node[key], kind=kind))
    return out


def cyclone_bas(g):
    d = g["cyclone_domain"]
    out = [src(var, d[key]) for key, var in DOMAIN_KEYS]
    out.append(src("D_RISER_SRC", g["risers"]["R1"]["D"], "R1 inner D"))
    for name in ("C1", "C4", "C5"):
        out += cyclone_case(g, name)
    return out


# ======================================================================
# calciner.bas
# ======================================================================
def calciner_bas(g):
    c, gn = g["calciner"], g["gooseneck"]
    return [
        src("D_VESSEL", c["D"], "effective inner D"),
        src("H_VESSEL", c["H"], "cone + cylinder"),
        src("CONE_DEG", c["cone_angle"]),
        src("M_KILN_GAS", c["throat_gas_flow"], "kg/s"),
        src("T_KILN_GAS", c["throat_gas_T"], "K"),
        src("X_N2", c["throat_gas_x_N2"]),
        src("X_O2", c["throat_gas_x_O2"]),
        src("X_H2O", c["throat_gas_x_H2O"]),
        src("X_CO2", c["throat_gas_x_CO2"]),
        src("U_THROAT", c["throat_velocity"], "m/s"),
        src("THROAT_LEN_OVER_D", c["throat_length_over_D"]),
        src("D_GOOSENECK_SRC", gn["D_leg"], "each leg"),
        src("GN_RISE_OVER_D", gn["rise_over_D_neck"], "x neck D"),
        src("GN_BEND_R_OVER_D", gn["bend_R_over_D_leg"], "x leg D"),
        src("GN_OUTLET_AT_VESSEL_H", gn["end_at_vessel_H"], "x H_VESSEL"),
        src("D_FEED", c["D_feed"]),
        src("FEED_SLOPE_DEG", g["cyclone_domain"]["meal_slope"], "below the horizontal"),
        src("FEED_BELOW_GN_OUT", c["feed_below_gooseneck_end"]),
        src("FEED_DEPTH", c["feed_depth"]),
        Const("OVERLAP_N", pg.OVERLAP_N, "grid per axis, the bends' shared volume [plant_geometry.py]", "Long"),
    ]


# ======================================================================
# plant_topology_2d.bas
# ======================================================================
def drawing_bas(g):
    cy = g["cyclones"]
    c1, c4, c5 = (pg.cyclone(g, n) for n in ("C1", "C4", "C5"))
    d, cal, gn = g["cyclone_domain"], g["calciner"], g["gooseneck"]
    k, coo, lay = g["kiln"], g["cooler"], g["layout"]
    br = pg.c1_branch(g)

    out = []
    for tag, c in (("C1", cy["C1"]), ("C4", cy["C4"])):
        out += [
            src(f"{tag}_D", c["D_barrel"], "barrel D"),
            src(f"{tag}_HB", c["H_barrel"], "barrel height"),
            src(f"{tag}_HC", c["H_cone"], "cone height"),
            src(f"{tag}_VD", c["D_vortex"], "vortex finder D"),
            src(f"{tag}_DD", c["D_dust"], "dust outlet D"),
        ]
    out += [
        src("C5_D", cy["C5"]["D_barrel_published"], "barrel D"),
        der("C5_HB", c5["H_barrel"], "barrel height, C4 x scale"),
        der("C5_HC", c5["H_cone"], "cone height, C4 x scale"),
        der("C5_VD", c5["D_vortex"], "vortex finder D, C4 x scale"),
        der("C5_DD", c5["D_dust"], "dust outlet D, C4 x scale"),
        der("C5_HIN", c5["H_inlet"], "volute inlet height, C4 x scale"),
        src("C4_VF_S", cy["C4"]["L_vortex"], "vortex finder immersion"),
        der("C4_OUT_RISE", c4["outlet_rise"], "outlet pipe rise over the roof"),
        der("C4_OUT_R", c4["outlet_bend_R"], "outlet bend centreline R"),
        der("C4_OUT_RUN", c4["outlet_run"], "outlet leg"),
        src("C4_IN_H", cy["C4"]["H_inlet"], "volute inlet height"),
        src("C4_IN_W", cy["C4"]["W_inlet"], "volute inlet width"),
        src("C4_TONGUE", d["volute_tongue"]),
        src("C4_IN_L", d["inlet_duct_length"], "inlet duct face from the axis"),
        src("C1_VF_S", cy["C1"]["L_vortex"], "vortex finder immersion"),
        src("R1_D", g["risers"]["R1"]["D"]),
        src("CALC_D", cal["D"]),
        src("CALC_H", cal["H"], "cone + cylinder"),
        der("CALC_THROAT_D", 2.0 * pg.throat_radius(g), "throat D"),
        src("CALC_CONE_DEG", cal["cone_angle"]),
        src("GN_D_SRC", gn["D_leg"], "a gooseneck leg"),
        src("GN_RISE_OVER_D", gn["rise_over_D_neck"], "neck rise, x neck D"),
        src("GN_BEND_R_OVER_D", gn["bend_R_over_D_leg"], "bend centreline R, x leg D"),
        src("GN_OUT_AT_H", gn["end_at_vessel_H"], "CFD legs' end, x CALC_H"),
        src("FEED_BELOW_GN_OUT", cal["feed_below_gooseneck_end"]),
        src("TA_D", cal["D_tertiary_air"], "tertiary air duct"),
        src("MEAL_SLOPE_DEG", d["meal_slope"]),
        src("KILN_D", k["D"]),
        src("KILN_L", k["L"]),
        src("KILN_SLOPE", k["slope"], "slope / 100", scale=0.01),
        src("COOLER_AREA", coo["grate_area"], "m2"),
        src("COOLER_W", coo["width"], "grate width"),
        src("COOLER_H", coo["casing_height"], "casing height"),
        der("C1_RISER_X", br["x"], "C1 riser branch axis from the C1 axis"),
        der("C1_RISER_Z0", br["z_floor"], "C1 CFD domain floor, over the dust outlet"),
        der("C1_BEND_Z", br["z_bend"], "C1 branch bend start"),
        der("C1_BEND_R", br["bend_R"], "C1 branch bend centreline R"),
        der("C1_BEND_DEG", br["bend_deg"], "C1 branch bend"),
        src("C1_TRANS_L", d["c1_riser_transition"], "round -> duct transition"),
        src("C1_DUCT_H", cy["C1"]["H_inlet"], "C1 inlet duct height"),
        der("C1_FEED_Z", br["z_feed"], "C1 feed chute axis at the branch wall"),
        src("C1_FEED_L", d["c1_feed_depth"], "C1 feed chute depth"),
        src("C1_FEED_W", d["c1_feed_width"], "C1 feed chute side"),
        der("C1_OUT_RISE", c1["outlet_rise"], "C1 outlet pipe rise"),
        der("C1_OUT_R", c1["outlet_bend_R"], "C1 outlet 180 deg bend centreline R"),
        src("STAGE_GAP", lay["stage_gap"]),
        src("ZIG_DX", lay["column_offset"], "outer column outboard of the inner"),
        src("C5_OVER_TA", lay["c5_over_tertiary_air"]),
        src("GN_TO_C5_GAP", lay["gooseneck_to_c5_gap"]),
        src("GN_BEND_LEG", lay["gooseneck_turn_leg_over_D"], "x leg D"),
        src("R1_BRANCH_HALF", lay["r1_branch_half"]),
        src("R1_UP_MIN", lay["r1_up_min"]),
        src("R1_LEG_ON", lay["r1_leg_on"]),
        src("KILN_AXIS_Z", lay["kiln_axis_z"]),
        src("CHAMBER_MARGIN", lay["chamber_margin"]),
        src("COOLER_DROP", lay["cooler_drop"]),
    ]
    return out


TARGETS = {
    "cyclone.bas": cyclone_bas,
    "calciner.bas": calciner_bas,
    "plant_topology_2d.bas": drawing_bas,
}


# ======================================================================
# Writing
# ======================================================================
def block(consts):
    return HEADER + "".join(c.line().rstrip() + "\n" for c in consts) + END


def render(text, consts, name):
    """text with its generated block replaced (CRLF kept as found)."""
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text.replace("\r\n", "\n")
    i, j = body.find(BEGIN), body.find(END)
    if i < 0 or j < i:
        raise SystemExit(f"{name}: no generated block ({BEGIN!r} ... {END!r})")
    body = body[:i] + block(consts) + body[j + len(END):]
    return body.replace("\n", nl)


def run(check=False, g=None):
    """Rewrite (or, with check, compare) every block; the stale ones."""
    g = g or pg.load()
    stale = []
    for name, build in TARGETS.items():
        path = MACROS / name
        text = path.read_bytes().decode("latin-1")
        new = render(text, build(g), name)
        if new != text:
            stale.append(name)
            if not check:
                path.write_bytes(new.encode("latin-1"))
    return stale


def main(argv):
    check = "--check" in argv
    stale = run(check=check)
    for name in stale:
        print(("stale: " if check else "wrote: ") + f"geometry/macros/{name}")
    if check and stale:
        return 1
    if not stale:
        print("geometry: every generated block is current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
