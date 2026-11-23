"""Write the plant's geometry into the macros, from its one source.

Every dimension is in geometry/plant_geometry.yaml once (single-source
rule, user decision 13-14 Oct 2026). The SolidWorks macros cannot read
it, so each holds a copy in a generated Const block between

    ' BEGIN GENERATED (tools/gen_geometry.py) ...
    ' END GENERATED

which this script writes, and the equipment documents a generated
table between

    <!-- BEGIN GENERATED (tools/gen_geometry.py) ... -->
    <!-- END GENERATED -->

Nothing between the markers is edited by hand. Values the source gives are written as given (the CFD domains
are rebuilt bit for bit); values it derives (geometry/plant_geometry.py)
at 1 um.

    python3 tools/gen_geometry.py           # rewrite the blocks
    python3 tools/gen_geometry.py --check   # exit 1 if any is stale
"""

import math
import re
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

    def __init__(self, name, value, note, kind="Double", derived=False, digits=None):
        self.name, self.value, self.note = name, value, note
        self.kind, self.derived = kind, derived
        self.digits = DERIVED_DIGITS if digits is None else digits

    def line(self):
        if self.kind == "Boolean":
            text = "True" if self.value else "False"
        elif self.kind == "String":
            if not str(self.value).isascii():
                raise ValueError(f"{self.name}: macro strings are ASCII (latin-1 file, VBA code page)")
            text = '"' + str(self.value).replace('"', '""') + '"'
        elif self.kind == "Long":
            text = str(int(self.value))
        else:
            x = round(self.value, self.digits) if self.derived else float(self.value)
            text = repr(x)
            if text.endswith(".0"):
                text = text[:-2] + "#"
        return f"Const {self.name:<28} As {self.kind:<7} = {text:<12} ' {self.note}"


def src(name, node, what="", kind="Double", scale=1.0):
    """A Const from a source entry: its value (x scale), tagged with
    its source and document."""
    tag = f"{node['source']}, {node['doc']}"
    return Const(name, scale * pg.v(node), f"{what} [{tag}]" if what else f"[{tag}]", kind)


def der(name, value, what, digits=None):
    """A derived Const; `digits` for a fraction that multiplies a length (6 digits
    of a fraction of 30 m is 15 um)."""
    return Const(name, value, f"{what} [derived]", derived=True, digits=digits)


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
    ("inlet_duct_length", "L_INLET_CASE"),
    ("inlet_riser", "RISER_IN_ON"),
    ("boi_radius", "BOI_RADIUS"),
)
# derived per case: the riser inlet's axis from the barrel axis (the
# plant's column offset, so the domain's riser is R2 / R3; 0 without one)
BOOL_KEYS = ("volute", "inlet_riser")
# D_x = D_vortex_over_D_barrel x D: the riser's bore (user decision, 21 Nov 2026)
VD_WHAT = "vortex finder D = riser D = D_vortex_over_D_barrel x D"

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
    ("riser_duct_slope_deg", "RISER_SLOPE_DEG"),
    ("riser_taper_deg", "RISER_TAPER_DEG"),
    ("riser_barrel_clearance", "RISER_IN_CLEAR"),
    ("riser_cfd_stub_over_D", "RISER_IN_STUB_OVER_D"),
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
            elif key == "D_vortex":
                out.append(der(f"{name}_{var}", c[key], VD_WHAT))
            elif key in pg.CYCLONE_DIMS or key == "inlet_duct_length":
                out.append(der(f"{name}_{var}", c[key], f"{base} x {c['scale']:.6f}"))
            else:
                kind = "Boolean" if key in BOOL_KEYS else "Double"
                out.append(Const(f"{name}_{var}", c[key], f"as {base}", kind))
        return out
    c = pg.cyclone(g, name)
    for key, var in CASE_KEYS:
        kind = "Boolean" if key in BOOL_KEYS else "Double"
        if key == "D_vortex":
            out.append(der(f"{name}_{var}", c[key], VD_WHAT))
        elif key in node:
            out.append(src(f"{name}_{var}", node[key], kind=kind))
        else:
            # not given for this cyclone: the domain's (inlet duct) or none (no bend, no riser)
            out.append(Const(f"{name}_{var}", c[key], "not given: the default", kind))
    return out


