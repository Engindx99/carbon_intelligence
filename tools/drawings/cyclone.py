"""A preheater cyclone's drawing values (the gooseneck-outlet cyclone,
C1, with its volute since 16 Nov 2026): every value
geometry/macros/drawings.bas shows or lists, with where it comes from
and how far to trust it.

The macro gets them through its generated Const block
(tools/gen_geometry.py, drawings_bas); the JSON next to the drawing
(tools/gen_drawings.py) lists the same Params.
"""

from geometry import plant_geometry as pg

from . import provenance as pv

# What the macro dimensions (its log names them "dim <key> <mm>"),
# each between edges the CFD solid really has; the rest of the table is
# listed, not dimensioned. The bend's centreline radius and the drop
# leg's length have no edge of their own on the solid (the pipe runs
# tangent into the bend), so they are listed only; leg_x is measured
# between the pipe's and the leg's inner walls in the section.
DIMENSIONED = (
    "D_barrel", "H_barrel", "H_cone", "height", "D_dust", "D_vortex",
    "L_vortex", "vortex_wall", "W_inlet", "H_inlet",
    "outlet_rise", "leg_x",
)

# Table order on the sheet.
ORDER = (
    "per_string", "D_barrel", "H_barrel", "H_cone", "height", "L_vortex",
    "D_vortex", "vortex_wall", "D_dust", "W_inlet", "H_inlet", "inlet_slope",
    "inlet_duct_length", "tongue", "overlap", "volute",
    "outlet_turn", "outlet_rise", "outlet_bend_R", "outlet_run", "leg_x",
    "top", "volume", "wet_area", "u_wall", "u_material", "u_flange",
    "u_support", "u_split",
)


def params(g, name):
    """{short key: Param} for cyclone `name` (a volute and a 180 deg
    gooseneck: C1)."""
    c = pg.cyclone(g, name)
    o = pg.cyclone_outlet(g, name)
    if not c["volute"] or c["outlet_turn"] != 180.0:
        raise ValueError(f"{name} is not a volute cyclone with a gooseneck outlet")
    dom = "cyclone_domain"
    P = {}

    def dim(key, label):
        P[key] = pv.cyclone_dim(g, name, key, label)

    P["per_string"] = pv.primary(g, f"cyclones.{name}.per_string", "Number per string",
                                 key=f"{name}.per_string")
    dim("D_barrel", "Barrel inner diameter D")
    dim("H_barrel", "Barrel height")
    dim("H_cone", "Cone height")
    P["height"] = pv.derived(f"{name}.height", "Barrel + cone height", c["height"], "m",
                             [P["H_barrel"], P["H_cone"]])
    dim("L_vortex", "Vortex finder immersion S")
    dim("D_vortex", "Vortex finder / outlet pipe bore Dx")
    P["vortex_wall"] = pv.primary(g, f"{dom}.vortex_wall", "Vortex finder wall")
    dim("D_dust", "Dust outlet diameter")
    dim("W_inlet", "Inlet width b (volute duct)")
    dim("H_inlet", "Inlet height a (volute duct)")
    dim("inlet_slope", "Inlet duct slope")
    P["inlet_duct_length"] = pv.primary(g, f"{dom}.inlet_duct_length",
                                        "Volute duct length (from tangent plane)")
    P["tongue"] = pv.primary(g, f"{dom}.volute_tongue", "Tongue (cut-water)")
    P["overlap"] = pv.primary(g, f"{dom}.volute_overlap", "Scroll's inner arc inside the barrel")
    dim("volute", "Volute")
    dim("outlet_turn", "Outlet bend angle")
    rise_k = pv.cyclone_dim(g, name, "outlet_rise_over_Dx", "")
    bend_k = pv.cyclone_dim(g, name, "outlet_bend_R_over_Dx", "")
    run_k = pv.cyclone_dim(g, name, "outlet_run_over_Dx", "")
    P["outlet_rise"] = pv.derived(f"{name}.outlet_rise", "Outlet pipe rise over the roof",
                                  c["outlet_rise"], "m", [rise_k, P["D_vortex"]])
    P["outlet_bend_R"] = pv.derived(f"{name}.outlet_bend_R", "Outlet bend centreline radius",
                                    c["outlet_bend_R"], "m", [bend_k, P["D_vortex"]])
    P["outlet_run"] = pv.derived(f"{name}.outlet_run", "Outlet drop leg",
                                 c["outlet_run"], "m", [run_k, P["D_vortex"]])
    P["leg_x"] = pv.derived(f"{name}.leg_x", "Barrel axis to drop leg axis",
                            o["leg_x"], "m", [P["outlet_bend_R"]])
    top = o["z_bend"] + o["bend_R"] + 0.5 * o["D"]
    P["top"] = pv.derived(f"{name}.top", "Dust outlet to top of the bend",
                          top, "m", [P["height"], P["outlet_rise"], P["outlet_bend_R"], P["D_vortex"]])
    P["volume"] = pv.derived(f"{name}.volume", "Volume (barrel + cone)", c["volume"], "m3",
                             [P["D_barrel"], P["H_barrel"], P["H_cone"], P["D_dust"]])
    P["wet_area"] = pv.derived(f"{name}.wet_area", "Wetted area (barrel, roof ring, cone)",
                               c["wet_area"], "m2",
                               [P["D_barrel"], P["H_barrel"], P["H_cone"], P["D_dust"], P["D_vortex"]])
    doc = P["D_barrel"].doc
    P["u_wall"] = pv.unknown(f"{name}.shell", "Shell / refractory thickness",
                             f"{doc}: CFD fluid volume, no structure modelled")
    P["u_material"] = pv.unknown(f"{name}.material", "Material", f"{doc}: no source")
    P["u_flange"] = pv.unknown(f"{name}.flanges", "Flanges / nozzles / manholes", f"{doc}: no source")
    P["u_support"] = pv.unknown(f"{name}.supports", "Supports / hangers", f"{doc}: no source")
    P["u_split"] = pv.unknown(f"{name}.y_split", "C1 Y split (riser to 2 cyclones)", f"{doc}: TBD")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P)
    return P


def cell(p):
    """A Param's value as the sheet's table prints it."""
    if p.value is None:
        return "-"
    if isinstance(p.value, bool):
        return "yes" if p.value else "no"
    if p.unit == "m":
        return pv.fmt_half_up(p.mm, 0)
    if p.unit in ("m3", "m2"):
        return pv.fmt_half_up(p.value, 2)
    if p.unit == "deg":
        # whole degrees as they are; any other angle to 0.1 deg, as
        # drawings.bas sets an angle dimension's precision (KIC 41.4237)
        if abs(p.value - round(p.value)) < 1e-9:
            return str(int(round(p.value)))
        return pv.fmt_half_up(p.value, 1)
    return f"{p.value:g}"


def unit(p):
    if p.value is None:
        return ""
    return {"m": "mm", "deg": "deg", "-": "-", "m3": "m3", "m2": "m2"}.get(p.unit, p.unit)


SOURCE_EN = {
    "published": "published",
    "derived_from_reference": "FLS ratio",
    "literature": "literature",
    "cfd_decision": "CFD decision",
    "model": "model parameter",
    "schematic": "schematic",
    "derived": "derived",
    "unknown": "no source",
}
