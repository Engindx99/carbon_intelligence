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
        der("C1_FEED_Z", br["z_feed"], "C1 feed chute axis at the branch wall"),
        src("C1_FEED_L", d["c1_feed_depth"], "C1 feed chute depth"),
        src("C1_FEED_W", d["c1_feed_width"], "C1 feed chute side"),
        der("C1_OUT_RISE", c1["outlet_rise"], "C1 outlet pipe rise"),
        der("C1_OUT_R", c1["outlet_bend_R"], "C1 outlet 180 deg bend centreline R"),
        src("STAGE_GAP", lay["stage_gap"]),
        src("ZIG_DX", lay["column_offset"], "outer column outboard of the inner"),
        src("C5_OVER_TA", lay["c5_over_tertiary_air"]),
        src("GN_TO_C5_GAP", lay["gooseneck_to_c5_gap"]),
        src("C1_TWIN_GAP", lay["c1_twin_gap"], "twin C1: gap between the branches' walls"),
        der("C1_TWIN_S", tw["spacing"], "twin C1: axis to axis"),
        der("C1_DUCT_Y", tw["y_duct"], "C1 inlet duct / branch axis from the C1 axis"),
        der("R1_BRANCH_HALF", tw["branch_half"], "R1's Y: each branch from R1's axis"),
        src("R1_UP_MIN", lay["r1_up_min"]),
        src("R1_LEG_ON", lay["r1_leg_on"]),
        src("KILN_AXIS_Z", lay["kiln_axis_z"]),
        src("CHAMBER_MARGIN", lay["chamber_margin"]),
        src("COOLER_DROP", lay["cooler_drop"]),
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
    s = pg.cyclone_slot_inlet(g, "C1")
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
        src("C1_D_VORTEX", cy["C1"]["D_vortex"], "vortex finder / outlet pipe bore"),
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
        der("C1_REACH", s["reach"], "inlet opening's upstream end on the barrel, -x"),
    ]
    out += _table_consts("C1", P, dcy.ORDER)
    out += _twin_sheet_consts(g)
    out += _volute_sheet_consts(g)
    out += _calciner_sheet_consts(g)
    out += _kiln_sheet_consts(g)
    return out


def _volute_sheet_consts(g):
    """What drawings.bas needs for the C4 and C5 sheets (volute cyclones
    with a 90 deg outlet), under their own prefix, and their tables."""
    from tools.drawings import volute as dvo

    d = g["cyclone_domain"]
    out = []
    for name in ("C4", "C5"):
        c = pg.cyclone(g, name)
        o = pg.cyclone_outlet(g, name)
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
            src(f"{name}_L_DUCT", d["inlet_duct_length"], "volute duct length (not scaled)"),
            der(f"{name}_HEIGHT", c["height"], "barrel + cone"),
            der(f"{name}_OUT_RISE", c["outlet_rise"], "outlet pipe rise over the roof"),
            der(f"{name}_OUT_R", c["outlet_bend_R"], "outlet bend centreline R"),
            der(f"{name}_OUT_RUN", c["outlet_run"], "outlet run after the bend"),
            der(f"{name}_EXIT_X", o["x_end"], "barrel axis to the gas outlet face"),
            der(f"{name}_Z_LEG", o["z_leg"], "the outlet run's axis, z"),
            der(f"{name}_TOP", o["z_leg"] + 0.5 * o["D"], "top of the outlet pipe"),
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
    out += _table_consts("calciner", dca.params(g), dca.ORDER)
    return out