def cyclone_bas(g):
    d = g["cyclone_domain"]
    out = [src(var, d[key]) for key, var in DOMAIN_KEYS]
    out.append(der("D_RISER_SRC", pg.r1_D(g), "R1 inner D = C2's D_x"))
    for name in ("C1", "C4", "C5"):
        out += cyclone_case(g, name)
        off = pg.cfd_riser_inlet(g, name)["offset"] if pg.cyclone(g, name)["inlet_riser"] else 0.0
        out.append(der(f"{name}_RISER_IN_OFFSET", off, "riser inlet axis from the barrel axis (the columns' offset)"))
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
        der("GN_OUTLET_AT_VESSEL_H", pg.gooseneck(g)["end_over_H"], "the arms' level runs' axis, x H_VESSEL (C5's inlet axis, plant_geometry.py)", digits=12),
        src("GN_SLOPE_DEG", gn["neck_slope"], "the neck's two inclined pieces, to the horizontal"),
        src("GN_PIECE_OVER_D", gn["neck_piece_over_D_neck"], "the neck's inclined pieces, x neck D"),
        src("GN_LEVEL_OVER_D", gn["neck_level_over_D_neck"], "the neck's level piece, x neck D"),
        src("GN_CHANNEL_OVER_D", gn["channel_over_D_neck"], "the vertical channel below the neck, x neck D"),
        src("GN_ARM_DEG", gn["arm_angle"], "each arm's angle to the vertical"),
        src("GN_ARM_RUN_OVER_D", gn["arm_run_over_D_leg"], "each arm's level run, x leg D"),
        der("GN_ROOT_FWD", pg.gooseneck(g)["root_forward"], "where the neck's first piece pierces the roof, in front of the axis, m (cap kept inside the vessel)"),
        der("GN_INSIDE_VESSEL", pg.gooseneck(g)["inside_vessel"], "the neck's first piece inside the vessel, m3 (grid, plant_geometry.py)"),
        der("GN_OVERLAP_NECK_ARM", pg.gooseneck(g)["overlap_neck_arm"], "channel x one arm, m3"),
        der("GN_OVERLAP_ARMS", pg.gooseneck(g)["overlap_arms"], "arm x arm, m3"),
        der("GN_OVERLAP_ALL", pg.gooseneck(g)["overlap_all"], "channel x both arms, m3"),
        src("D_TA", c["D_tertiary_air"], "tertiary air duct"),
        src("TA_CONE_CLEARANCE", c["tertiary_air_cone_clearance"], "its lower edge over the cone's top"),
        src("TA_WALL_RELIEF", c["tertiary_air_wall_relief"], "its outer wall inside the vessel's"),
        src("TA_STUB_LEN", c["tertiary_air_stub_length"], "its face past the vessel's tangent plane"),
        src("FEED_ABOVE_TA", c["feed_above_tertiary_air"], "meal / fuel holes over the duct's top"),
        src("D_FEED", c["D_feed"]),
        src("FEED_SLOPE_DEG", g["cyclone_domain"]["meal_slope"], "below the horizontal"),
        src("FEED_DEPTH", c["feed_depth"], "meal and fuel pipes past the wall"),
        src("D_FUEL", c["D_fuel"]),
        src("FUEL_SLOPE_DEG", c["fuel_slope"], "below the horizontal"),
        src("DP_EXIT_DEG", c["dispersion_plate_exit_angle"], "dispersion plate's exit, above the horizontal"),
        src("DP_PROT_OVER_D", c["dispersion_plate_protrusion_over_D_feed"], "its edge past the wall, x D_FEED"),
        src("DP_WIDTH_OVER_D", c["dispersion_plate_width_over_D_feed"], "its width, x D_FEED"),
        src("DP_THICKNESS", c["dispersion_plate_thickness"]),
        src("DP_LIP_CLEARANCE", c["dispersion_plate_lip_clearance"], "its meal face under the hole's lowest point"),
        src("DP_TAIL", c["dispersion_plate_tail"], "its tail on into the wall, along the pipe slope"),
        der("DP_INSIDE_VESSEL", pg.calciner_dispersion_plate(g)["inside_vessel"], "one plate inside the vessel, m3 (the fluid it removes; plant_geometry.py)"),
        Const("OVERLAP_N", pg.OVERLAP_N, "grid per axis, the bends' shared volume [plant_geometry.py]", "Long"),
        Const("P_ATM", pg.P_ATM, "Pa, the throat's gas [plant_geometry.py]"),
        Const("R_GAS", pg.R_GAS, "J/(mol K) [plant_geometry.py]"),
    ] + [
        Const(f"M_{s}", m, "kg/mol [plant_geometry.py]") for s, m in pg.MOLAR_MASS.items()
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
    tw = pg.c1_twin(g)
    L = pg.layout(g)

    out = []
    for tag, c in (("C1", cy["C1"]), ("C4", cy["C4"])):
        out += [
            src(f"{tag}_D", c["D_barrel"], "barrel D"),
            src(f"{tag}_HB", c["H_barrel"], "barrel height"),
            src(f"{tag}_HC", c["H_cone"], "cone height"),
            der(f"{tag}_VD", pg.cyclone(g, tag)["D_vortex"], "vortex finder D = riser D, D / 2"),
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
        der("C4_OUT_R", c4["outlet_bend_R"], "outlet bend centreline R (0: straight, 17 Nov 2026)"),
        der("C4_OUT_RUN", c4["outlet_run"], "outlet leg (0: straight)"),
        src("C4_IN_H", cy["C4"]["H_inlet"], "volute inlet height"),
        src("C4_IN_W", cy["C4"]["W_inlet"], "volute inlet width"),
        src("C4_TONGUE", d["volute_tongue"]),
        der("C4_IN_L", c4["inlet_duct_length"], "level inlet duct, its face back from the tangent plane"),
        src("C1_VF_S", cy["C1"]["L_vortex"], "vortex finder immersion"),
        der("R1_D", pg.r1_D(g), "R1 = C2's outlet pipe, D_x"),
        src("CALC_D", cal["D"]),
        src("CALC_H", cal["H"], "cone + cylinder"),
        der("CALC_THROAT_D", 2.0 * pg.throat_radius(g), "throat D"),
        src("CALC_CONE_DEG", cal["cone_angle"]),
        src("GN_D_SRC", gn["D_leg"], "a gooseneck leg"),
        src("GN_SLOPE_DEG", gn["neck_slope"], "the neck's inclined pieces, to the horizontal"),
        src("GN_PIECE_OVER_D", gn["neck_piece_over_D_neck"], "the neck's inclined pieces, x neck D"),
        src("GN_LEVEL_OVER_D", gn["neck_level_over_D_neck"], "the neck's level piece, x neck D"),
        src("GN_CHANNEL_OVER_D", gn["channel_over_D_neck"], "the vertical channel below the neck, x neck D"),
        src("GN_ARM_DEG", gn["arm_angle"], "each arm's angle to the vertical"),
        src("GN_ARM_RUN_OVER_D", gn["arm_run_over_D_leg"], "each arm's level run, x leg D"),
        der("GN_ROOT_FWD", pg.gooseneck(g)["root_forward"], "the neck's first piece pierces the roof this far in front of the axis, m"),
        der("GN_OUT_AT_H", pg.gooseneck(g)["end_over_H"], "CFD arms' level runs' axis, x CALC_H", digits=12),
        der("CALC_TA_Z", pg.calciner_inlets(g)["tertiary_air"]["z"], "tertiary air axis over the throat's foot"),
        der("CALC_FEED_Z", pg.calciner_inlets(g)["meal"]["z_wall"], "meal pipes' axes at the wall, over the throat's foot"),
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
        der("C1_VOL_OUT", pg.cyclone_duct_inlet(g, "C1")["y_outer"], "C1 volute duct's outer wall from the C1 axis"),
        der("C1_VOL_FAR", -pg.cyclone_volute_extent(g, "C1")["y_min"], "C1 volute scroll's end, the side away from the duct"),
        der("C1_FEED_Z", br["z_feed"], "C1 feed chute axis at the branch wall"),
        src("C1_FEED_L", d["c1_feed_depth"], "C1 feed chute depth"),
        src("C1_FEED_W", d["c1_feed_width"], "C1 feed chute side"),
        der("C1_OUT_RISE", c1["outlet_rise"], "C1 outlet pipe rise"),
        der("C1_OUT_R", c1["outlet_bend_R"], "C1 outlet 180 deg bend centreline R"),
        src("STAGE_GAP", lay["stage_gap"]),
        der("ZIG_DX", L["column_offset"], "outer column outboard of the inner: the widest riser's offset"),
        src("DUST_OVER_ROOF", lay["dust_over_roof"], "C4..C2's dust outlet over the roof below"),
        src("RISER_SLOPE_DEG", d["riser_duct_slope_deg"], "R2..R4's inclined duct climbs at this slope into the level duct"),
        src("RISER_TAPER_DEG", d["riser_taper_deg"], "the inclined duct's sides narrow from D to W at this angle at most"),
        der("R4_RISE_V", L["riser_vertical"][4], "R4 vertical, C5's roof to its turn"),
        der("R3_RISE_V", L["riser_vertical"][3], "R3 vertical, C4's roof to its turn"),
        der("R2_RISE_V", L["riser_vertical"][2], "R2 vertical, C3's roof to its turn"),
        der("RISER_RUN", L["riser"][3]["run"], "R2/R3's transition: horizontal run, riser axis to the level duct's face"),
        der("RISER_RUN4", L["riser"][4]["run"], "R4's transition: horizontal run"),
        der("RISER_Y", L["riser"][3]["y"], "a riser's axis across from its cyclone's axis (depth): under the duct"),
        src("C5_OVER_TA", lay["c5_over_tertiary_air"]),
        src("GN_TO_C5_GAP", lay["gooseneck_to_c5_gap"]),
        src("C1_TWIN_GAP", lay["c1_twin_gap"], "twin C1: gap between the branches' walls"),
        der("C1_TWIN_S", tw["spacing"], "twin C1: axis to axis"),
        der("C1_DUCT_Y", tw["y_duct"], "C1 inlet duct / branch axis from the C1 axis"),
        der("R1_BRANCH_HALF", tw["branch_half"], "R1's Y: each branch from R1's axis"),
        src("R1_UP_MIN", lay["r1_up_min"]),
        src("KILN_AXIS_Z", lay["kiln_axis_z"]),
        src("CHAMBER_MARGIN", lay["chamber_margin"]),
        src("KIC_RAMP_DEG", g["kiln_inlet_chamber"]["ramp_deg"], "KIC ramp, to the horizontal"),
        src("KIC_RAMP_FOOT", g["kiln_inlet_chamber"]["ramp_foot"], "KIC ramp's level foot, toe to the kiln mouth"),
        der("KIC_TOP", pg.chamber_section(g)["height"], "KIC floor level to its top = the calciner's throat foot (the roof's highest point under the throat)"),
        src("COOLER_DROP", lay["cooler_drop"]),
        der("HOOD_L", pg.kiln_hood(g)["depth"], "kiln hood: depth along x from the kiln's end (the cooler's hood opening)"),
        der("HOOD_H", pg.kiln_hood(g)["H"], "kiln hood: height, the cooler's roof to the seal's top + clearance"),
        der("HOOD_TA_X", pg.kiln_flame(g)["h_ta"], "kiln hood: the tertiary air mouth's axis from the kiln's end, x"),
    ]
    return out


# ======================================================================
# drawings.bas: the equipment drawings (inner, fluid geometry)
# ======================================================================
TABLE_CHUNKS = 8          # TAB_1 .. TAB_8; a VBA line holds ~1000 characters
TABLE_CHUNK_LEN = 700


def _table_consts(prefix, P, order):
    """The sheet's parameter table as TAB_1..TAB_8 strings: rows split
    by ';', fields by '~': key, label, value, unit, source, status."""
    from tools.drawings import cyclone as dcy

    rows = []
    for k in order:
        p = P[k]
        fields = (k, p.label, dcy.cell(p), dcy.unit(p), dcy.SOURCE_EN[p.source], p.status)
        for f in fields:
            if any(ch in f for ch in ";~\""):
                raise ValueError(f"{k}: a table field may not contain ; ~ or a quote: {f!r}")
        rows.append("~".join(fields) + ";")
    chunks, cur = [], ""
    for r in rows:
        if len(cur) + len(r) > TABLE_CHUNK_LEN:
            chunks.append(cur)
            cur = ""
        cur += r
    chunks.append(cur)
    if len(chunks) > TABLE_CHUNKS:
        raise ValueError(f"{prefix}: the table needs {len(chunks)} chunks, the macro reads {TABLE_CHUNKS}")
    chunks += [""] * (TABLE_CHUNKS - len(chunks))
    return [Const(f"{prefix}_TAB_{i + 1}", s, "parameter table rows", kind="String")
            for i, s in enumerate(chunks)]


def drawings_bas(g):
    from tools.drawings import cyclone as dcy

    cy, d = g["cyclones"], g["cyclone_domain"]
    c1 = pg.cyclone(g, "C1")
    s = pg.cyclone_duct_inlet(g, "C1")
    o = pg.cyclone_outlet(g, "C1")
    P = dcy.params(g, "C1")
    nx, nz = s["normal"]
    cex, _, cez = s["face_centre"]
    h = 0.5 * c1["H_inlet"]
    out = [
        src("C1_D_BARREL", cy["C1"]["D_barrel"], "barrel inner D"),
        src("C1_H_BARREL", cy["C1"]["H_barrel"], "barrel height"),
        src("C1_H_CONE", cy["C1"]["H_cone"], "cone height"),
        src("C1_L_VORTEX", cy["C1"]["L_vortex"], "vortex finder immersion"),
        der("C1_D_VORTEX", c1["D_vortex"], "vortex finder / outlet pipe bore, D / 2"),
        src("C1_D_DUST", cy["C1"]["D_dust"], "dust outlet D"),
        src("C1_W_INLET", cy["C1"]["W_inlet"], "inlet width"),
        src("C1_H_INLET", cy["C1"]["H_inlet"], "inlet height, normal to the duct"),
        src("C1_INLET_SLOPE_DEG", cy["C1"]["inlet_slope"], "inlet duct slope"),
        src("C1_VORTEX_WALL", d["vortex_wall"], "vortex finder wall"),
        der("C1_HEIGHT", c1["height"], "barrel + cone"),
        der("C1_OUT_RISE", c1["outlet_rise"], "outlet pipe rise over the roof"),
        der("C1_OUT_R", c1["outlet_bend_R"], "outlet bend centreline R"),
        der("C1_OUT_RUN", c1["outlet_run"], "outlet drop leg"),
        der("C1_LEG_X", o["leg_x"], "barrel axis to drop leg axis"),
        der("C1_TOP", P["top"].value, "dust outlet to the top of the bend"),
        der("C1_Y_INNER", s["y_inner"], "inlet duct inner wall, y"),
        der("C1_Y_OUTER", s["y_outer"], "inlet duct outer wall, y"),
        der("C1_FACE_TOP_X", cex + h * nx, "inlet face, upper edge x"),
        der("C1_FACE_TOP_Z", cez + h * nz, "inlet face, upper edge z"),
        der("C1_FACE_BOT_X", cex - h * nx, "inlet face, lower edge x"),
        der("C1_FACE_BOT_Z", cez - h * nz, "inlet face, lower edge z"),
        der("C1_REACH", s.get("reach", 0.0), "inlet opening's upstream end on the barrel, -x (0: a volute)"),
    ]
    out += _table_consts("C1", P, dcy.ORDER)
    out += _twin_sheet_consts(g)
    out += _volute_sheet_consts(g)
    out += _calciner_sheet_consts(g)
    out += _kiln_sheet_consts(g)
    out += _kiln_rotax_sheet_consts(g)
    out += _kiln_burner_sheet_consts(g)
    out += _kiln_burner_body_sheet_consts(g)
    out += _kiln_flame_sheet_consts(g)
    out += _cooler_sheet_consts(g)
    out += _kic_sheet_consts(g)
    out += _idf_sheet_consts(g)
    return out


def _volute_sheet_consts(g):
    """What drawings.bas needs for the C4 and C5 sheets (volute cyclones
    with a riser inlet and a straight outlet), under their own prefix,
    and their tables."""
    from tools.drawings import volute as dvo

    d = g["cyclone_domain"]
    out = []
    for name in ("C4", "C5"):
        c = pg.cyclone(g, name)
        o = pg.cyclone_outlet(g, name)
        r = pg.cfd_riser_inlet(g, name)
        out += [
            der(f"{name}_D_BARREL", c["D_barrel"], "barrel inner D"),
            der(f"{name}_H_BARREL", c["H_barrel"], "barrel height"),
            der(f"{name}_H_CONE", c["H_cone"], "cone height"),
            der(f"{name}_L_VORTEX", c["L_vortex"], "vortex finder immersion"),
            der(f"{name}_D_VORTEX", c["D_vortex"], "vortex finder / outlet pipe bore"),
            der(f"{name}_D_DUST", c["D_dust"], "dust outlet D"),
            der(f"{name}_W_INLET", c["W_inlet"], "volute duct width"),
            der(f"{name}_H_INLET", c["H_inlet"], "volute duct height"),
            src(f"{name}_VORTEX_WALL", d["vortex_wall"], "vortex finder wall (not scaled)"),
            src(f"{name}_TONGUE", d["volute_tongue"], "volute tongue (not scaled)"),
            der(f"{name}_L_DUCT", c["inlet_duct_length"], "level volute duct length"),
            der(f"{name}_HEIGHT", c["height"], "barrel + cone"),
            der(f"{name}_OUT_RISE", c["outlet_rise"], "outlet pipe rise over the roof"),
            der(f"{name}_TOP", o["z_top"], "the straight outlet pipe's end face, z"),
            der(f"{name}_RISER_D", r["D"], "riser inlet D"),
            der(f"{name}_RISER_X", r["x"], "riser axis, x (the duct runs to -x)"),
            der(f"{name}_RISER_Y", r["y"], "riser axis, y (under the duct's middle)"),
            der(f"{name}_RISER_OFFSET", r["offset"], "riser axis from the barrel axis"),
            der(f"{name}_RISER_ZTOP", c["height"] - r["drop"], "the seam's foot (the riser's sides on the inclined floor), z"),
            der(f"{name}_RISER_ZOUT", c["height"] - r["drop_top"], "the riser's top on its axis (the inclined roof), z"),
            der(f"{name}_RISER_ZBOT", c["height"] - r["drop"] - r["stub"], "the riser's gas inlet face, z"),
        ]
        out += _table_consts(name, dvo.params(g, name), dvo.ORDER)
    return out


def _calciner_sheet_consts(g):
    """What drawings.bas needs for the calciner sheet, under a CAL_
    prefix, and its table."""
    from tools.drawings import calciner as dca

    c = g["calciner"]
    cal, inl, gn = pg.calciner(g), pg.calciner_inlets(g), pg.gooseneck(g)
    ta, meal, fuel = inl["tertiary_air"], inl["meal"], inl["fuel"]
    sf = math.sin(math.radians(pg.v(c["fuel_slope"])))
    out = [
        der("CAL_D_THROAT", cal["D_throat"], "throat (kiln gas inlet) D"),
        der("CAL_L_THROAT", cal["z_throat_top"], "throat length"),
        der("CAL_H_CONE", cal["h_cone"], "cone height"),
        der("CAL_D_VESSEL", cal["D"], "vessel inner D"),
        der("CAL_H_VESSEL", cal["H"], "cone + cylinder"),
        der("CAL_H_CYL", cal["h_cylinder"], "cylinder height"),
        der("CAL_Z_CONE", cal["z_cone_top"], "the cone's top, z"),
        der("CAL_Z_ROOF", cal["z_roof"], "the roof, z"),
        der("CAL_D_NECK", gn["D_neck"], "gooseneck neck D"),
        der("CAL_PIECE", gn["piece"], "the neck's inclined pieces"),
        der("CAL_LEVEL", gn["level"], "the neck's level piece"),
        der("CAL_Z_BEND", gn["nodes"][1][1], "the level piece's axis, z"),
        der("CAL_D_LEG", gn["D_leg"], "gooseneck arm D"),
        der("CAL_X_LEG", gn["x_leg"], "the arms' outlet faces, x"),
        der("CAL_Z_END", gn["z_end"], "the arms' level runs' axis, z"),
        der("CAL_WIDTH", 2.0 * gn["x_leg"], "overall width over the arms' outlet faces, x"),
        der("CAL_Z_SPLIT", gn["z_split"], "the channel's lower end, where the arms leave, z"),
        der("CAL_X_BEND", gn["x_bend"], "where an arm turns level, x"),
        der("CAL_Y_OFF", gn["y_off"], "the channel and the arms, in front of the axis"),
        der("CAL_TOP", gn["crown"], "the neck's crown, z"),
        der("CAL_Y_FRONT", gn["y_front"], "the channel's far side, forward of the axis"),
        der("CAL_TA_D", ta["D"], "tertiary air duct D"),
        der("CAL_TA_Y", ta["y"], "its axis, y"),
        der("CAL_TA_Z", ta["z"], "its axis, z"),
        der("CAL_TA_X", ta["x_end"], "its face, x"),
        der("CAL_FEED_D", meal["D"], "meal pipe D"),
        der("CAL_FEED_X", meal["end"][0], "meal pipe end face centre, x"),
        der("CAL_FEED_Z", meal["end"][1], "meal pipe end face centre, z"),
        der("CAL_FUEL_D", fuel["D"], "fuel pipe D"),
        der("CAL_FUEL_Y", fuel["end"][0], "fuel pipe end face centre, y"),
        der("CAL_FUEL_Z", fuel["end"][1], "fuel pipe end face centre, z"),
        der("CAL_BOX_Y", fuel["end"][0] + 0.5 * fuel["D"] * sf, "the fuel pipes' far side, y"),
    ]
    dp = pg.calciner_dispersion_plate(g)
    out += [
        der("CAL_DP_R", dp["R_arc"], "dispersion plate (+x): the meal face's radius"),
        der("CAL_DP_T", dp["thickness"], "its thickness"),
        der("CAL_DP_CX", dp["centre"][0], "the arcs' centre, x"),
        der("CAL_DP_CZ", dp["centre"][1], "the arcs' centre, z"),
        der("CAL_DP_AX", dp["A"][0], "the meal face's start on the wall, x"),
        der("CAL_DP_AZ", dp["A"][1], "the meal face's start on the wall, z"),
        der("CAL_DP_EX", dp["E"][0], "the meal face's edge, x"),
        der("CAL_DP_EZ", dp["E"][1], "the meal face's edge, z"),
        der("CAL_DP_ELX", dp["E_low"][0], "the lower face's edge, x"),
        der("CAL_DP_ELZ", dp["E_low"][1], "the lower face's edge, z"),
        der("CAL_DP_ZLOW", dp["z_low"], "the lower face's lowest point, z"),
        der("CAL_DP_PROT", dp["protrusion"], "the edge past the wall"),
        der("CAL_DP_EXIT", dp["exit_angle"], "the exit angle above the horizontal, deg"),
        der("CAL_DP_SLOPE", pg.calciner_inlets(g)["meal"]["slope"], "the meal pipe's slope, where the plate starts, deg"),
    ]
    out += _table_consts("calciner", dca.params(g), dca.ORDER)
    return out


def _kiln_sheet_consts(g):
    """What drawings.bas needs for the kiln sheet (its bore and its wall as the
    twin models it), under a KLN_ prefix: the radii, the layer legend
    from physics/shell.py's stacks, and the table."""
    from tools.drawings import kiln as dkl

    k = pg.kiln(g)
    w = k["wall"]
    out = [
        der("KLN_L", k["L"], "kiln length, all lined"),
        der("KLN_TL", k["transition_L"], "the transition (alumina) zone from the back end"),
        der("KLN_R_FLOW", w["r_flow"], "the flow bore: the brick's hot face, both zones"),
        der("KLN_Z_CFD0", k["z_cfd0"], "the CFD solid's back face (kiln.SLDPRT; the KIC's stub before it)"),
        der("KLN_BRICK_L", pg.v(g["kiln"]["brick_length"]), "one brick ring along the axis (ISO 5417)"),
        der("KLN_BRICK_N", w["brick_n_burning"], "bricks per ring (both zones)"),
    ]
    out += [
        der("KLN_R_SHELL_IN", w["r_shell_in_burning"], "shell inner radius = brick cold face (one tube)"),
        der("KLN_R_SHELL", w["r_shell_burning"], "shell outer radius (one tube)"),
    ]
    for i, (body, where, name, kc, rho, cp) in enumerate(dkl.layer_properties()):
        text = (f"{body} ({where}): {name}, k {kc:g} W/(m K), rho {rho:g} kg/m3, cp {cp:g} J/(kg K)")
        out.append(Const(f"KLN_LAYER_{i + 1}", text, "physics/shell.py DEFAULT_WALL_STACKS", kind="String"))
    out += _table_consts("kiln", dkl.params(g), dkl.ORDER)
    return out


def _kiln_rotax_sheet_consts(g):
    """What drawings.bas needs for the kiln_rotax sheet (the ROTAX-2 parts
    of kiln_rotax.SLDPRT), under an RTX_ prefix: the part's body count and
    joint extent (the box check), the radii and places the views, the
    dimensions and the kiln shell's phantom outline use, and the table."""
    from tools.drawings import kiln_rotax as drx

    r = pg.kiln_rotax(g)
    k = pg.kiln(g)
    by = {b["name"]: b for b in r["bodies"]}
    box = [min(b["box"][i] for b in r["bodies"]) for i in range(3)] + \
          [max(b["box"][i] for b in r["bodies"]) for i in range(3, 6)]
    t = by["tyre_inlet"]["p"]                       # ring r0, r1, z0, z1
    band = by["tyre_section_inlet"]["p"]
    rol = by["roller_inlet_R"]["p"]                 # cyl base, axis, r, length
    out = [
        der("RTX_N", len(r["bodies"]), "bodies in kiln_rotax.SLDPRT"),
        der("RTX_X0", box[0], "the part's x min"), der("RTX_Y0", box[1], "the part's y min (the inlet pier's foot)"),
        der("RTX_Z0", box[2], "the part's z min (the inlet pier, behind the drive)"),
        der("RTX_X1", box[3], "the part's x max"), der("RTX_Y1", box[4], "the part's y max (the tyres' top)"),
        der("RTX_Z1", box[5], "the part's z max (the hood end)"),
        der("RTX_L", k["L"], "kiln length (the shell's phantom outline)"),
        der("RTX_R_SHELL", k["wall"]["r_shell_burning"], "kiln shell's outer radius (phantom outline)"),
        der("RTX_Z_IN", r["z_tyre_inlet"], "inlet tyre centre"),
        der("RTX_Z_OUT", r["z_tyre_outlet"], "outlet tyre centre"),
        der("RTX_TZ0", t[2], "inlet tyre's back face"), der("RTX_TZ1", t[3], "inlet tyre's hood face"),
        der("RTX_OUT_TZ0", by["tyre_outlet"]["p"][2], "outlet tyre's back face"),
        der("RTX_R_TB", t[0], "tyre bore radius"), der("RTX_R_TO", t[1], "tyre outer radius"),
        der("RTX_R_BAND", band[1], "tyre section plate's outer radius"),
        der("RTX_BZ0", band[2], "inlet tyre section's back end"), der("RTX_BZ1", band[3], "inlet tyre section's hood end"),
        der("RTX_R_R", rol[6], "support roller radius"),
        der("RTX_RZ1", rol[2] + rol[7], "inlet rollers' hood face (A-A cuts just past it)"),
        der("RTX_R_IS", by["inlet_seal"]["p"][1], "inlet seal housing's outer radius"),
        der("RTX_X_R", rol[0], "support roller centre, x (+)"), der("RTX_Y_R", rol[1], "support roller centre, y"),
        der("RTX_Y_PIER", r["y_pier_top"], "pier top"),
        der("RTX_G_IN", r["ground_inlet"], "ground under the inlet pier"),
        der("RTX_G_OUT", r["ground_outlet"], "ground under the outlet pier"),
        der("RTX_Z_HTD", by["htd"]["p"][2], "thrust roller's centre, z"),
        der("RTX_Z_MOTOR", by["motor_R"]["p"][4], "main motors' back end"),
        der("RTX_Z_FAN1", by["shell_fan_1"]["p"][2], "first shell fan, z"),
        der("RTX_X_WALK", 0.5 * (by["walkway"]["p"][0] + by["walkway"]["p"][1]), "walkway's middle, x"),
        der("RTX_Y_WALK", by["walkway"]["p"][2], "walkway's underside"),
        der("RTX_Z_NOSE", by["nose_ring_fan"]["p"][2], "nose ring fan, z"),
    ]
    out += _table_consts("kiln_rotax", drx.params(g), drx.ORDER)
    return out


def _kiln_burner_sheet_consts(g):
    """What drawings.bas needs for the kiln_burner sheet (the burner's
    channels, kiln_burner.SLDPRT), under a BRN_ prefix: each channel's
    volume (the part check), the radii and planes the views and the
    dimensions use, and the table."""
    from tools.drawings import kiln_burner as dkb

    r = pg.kiln_burner(g)
    gr = r["groups"]
    (sw0, sw1), (ax0, ax1) = r["swirl_plenum"], r["axial_plenum"]
    out = [
        der("BRN_V_COAL", gr["coal"]["V"], "coal channel volume [m3]", digits=9),
        der("BRN_V_AXIAL", gr["axial"]["V"], "axial channel volume [m3]", digits=9),
        der("BRN_V_SWIRL", gr["swirl"]["V"], "swirl channel volume [m3]", digits=9),
        der("BRN_R_C", 0.5 * r["D_coal"], "coal pipe radius"),
        der("BRN_Y_C", r["y_coal"], "coal pipe axis above the tip axis"),
        der("BRN_L_C", r["L_coal"], "coal pipe length (its inlet at z = -L)"),
        der("BRN_SW_R0", sw0, "swirl plenum inner radius"), der("BRN_SW_R1", sw1, "swirl plenum outer radius"),
        der("BRN_AX_R0", ax0, "axial plenum inner radius"), der("BRN_AX_R1", ax1, "axial plenum outer radius"),
        der("BRN_T", r["plate_t"], "front plate: the openings run z -T .. 0"),
        der("BRN_LP", r["plenum_L"], "plenums: z -T-LP .. -T"),
        der("BRN_R_S", r["r_slots"], "slot ring radius (one slot on top, x = 0)"),
        der("BRN_R_H", r["r_holes"], "hole ring radius"),
        der("BRN_SLOT_L", r["slot_l"], "slot long side"), der("BRN_SLOT_W", r["slot_w"], "slot short side"),
    ]
    out += _table_consts("kiln_burner", dkb.params(g), dkb.ORDER)
    return out


def _kiln_burner_body_sheet_consts(g):
    """What drawings.bas needs for the kiln_burner_body sheet (the whole
    burner, kiln_burner_body.SLDPRT), under a KBD_ prefix, and its table."""
    from tools.drawings import kiln_burner_body as dkd

    r = pg.kiln_burner_body(g)
    by = {b["name"]: b for b in r["bodies"]}
    bx = r["box"]
    out = [
        der("KBD_N", len(r["groups"]), "bodies in kiln_burner_body.SLDPRT"),
        der("KBD_X0", bx[0], "the part's x min (the air inlets)"), der("KBD_Y0", bx[1], "the part's y min"),
        der("KBD_Z0", bx[2], "the part's z min (the beam's back end)"),
        der("KBD_X1", bx[3], "the part's x max"), der("KBD_Y1", bx[4], "the part's y max (the beam's top)"),
        der("KBD_Z1", bx[5], "the part's z max (the tip)"),
        der("KBD_R_TIP", 0.5 * r["D_tip"], "tip ring's outer radius"),
        der("KBD_R_C", r["R_castable"], "castable's outer radius"),
        der("KBD_Z_RING", r["z_ring"], "tip ring's back face"),
        der("KBD_Z_CAST", r["z_castable"], "castable's back end"),
        der("KBD_Z_FL", r["z_flange"], "head's front face (the flange's back)"),
        der("KBD_Z_HEAD", r["z_head"], "head's back face"),
        der("KBD_R_HEAD", r["r_head"], "head's radius"),
        der("KBD_R_FL", by["flange"]["p"][6], "flange's radius"),
        der("KBD_R_BEL", by["bellows"]["p"][6], "expansion joint's radius"),
        der("KBD_Z_BEL", r["z_bellows"], "expansion joint's back face"),
        der("KBD_Z_COAL", r["z_coal"], "coal inlet flange's back face centre (the burner's back end)"),
        der("KBD_R_COALF", by["coal_inlet_flange"]["p"][6], "coal inlet flange's radius"),
        der("KBD_Y_C", by["coal_inlet"]["p"][1], "coal inlet's axis over the burner's"),
        der("KBD_Y_COALE", r["y_coal_flange"], "coal inlet flange's back face centre (the pipe tilted up), y"),
        der("KBD_Y_BEAM", by["beam_web_R"]["p"][2], "beam's underside"),
        der("KBD_Z_IN1", r["z_elbow_up"], "air inlet 1 (the elbow) rises here, z"),
        der("KBD_Z_IN2", r["z_inlet2"], "air inlet 2, z"),
        der("KBD_X_IN", r["x_inlet2"], "air inlet 2's outer end, x"),
        der("KBD_X_EL", r["x_elbow"], "the elbow's leg, x"),
        der("KBD_R_HF", r["r_head_flange"], "head flanges' radius"),
        der("KBD_Z_PART", r["z_partition"], "head partition, z"),
        der("KBD_Z_SEC", r["z_elbow_up"], "section B-B: through the head's front compartment at air inlet 1, z"),
        der("KBD_R_CORE", pg.kiln_burner(g)["swirl_plenum"][0], "core tube's outer radius (= swirl plenum's inner)"),
    ]
    out += _table_consts("kiln_burner_body", dkd.params(g), dkd.ORDER)
    return out


def _kiln_flame_sheet_consts(g):
    """What drawings.bas needs for the kiln_flame sheet (the flame zone's
    CFD volume, kiln_flame.SLDPRT, kiln frame), under a KFD_ prefix: the
    part's box and the model points the dimensions pick, and its table."""
    from tools.drawings import kiln_flame as dkf

    f, hd, co, kl = pg.kiln_flame(g), pg.kiln_hood(g), pg.cooler(g), pg.kiln(g)
    ch = pg.kiln_burner(g)
    Hd, U = f["Hd"], f["U"]
    K = (0.0, 0.0, kl["L"])

    def at(h, u, x=0.0):
        return (K[0] + x, K[1] + h * Hd[1] + u * U[1], K[2] + h * Hd[2] + u * U[2])

    def pt(name, p, what):
        return [der(f"{name}_{c}", p[i], f"{what}, {c.lower()}") for i, c in enumerate("XYZ")]

    d, W, above, below = hd["depth"], hd["W"], hd["above"], hd["below"]
    st, seg, cw = pg.v(g["kiln_hood"]["flame_stub_L"]), co["segment_L"], co["width"]
    R, r_ta, z_cut, tip = 0.5 * kl["D"], f["r_ta"], f["z_cut"], f["tip"]
    c_ta = at(f["h_ta"], above + st)
    bx = f["box"]
    out = [
        der("KFD_X0", bx[0], "the part's x min"), der("KFD_Y0", bx[1], "the part's y min (segment 2's stub)"),
        der("KFD_Z0", bx[2], "the part's z min (the kiln gas outlet)"),
        der("KFD_X1", bx[3], "the part's x max"), der("KFD_Y1", bx[4], "the part's y max (the tertiary air mouth)"),
        der("KFD_Z1", bx[5], "the part's z max (the hood's front wall)"),
        der("KFD_W", W, "hood inner width"), der("KFD_DEPTH", d, "hood depth"),
        der("KFD_SEG", seg, "cooler segment under the hood"),
        der("KFD_R", R, "kiln bore radius"), der("KFD_Z_CUT", z_cut, "kiln gas outlet, z"),
        der("KFD_R_TA", r_ta, "tertiary air mouth radius"), der("KFD_Z_TA", c_ta[2], "its top face's centre, z"),
        der("KFD_Z_TIP", tip[2], "burner tip, z"), der("KFD_TIP_TO_CUT", tip[2] - z_cut, "burner tip to the gas outlet"),
        der("KFD_Z_FRONT", at(d, 0.0)[2], "hood front wall at the kiln axis, z"),
    ]
    xs = -0.5 * W                                     # the side view looks from -x
    out += pt("KFD_BACK", at(0.0, 0.5 * (above + 0.5 * kl["D"]), xs), "back wall's edge, side view")
    out += pt("KFD_FRONT", at(d, 0.5 * (above + 0.5 * kl["D"]), xs), "front wall's edge, side view")
    out += pt("KFD_SEGA", at(seg, -below - 1.5 * st, -0.5 * cw), "segment 2 stub's back edge, side view")
    out += pt("KFD_SEGB", at(2.0 * seg, -below - 1.5 * st, -0.5 * cw), "segment 2 stub's front edge, side view")
    out += pt("KFD_BORE", (-0.7071 * R, 0.7071 * R, z_cut), "kiln gas outlet circle, a point on it")
    out += pt("KFD_TA", tuple(c_ta[i] + r_ta * 0.7071 * ((1.0, 0.0, 0.0)[i] + Hd[i]) for i in range(3)),
              "tertiary air mouth circle, a point on it")
    r_tipline = -0.5 * (ch["axial_plenum"][1] + 0.5 * pg.kiln_burner_body(g)["D_tip"])
    out += pt("KFD_TIPL", (0.0, r_tipline, tip[2]), "burner tip face's cut edge, A-A")
    out += pt("KFD_CUTL", (0.0, -0.5 * R, z_cut), "kiln gas outlet's cut edge, A-A")
    out += pt("KFD_SEC_T", at(d, above + 0.3), "A-A's cutting line, top (front view)")
    out += pt("KFD_SEC_B", at(d, -below - 2.0 * st - 0.3), "A-A's cutting line, bottom (front view)")
    out += _table_consts("kiln_flame", dkf.params(g), dkf.ORDER)
    return out


def _idf_sheet_consts(g):
    """What drawings.bas needs for the ID fan sheet, under an IDF_ prefix,
    and its table."""
    from tools.drawings import id_fan as dif

    f = pg.id_fan(g)
    out = [
        der("IDF_R1", 0.5 * f["D_inlet"], "the eye's circle (y = b1)"),
        der("IDF_R2", 0.5 * f["D_impeller"], "the tip's circle (y = b2)"),
        der("IDF_B1", f["b1"], "the eye's plane y"),
        der("IDF_B2", f["b2"], "the outlet width b2: the rim ring's top y"),
        der("IDF_R_MRF", f["r_mrf"], "the rotating zone's rim"),
        der("IDF_VOL_B", f["B"], "the volute's width, y = 0 .. B"),
        der("IDF_E_TOP_X", f["e_top"][0], "the outlet face's outer edge (along y), x"),
        der("IDF_E_TOP_Z", f["e_top"][1], "the outlet face's outer edge, z"),
        der("IDF_E_LOW_X", f["e_low"][0], "the outlet face's lower edge (along y), x"),
        der("IDF_E_LOW_Z", f["e_low"][1], "the outlet face's lower edge, z"),
        der("IDF_DIS_DX", f["discharge_dir"][0], "the discharge's direction, x", digits=9),
        der("IDF_DIS_DZ", f["discharge_dir"][1], "the discharge's direction, z", digits=9),
        der("IDF_X_MIN", f["volute_box"][0], "the fan's x min (the volute)"),
        der("IDF_Z_MIN", f["volute_box"][1], "the fan's z min (the volute)"),
        der("IDF_Z_MAX", f["volute_box"][3], "the fan's z max (the outlet's outer edge)"),
        der("IDF_Y_BOX", f["y_box"], "the inlet box's floor, y"),
        der("IDF_BOX_H", f["H_box"], "the inlet box's height (z), x from -BOX_H/2"),
        der("IDF_BOX_DEPTH", f["depth_box"], "the inlet box's depth (y)"),
        der("IDF_BOX_REACH", f["reach_box"], "the box's inlet face, x"),
        der("IDF_V_ROTOR", f["V_rotor_bladed"], "the bladed rotor's volume: tells today's solid from an older one [m3]"),
    ]
    out += _table_consts("id_fan", dif.params(g), dif.ORDER)
    return out


def _kic_sheet_consts(g):
    """What drawings.bas needs for the kiln inlet chamber sheet, under a
    KIC_ prefix, and its table."""
    from tools.drawings import kiln_inlet_chamber as dkc

    ch = pg.kiln_inlet_chamber(g)
    out = [
        der("KIC_A", ch["side"], "plan: across (y)"),
        der("KIC_H", ch["height"], "floor level to the throat's top (outlet)"),
        der("KIC_D_THROAT", ch["D_throat"], "the throat (outlet); its walls x = +-r"),
        src("KIC_D_MOUTH", g["kiln"]["D"], "the kiln tube's stub, its end disc the inlet"),
        der("KIC_ALPHA", ch["alpha"], "the kiln's slope [rad]", digits=9),
        der("KIC_RAMP_TOP_Z", ch["ramp_top"][1], "the ramp's top on the left wall x = -r"),
        der("KIC_ROOF_LEFT_Z", ch["roof_left"][1], "the roof at the left wall x = -r"),
        der("KIC_TOE_X", ch["toe"][0], "the ramp's toe"),
        der("KIC_TOE_Z", ch["toe"][1], "the ramp's toe"),
        der("KIC_LIP_LO_X", ch["lip_low"][0], "the mouth's lower lip"),
        der("KIC_LIP_LO_Z", ch["lip_low"][1], "the mouth's lower lip"),
        der("KIC_LIP_UP_X", ch["lip_up"][0], "the mouth's upper lip"),
        der("KIC_LIP_UP_Z", ch["lip_up"][1], "the mouth's upper lip"),
        der("KIC_STUB_L", ch["L_stub"], "the kiln tube's stub along its axis"),
        src("KIC_RAMP_DEG", g["kiln_inlet_chamber"]["ramp_deg"], "the ramp, to the horizontal"),
    ]
    out += _table_consts("kiln_inlet_chamber", dkc.params(g), dkc.ORDER)
    return out


def _cooler_sheet_consts(g):
    """What drawings.bas needs for the cooler sheet, under a COO_ prefix,
    and its table."""
    from tools.drawings import cooler as dco

    c = pg.cooler(g)
    out = [
        der("COO_L", c["length"], "grate length, hot end x = 0 to the cold end"),
        der("COO_W", c["width"], "grate width"),
        der("COO_H", c["casing_height"], "grate to roof"),
        der("COO_SEG_L", c["segment_L"], "one segment's length"),
        der("COO_HOOD_L", c["hood_L"], "the hood opening's length from x = 0"),
        der("COO_SEGMENTS", float(c["segments"]), "undergrate air segments"),
    ]
    out += _table_consts("cooler", dco.params(g), dco.ORDER)
    return out


def _twin_sheet_consts(g):
    """What drawings.bas needs for the C1_twin sheet: c1_twin.bas' own
    Consts under a TW_ prefix, the section's level, the sheet's table."""
    from tools.drawings import twin as dtw

    d = g["cyclone_domain"]
    br, tw = pg.c1_branch(g), pg.c1_twin(g)
    c1, o = pg.cyclone(g, "C1"), pg.cyclone_outlet(g, "C1")
    L = pg.layout(g)
    th = math.radians(pg.v(d["meal_slope"]))
    rb = 0.5 * br["D"]
    # the feed chute's top corner and its far side, in the C1 frame
    chute_top = br["z_feed"] + pg.v(d["c1_feed_depth"]) * math.sin(th) + 0.5 * pg.v(d["c1_feed_width"]) * math.cos(th)
    y_min = -(br["x"] + rb + pg.v(d["c1_feed_depth"]) * math.cos(th) + 0.5 * pg.v(d["c1_feed_width"]) * math.sin(th))
    out = [
        der("TW_R1_D", pg.r1_D(g), "R1 bore = C2's D_x"),
        src("TW_GAP", g["layout"]["c1_twin_gap"], "the branches' walls apart"),
        der("TW_S", tw["spacing"], "C1 axis to axis"),
        der("TW_BRANCH_HALF", tw["branch_half"], "each branch from R1's axis, x"),
        der("TW_BRANCH_D", br["D"], "branch bore"),
        der("TW_Y_BRANCH", tw["y_branch"], "branches and R1 in front of the C1 axes, y"),
        der("TW_Z_BRANCH", tw["z_branch"], "the branches' floor"),
        der("TW_Z_SPLIT", tw["z_split"], "R1's top: the Y starts"),
        der("TW_R1_STUB_L", L["z_r1_split"] - L["z_r1_foot"], "R1 straight under its Y, from C2's CFD outlet top"),
        der("TW_Z_CUT", 0.5 * (chute_top + br["z_bend"]), "section A-A: clear of the feed chutes and the bends"),
        der("TW_C1_R", 0.5 * c1["D_barrel"], "barrel radius"),
        der("TW_C1_FAR", -pg.cyclone_volute_extent(g, "C1")["y_min"] if c1["volute"] else 0.5 * c1["D_barrel"],
            "each C1's outer side from its axis: the barrel, or the volute's scroll end"),
        der("TW_Y_MIN", y_min, "the feed chutes' far side, y (the C1_riser solid's -x)"),
        der("TW_Y_MAX", o["leg_x"] + 0.5 * o["D"], "the outlet legs' far side, y"),
        der("TW_TOP", o["z_bend"] + o["bend_R"] + 0.5 * o["D"], "the outlet bends' crown"),
    ]
    out += _table_consts("C1_twin", dtw.params(g), dtw.ORDER)
    return out


# ======================================================================
# c1_twin.bas
# ======================================================================
def c1_twin_bas(g):
    d, lay = g["cyclone_domain"], g["layout"]
    c1, br, tw = pg.cyclone(g, "C1"), pg.c1_branch(g), pg.c1_twin(g)
    o = pg.cyclone_outlet(g, "C1")
    L = pg.layout(g)
    th = math.radians(pg.v(d["meal_slope"]))
    rb = 0.5 * br["D"]
    # the feed chute's far corner, out along -x of the C1 frame
    tip = -(br["x"] + rb + pg.v(d["c1_feed_depth"]) * math.cos(th) + 0.5 * pg.v(d["c1_feed_width"]) * math.sin(th))
    return [
        der("R1_D", pg.r1_D(g), "R1 bore = C2's D_x"),
        src("TWIN_GAP", lay["c1_twin_gap"], "the branches' walls apart"),
        der("TWIN_S", tw["spacing"], "C1 axis to axis"),
        der("BRANCH_HALF", tw["branch_half"], "each branch from R1's axis, x"),
        der("BRANCH_D", br["D"], "branch bore (half R1's area)"),
        der("BRANCH_Y", tw["y_branch"], "branches and R1 in front of the C1 axes, y"),
        der("Z_BRANCH", tw["z_branch"], "the branches' floor (the C1_riser inlet face)"),
        der("Z_SPLIT", tw["z_split"], "R1's top: the Y starts"),
        der("R1_STUB_L", L["z_r1_split"] - L["z_r1_foot"], "R1 straight under its Y, from the top of C2's CFD outlet pipe"),
        der("C1_R", 0.5 * c1["D_barrel"], "barrel radius"),
        der("C1_Y_FAR", -pg.cyclone_volute_extent(g, "C1")["y_min"] if c1["volute"] else 0.5 * c1["D_barrel"],
            "the C1_riser solid's side away from its duct (C1 frame -y): the barrel, or the volute's scroll end"),
        der("C1_TOP", o["z_bend"] + o["bend_R"] + 0.5 * o["D"], "the outlet bend's crown"),
        der("C1_X_MAX", o["leg_x"] + 0.5 * o["D"], "the C1_riser solid's far side, its outlet leg (C1 frame x)"),
        der("C1_X_MIN", tip, "the C1_riser solid's near side, its feed chute (C1 frame x)"),
        der("OUT_Z_END", o["z_end"], "the outlet legs' end faces"),
    ]


# ======================================================================
# kiln.bas
# ======================================================================
def cooler_bas(g):
    c, cc = g["cooler"], pg.cooler(g)
    return [
        src("COOLER_W", c["width"], "grate width"),
        src("COOLER_H", c["casing_height"], "grate to roof"),
        src("COOLER_SEGMENTS", c["segments"], "undergrate air segments (FLS)"),
        src("COOLER_HOOD_SEGMENTS", c["hood_segments"], "segments from the hot end under the hood's opening"),
        der("COOLER_L", cc["length"], "grate area / width, hot end x = 0 to the cold end"),
        der("COOLER_SEG_L", cc["segment_L"], "one segment's length"),
        der("COOLER_HOOD_L", cc["hood_L"], "the hood opening's length from x = 0"),
    ]


def kiln_inlet_chamber_bas(g):
    s, kl = pg.chamber_section(g), g["kiln"]
    return [
        der("CH_A", s["a"], "half the plan (y), and the kiln axis over the floor level at x = a: kiln D / 2 + the layout margin"),
        src("KILN_D", kl["D"], "the kiln tube's bore: the stub and its end disc (kiln_gas_inlet)"),
        der("CH_ALPHA", s["alpha"], "the kiln's slope [rad]: the stub's axis falls at it towards +x", digits=9),
        der("CH_H", s["height"], "the throat's top (throat_outlet), over the floor level"),
        der("CH_R_THROAT", s["r_throat"], "the calciner throat's radius; its walls x = +-r"),
        der("CH_RAMP_TOP_Z", s["ramp_top"][1], "the ramp's top on the left wall x = -r"),
        der("CH_TOE_X", s["toe"][0], "the ramp's toe: the foot (the kiln's bottom line) starts"),
        der("CH_TOE_Z", s["toe"][1], "the ramp's toe"),
        der("CH_LIP_LO_X", s["lip_low"][0], "the mouth's lower lip (the end face square to the kiln axis)"),
        der("CH_LIP_LO_Z", s["lip_low"][1], "the mouth's lower lip"),
        der("CH_LIP_UP_X", s["lip_up"][0], "the mouth's upper lip"),
        der("CH_LIP_UP_Z", s["lip_up"][1], "the mouth's upper lip"),
        der("CH_ROOF_LEFT_Z", s["roof_left"][1], "the roof (the kiln's top line) at the left wall x = -r"),
        der("CH_ROOF_THROAT_Z", s["roof_at_throat"], "the roof at the throat's right wall x = +r"),
        der("CH_STUB_L", s["L_stub"], "the kiln tube's stub along its axis, mouth face to kiln_gas_inlet"),
        der("CH_V_BOX", s["V_box"], "the section's prism, the plan across [m3]"),
        der("CH_V_THROAT", s["V_throat"], "the throat cylinder over the roof [m3]"),
        der("CH_V_STUB", s["V_stub"], "the kiln tube's stub [m3]"),
    ]


def id_fan_bas(g):
    f, fan = g["id_fan"], pg.id_fan(g)
    return [
        der("FAN_R1", 0.5 * fan["D_inlet"], "eye radius: the blades' leading edge, the shroud's inner rim"),
        der("FAN_R2", 0.5 * fan["D_impeller"], "impeller tip radius"),
        der("FAN_B1", fan["b1"], "blade height at r1: hub (y = 0) to the shroud, the eye's plane"),
        der("FAN_B2", fan["b2"], "blade height at r2 (the outlet width)"),
        der("FAN_R_MRF", fan["r_mrf"], "the rotating zone's rim"),
        Const("FAN_Z", fan["z"], "blade count [derived]", kind="Long"),
        src("BLADE_T", f["blade_thickness"], "plate blade thickness"),
        der("BLADE_R_IN", fan["blade_r_in"], "the blades' inner cap: r1 + the edge clearance"),
        der("BLADE_R_OUT", fan["blade_r_out"], "the blades' outer cap: r2 - the edge clearance"),
        der("BLADE_RB", fan["blade_arc_R"], "the blade centreline's arc radius"),
        der("BLADE_RC", fan["blade_arc_centre_r"], "the arc centre's distance from the axis"),
        der("BLADE_SENSE", fan["blade_sense"], "+1: a point at radius r sits +phi(r) from the centre's ray (backward)"),
        der("VOL_B", fan["B"], "volute width, y = 0 (back wall, the hub's plane) to B"),
        der("VOL_R3", fan["r3"], "the spiral's start radius (tongue circle)"),
        der("VOL_K", fan["k_spiral"], "log spiral r = R3 exp(K theta), K = tan(alpha), from the outlet velocity", digits=9),
        der("VOL_PSI0", math.radians(fan["psi0"]), "the spiral's start ray from +x towards +z [rad]", digits=9),
        der("NOSE_R", fan["tongue_radius"], "the tongue's nose radius"),
        der("DIS_DX", fan["discharge_dir"][0], "the discharge's direction, x (-cos gamma)", digits=9),
        der("DIS_DZ", fan["discharge_dir"][1], "the discharge's direction, z (sin gamma)", digits=9),
        der("VOL_S_EXIT", fan["s_exit"], "the outlet face: the plane p . (DIS_DX, 0, DIS_DZ) = this"),
        der("CONE_R", 0.5 * fan["D_cone"], "the inlet cone's mouth radius (r1 at y = B1)"),
        der("CONE_L", fan["L_cone"], "the inlet cone's length, y = B1 to the box's floor (B + the front plate)"),
        der("BOX_H", fan["H_box"], "the inlet box's height (z) and width behind the axis (x from -BOX_H/2)"),
        der("BOX_DEPTH", fan["depth_box"], "the inlet box's depth along y"),
        der("BOX_REACH", fan["reach_box"], "the box's inlet face, x"),
        der("V_ROTOR", fan["V_rotor"], "rotating zone before the blades are cut [m3]"),
        der("V_BLADES", fan["V_blades"], "the blades' volume, hub to shroud [m3]"),
        der("V_VOLUTE", fan["V_volute"], "volute + discharge outside the rotating zone [m3]"),
        der("V_CONE", fan["V_cone"], "inlet cone [m3]"),
        der("V_BOX", fan["V_box"], "inlet box [m3]"),
    ]


def kiln_bas(g):
    k = g["kiln"]
    return [
        src("KILN_D", k["D"], "effective inner diameter"),
        src("KILN_L", k["L"], "back end (z = 0) to hood end"),
        der("KILN_Z0", pg.kiln(g)["z_cfd0"], "the solid's back face: the kiln inlet chamber's stub ends here (stub + solid = KILN_L)"),
        src("KILN_SLOPE", k["slope"], "%: the installed slope, not built into the solid"),
        src("KILN_TRANSITION_L", k["transition_L"], "the transition zone from the back end (model split)"),
    ]


def kiln_wall_bas(g):
    k, w = g["kiln"], pg.kiln(g)["wall"]
    n_t, n_b = w["brick_n_transition"], w["brick_n_burning"]
    if n_t != n_b or w["V_brick_ring_transition"] != w["V_brick_ring_burning"]:
        raise ValueError("kiln wall: the zones' brick rings differ; one tube cannot hold both")
    v_ring = w["V_brick_ring_burning"]
    return [
        src("KILN_D", k["D"], "the flow (gas) bore: the brick's hot face, the whole tube (the twin's D)"),
        src("KILN_L", k["L"], "back end (z = 0) to hood end: the whole tube is lined"),
        src("KILN_SHELL_T", k["shell_t"], "steel shell plate"),
        src("KILN_BRICK_T", k["lining_t"], "brick ring, both zones"),
        der("V_SHELL", w["V_shell_transition"] + w["V_shell_burning"], "steel shell, one tube 0 .. L [m3]"),
        src("KILN_BRICK_L", k["brick_length"], "brick length along the axis (ISO 5417): one ring"),
        der("BRICK_N", n_b, "bricks per ring (both zones)"),
        der("V_RING", v_ring, "one brick ring, all its bricks [m3]"),
        der("V_BRICK", w["V_brick_transition"] + w["V_brick_burning"] - 2.0 * v_ring,
            "brick tube between the two brick-by-brick end rings [m3]"),
    ]


KRX_CHUNKS = 20


def _fixed(q):
    t = f"{q:.9f}".rstrip("0").rstrip(".")
    return "0" if t in ("", "-0") else t


def kiln_rotax_bas(g):
    """kiln_rotax.bas: every body plant_geometry.kiln_rotax() lays out as
    name|kind|params|V|box (x0 y0 z0 x1 y1 z1)|r g b, the bodies joined by
    ";" into KRX_CHUNKS strings (a VBA line holds about 1000 characters;
    the macro joins KRX_1 .. KRX_20)."""
    r = pg.kiln_rotax(g)
    recs = []
    for b in r["bodies"]:
        nums = list(b["p"]) + [b["V"]] + list(b["box"]) + list(b["rgb"])
        # fixed point (VBA's Val reads it in any locale; no exponent)
        recs.append("|".join([b["name"], b["kind"]] + [_fixed(q) for q in nums]) + ";")
    chunks, cur = [], ""
    for rec in recs:
        if len(cur) + len(rec) > 900:
            chunks.append(cur)
            cur = ""
        cur += rec
    chunks.append(cur)
    if len(chunks) > KRX_CHUNKS:
        raise ValueError(f"kiln_rotax: {len(chunks)} chunks, the macro joins {KRX_CHUNKS}")
    chunks += [""] * (KRX_CHUNKS - len(chunks))
    out = [der("N_BODIES", len(recs), "bodies in the part")]
    out += [Const(f"KRX_{i + 1}", c, "plant_geometry.kiln_rotax() bodies", kind="String")
            for i, c in enumerate(chunks)]
    return out


KBB_CHUNKS = 16


def kiln_burner_body_bas(g):
    """kiln_burner_body.bas: the whole burner's envelope bodies
    (plant_geometry.kiln_burner_body()) as name|group|kind|params|V|box|rgb,
    joined by the macro from KBB_1 .. KBB_16; KBB_GROUPS lists each group
    (the part's bodies) as name|V|n, V -1 where its parts overlap."""
    r = pg.kiln_burner_body(g)
    recs = []
    for b in r["bodies"]:
        nums = list(b["p"]) + [b["V"]] + list(b["box"]) + list(b["rgb"])
        recs.append("|".join([b["name"], b["group"], b["kind"]] + [_fixed(q) for q in nums]) + ";")
    chunks, cur = [], ""
    for rec in recs:
        if len(cur) + len(rec) > 900:
            chunks.append(cur)
            cur = ""
        cur += rec
    chunks.append(cur)
    if len(chunks) > KBB_CHUNKS:
        raise ValueError(f"kiln_burner_body: {len(chunks)} chunks, the macro joins {KBB_CHUNKS}")
    chunks += [""] * (KBB_CHUNKS - len(chunks))
    grp = "".join(f"{n}|{_fixed(q['V']) if q['V'] is not None else '-1'}|{q['n']};" for n, q in r["groups"].items())
    if len(grp) > 1000:
        raise ValueError("kiln_burner_body: the group list is too long for one VBA string")
    out = [der("N_BODIES", len(recs), "bodies before joining"), der("N_GROUPS", len(r["groups"]), "bodies in the part")]
    out += [Const(f"KBB_{i + 1}", c, "plant_geometry.kiln_burner_body() bodies", kind="String")
            for i, c in enumerate(chunks)]
    out.append(Const("KBB_GROUPS", grp, "the part's bodies: name|V (-1: parts overlap)|parts", kind="String"))
    return out


KBR_CHUNKS = 24


def kiln_burner_bas(g):
    """kiln_burner.bas: every body plant_geometry.kiln_burner() lays out as
    name|group|kind|params|V|box|r g b (KBR_1 .. KBR_24, as kiln_rotax_bas),
    and per channel (coal, axial, swirl) the joined body's volume, extent,
    outlet count and area, inlet area."""
    r = pg.kiln_burner(g)
    recs = []
    for b in r["bodies"]:
        nums = list(b["p"]) + [b["V"]] + list(b["box"]) + list(b["rgb"])
        recs.append("|".join([b["name"], b["group"], b["kind"]] + [_fixed(q) for q in nums]) + ";")
    chunks, cur = [], ""
    for rec in recs:
        if len(cur) + len(rec) > 900:
            chunks.append(cur)
            cur = ""
        cur += rec
    chunks.append(cur)
    if len(chunks) > KBR_CHUNKS:
        raise ValueError(f"kiln_burner: {len(chunks)} chunks, the macro joins {KBR_CHUNKS}")
    chunks += [""] * (KBR_CHUNKS - len(chunks))
    out = [der("N_BODIES", len(recs), "bodies before joining")]
    out += [Const(f"KBR_{i + 1}", c, "plant_geometry.kiln_burner() bodies", kind="String")
            for i, c in enumerate(chunks)]
    for grp in ("coal", "axial", "swirl"):
        q = r["groups"][grp]
        G = grp.upper()
        out += [der(f"{G}_V", q["V"], f"{grp} channel volume [m3]", digits=9),
                Const(f"{G}_N_OUT", q["n_out"], f"{grp} outlet faces in the tip plane [derived]", kind="Long"),
                der(f"{G}_A_OUT", q["a_out"], f"{grp} outlet area [m2]", digits=9),
                der(f"{G}_A_IN", q["a_in"], f"{grp} inlet area [m2]", digits=9)]
        out += [der(f"{G}_BOX_{i}", x, f"{grp} extent ({'x0 y0 z0 x1 y1 z1'.split()[i]}) [m]")
                for i, x in enumerate(q["box"])]
    return out


KFL_CHUNKS = 4


def kiln_flame_bas(g):
    """kiln_flame.bas: the flame zone's CFD volume (plant_geometry.kiln_flame()):
    its bodies as KFL_1.., its boundary faces as KFL_FACES
    (name|point|normal|area|rgb), the burner's placement (the channels
    copied in from kiln_burner.SLDPRT: rows R, tip T) and, to check it,
    where the coal pipe and the whole burner land in the kiln frame."""
    r = pg.kiln_flame(g)
    pl = pg.kiln_burner_placement(g)
    recs = []
    for b in r["bodies"]:
        nums = list(b["p"]) + [b["V"]] + list(b["box"]) + list(b["rgb"])
        recs.append("|".join([b["name"], b["group"], b["kind"]] + [_fixed(q) for q in nums]) + ";")
    chunks, cur = [], ""
    for rec in recs:
        if len(cur) + len(rec) > 900:
            chunks.append(cur)
            cur = ""
        cur += rec
    chunks.append(cur)
    if len(chunks) > KFL_CHUNKS:
        raise ValueError(f"kiln_flame: {len(chunks)} chunks, the macro joins {KFL_CHUNKS}")
    chunks += [""] * (KFL_CHUNKS - len(chunks))
    faces = "".join("|".join([n] + [_fixed(q) for q in list(pt) + list(nv) + [a] + list(rgb)]) + ";"
                    for n, pt, nv, a, rgb in r["faces"])
    if len(faces) > 1000:
        raise ValueError("kiln_flame: the face list is too long for one VBA string")

    def kbox(box):          # a box in the burner's frame -> its extent in the kiln frame
        pts = [pl["to_kiln"]((x, y, z)) for x in (box[0], box[3]) for y in (box[1], box[4]) for z in (box[2], box[5])]
        return [min(q[i] for q in pts) for i in range(3)] + [max(q[i] for q in pts) for i in range(3)]

    coal = kbox(pg.kiln_burner(g)["groups"]["coal"]["box"])
    whole = kbox(pg.kiln_burner_body(g)["box"])
    out = [der("N_BODIES", len(recs), "bodies before joining"), der("N_GROUPS", 1, "bodies in the part"),
           der("N_FACES", len(r["faces"]), "boundary faces")]
    out += [Const(f"KFL_{i + 1}", c, "plant_geometry.kiln_flame() bodies", kind="String") for i, c in enumerate(chunks)]
    out.append(Const("KFL_GROUPS", f"flame|-1|{len(recs)};", "the part's body: name|V (-1: parts overlap)|parts",
                     kind="String"))
    out.append(Const("KFL_FACES", faces, "boundaries: name|point|outward normal|area|rgb", kind="String"))
    for i in range(3):
        for k in range(3):
            out.append(der(f"KFL_R{i + 1}{k + 1}", pl["R"][i][k], f"the burner's {'xyz'[i]} axis, kiln {'xyz'[k]}"))
    for i in range(3):
        out.append(der(f"KFL_T{'XYZ'[i]}", pl["tip"][i], f"the burner's tip, kiln {'xyz'[i]}"))
    for i, nm in enumerate(("X0", "Y0", "Z0", "X1", "Y1", "Z1")):
        out.append(der(f"KFL_COAL_{nm}", coal[i], "the copied coal channel's extent, kiln frame"))
    for i, nm in enumerate(("X0", "Y0", "Z0", "X1", "Y1", "Z1")):
        out.append(der(f"KFL_BRN_{nm}", whole[i], "the placed whole burner's extent, kiln frame"))
    return out


def pid_bas(g):
    """The P&ID macro's records (geometry/pid/pid.yaml; tools/pid/)."""
    from tools.pid import encode, model

    return encode.consts(model.load(), g)


TARGETS = {
    "cooler.bas": cooler_bas,
    "kiln.bas": kiln_bas,
    "kiln_wall.bas": kiln_wall_bas,
    "kiln_rotax.bas": kiln_rotax_bas,
    "kiln_burner.bas": kiln_burner_bas,
    "kiln_burner_body.bas": kiln_burner_body_bas,
    "kiln_flame.bas": kiln_flame_bas,
    "kiln_inlet_chamber.bas": kiln_inlet_chamber_bas,
    "id_fan.bas": id_fan_bas,
    "cyclone.bas": cyclone_bas,
    "calciner.bas": calciner_bas,
    "plant_topology_2d.bas": drawing_bas,
    "drawings.bas": drawings_bas,
    "c1_twin.bas": c1_twin_bas,
    "pid.bas": pid_bas,
}


# ======================================================================
# Documents: one table each
# ======================================================================
DOCS_DIR = ROOT / "geometry"
MD_BEGIN = "<!-- BEGIN GENERATED (tools/gen_geometry.py)"
MD_END = "<!-- END GENERATED -->"
MD_HEADER = (
    MD_BEGIN + " -- elle düzenlenmez; kaynak geometry/plant_geometry.yaml -->\n"
)
SOURCE_TR = {
    "published": "yayınlanmış",
    "derived_from_reference": "FLS oranıyla türetilmiş",
    "literature": "literatür",
    "cfd_decision": "CFD kararı",
    "model": "modelleme",
    "schematic": "şematik",
}
UNITS = {"N/MW": "N/MW", "MJ/kg": "MJ/kg", "rpm": "dev/dk", "g/mol": "g/mol", "Pa": "Pa", "m": "m", "deg": "°", "%": "%", "m2": "m²", "-": "", "kg/s": "kg/s",
         "K": "K", "m/s": "m/s", "mol/mol": "mol/mol"}


def _num(x, digits):
    if isinstance(x, bool):
        return "var" if x else "yok"
    return f"{x:.{digits}f}"


def row_src(label, node, scale=1.0, unit=None, digits=None, note=""):
    """A table row from a source entry."""
    x = pg.v(node)
    if not isinstance(x, bool):
        x = scale * x
    u = UNITS.get(unit or node["unit"], unit or node["unit"])
    if digits is None:
        text = _num(x, 0) if isinstance(x, bool) else repr(float(x)).removesuffix(".0")
    else:
        text = _num(x, digits)
    tag = SOURCE_TR[node["source"]] + (f"; {note}" if note else "")
    return (label, f"{text} {u}".strip(), tag)


def row_der(label, x, unit, digits=3, note="türetilmiş"):
    return (label, f"{_num(x, digits)} {unit}".strip(), note)


def _cyclone_rows(g, name):
    node = g["cyclones"][name]
    base_name = node.get("same_as") or node.get("scaled_from") or name
    base = g["cyclones"][base_name]
    c = pg.cyclone(g, name)
    scaled = "scaled_from" in node
    labels = (
        ("D_barrel", "Efektif iç çap D"), ("H_barrel", "Silindirik gövde yüksekliği"),
        ("H_cone", "Koni yüksekliği"), ("L_vortex", "Vorteks bulucu daldırması S"),
        ("D_vortex", "Vorteks bulucu çapı D_x"), ("D_dust", "Toz çıkışı çapı"),
        ("W_inlet", "Giriş genişliği"), ("H_inlet", "Giriş yüksekliği"),
    )
    rows = [row_src("Hat başına adet", node["per_string"])]
    for key, label in labels:
        if scaled and key == "D_barrel":
            rows.append(row_src(label, node["D_barrel_published"]))
        elif key == "D_vortex":
            rows.append(row_src("D_x / D (= riser çapı / D)", base["D_vortex_over_D_barrel"],
                                note="" if base_name == name else f"{base_name} ile özdeş"))
            rows.append(row_der(label + " (= riser çapı)", c[key], "m", 4,
                                f"{c['D_vortex_over_D_barrel']:g} D"))
        elif scaled:
            rows.append(row_der(label, c[key], "m", 4, f"C4 × {c['scale']:.6f}"))
        else:
            note = "" if base_name == name else f"{base_name} ile özdeş"
            rows.append(row_src(label, base[key], note=note))
    note = "" if base_name == name else f"{base_name} ile özdeş"
    rows += [
        row_src("Giriş eğimi", base["inlet_slope"], note=note),
        row_src("Volüt", base["volute"], note=note),
        row_src("Çıkış dönüşü", base["outlet_turn"], note=note),
        row_der("Çıkış borusu yükselişi (çatının üstünde)", c["outlet_rise"], "m", 3,
                f"{c['outlet_rise_over_Dx']:g} D_x"),
    ]
    if c["outlet_turn"] != 0.0:
        rows += [
            row_der("Çıkış dirseği merkez yarıçapı", c["outlet_bend_R"], "m", 3,
                    f"{c['outlet_bend_R_over_Dx']:g} D_x"),
            row_der("Çıkış bacağı / inişi", c["outlet_run"], "m", 3,
                    f"{c['outlet_run_over_Dx']:g} D_x"),
        ]
    if c["inlet_riser"]:
        r = pg.cfd_riser_inlet(g, name)
        rows += [
            row_der("Yatay giriş kanalı (teğet düzleminden)", c["inlet_duct_length"], "m", 3),
            row_src("Riserdan kanala eğik kanalın eğimi", g["cyclone_domain"]["riser_duct_slope_deg"]),
            row_src("Eğik kanalın yan duvarlarının daralma açısı (en çok)", g["cyclone_domain"]["riser_taper_deg"]),
            row_der("Eğik kanalın daralan boyu (D → W)", r["taper_L"], "m", 3,
                    f"{r['taper_deg']:.1f}° yan duvar"),
            row_der("Riser ekseni, gövde ekseninden (kolon aralığı)", r["offset"], "m", 3),
            row_der("Riser ekseninden kanal ağzına yatay mesafe", r["run"], "m", 3),
            row_der("CFD domenindeki dik riser (dönüşün altında)", r["stub"], "m", 3),
        ]
    rows += [
        row_der("Toplam yükseklik (gövde + koni)", c["height"], "m", 3),
        row_der("**Ekipman hacmi (gövde + koni)**", c["volume"], "m³", 2),
        row_der("**Islak alan (gövde + çatı halkası + koni)**", c["wet_area"], "m²", 2),
    ]
    return rows


GEN = {2: "'nin", 3: "'ün", 4: "'ün", 5: "'in"}     # Turkish genitive after C2..C5


def _riser_rows(g, k):
    if k == 1:
        r = pg.r1_path(g)
        p = r["parts"]
        br = r["branch"]
        tw = pg.c1_twin(g)
        rows = [
            row_der("C2 çıkış borusu yükselişi (Ø{:.3f})".format(p[0]["D"]), p[0]["length"], "m"),
            row_der("R1 iç çapı (= C2 D_x, daraltıcı yok)", p[1]["D"], "m"),
            row_der("R1 dik boyu, C2 CFD çıkışından Y'ye", p[1]["length"], "m"),
            row_der("İkiz C1 kolu çapı (R1 alanının yarısı)", br["D"], "m"),
            row_der("Kol başına boy (dik + {:.0f}° dirsek + geçiş + kanal)".format(pg.c1_branch(g)["bend_deg"]), br["length"], "m"),
            row_der("Kol sayısı", r["branches"], "", 0),
            row_src("İkiz C1 kolları arası boşluk (cidardan cidara)", g["layout"]["c1_twin_gap"]),
            row_der("İkiz C1 eksenleri arası", tw["spacing"], "m"),
            row_der("İkiz C1 gövdeleri arası boşluk", tw["barrel_gap"], "m"),
            row_der("Y'den her kolun R1 eksenine uzaklığı", tw["branch_half"], "m"),
            row_der("Y'nin yüksekliği (R1 tepesinden kolların dik kısmına)", tw["y_rise"], "m"),
            row_der("R1 ve kollar, C1 eksenlerinin önünde", -tw["y_branch"], "m"),
        ]
    else:
        r = pg.stage_riser(g, k)
        p = r["parts"]
        rows = [
            row_der(f"Çap (C{k + 1}'in vorteks bulucusu D_x)", p[0]["D"], "m"),
            row_der(f"Dik riser, C{k + 1}'in çatısından dönüşe (ilk {pg.cyclone(g, f'C{k + 1}')['outlet_rise']:.3f} m CFD çıkış borusu)",
                    p[0]["length"], "m"),
            row_src("Riserdan kanala eğik kanalın eğimi", g["cyclone_domain"]["riser_duct_slope_deg"]),
            row_der(f"Riserın üst ucu + eğik kanal, merkez çizgisi boyu (→ C{k} girişi)", p[1]["length"], "m"),
            row_der(f"Yatay kanal, C{k}{GEN[k]} volütüne", p[2]["length"], "m"),
            row_der(f"Riser ekseni, C{k}{GEN[k]} ekseninden", r["riser"]["offset"], "m"),
            row_der("Toplam boy", sum(q["length"] for q in p), "m"),
        ]
    rows += [
        row_der("**Ekipman hacmi (hat başına)**", r["volume"], "m³", 2),
        row_der("**Duvar alanı (hat başına)**", r["wall_area"], "m²", 2),
    ]
    return rows


def _gooseneck_rows(g):
    gn, n, gp = pg.gooseneck(g), g["gooseneck"], pg.gooseneck_plant(g)
    return [
        row_src("Kol iç çapı", n["D_leg"]),
        row_der("Ortak boyun çapı (kol × √2)", gn["D_neck"], "m"),
        row_der("Boyunun eğik parçaları (2 adet): boy", gn["piece"], "m", 3, f"{pg.v(n['neck_piece_over_D_neck']):g} × boyun çapı; modelleme"),
        row_der("Boyunun eğimi (yataya)", gn["slope"], "°", 1, "modelleme (kullanıcı kararı)"),
        row_der("Boyunun yatay parçası: boy", gn["level"], "m", 3, f"{pg.v(n['neck_level_over_D_neck']):g} × boyun çapı; modelleme"),
        row_der("Düşey kanal: boy", gn["channel"], "m", 3, f"{pg.v(n['channel_over_D_neck']):g} × boyun çapı; modelleme (kullanıcı kararı)"),
        row_der("Kanalın ekseni, gövde ekseninin önünde (−y)", gn["y_off"], "m"),
        row_der("Kemerin tepesi (boru dış kenarı)", gn["crown"], "m"),
        row_der("Kanalın başladığı kot (üçüncü parçanın alt ucu)", gn["z_n3"], "m"),
        row_der("Kolların ayrıldığı kot (kanalın alt ucu)", gn["z_split"], "m"),
        row_der("Kolun boyuna açısı (düşeyden)", gn["arm_angle"], "°", 1, "modelleme (kullanıcı kararı)"),
        row_der("Kolun eğik parçası: boy (yatay kolun eksenine kadar)", gn["arm_piece"], "m", 3, "C5 giriş ekseninden türetilir"),
        row_der("Kolun yataya döndüğü nokta, x", gn["x_bend"], "m"),
        row_der("Kolun yatay kısmı: boy", gn["arm_run"], "m", 3, f"{pg.v(n['arm_run_over_D_leg']):g} × kol çapı; modelleme (kullanıcı çizimi)"),
        row_der("Kol çıkış yüzü (dikey düzlem), x", gn["x_leg"], "m"),
        row_der("Boru kökünün (çatıyı deldiği nokta) gövde ekseninin önüne kayması", gn["root_forward"], "m", 3, "kapak gövdenin içinde kalsın diye türetilir (5 cm pay)"),
        row_der("Birinci parçanın gövde içindeki hacmi", gn["inside_vessel"], "m³"),
        row_der("Kanal ile bir kolun ortak hacmi", gn["overlap_neck_arm"], "m³"),
        row_der("İki kolun ortak hacmi", gn["overlap_arms"], "m³"),
        row_der("CFD: kolların yatay kısmının ekseni (C5 giriş ekseni), z", gn["z_end"], "m"),
        row_der("CFD: hacim", gn["volume"], "m³", 2),
        row_der("CFD: duvar alanı", gn["wall_area"], "m²", 2),
        row_der("Tesis: yatay kolun CFD çıkışından C5 namlusuna uzantısı", gp["leg_length"], "m"),
        row_der("**Tesis: hacim (iki kol)**", gp["volume"], "m³", 2),
        row_der("**Tesis: duvar alanı (iki kol)**", gp["wall_area"], "m²", 2),
    ]


def _calciner_rows(g):
    c, cal = g["calciner"], pg.calciner(g)
    dp = pg.calciner_dispersion_plate(g)
    return [
        row_src("Gövde (shell) çapı", c["D_shell"]),
        row_src("Efektif iç çap", c["D"], note="7.20 × 3.08 / 3.29"),
        row_src("Gövde boyu (koni + silindir)", c["H"]),
        row_src("Alt koni duvar açısı (yatayla)", c["cone_angle"]),
        row_der("Boğaz çapı", cal["D_throat"], "m", 3, "literatür akışı / literatür hızı"),
        row_der("Alt koni yüksekliği", cal["h_cone"], "m"),
        row_der("Silindir boyu", cal["h_cylinder"], "m"),
        row_src("Tersiyer hava kanalı çapı", c["D_tertiary_air"]),
        row_src("Farin besleme borusu çapı", c["D_feed"], note="Fidaros 2007 × √2"),
        row_src("Yakıt borusu çapı", c["D_fuel"], note="Fidaros 2007 × √2"),
        row_src("Dağıtma plakası çıkış açısı (yatayın üstü)", c["dispersion_plate_exit_angle"],
                note="tip: KHD US 6,875,267 + üretici görseli; açı görselden"),
        row_der("Dağıtma plakası yay yarıçapı", dp["R_arc"], "m", 3, "çıkıntıdan ve açılardan"),
        row_der("Dağıtma plakası duvardan çıkıntısı", dp["protrusion"], "m", 3, "0.5 × farin borusu çapı (model)"),
        row_der("Dağıtma plakası genişliği", dp["width"], "m", 4, "1.0 × farin borusu çapı (model)"),
        row_src("Dağıtma plakası kalınlığı", c["dispersion_plate_thickness"]),
        row_der("**Ekipman hacmi (koni + silindir)**", cal["vessel_volume"], "m³", 2),
        row_der("**Duvar alanı (silindir + koni + tavan halkası)**", cal["vessel_wall_area"], "m²", 2),
    ]


def _kiln_rows(g):
    k, kk = g["kiln"], pg.kiln(g)
    rx = pg.kiln_rotax(g)
    return [
        row_src("Efektif iç çap", k["D"]),
        row_src("Boy", k["L"]),
        row_src("Eğim", k["slope"]),
        row_src("Geçiş bölgesi (arka uç)", k["transition_L"]),
        row_der("Yanma bölgesi", kk["burning_L"], "m", 2),
        row_src("Sac kabuk kalınlığı", k["shell_t"], digits=3),
        row_src("Tuğla (astar) kalınlığı", k["lining_t"], digits=3),
        row_src("Tuğla soğuk yüzü A (ISO 5417)", k["brick_cold_face"], digits=3),
        row_src("Tuğla boyu L, bir halka (ISO 5417)", k["brick_length"], digits=3),
        # ROTAX-2 mechanical parts (kiln_rotax.bas)
        row_src("Giriş tayrı, L'nin oranı (ROTAX-2)", g["kiln_rotax"]["tyre_inlet_at"], digits=2),
        row_src("Çıkış tayrı, L'nin oranı (ROTAX-2)", g["kiln_rotax"]["tyre_outlet_at"], digits=2),
        row_der("Tayr açıklığı", rx["tyre_span"], "m", 2),
        row_src("Tayr genişliği", g["kiln_rotax"]["tyre_width"], digits=2),
        row_src("Tayr kalınlığı (radyal)", g["kiln_rotax"]["tyre_thickness"], digits=2),
        row_src("Tayr ile sac arası (teğet askı)", g["kiln_rotax"]["tyre_gap"], digits=2),
        row_der("Tayr dış çapı", rx["D_tyre"], "m", 2),
        row_src("Tayr altı sac kalınlığı", g["kiln_rotax"]["tyre_section_t"], digits=3),
        row_src("Makara çapı / tayr çapı", g["kiln_rotax"]["roller_over_tyre"], digits=3),
        row_src("Makara açısı (düşeyden)", g["kiln_rotax"]["roller_angle"], digits=1),
        row_der("Makara çapı", rx["D_roller"], "m", 2),
        row_der("**Ekipman hacmi**", kk["volume"], "m³", 2),
        row_der("**Duvar alanı**", kk["wall_area"], "m²", 2),
    ]


def _cooler_rows(g):
    c, cc = g["cooler"], pg.cooler(g)
    return [
        row_src("Izgara alanı", c["grate_area"]),
        row_src("Izgara genişliği w", c["width"]),
        row_der("Izgara boyu L", cc["length"], "m", 2, "alan / genişlik"),
        row_src("Gövde yüksekliği H", c["casing_height"]),
        row_src("Taban segmenti sayısı", c["segments"]),
        row_src("Hood açıklığı (sıcak uçtan, segment)", c["hood_segments"]),
        row_der("Segment boyu L/n", cc["segment_L"], "m", 2, "boy / segment sayısı"),
        row_der("Hood açıklığı boyu", cc["hood_L"], "m", 2, "hood segmentleri × segment boyu"),
        row_der("**Gövde hacmi**", cc["box_volume"], "m³", 2),
        row_der("Duvar alanı (yanlar, uçlar, hood dışı tavan)", cc["wall_area"], "m²", 2),
    ]


def _id_fan_rows(g):
    f, fan = g["id_fan"], pg.id_fan(g)
    return [
        row_src("Fan sayısı (hat başına)", f["per_string"]),
        row_src("Egzoz debisi (hat başına)", f["exhaust_flow_per_string"]),
        row_src("Egzoz sıcaklığı", f["exhaust_T"]),
        row_src("Gaz mol kütlesi", f["exhaust_molar_mass"]),
        row_src("Fan girişi, atmosferin altında", f["inlet_underpressure"]),
        row_src("Toplam basınç artışı", f["total_pressure"]),
        row_src("Verim", f["efficiency"]),
        row_src("Dönme hızı", f["speed"]),
        row_der("Giriş gaz yoğunluğu", fan["rho"], "kg/m³", 3),
        row_der("Hacimsel debi (hat başına)", fan["q"], "m³/s", 2),
        row_der("Hacimsel debi (hat başına)", fan["q_h"], "m³/h", 0),
        row_der("Hacimsel debi (iki hat)", fan["q_total_h"], "m³/h", 0),
        row_der("Mil gücü", fan["p_shaft"] / 1e3, "kW", 0),
        row_der("Motor gücü (×1.10)", fan["p_motor"] / 1e3, "kW", 0),
        row_der("Uç hızı", fan["u_tip"], "m/s", 1),
        row_der("Çark çapı D2", fan["D_impeller"], "m", 3),
        row_src("Göz oranı D1/D2", f["eye_ratio"]),
        row_der("Göz çapı D1", fan["D_inlet"], "m", 3),
        row_der("Göz hızı c0", fan["c0"], "m/s", 1),
        row_der("Debi katsayısı φ", fan["phi"], "-", 4),
        row_src("Kanat çıkış açısı β2 (teğetten)", f["blade_outlet_angle"]),
        row_src("Kanat sayısı katsayısı k", f["blade_number_coeff"]),
        row_der("Kanat sayısı z = k sinβ2 / (1 − D1/D2)", fan["z"], "-", 0),
        row_src("Kanat kalınlığı", f["blade_thickness"]),
        row_src("Kanat uçlarının göz/uç dairesine boşluğu", f["blade_edge_clearance"]),
        row_src("Hücum açısı", f["incidence"]),
        row_der("Kanat giriş açısı β1", fan["beta1"], "°", 1),
        row_der("Çark giriş genişliği b1", fan["b1"], "m", 3),
        row_src("Hidrolik verim η_h", f["hydraulic_efficiency"]),
        row_der("Wiesner kayma katsayısı", fan["slip"], "-", 3),
        row_der("Wiesner D1/D2 sınırı", fan["slip_limit"], "-", 3),
        row_der("Çıkış teğetsel hızı cu2", fan["cu2"], "m/s", 1),
        row_der("Çıkış meridyen hızı cm2", fan["cm2"], "m/s", 1),
        row_der("Çark çıkış genişliği b2", fan["b2"], "m", 3),
        row_der("Kanat yayı yarıçapı", fan["blade_arc_R"], "m", 2),
        row_src("Salyangoz genişlik oranı B/b2", f["volute_width_ratio"]),
        row_der("Salyangoz genişliği B", fan["B"], "m", 3),
        row_src("Dil boşluğu / D2", f["tongue_gap_ratio"]),
        row_der("Dil dairesi r3", fan["r3"], "m", 3),
        row_src("Dil burun yarıçapı / D2", f["tongue_radius_ratio"]),
        row_src("Salyangoz çıkış hızı", f["volute_outlet_velocity"]),
        row_der("Spiral açısı (çıkış hızından)", fan["spiral_angle"], "°", 2),
        row_der("Spiral sonu r_end", fan["r_end"], "m", 3),
        row_der("Spiral sonu kesiti (yükseklik)", fan["h_out"], "m", 3),
        row_der("Spiral sonu kesitinde hız", fan["u_section"], "m/s", 1),
        row_der("Çıkış ağzı yüksekliği (h cosα − 2 burun)", fan["h_stub"], "m", 3, f"türetilmiş; alan {fan['a_out']:.3f} m²"),
        row_der("Çıkış hızı (ağız)", fan["u_out"], "m/s", 1),
        row_src("Çıkış düz parçası / yükseklik", f["outlet_stub_ratio"]),
        row_src("Çıkış yönü (yataydan yukarı)", f["discharge_angle"]),
        row_src("MRF kenarı (dil boşluğunun payı)", f["mrf_gap_fraction"]),
        row_der("MRF bölgesi yarıçapı", fan["r_mrf"], "m", 3),
        row_src("Giriş konisi ağzı / D1", f["cone_inlet_ratio"]),
        row_src("Ön yan sac (salyangoz ile kutu arası)", f["side_plate_gap"]),
        row_der("Giriş konisi boyu (gözden kutu tabanına)", fan["L_cone"], "m", 3),
        row_der("Giriş konisi ağız çapı", fan["D_cone"], "m", 3),
        row_src("Giriş kutusu alan oranı", f["inlet_box_area_ratio"]),
        row_src("Giriş kutusu yükseklik oranı", f["inlet_box_height_ratio"]),
        row_src("Giriş kutusu uzanım oranı", f["inlet_box_reach_ratio"]),
        row_der("Giriş kutusu yüzü (yükseklik × derinlik)", fan["H_box"], "m", 3, f"türetilmiş; yükseklik, derinlik {fan['depth_box']:.3f} m"),
        row_der("Giriş kutusu hızı", fan["u_box"], "m/s", 1),
        row_der("Hacim: dönen bölge (kanatsız)", fan["V_rotor"], "m³", 3),
        row_der("Hacim: kanatlar", fan["V_blades"], "m³", 4),
        row_der("Hacim: dönen bölge (kanatlı)", fan["V_rotor_bladed"], "m³", 3),
        row_der("Hacim: salyangoz + çıkış", fan["V_volute"], "m³", 3),
        row_der("Hacim: giriş konisi", fan["V_cone"], "m³", 3),
        row_der("Hacim: giriş kutusu", fan["V_box"], "m³", 3),
    ]


def _kiln_burner_rows(g):
    b, bu = g["kiln_burner"], pg.kiln_burner(g)
    bd = pg.kiln_burner_body(g)
    gr = bu["groups"]
    return [
        row_src("Kiln yakıtı", b["fuel_flow"]),
        row_src("Yakıt alt ısıl değeri", b["fuel_LHV"]),
        row_src("Fırın yanma havası", b["kiln_air_flow"]),
        row_src("Birincil hava payı (eksenel + girdap)", b["primary_air_fraction"]),
        row_src("Birincil hava sıcaklığı", b["primary_air_T"]),
        row_src("Eksenel hava basıncı", b["axial_pressure"]),
        row_src("Girdap hava basıncı", b["swirl_pressure"]),
        row_src("Kömür / taşıma havası yüklemesi", b["transport_loading"]),
        row_src("Alev momentumu, alt sınır", b["momentum_min_per_MW"]),
        row_src("Alev momentumu, üst sınır", b["momentum_max_per_MW"]),
        row_src("Kömür hızı, karşılaştırma", b["coal_velocity_ref"]),
        row_src("Eksenel yarık sayısı", b["n_axial"]),
        row_src("Yarık alanı / D_uç²", b["axial_slot_area_over_D2"]),
        row_src("Yarık boy / en", b["axial_slot_aspect"]),
        row_src("Yarığın teğetten açısı", b["axial_slot_tilt"]),
        row_src("Yarık halkası r / D_uç", b["axial_ring_r_over_D"]),
        row_src("Girdap deliği sayısı", b["n_swirl"]),
        row_src("Delik ağzı alanı / D_uç²", b["swirl_hole_area_over_D2"]),
        row_src("Delik halkası r / D_uç", b["swirl_ring_r_over_D"]),
        row_src("Katı yakıt borusu D / D_uç", b["coal_pipe_D_over_D"]),
        row_src("Katı yakıt borusu kaçıklığı (yukarı) / D_uç", b["coal_pipe_offset_over_D"]),
        row_src("Girdap deliği eksen açısı", b["swirl_angle"]),
        row_src("Ön plaka kalınlığı", b["plate_t"]),
        row_src("Plenum boyu", b["plenum_L"]),
        row_src("Kömür borusu boyu / D", b["coal_pipe_L_over_D"]),
        row_src("Plenum açıklığı", b["plenum_clearance"]),
        row_src("Kanallar arası en ince duvar", b["wall_min"]),
        row_der("Isıl güç", bu["thermal_MW"], "MW", 2),
        row_der("Birincil hava (eksenel + girdap)", bu["m_pa"], "kg/s", 3),
        row_der("Eksenel hava", bu["m_axial"], "kg/s", 3),
        row_der("Girdap hava", bu["m_swirl"], "kg/s", 3),
        row_der("Girdap payı", bu["swirl_share"], "", 3),
        row_der("Taşıma havası", bu["m_transport"], "kg/s", 3),
        row_der("Fırına giren soğuk hava payı (birincil + taşıma)", bu["primary_total_share"], "", 3),
        row_der("Eksenel jet hızı", bu["u_axial"], "m/s", 1),
        row_der("Girdap jet hızı", bu["u_swirl"], "m/s", 1),
        row_der("Momentum (Σ ṁu)", bu["momentum_N"], "N", 0),
        row_der("Momentum / ısıl güç", bu["momentum_per_MW"], "N/MW", 2),
        row_der("Eksenel momentum bileşeni", bu["momentum_axial_N"], "N", 0),
        row_der("Uç dış çapı D_uç", bu["D_tip"] * 1e3, "mm", 0),
        row_der("Eksenel açıklık alanı", bu["A_axial"], "m²", 5),
        ("Yarık boy × en", f"{bu['slot_l'] * 1e3:.1f} × {bu['slot_w'] * 1e3:.1f} mm", "türetilmiş"),
        row_der("Yarık halkası yarıçapı", bu["r_slots"] * 1e3, "mm", 1),
        row_der("Girdap akış alanı (deliğe dik)", bu["A_swirl"], "m²", 5),
        row_der("Girdap deliği kenarı (deliğe dik)", bu["hole_a"] * 1e3, "mm", 1),
        row_der("Delik halkası yarıçapı", bu["r_holes"] * 1e3, "mm", 1),
        row_der("Kömür borusu iç çapı", bu["D_coal"] * 1e3, "mm", 1),
        row_der("Kömür borusu kaçıklığı (yukarı)", bu["y_coal"] * 1e3, "mm", 1),
        row_der("Kömür borusu hızı", bu["u_coal"], "m/s", 1),
        ("Eksenel plenum r", f"{bu['axial_plenum'][0] * 1e3:.1f} … {bu['axial_plenum'][1] * 1e3:.1f} mm", "türetilmiş"),
        ("Girdap plenumu r", f"{bu['swirl_plenum'][0] * 1e3:.1f} … {bu['swirl_plenum'][1] * 1e3:.1f} mm", "türetilmiş"),
        ("Hacim: kömür / eksenel / girdap", f"{gr['coal']['V']:.4f} / {gr['axial']['V']:.4f} / {gr['swirl']['V']:.4f} m³", "türetilmiş"),
        row_src("Gövde: uç halkası boyu / D_uç", b["body_tip_ring_L"]),
        row_src("Gövde: refrakter boyu / D_uç", b["body_castable_L"]),
        row_src("Gövde: refrakter çapı / D_uç", b["body_castable_D"]),
        row_src("Gövde: arka kafa boyu / D_uç", b["body_head_L"]),
        row_src("Gövde: arka kafa çapı / D_uç", b["body_head_D"]),
        row_src("Gövde: kömür girişi boyu / D_uç", b["body_coal_L"]),
        row_src("Gövde: kiriş boyu / D_uç", b["body_beam_L"]),
        row_src("Gövde: çelik brülör borusu et kalınlığı", b["body_pipe_t"]),
        row_der("Brülör toplam boyu", bd["L_total"], "m", 2),
        row_der("Refrakter dış çapı (uç halkasının arkası)", 2e3 * bd["R_castable"], "mm", 0),
        row_der("Çelik brülör borusu dış çapı", 2e3 * bd["r_pipe"], "mm", 0),
        row_der("Refrakter boru boyu", -bd["z_castable"], "m", 2),
    ]


def _kiln_hood_rows(g):
    h, hd = g["kiln_hood"], pg.kiln_hood(g)
    return [
        row_src("İkincil hava debisi", h["secondary_air_flow"]),
        row_src("Hız ölçütü, alt", h["air_velocity_min"]),
        row_src("Hız ölçütü, üst", h["air_velocity_max"]),
        row_der("Başlıktan geçen hava (ikincil + tersiyer)", hd["m"], "kg/s", 2),
        row_der("Hacimsel debi (1073 K)", hd["q"], "m³/s", 1),
        row_der("Çıkış contasının dış yarıçapı (ROTAX)", hd["R_seal"], "m", 2),
        row_src("Conta çevresindeki pay", h["seal_clearance"]),
        row_der("Başlık genişliği (2 × (conta + pay))", hd["W"], "m", 2),
        row_der("Başlık yüksekliği (soğutucu tavanından contanın üstüne)", hd["H"], "m", 2),
        row_der("Başlık derinliği (soğutucunun başlık açıklığı)", hd["depth"], "m", 2),
        row_der("Kesit alanı (genişlik × yükseklik)", hd["area"], "m²", 2),
        row_der("Hız (1073 K)", hd["u"], "m/s", 2),
        row_der("Hız (1250 K)", hd["u_hot"], "m/s", 2),
        row_der("Ölçütün izin verdiği en küçük kesit", hd["area_min"], "m²", 2),
    ]


def _kiln_chamber_rows(g):
    c, ch = g["kiln_inlet_chamber"], pg.kiln_inlet_chamber(g)
    return [
        row_src("Fırın girişi gaz hızı üst sınırı", c["gas_velocity_max"]),
        row_der("Fırın gazı hacimsel debisi (1323 K)", ch["q"], "m³/s", 1),
        row_der("Oda planı (boğazın sol duvarından ağza × 2a)", ch["plan_area"], "m²", 2),
        row_der("Hız, oda planında", ch["u_chamber"], "m/s", 2),
        row_der("Hız, fırın tüpünün girişinde (CFD debisi)", ch["u_kiln"], "m/s", 2),
        row_der("Ölçütün izin verdiği en küçük kenar", ch["side_min"], "m", 2),
        row_src("Başvuru sınırı (Holcim StDC 2022; tek şirketin standardı)", c["gas_velocity_ref_holcim"]),
        row_der("Oda yüksekliği (boğazın üstü, zeminden)", ch["height"], "m", 3),
        row_der("Boğaz çapı (kalsinatörün; duvarları x = ±r aşağı iner)", ch["D_throat"], "m", 3),
        row_src("Rampa eğimi (yataya)", c["ramp_deg"]),
        row_src("Rampa ayağı (yatay; fırının alt çizgisi, kiln.slope ile düşer)", c["ramp_foot"]),
        row_der("Rampanın üstü, sol boğaz duvarında (zeminden)", ch["ramp_top"][1], "m", 3),
        row_der("Tavan, sağ boğaz duvarında (fırının üst çizgisi; zeminden)", ch["roof_at_throat"], "m", 3),
        row_src("Fırın borusu ucu (CFD katısı; D'ye oran)", c["mouth_stub_over_D"]),
        row_der("CFD hacmi (kesit prizması + boğaz + fırın ucu)", ch["volume"], "m³", 2),
    ]


def _meal_pipe_rows(g, stage):
    mp = pg.meal_pipes(g)[stage]
    m = g["meal_pipe"]
    flow_node = m["c5_meal_per_string"] if stage == 5 else m["feed_per_string"]
    share = " (hat başına borunun yarısı)" if stage == 1 else ""
    return [
        row_der("Boru sayısı (hat başına)", float(mp["count_per_string"]), "", 0, "yerleşim kararı"),
        row_src("Hat başına farin debisi", flow_node),
        row_der("Bir borunun debisi" + share, mp["m"], "kg/s", 2),
        row_der("Kütle akışı (kalsinatör borusunun)", mp["flux"], "kg/(m² s)", 1),
        row_der("İç çap", mp["D"], "m", 3, "kütle akışı ölçeği"),
        row_der("Kesit alanı", mp["area"], "m²", 3),
        row_der("Yatayla eğim", mp["slope"], "°", 0, "literatür (kalsinatör borusu)"),
        row_der("Siklonun toz çıkışı çapı (arayüz, boru çapı değil)", mp["D_dust"], "m", 3),
        row_der("Toz çıkışındaki kütle akışı (aynı debi)", mp["flux_dust"], "kg/(m² s)", 1),
        row_der("Toz çıkışı akışı / boru akışı", mp["dust_over_pipe"], "", 2),
    ]


def _fluid_volume_rows(g):
    t = pg.twin_sections(g)
    n = t["preheater"]["strings"]
    rows = []
    for i, st in enumerate(t["preheater"]["stages"], start=1):
        cyc = n * st["cyclones_per_string"] * st["cyclone_volume"]
        ris = n * st["riser_volume"]
        k = int(st["cyclone"][1:])
        riser = "R1" if k == 1 else f"R{k}"
        rows.append((f"Ön ısıtıcı, kademe {i}",
                     f"{riser} + {st['cyclones_per_string']} {st['cyclone']} (×{n})",
                     f"{ris:.2f} + {cyc:.2f} = **{cyc + ris:.2f}**"))
    for seg in t["calciner"]["zone_segments"]:
        label = {"vessel": "kalsinatör gövdesi, farin girişinden tavana (yakıt burada)",
                 "gooseneck": "kaz boynu, C5 girişlerine kadar",
                 "C5": f"C5 (×{n})"}[seg["name"]]
        rows.append(("Kalsinatör bölgesi", label, f"**{seg['volume']:.2f}**"))
    kk, cc = pg.kiln(g), pg.cooler(g)
    a = 0.25 * math.pi * kk["D"] ** 2
    rows.append(("Geçiş", f"fırının arka {kk['transition_L']:g} m'si", f"**{a * kk['transition_L']:.2f}**"))
    rows.append(("Yanma", f"fırının ön {kk['burning_L']:.2f} m'si", f"**{a * kk['burning_L']:.2f}**"))
    rows.append(("Soğutucu", "ızgara kutusu", f"**{cc['box_volume']:.2f}**"))
    return rows


def _topology_equipment(g):
    c1, c4, c5 = (pg.cyclone(g, n) for n in ("C1", "C4", "C5"))
    cal, gn, k, co = pg.calciner(g), pg.gooseneck(g), pg.kiln(g), pg.cooler(g)
    return [
        ("C1 (hat başına ikiz)", f"D {c1['D_barrel']:.2f}, gövde {c1['H_barrel']:.2f}", "cyclone_C1.md (CFD)"),
        ("C2 = C3 = C4", f"D {c4['D_barrel']:.2f}, gövde {c4['H_barrel']:.2f} (h = D)", "cyclone_C4.md (CFD)"),
        ("C5", f"D {c5['D_barrel']:.2f}, gövde {c5['H_barrel']:.2f} (CFD C4 × {c5['scale']:.4f})", "cyclone_C5.md"),
        ("R1 (hat başına)", f"Ø{pg.r1_D(g):.3f}", "C2'nin dik çıkış borusu, D_x = D/2 (riser_R1.md)"),
        ("R2 / R3 / R4 (hat başına)", " / ".join(f"Ø{pg.stage_riser(g, kk)['parts'][0]['D']:.3f}" for kk in (2, 3, 4)),
         "C3 / C4 / C5'in dik çıkış borusu, 45° ile üst siklona (riser_R2–R4.md)"),
        ("Kalsinatör", f"Ø{cal['D']:.4f}, {cal['H']:.1f} m (koni dahil), boğaz Ø{cal['D_throat']:.3f}, koni {pg.v(g['calciner']['cone_angle']):g}°",
         "calciner.md (PF5000)"),
        ("Kaz boynu", f"üç düz parçalı boyun (45°/0°/45°), Ø{gn['D_neck']:.3f}, aşağıda 2 kol × Ø{gn['D_leg']:.2f}, her kol C5 girişine iner", "gooseneck.md"),
        ("Tersiyer hava kanalı", f"Ø{cal['D_tertiary_air']:.4f}", "calciner.md"),
        ("Fırın", f"Ø{k['D']:g} × {k['L']:g} m, %{k['slope']:g} eğim", "kiln.md (PF5000)"),
        ("Soğutucu", f"ızgara {co['grate_area']:g} m² = {co['width']:g} × {co['length']:.2f} m, gövde {co['casing_height']:g} m", "cooler.md (PF5000, FLS)"),
    ]


def _topology_cfd(g):
    c1, c4, c5 = (pg.cyclone(g, n) for n in ("C1", "C4", "C5"))
    d, br = g["cyclone_domain"], pg.c1_branch(g)
    L_in = c4["inlet_duct_length"]
    r4 = pg.cfd_riser_inlet(g, "C4")

    def mid(c, k=1.0):
        return (f"Ø{r4['D']:.2f} dik riser {r4['stub']:.2f} m, {pg.v(d['riser_duct_slope_deg']):g}° eğik kanal, "
                f"{L_in:.2f} m yatay kanal, volüt, gövde, VF {c['L_vortex']:.3f}, "
                f"{c['outlet_rise']:.3f} m ({c['outlet_rise_over_Dx']:g}·VD) dik çıkış borusu")

    def out(c):
        return f"çıkış borusunun ucu, eksende, çatının {c['outlet_rise']:.3f} m üstünde"
    return [
        ("C1 (×4)",
         f"gövde, VF {c1['L_vortex']:.2f}, Ø{br['D']:.3f} kol, {br['bend_deg']:g}° R {br['bend_R']:.3f} dirsek, "
         f"{br['transition']:g} m geçiş, {c1['inlet_slope']:g}° kanal, {pg.v(d['c1_feed_width']):g} m oluk; "
         f"{c1['outlet_rise']:.2f} m çıkış borusu, R {c1['outlet_bend_R']:.2f} 180° dirsek, {c1['outlet_run']:.2f} m iniş",
         f"kolun tabanı, toz çıkışının {br['z_floor']:.3f} m üstü",
         f"inişin ucu, çatı kotunda, eksenden {2 * c1['outlet_bend_R']:.2f} m"),
        ("C2–C4 (×6)", mid(c4), f"riser parçasının tabanı, gövde ekseninden {r4['offset']:.3f} m, "
         f"dönüşün {r4['stub']:.2f} m altı", out(c4)),
        ("C5 (×2)", f"C2–C4'ün {c5['scale']:.4f} katı (CFD'si ayrıca çözülmez)",
         f"riser parçasının tabanı, eksenden {c5['scale'] * r4['offset']:.3f} m", out(c5)),
    ]


def _topology_layout(g):
    L = pg.layout(g)
    f = lambda x: f"{x:.3f}"
    xs = lambda a, b: f"{a:.3f} .. {b:.3f}"
    rows = [
        ("Fırın giriş odası", f"x = −{f(L['a_chamber'])} .. {f(L['a_chamber'])}, z {xs(L['z_chamber_floor'], L['z_calciner_throat'])}; taban rampası {L['chamber_ramp_deg']:.1f}°"),
        ("Kalsinatör", f"z {xs(L['z_calciner_throat'], L['z_calciner_roof'])}; kaz boynu tepesi z {f(L['z_gooseneck_top'])}, kol inişi x = ±{f(L['x_gooseneck_leg'])}, C5 giriş kotu z {f(L['z_c5_inlet'])}"),
        ("Tersiyer hava kanalı", f"eksen z {f(L['z_tertiary_air'])}"),
        ("İç kolon (C5, C3)", f"x = ±{f(L['x_inner'])}"),
        ("Dış kolon (C4, C2)", f"x = ±{f(L['x_outer'])}"),
        ("R1", f"x = ±{f(L['x_r1'])}"),
        ("İkiz C1", "x = ±" + " ve ±".join(f(x) for x in L["x_c1"])),
    ]
    rows += [(f"C{s} toz çıkışı / çıkış borusu tepesi", f"z {f(L['z_dust'][s])} / {f(L['z_top'][s])}") for s in (5, 4, 3, 2, 1)]
    rows += [
        ("Kule tepesi (C1 çıkış dirseklerinin tepesi)", f"z {f(L['z_tower'])}"),
        ("Fırın", f"({f(L['a_chamber'])}, {f(pg.v(g['layout']['kiln_axis_z']))}) → ({f(L['kiln_end'][0])}, {f(L['kiln_end'][1])})"),
        ("Soğutucu", f"x {xs(*L['cooler_x'])}, z {xs(*L['cooler_z'])}"),
        ("Fırın başlığı", f"x {xs(*L['hood_x'])}, z {xs(*L['hood_z'])}"),
    ]
    return rows


def _calciner_cfd(g):
    """calciner.bas's domain: where each piece is (z from the throat's
    foot) and the closed-form volume after each build step."""
    cal, gn = pg.calciner(g), pg.gooseneck(g)
    R, r, rl = cal["R"], cal["r_throat"], 0.5 * gn["D_leg"]
    v_cyl = math.pi * R * R * cal["h_cylinder"]
    v_cone = cal["vessel_volume"] - v_cyl
    r_n = 0.5 * gn["D_neck"]
    a_n = math.pi * r_n * r_n
    L1, L2, st = gn["piece"], gn["level"], gn["setback"]
    v_p1 = a_n * (st + L1) - gn["inside_vessel"]       # the first piece, less the part inside the vessel
    v_p2 = a_n * L2
    v_p3 = a_n * L1
    v_p4 = a_n * gn["channel"]
    v_arm = math.pi * rl * rl * gn["arm_length"]
    f = lambda x: f"{x:.3f}"
    steps = [cal["v_throat"] + cal["vessel_volume"]]
    ins = pg.calciner_inlets(g)
    ta, meal, fuel = ins["tertiary_air"], ins["meal"], ins["fuel"]
    dp = pg.calciner_dispersion_plate(g)
    for dv in (v_p1 + v_p2 + v_p3 + v_p4, v_arm - gn["overlap_neck_arm"],
               v_arm - gn["overlap_neck_arm"] - gn["overlap_arms"] + gn["overlap_all"],
               meal["volume"], meal["volume"], ta["volume"], fuel["volume"], fuel["volume"],
               -dp["inside_vessel"], -dp["inside_vessel"]):
        steps.append(steps[-1] + dv)
    return [
        ("Boğaz", f"Ø{f(cal['D_throat'])}, z 0 .. {f(cal['z_throat_top'])}", f"{cal['v_throat']:.3f}"),
        ("Koni", f"{pg.v(g['calciner']['cone_angle']):g}°, z {f(cal['z_throat_top'])} .. {f(cal['z_cone_top'])}", f"{v_cone:.3f}"),
        ("Silindir (düz tavan)", f"Ø{cal['D']:.4f}, z {f(cal['z_cone_top'])} .. {f(cal['z_roof'])}", f"{v_cyl:.3f}"),
        ("Gövde (koni + silindir)", "", f"**{cal['vessel_volume']:.3f}**"),
        ("1 domen (boğaz + gövde)", "", f"{steps[0]:.3f}"),
        ("2 + boyun (üç düz parça) ve düşey kanal", f"Ø{f(gn['D_neck'])}; 1) tavan ortasından {gn['slope']:g}° yukarı-öne, boy {f(gn['piece'])} (kapağı {f(gn['setback'])} geride, gövdenin içinde; içeride kalan {gn['inside_vessel']:.3f}), "
         f"2) yatay {f(gn['level'])}, z {f(gn['nodes'][1][1])}, 3) {gn['slope']:g}° aşağı-öne {f(gn['piece'])}, z {f(gn['z_n3'])} ile biter; 4) düşey kanal {f(gn['channel'])}; mitre birleşimleri; "
         f"kanalın alt ucu y = −{f(gn['y_off'])}, z {f(gn['z_split'])}, tepe z {f(gn['crown'])}",
         f"{steps[1]:.3f} (+{steps[1] - steps[0]:.3f})"),
        ("3a + kol +x", f"Ø{gn['D_leg']:g}, kanalın alt ucundan x–z düzleminde düşeyden {gn['arm_angle']:g}° dışa, eğik parça {f(gn['arm_piece'])}, "
         f"mitre ile yatay kol {f(gn['arm_run'])} (eksen z {f(gn['z_end'])}), çıkış yüzü x = {f(gn['x_leg'])} → gas_outlet_1",
         f"{steps[2]:.3f} (+{v_arm:.3f} − ortak {gn['overlap_neck_arm']:.3f})"),
        ("3b + kol −x", f"kanalla ortak {gn['overlap_neck_arm']:.3f}, kolların ortak hacmi {gn['overlap_arms']:.3f}, üçünün {gn['overlap_all']:.3f} (sayısal, {pg.OVERLAP_N}³ nokta) → gas_outlet_2",
         f"{steps[3]:.3f}"),
        ("5a / 5b + farin boruları ±x", f"Ø{meal['D']:g}, {meal['slope']:g}°, eksenleri duvarı z {f(meal['z_wall'])}'da keser; "
         f"deliğin alt kenarı z {f(meal['hole_bottom'])}, uç yüzleri (±{f(meal['end'][0])}, 0, {f(meal['end'][1])})",
         f"{steps[4]:.3f} / {steps[5]:.3f} (+{meal['volume']:.4f} her biri)"),
        ("6 + tersiyer hava", f"Ø{ta['D']:g}, teğetsel, eksen y {f(ta['y'])}, z {f(ta['z'])}; üst kenarı z {f(ta['top'])}, "
         f"yüzü x {f(ta['x_end'])}", f"{steps[6]:.3f} (+{ta['volume']:.3f})"),
        ("7a / 7b + yakıt boruları ±y", f"Ø{fuel['D']:g}, {fuel['slope']:g}°, eksenleri duvarı z {f(fuel['z_wall'])}'da keser; "
         f"uç yüzleri (0, ±{f(fuel['end'][0])}, {f(fuel['end'][1])})",
         f"{steps[7]:.3f} / {steps[8]:.3f} (+{fuel['volume']:.4f} her biri)"),
        ("8a / 8b − dağıtma plakaları ±x", f"farin deliğinin en alt noktasının {pg.v(g['calciner']['dispersion_plate_lip_clearance']):g} altında, duvarda {meal['slope']:g}° eğimle başlar, "
         f"R {f(dp['R_arc'])} yayla +{dp['exit_angle']:g}°'ye döner; kenarı ρ {f(dp['E'][0])}, z {f(dp['E'][1])}; en alt noktası z {f(dp['z_low'])}; "
         f"genişlik {f(dp['width'])}, kalınlık {dp['thickness']:g}; kuyruk {dp['tail']:g} duvarın içine; akıştan kesilir (katı hacmi {dp['volume']:.4f})",
         f"{steps[9]:.3f} / **{steps[10]:.3f}** (−{dp['inside_vessel']:.4f} her biri)"),
        ("**Uyarı: eski CFD sonuçları**", "Bu belgedeki CFD sonuçları (η, p_CO2, VDZ) 15 Kas 2026 öncesi, doğrudan Y gooseneck'iyle alındı; "
         "kaz boynu + düşey kanal + Y + yatay kollu bu katıyla yeniden koşulmalı", "—"),
        ("Yeniden koşu: domen", "geometry/output/2500/calciner.step; sınır adları ve yüz boyutları geometry/output/2500/calciner_named_selections.py",
         f"{steps[10]:.3f}"),
        ("Yeniden koşu: çıkışlar", f"gas_outlet_1 / gas_outlet_2: dikey düzlem, x = ±{f(gn['x_leg'])}, y = −{f(gn['y_off'])}, z {f(gn['z_end'])}; "
         f"yatay kol {gn['arm_run'] / gn['D_leg']:g} çap ({f(gn['arm_run'])}), eğik parçadan {90.0 - gn['arm_angle']:g}° mitre sonrası", f"{math.pi * rl * rl:.3f} m² her biri"),
    ]


def _drawing_consts():
    """Every numeric Const of the drawing, in file order, and whether
    the generated block (the source) or the drawing itself writes it."""
    text = (MACROS / "plant_topology_2d.bas").read_text(encoding="latin-1")
    i, j = text.index(BEGIN), text.index(END)
    out = []
    for m in re.finditer(r"^Const\s+(\w+)\s+As\s+(?:Double|Long)\s*=\s*([-\d.]+)#?", text, re.M):
        if m.group(1) in ("PI",):
            continue
        out.append((m.group(1), float(m.group(2)), i < m.start() < j))
    return out


def _topology_params(g):
    rows = []
    for name, x, generated in _drawing_consts():
        text = repr(x).removesuffix(".0")
        rows.append((f"`{name}`", text, "plant_geometry.yaml" if generated else "çizimin kendi Const'u"))
    return rows


def _pid_rows(what, g):
    from tools.pid import encode, model

    return getattr(encode, f"rows_{what}")(model.load(), g)


DOCS = {
    "preheater/cyclone_C1.md": lambda g: _cyclone_rows(g, "C1"),
    "preheater/cyclone_C2.md": lambda g: _cyclone_rows(g, "C2"),
    "preheater/cyclone_C3.md": lambda g: _cyclone_rows(g, "C3"),
    "preheater/cyclone_C4.md": lambda g: _cyclone_rows(g, "C4"),
    "preheater/cyclone_C5.md": lambda g: _cyclone_rows(g, "C5"),
    "preheater/riser_R1.md": lambda g: _riser_rows(g, 1),
    "preheater/riser_R2.md": lambda g: _riser_rows(g, 2),
    "preheater/riser_R3.md": lambda g: _riser_rows(g, 3),
    "preheater/riser_R4.md": lambda g: _riser_rows(g, 4),
    "preheater/gooseneck.md": _gooseneck_rows,
    "calciner/calciner.md": _calciner_rows,
    "kiln/kiln.md": _kiln_rows,
    "kiln/kiln_burner.md": _kiln_burner_rows,
    **{f"preheater/meal_pipe_C{s_}.md": (lambda g, s_=s_: _meal_pipe_rows(g, s_)) for s_ in range(1, 6)},
    "kiln/kiln_hood.md": _kiln_hood_rows,
    "kiln/kiln_inlet_chamber.md": _kiln_chamber_rows,
    "fan/id_fan.md": _id_fan_rows,
    "cooler/cooler.md": _cooler_rows,
    "fluid_volumes.md": _fluid_volume_rows,
    "calciner/calciner.md#cfd": _calciner_cfd,
    "plant_topology.md#equipment": _topology_equipment,
    "plant_topology.md#cfd": _topology_cfd,
    "plant_topology.md#layout": _topology_layout,
    "plant_topology.md#params": _topology_params,
    "pid/pid.md#sheets": lambda g: _pid_rows("sheets", g),
    "pid/pid.md#equipment": lambda g: _pid_rows("equipment", g),
    "pid/pid.md#lines": lambda g: _pid_rows("lines", g),
    "pid/pid.md#instruments": lambda g: _pid_rows("instruments", g),
    "pid/pid.md#connectors": lambda g: _pid_rows("connectors", g),
}
DOC_HEADS = {
    "fluid_volumes.md": ("Twin bölgesi", "Ekipman", "Hacim [m³]"),
    "calciner/calciner.md#cfd": ("Adım / parça", "Konum [m]", "Hacim [m³]"),
    "plant_topology.md#equipment": ("Ekipman", "Ölçü [m]", "Kaynak"),
    "plant_topology.md#cfd": ("Blok", "Domen (donmuş)", "Giriş yüzü", "Çıkış yüzü"),
    "plant_topology.md#layout": ("Ne", "Konum [m]"),
    "plant_topology.md#params": ("Const", "Değer", "Nerede yazılı"),
    "pid/pid.md#sheets": ("No", "Kod", "Başlık", "Ekipman", "Hat", "Enstrüman"),
    "pid/pid.md#equipment": ("Kimlik", "Etiket", "Sembol", "Sayfa", "Adet"),
    "pid/pid.md#lines": ("Hat", "Servis", "Nereden", "Nereye", "Sayfa", "Ölçü [m]", "Durum"),
    "pid/pid.md#instruments": ("Etiket", "Değişken", "Twin anahtarı", "Durum", "Referans değer (SI)", "Yer"),
    "pid/pid.md#connectors": ("Kimlik", "Servis", "Nereden sayfa", "Nereye sayfa", "Açıklama"),
}


def md_begin(name):
    """A document's block marker; a document with several blocks names
    each after '#' (plant_topology.md#layout)."""
    tag = name.partition("#")[2]
    return MD_BEGIN + (f" {tag}" if tag else "")


def md_block(name, rows):
    head = DOC_HEADS.get(name, ("Ölçü", "Değer", "Kaynak"))
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return (md_begin(name) + MD_HEADER[len(MD_BEGIN):] + "\n".join(lines) + "\n" + MD_END)


# ======================================================================
# Writing
# ======================================================================
def block(consts):
    return HEADER + "".join(c.line().rstrip() + "\n" for c in consts) + END


def render(text, new_block, name, begin=BEGIN, end=END):
    """text with its generated block replaced (CRLF kept as found)."""
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text.replace("\r\n", "\n")
    i = body.find(begin)
    j = body.find(end, i)
    if i < 0 or j < i:
        raise SystemExit(f"{name}: no generated block ({begin!r} ... {end!r})")
    body = body[:i] + new_block + body[j + len(end):]
    return body.replace("\n", nl)


def run(check=False, g=None):
    """Rewrite (or, with check, compare) every block; the stale ones."""
    g = g or pg.load()
    stale = []
    for name, build in TARGETS.items():
        path = MACROS / name
        text = path.read_bytes().decode("latin-1")
        new = render(text, block(build(g)), name)
        if new != text:
            stale.append(f"geometry/macros/{name}")
            if not check:
                path.write_bytes(new.encode("latin-1"))
    for name, build in DOCS.items():
        path = DOCS_DIR / name.partition("#")[0]
        text = path.read_bytes().decode("utf-8")
        begin = md_begin(name) + (" " if "#" in name else " --")
        new = render(text, md_block(name, build(g)), name, begin, MD_END)
        if new != text:
            stale.append(f"geometry/{name}")
            if not check:
                path.write_bytes(new.encode("utf-8"))
    return stale


def main(argv):
    check = "--check" in argv
    stale = run(check=check)
    for name in stale:
        print(("stale: " if check else "wrote: ") + name)
    if check and stale:
        return 1
    if not stale:
        print("geometry: every generated block is current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
