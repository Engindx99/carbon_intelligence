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
        rows = [
            row_der("C2 çıkış borusu yükselişi (Ø{:.3f})".format(p[0]["D"]), p[0]["length"], "m"),
            row_der("C2 çıkış dirseği, 90° yay", p[1]["length"], "m"),
            row_der("C2 çıkış bacağı, R1 eksenine", p[2]["length"], "m"),
            row_src("R1 iç çapı", g["risers"]["R1"]["D"]),
            row_der("R1 dik boyu, Y'ye kadar", p[3]["length"], "m"),
            row_der("İkiz C1 kolu çapı (R1 alanının yarısı)", br["D"], "m"),
            row_der("Kol başına boy (dik + 95° dirsek + geçiş + kanal)", br["length"], "m"),
            row_der("Kol sayısı", r["branches"], "", 0),
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
        row_der("Boyun yükselişi", gn["rise"], "m", 3, f"{pg.v(n['rise_over_D_neck']):g} × boyun çapı; modelleme"),
        row_der("180° dirsek merkez yarıçapı", gn["bend_R"], "m", 3, f"{pg.v(n['bend_R_over_D_leg']):g} × kol çapı; modelleme"),
        row_der("İki dirseğin ortak hacmi", gn["bend_overlap"], "m³"),
        row_der("CFD: iniş (gövdenin yarı yüksekliğine)", gn["drop"], "m"),
        row_der("CFD: hacim", gn["volume"], "m³", 2),
        row_der("CFD: duvar alanı", gn["wall_area"], "m²", 2),
        row_der("Tesis: kol boyu (iniş + 45° + C5 girişine yatay)", gp["leg_length"], "m"),
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
        ("Kaz boynu", f"Y: boyun Ø{gn['D_neck']:.3f}, 2 kol × Ø{gn['D_leg']:.2f}, her kol C5 girişine iner", "gooseneck.md"),
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
    v_neck = math.pi * (0.5 * gn["D_neck"]) ** 2 * gn["rise"]
    v_bend = math.pi * rl * rl * math.pi * gn["bend_R"]
    v_leg = math.pi * rl * rl * gn["drop"]
    f = lambda x: f"{x:.3f}"
    steps = [cal["v_throat"] + cal["vessel_volume"]]
    ins = pg.calciner_inlets(g)
    ta, meal, fuel = ins["tertiary_air"], ins["meal"], ins["fuel"]
    for dv in (v_neck, v_bend, v_bend - gn["bend_overlap"], 2.0 * v_leg,
               meal["volume"], meal["volume"], ta["volume"], fuel["volume"], fuel["volume"]):
        steps.append(steps[-1] + dv)
    return [
        ("Boğaz", f"Ø{f(cal['D_throat'])}, z 0 .. {f(cal['z_throat_top'])}", f"{cal['v_throat']:.3f}"),
        ("Koni", f"{pg.v(g['calciner']['cone_angle']):g}°, z {f(cal['z_throat_top'])} .. {f(cal['z_cone_top'])}", f"{v_cone:.3f}"),
        ("Silindir (düz tavan)", f"Ø{cal['D']:.4f}, z {f(cal['z_cone_top'])} .. {f(cal['z_roof'])}", f"{v_cyl:.3f}"),
        ("Gövde (koni + silindir)", "", f"**{cal['vessel_volume']:.3f}**"),
        ("1 domen (boğaz + gövde)", "", f"{steps[0]:.3f}"),
        ("2 + boyun", f"Ø{f(gn['D_neck'])}, eksende, z {f(cal['z_roof'])} .. {f(gn['z_top'])}", f"{steps[1]:.3f} (+{v_neck:.3f})"),
        ("3a + dirsek +x", f"kol Ø{gn['D_leg']:g}, başlangıç diski x = ±{f(gn['x_leg_start'])}; 180°, R {f(gn['bend_R'])}, tepe z {f(gn['z_top'] + gn['bend_R'] + rl)}", f"{steps[2]:.3f} (+{v_bend:.3f}, Pappus)"),
        ("3b + dirsek −x", f"iki dirseğin ortak hacmi {gn['bend_overlap']:.3f} (sayısal, {pg.OVERLAP_N}³ nokta)", f"{steps[3]:.3f}"),
        ("4 + iki iniş", f"x = ±{f(gn['x_leg'])}, z {f(gn['z_top'])} .. {f(gn['z_end'])} → gas_outlet_1 (+x), gas_outlet_2 (−x)", f"{steps[4]:.3f} (+2 × {v_leg:.3f})"),
        ("5a / 5b + farin boruları ±x", f"Ø{meal['D']:g}, {meal['slope']:g}°, eksenleri duvarı z {f(meal['z_wall'])}'da keser; "
         f"deliğin alt kenarı z {f(meal['hole_bottom'])}, uç yüzleri (±{f(meal['end'][0])}, 0, {f(meal['end'][1])})",
         f"{steps[5]:.3f} / {steps[6]:.3f} (+{meal['volume']:.4f} her biri)"),
        ("6 + tersiyer hava", f"Ø{ta['D']:g}, teğetsel, eksen y {f(ta['y'])}, z {f(ta['z'])}; üst kenarı z {f(ta['top'])}, "
         f"yüzü x {f(ta['x_end'])}", f"{steps[7]:.3f} (+{ta['volume']:.3f})"),
        ("7a / 7b + yakıt boruları ±y", f"Ø{fuel['D']:g}, {fuel['slope']:g}°, eksenleri duvarı z {f(fuel['z_wall'])}'da keser; "
         f"uç yüzleri (0, ±{f(fuel['end'][0])}, {f(fuel['end'][1])})",
         f"{steps[8]:.3f} / **{steps[9]:.3f}** (+{fuel['volume']:.4f} her biri)"),
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