def _kiln_sheet_consts(g):
    """What drawings.bas needs for the kiln sheet, under a KIL_ prefix,
    and its table."""
    from tools.drawings import kiln as dki

    k = pg.kiln(g)
    out = [
        der("KIL_D", k["D"], "kiln inner D"),
        der("KIL_L", k["L"], "kiln length, back end to hood end"),
    ]
    out += _table_consts("kiln", dki.params(g), dki.ORDER)
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
        src("TW_R1_D", g["risers"]["R1"]["D"], "R1 bore"),
        src("TW_GAP", g["layout"]["c1_twin_gap"], "the branches' walls apart"),
        der("TW_S", tw["spacing"], "C1 axis to axis"),
        der("TW_BRANCH_HALF", tw["branch_half"], "each branch from R1's axis, x"),
        der("TW_BRANCH_D", br["D"], "branch bore"),
        der("TW_Y_BRANCH", tw["y_branch"], "branches and R1 in front of the C1 axes, y"),
        der("TW_Z_BRANCH", tw["z_branch"], "the branches' floor"),
        der("TW_Z_SPLIT", tw["z_split"], "R1's top: the Y starts"),
        der("TW_R1_STUB_L", L["z_r1_split"] - L["z_r1_leg_top"], "R1 straight under its Y"),
        der("TW_Z_CUT", 0.5 * (chute_top + br["z_bend"]), "section A-A: clear of the feed chutes and the bends"),
        der("TW_C1_R", 0.5 * c1["D_barrel"], "barrel radius"),
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
        src("R1_D", g["risers"]["R1"]["D"], "R1 bore"),
        src("TWIN_GAP", lay["c1_twin_gap"], "the branches' walls apart"),
        der("TWIN_S", tw["spacing"], "C1 axis to axis"),
        der("BRANCH_HALF", tw["branch_half"], "each branch from R1's axis, x"),
        der("BRANCH_D", br["D"], "branch bore (half R1's area)"),
        der("BRANCH_Y", tw["y_branch"], "branches and R1 in front of the C1 axes, y"),
        der("Z_BRANCH", tw["z_branch"], "the branches' floor (the C1_riser inlet face)"),
        der("Z_SPLIT", tw["z_split"], "R1's top: the Y starts"),
        der("R1_STUB_L", L["z_r1_split"] - L["z_r1_leg_top"], "R1 straight under its Y, over C2's outlet leg"),
        der("C1_R", 0.5 * c1["D_barrel"], "barrel radius"),
        der("C1_TOP", o["z_bend"] + o["bend_R"] + 0.5 * o["D"], "the outlet bend's crown"),
        der("C1_X_MAX", o["leg_x"] + 0.5 * o["D"], "the C1_riser solid's far side, its outlet leg (C1 frame x)"),
        der("C1_X_MIN", tip, "the C1_riser solid's near side, its feed chute (C1 frame x)"),
        der("OUT_Z_END", o["z_end"], "the outlet legs' end faces"),
    ]


# ======================================================================
# kiln.bas
# ======================================================================
def kiln_bas(g):
    k = g["kiln"]
    return [
        src("KILN_D", k["D"], "effective inner diameter"),
        src("KILN_L", k["L"], "back end (z = 0) to hood end"),
        src("KILN_SLOPE", k["slope"], "%: the installed slope, not built into the solid"),
        src("KILN_TRANSITION_L", k["transition_L"], "the transition zone from the back end (model split)"),
    ]


