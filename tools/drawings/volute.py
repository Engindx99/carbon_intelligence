"""A volute preheater cyclone's drawing values (C4; C2 and C3 are C4,
C5 is C4 x 6.50 / 6.30): every value geometry/macros/drawings.bas
shows or lists, with where it comes from and how far to trust it
(same scheme as cyclone.py).

The solids are C4.SLDPRT / C5.SLDPRT (cyclone.bas, VOLUTE_ON, a 90 deg
outlet). C5's body lengths scale; the vortex finder wall, the volute's
tongue and the duct's length do not (cyclone.bas: they are in the
shared block, not in the C5 case).
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has. The volute's spiral is a
# spline and the elbow's centreline radius has no edge, so they are
# listed only.
DIMENSIONED = (
    "D_barrel", "H_barrel", "H_cone", "height", "D_dust", "D_vortex",
    "L_vortex", "vortex_wall", "W_inlet", "H_inlet", "outlet_axis", "exit_x",
)

# Cyclones whose sheet this one is (geometry/preheater: C2 and C3 are C4).
ALSO = {"C4": ["C2", "C3"]}

# Table order on the sheet.
ORDER = (
    "per_string", "D_barrel", "H_barrel", "H_cone", "height", "L_vortex",
    "D_vortex", "vortex_wall", "D_dust", "W_inlet", "H_inlet", "inlet_duct_length",
    "tongue", "overlap", "volute", "outlet_turn", "outlet_rise", "outlet_bend_R",
    "outlet_run", "outlet_axis", "exit_x", "top", "volume", "wet_area",
    "u_wall", "u_material", "u_flange", "u_support",
)


def params(g, name):
    """{short key: Param} for the volute cyclone `name` (C4 or C5)."""
    c = pg.cyclone(g, name)
    if not c["volute"] or c["outlet_turn"] != 90.0:
        raise ValueError(f"{name} is not a volute cyclone with a 90 deg outlet")
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
    P["outlet_run"] = pv.derived(f"{name}.outlet_run", "Outlet run after the bend",
                                 c["outlet_run"], "m", [run_k, P["D_vortex"]])
    o = pg.cyclone_outlet(g, name)
    P["outlet_axis"] = pv.derived(f"{name}.outlet_axis", "Roof to the outlet run's axis",
                                  c["outlet_rise"] + c["outlet_bend_R"], "m",
                                  [P["outlet_rise"], P["outlet_bend_R"]])
    P["exit_x"] = pv.derived(f"{name}.exit_x", "Barrel axis to the gas outlet face",
                             o["x_end"], "m", [P["outlet_bend_R"], P["outlet_run"]])
    P["top"] = pv.derived(f"{name}.top", "Dust outlet to the top of the outlet pipe",
                          o["z_leg"] + 0.5 * o["D"], "m",
                          [P["height"], P["outlet_rise"], P["outlet_bend_R"], P["D_vortex"]])
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
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P)
    return P
