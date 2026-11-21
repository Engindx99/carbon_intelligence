"""The twin C1 over its common R1: every value geometry/macros/drawings.bas
shows or lists for the C1_twin sheet, with where it comes from and how
far to trust it (same scheme as cyclone.py).

The solid is C1_twin.SLDPRT (c1_twin.bas); the spacing and the Y are
derived in plant_geometry.c1_twin from c1_twin_gap, which no source
gives (a model choice), so everything that follows from it is
Estimated. R1's bore is published; the stub under the Y is a layout
value (Schematic) and is listed, never dimensioned.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between circles the CFD solid really has: R1's floor, the branches'
# and the barrels' sections in A-A, R1's top and a branch's floor.
DIMENSIONED = (
    "R1_D", "D_barrel", "branch_D", "spacing", "branch_pitch", "y_branch", "y_rise",
)

# Table order on the sheet.
ORDER = (
    "R1_D", "branch_D", "twin_gap", "spacing", "barrel_gap", "branch_pitch",
    "y_branch", "y_rise", "r1_stub", "D_barrel", "height", "D_vortex", "top",
    "u_wall", "u_material", "u_flange", "u_support",
)


def params(g, name="C1_twin"):
    """{short key: Param} for the twin C1 (name is the sheet's, unused)."""
    tw = pg.c1_twin(g)
    br = pg.c1_branch(g)
    c1 = pg.cyclone(g, "C1")
    o = pg.cyclone_outlet(g, "C1")
    L = pg.layout(g)
    dom = "cyclone_domain"
    P = {}

    # the entries everything below rests on
    # R1 = C2's outlet pipe, its bore D_x = D / 2 (user decision, 21 Nov 2026)
    r1 = pv.derived("R1_D", "R1 bore", pg.r1_D(g), "m",
                    [pv.cyclone_dim(g, "C2", "D_vortex", "C2 vortex finder bore")])
    share = pv.primary(g, f"{dom}.c1_riser_area_share", "branch area share of R1")
    gap = pv.primary(g, "layout.c1_twin_gap", "Branches' walls apart")
    w_in = pv.cyclone_dim(g, "C1", "W_inlet", "inlet width")
    h_in = pv.cyclone_dim(g, "C1", "H_inlet", "inlet height")
    slope = pv.cyclone_dim(g, "C1", "inlet_slope", "inlet slope")
    relief = pv.primary(g, f"{dom}.inlet_tangent_relief", "tangent relief")
    clear = pv.primary(g, f"{dom}.inlet_roof_clearance", "opening below the roof")
    ductl = pv.primary(g, f"{dom}.inlet_duct_length", "inlet duct length")
    trans = pv.primary(g, f"{dom}.c1_riser_transition", "transition length")
    bend = pv.primary(g, f"{dom}.c1_riser_bend_R_over_D", "bend R over D")
    below = pv.primary(g, f"{dom}.c1_riser_below_feed", "riser below the feed")
    above = pv.primary(g, f"{dom}.c1_riser_above_feed", "riser above the feed")
    up_min = pv.primary(g, "layout.r1_up_min", "R1 over C2's CFD outlet pipe")
    stage = pv.primary(g, "layout.stage_gap", "stage gap")
    D_b = pv.cyclone_dim(g, "C1", "D_barrel", "Barrel inner diameter D")
    H_b = pv.cyclone_dim(g, "C1", "H_barrel", "Barrel height")
    H_c = pv.cyclone_dim(g, "C1", "H_cone", "Cone height")
    D_v = pv.cyclone_dim(g, "C1", "D_vortex", "Vortex finder / outlet pipe bore Dx")

    P["R1_D"] = r1
    P["R1_D"].label = "R1 bore"
    P["branch_D"] = pv.derived("c1_twin.branch_D", "Branch bore (half R1's area)", br["D"], "m", [r1, share])
    P["twin_gap"] = gap
    P["twin_gap"].key = "c1_twin.gap"
    P["twin_gap"].label = "Branches' walls apart"
    spacing_in = [gap, r1, share, w_in, relief]
    P["spacing"] = pv.derived("c1_twin.spacing", "C1 axis to axis", tw["spacing"], "m", spacing_in)
    P["barrel_gap"] = pv.derived("c1_twin.barrel_gap", "Barrel wall to wall", tw["barrel_gap"], "m",
                                 spacing_in + [D_b])
    P["branch_pitch"] = pv.derived("c1_twin.branch_pitch", "Branch axis to axis (Y)",
                                   2.0 * tw["branch_half"], "m", spacing_in)
    P["y_branch"] = pv.derived("c1_twin.y_branch", "R1 / branches in front of the C1 axes",
                               -tw["y_branch"], "m",
                               [r1, share, w_in, h_in, slope, relief, clear, ductl, trans, bend])
    P["y_rise"] = pv.derived("c1_twin.y_rise", "Y height (R1 top to the branches' floor)",
                             tw["y_rise"], "m", spacing_in)
    P["r1_stub"] = pv.derived("c1_twin.r1_stub", "R1 straight under its Y",
                              L["z_r1_split"] - L["z_r1_foot"], "m", [up_min, stage])
    P["D_barrel"] = D_b
    P["height"] = pv.derived("C1.height", "Barrel + cone height", c1["height"], "m", [H_b, H_c])
    P["D_vortex"] = D_v
    top = o["z_bend"] + o["bend_R"] + 0.5 * o["D"]
    P["top"] = pv.derived("c1_twin.top", "Dust outlets to the top of the bends", top, "m",
                          [P["height"], D_v, pv.cyclone_dim(g, "C1", "outlet_rise_over_Dx", ""),
                           pv.cyclone_dim(g, "C1", "outlet_bend_R_over_Dx", "")])

    doc = D_b.doc
    P["u_wall"] = pv.unknown("c1_twin.shell", "Shell / refractory thickness",
                             f"{doc}: CFD fluid volume, no structure modelled")
    P["u_material"] = pv.unknown("c1_twin.material", "Material", f"{doc}: no source")
    P["u_flange"] = pv.unknown("c1_twin.flanges", "Flanges / nozzles / manholes", f"{doc}: no source")
    P["u_support"] = pv.unknown("c1_twin.supports", "Supports / hangers", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P)
    return P