TARGETS = {
    "kiln.bas": kiln_bas,
    "cyclone.bas": cyclone_bas,
    "calciner.bas": calciner_bas,
    "plant_topology_2d.bas": drawing_bas,
    "drawings.bas": drawings_bas,
    "c1_twin.bas": c1_twin_bas,
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
UNITS = {"m": "m", "deg": "°", "%": "%", "m2": "m²", "-": "", "kg/s": "kg/s",
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
        row_der("Çıkış dirseği merkez yarıçapı", c["outlet_bend_R"], "m", 3,
                f"{c['outlet_bend_R_over_Dx']:g} D_x"),
        row_der("Çıkış bacağı / inişi", c["outlet_run"], "m", 3,
                f"{c['outlet_run_over_Dx']:g} D_x"),
        row_der("Toplam yükseklik (gövde + koni)", c["height"], "m", 3),
        row_der("**Ekipman hacmi (gövde + koni)**", c["volume"], "m³", 2),
        row_der("**Islak alan (gövde + çatı halkası + koni)**", c["wet_area"], "m²", 2),
    ]
    return rows


def _riser_rows(g, k):
    if k == 1:
        r = pg.r1_path(g)
        p = r["parts"]
        br = r["branch"]
        tw = pg.c1_twin(g)
        rows = [
            row_der("C2 çıkış borusu yükselişi (Ø{:.3f})".format(p[0]["D"]), p[0]["length"], "m"),
            row_der("C2 çıkış dirseği, 90° yay", p[1]["length"], "m"),
            row_der("C2 çıkış bacağı, R1 eksenine", p[2]["length"], "m"),
            row_src("R1 iç çapı", g["risers"]["R1"]["D"]),
            row_der("R1 dik boyu, Y'ye kadar", p[3]["length"], "m"),
            row_der("İkiz C1 kolu çapı (R1 alanının yarısı)", br["D"], "m"),
            row_der("Kol başına boy (dik + 95° dirsek + geçiş + kanal)", br["length"], "m"),
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
            row_der(f"C{k + 1} çıkış borusu yükselişi", p[0]["length"], "m"),
            row_der("90° dirsek, merkez yayı", p[1]["length"], "m"),
            row_der(f"Bacak, C{k} gövdesine", p[2]["length"], "m"),
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
        row_der("**Ekipman hacmi (koni + silindir)**", cal["vessel_volume"], "m³", 2),
        row_der("**Duvar alanı (silindir + koni + tavan halkası)**", cal["vessel_wall_area"], "m²", 2),
    ]


def _kiln_rows(g):
    k, kk = g["kiln"], pg.kiln(g)
    return [
        row_src("Efektif iç çap", k["D"]),
        row_src("Boy", k["L"]),
        row_src("Eğim", k["slope"]),
        row_src("Geçiş bölgesi (arka uç)", k["transition_L"]),
        row_der("Yanma bölgesi", kk["burning_L"], "m", 2),
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
        row_der("**Gövde hacmi**", cc["box_volume"], "m³", 2),
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
        ("R1 (hat başına)", f"Ø{pg.v(g['risers']['R1']['D']):.2f}", "riser_R1.md (HFC2500)"),
        ("R2 / R3 / R4 (hat başına)", " / ".join(f"Ø{pg.stage_riser(g, kk)['parts'][0]['D']:.3f}" for kk in (2, 3, 4)),
         "C3 / C4 / C5'in CFD çıkış borusu (riser_R2–R4.md)"),
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
    L_in = pg.v(d["inlet_duct_length"])

    def mid(c, k=1.0):
        return (f"gövde, VF {c['L_vortex']:.3f}, volüt ve {k * L_in:.2f} m giriş kanalı, "
                f"{c['outlet_rise']:.3f} m ({c['outlet_rise_over_Dx']:g}·VD) çıkış borusu, "
                f"R {c['outlet_bend_R']:.3f} 90° dirsek, {c['outlet_run']:.3f} m bacak")

    def out(c):
        return (f"bacağın ucu, eksenden {c['outlet_bend_R'] + c['outlet_run']:.3f} m, "
                f"çatının {c['outlet_rise'] + c['outlet_bend_R']:.3f} m üstünde")
    return [
        ("C1 (×4)",
         f"gövde, VF {c1['L_vortex']:.2f}, Ø{br['D']:.3f} kol, {br['bend_deg']:g}° R {br['bend_R']:.3f} dirsek, "
         f"{br['transition']:g} m geçiş, {c1['inlet_slope']:g}° kanal, {pg.v(d['c1_feed_width']):g} m oluk; "
         f"{c1['outlet_rise']:.2f} m çıkış borusu, R {c1['outlet_bend_R']:.2f} 180° dirsek, {c1['outlet_run']:.2f} m iniş",
         f"kolun tabanı, toz çıkışının {br['z_floor']:.3f} m üstü",
         f"inişin ucu, çatı kotunda, eksenden {2 * c1['outlet_bend_R']:.2f} m"),
        ("C2–C4 (×6)", mid(c4), f"giriş kanalının ucu, eksenden {L_in:.2f} m (`C4_IN_L`)", out(c4)),
        ("C5 (×2)", f"C2–C4'ün {c5['scale']:.4f} katı (CFD'si ayrıca çözülmez)",
         f"eksenden {c5['scale'] * L_in:.2f} m", out(c5)),
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
    for dv in (v_p1 + v_p2 + v_p3 + v_p4, v_arm - gn["overlap_neck_arm"],
               v_arm - gn["overlap_neck_arm"] - gn["overlap_arms"] + gn["overlap_all"],
               meal["volume"], meal["volume"], ta["volume"], fuel["volume"], fuel["volume"]):
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
         f"{steps[7]:.3f} / **{steps[8]:.3f}** (+{fuel['volume']:.4f} her biri)"),
        ("**Uyarı: eski CFD sonuçları**", "Bu belgedeki CFD sonuçları (η, p_CO2, VDZ) 15 Kas 2026 öncesi, doğrudan Y gooseneck'iyle alındı; "
         "kaz boynu + düşey kanal + Y + yatay kollu bu katıyla yeniden koşulmalı", "—"),
        ("Yeniden koşu: domen", "geometry/output/2500/calciner.step; sınır adları ve yüz boyutları geometry/output/2500/calciner_named_selections.py",
         f"{steps[8]:.3f}"),
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
    "cooler/cooler.md": _cooler_rows,
    "fluid_volumes.md": _fluid_volume_rows,
    "calciner/calciner.md#cfd": _calciner_cfd,
    "plant_topology.md#equipment": _topology_equipment,
    "plant_topology.md#cfd": _topology_cfd,
    "plant_topology.md#layout": _topology_layout,
    "plant_topology.md#params": _topology_params,
}
DOC_HEADS = {
    "fluid_volumes.md": ("Twin bölgesi", "Ekipman", "Hacim [m³]"),
    "calciner/calciner.md#cfd": ("Adım / parça", "Konum [m]", "Hacim [m³]"),
    "plant_topology.md#equipment": ("Ekipman", "Ölçü [m]", "Kaynak"),
    "plant_topology.md#cfd": ("Blok", "Domen (donmuş)", "Giriş yüzü", "Çıkış yüzü"),
    "plant_topology.md#layout": ("Ne", "Konum [m]"),
    "plant_topology.md#params": ("Const", "Değer", "Nerede yazılı"),
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
