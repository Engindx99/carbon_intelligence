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
        label = {"vessel": "kalsinatör gövdesi (koni + silindir; yakıt burada)",
                 "gooseneck": "kaz boynu, C5 girişlerine kadar",
                 "C5": f"C5 (×{n})"}[seg["name"]]
        rows.append(("Kalsinatör bölgesi", label, f"**{seg['volume']:.2f}**"))
    kk, cc = pg.kiln(g), pg.cooler(g)
    a = 0.25 * math.pi * kk["D"] ** 2
    rows.append(("Geçiş", f"fırının arka {kk['transition_L']:g} m'si", f"**{a * kk['transition_L']:.2f}**"))
    rows.append(("Yanma", f"fırının ön {kk['burning_L']:.2f} m'si", f"**{a * kk['burning_L']:.2f}**"))
    rows.append(("Soğutucu", "ızgara kutusu", f"**{cc['box_volume']:.2f}**"))
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
}
DOC_HEADS = {"fluid_volumes.md": ("Twin bölgesi", "Ekipman", "Hacim [m³]")}


def md_block(name, rows):
    head = DOC_HEADS.get(name, ("Ölçü", "Değer", "Kaynak"))
    lines = [f"| {head[0]} | {head[1]} | {head[2]} |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return MD_HEADER + "\n".join(lines) + "\n" + MD_END


# ======================================================================
# Writing
# ======================================================================
def block(consts):
    return HEADER + "".join(c.line().rstrip() + "\n" for c in consts) + END


def render(text, new_block, name, begin=BEGIN, end=END):
    """text with its generated block replaced (CRLF kept as found)."""
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text.replace("\r\n", "\n")
    i, j = body.find(begin), body.find(end)
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
        path = DOCS_DIR / name
        text = path.read_bytes().decode("utf-8")
        new = render(text, md_block(name, build(g)), name, MD_BEGIN, MD_END)
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
