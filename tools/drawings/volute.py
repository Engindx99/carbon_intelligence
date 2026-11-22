"""A volute preheater cyclone's drawing values (C4; C2 and C3 are C4,
C5 is C4 x 6.50 / 6.30): every value geometry/macros/drawings.bas
shows or lists, with where it comes from and how far to trust it
(same scheme as cyclone.py).

The solids are C4.SLDPRT / C5.SLDPRT (cyclone.bas, VOLUTE_ON; since
17 Nov 2026 a riser inlet turning in at 45 deg and a straight outlet).
C5's lengths scale, the level duct and riser included; the vortex
finder wall and the volute's tongue do not (cyclone.bas: they are in
the shared block, not in the C5 case).
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has. The volute's spiral is a
# spline, so it is listed only. Since 17 Nov 2026 the domain's outlet is
# a straight pipe and its inlet a riser turning in at 45 deg (R2 / R3 as
# the plant has them).
DIMENSIONED = (
    "D_barrel", "H_barrel", "H_cone", "height", "D_dust", "D_vortex",
    "L_vortex", "vortex_wall", "W_inlet", "H_inlet", "outlet_rise",
)
# riser_offset is in the table only since 22 Nov 2026: the riser meets its
# elbow along four spline arcs (no circle or ellipse edge to dimension to)

# Cyclones whose sheet this one is (geometry/preheater: C2 and C3 are C4).
ALSO = {"C4": ["C2", "C3"]}

# Table order on the sheet.
ORDER = (
    "per_string", "D_barrel", "H_barrel", "H_cone", "height", "L_vortex",
    "D_vortex", "vortex_wall", "D_dust", "W_inlet", "H_inlet", "inlet_duct_length",
    "tongue", "overlap", "volute", "riser_cut", "riser_offset", "riser_run",
    "riser_stub", "outlet_turn", "outlet_rise", "top", "volume", "wet_area",
    "u_wall", "u_material", "u_flange", "u_support",
)


def params(g, name):
    """{short key: Param} for the volute cyclone `name` (C4 or C5)."""
    c = pg.cyclone(g, name)
    if not c["volute"] or c["outlet_turn"] != 0.0 or not c["inlet_riser"]:
        raise ValueError(f"{name} is not a volute cyclone with a riser inlet and a straight outlet")
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
    dim("inlet_duct_length", "Level duct length (from tangent plane)")
    P["tongue"] = pv.primary(g, f"{dom}.volute_tongue", "Tongue (cut-water)")
    P["overlap"] = pv.primary(g, f"{dom}.volute_overlap", "Scroll's inner arc inside the barrel")
    dim("volute", "Volute")
    r = pg.cfd_riser_inlet(g, name)
    cut = pv.primary(g, f"{dom}.riser_cut_deg", "Riser's cut under the elbow, tilt")
    bend_k = pv.primary(g, f"{dom}.riser_bend_R_over_H", "")
    stub_k = pv.primary(g, f"{dom}.riser_cfd_stub_over_D", "")
    P["riser_cut"] = cut
    P["riser_offset"] = pv.derived(f"{name}.riser_offset", "Riser axis from the barrel axis (the columns' offset)",
                                   r["offset"], "m", [bend_k, P["H_inlet"], P["W_inlet"], P["inlet_duct_length"]])
    P["riser_run"] = pv.derived(f"{name}.riser_run", "Elbow centreline radius, riser axis to the duct face",
                                r["run"], "m", [P["riser_offset"], P["W_inlet"], P["inlet_duct_length"]])
    P["riser_stub"] = pv.derived(f"{name}.riser_stub", "Vertical riser in the domain, under the cut",
                                 r["stub"], "m", [stub_k, P["D_vortex"]])
    dim("outlet_turn", "Outlet bend angle (0: straight)")
    rise_k = pv.cyclone_dim(g, name, "outlet_rise_over_Dx", "")
    P["outlet_rise"] = pv.derived(f"{name}.outlet_rise", "Outlet pipe rise over the roof (the domain's end)",
                                  c["outlet_rise"], "m", [rise_k, P["D_vortex"]])
    P["top"] = pv.derived(f"{name}.top", "Dust outlet to the outlet face",
                          c["height"] + c["outlet_rise"], "m", [P["height"], P["outlet_rise"]])
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
