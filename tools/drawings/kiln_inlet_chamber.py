"""The kiln inlet chamber's drawing values (the gas volume between the
kiln's mouth and the calciner's throat): every value
geometry/macros/drawings.bas shows or lists, with where it comes from and
how far to trust it (same scheme as cyclone.py).

The solid is kiln_inlet_chamber.SLDPRT (kiln_inlet_chamber.bas): x from the
calciner axis (the kiln comes in from +x), y across (the axis at y = 0), z up
from the chamber's floor level (a reference: the solid has no face there).
The section is plant_geometry.chamber_section (user sketch, 21 Nov 2026):
the throat's walls x = +-r run down, the left one to the ramp's top, the
ramp at ramp_deg to a foot along the kiln's bottom line, the roof the
kiln's top line; the kiln tube's stub on the mouth's face.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has. (H is listed only: the floor
# level z = 0 has no edge. The ramp's slope has no horizontal edge to be
# measured from: the angle dimensioned is the ramp's to the throat's
# left wall, 90 - ramp_deg.)
DIMENSIONED = ("a_plan", "D_throat", "D_mouth", "L_stub", "h_left", "ramp_wall_deg")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "a_plan", "H", "D_throat", "D_mouth", "margin", "ramp_deg", "ramp_wall_deg", "ramp_foot", "h_left",
    "stub_over_D", "L_stub", "volume",
    "u_ports", "u_bypass", "u_meal", "u_shell", "u_material",
)


def params(g, name="kiln_inlet_chamber"):
    """{short key: Param} for the kiln inlet chamber (name is the sheet's, unused)."""
    ch = pg.kiln_inlet_chamber(g)
    P = {}
    kiln_d = pv.primary(g, "kiln.D", "Kiln mouth diameter (the kiln's effective D)", key="kiln.D")
    slope = pv.primary(g, "kiln.slope", "Kiln slope", key="kiln.slope")
    margin = pv.primary(g, "layout.chamber_margin", "Margin round the kiln (plan = D + 2 margin)",
                        key="layout.chamber_margin")
    ramp = pv.primary(g, "kiln_inlet_chamber.ramp_deg", "Ramp's slope (to the horizontal)",
                      key="kiln_inlet_chamber.ramp_deg")
    foot = pv.primary(g, "kiln_inlet_chamber.ramp_foot", "Ramp's foot, toe to the mouth (horizontal, at the kiln's slope)",
                      key="kiln_inlet_chamber.ramp_foot")
    stub = pv.primary(g, "kiln_inlet_chamber.mouth_stub_over_D", "Kiln tube's stub over D (CFD inlet)",
                      key="kiln_inlet_chamber.mouth_stub_over_D")
    flow = pv.primary(g, "calciner.throat_gas_flow", "Kiln gas flow")
    temp = pv.primary(g, "calciner.throat_gas_T", "Kiln gas temperature")
    vel = pv.primary(g, "calciner.throat_velocity", "Throat velocity")
    lod = pv.primary(g, "calciner.throat_length_over_D", "Throat length over D")
    P["D_mouth"] = kiln_d
    P["margin"] = margin
    P["ramp_deg"] = ramp
    P["ramp_foot"] = foot
    P["stub_over_D"] = stub
    P["a_plan"] = pv.derived("kiln_inlet_chamber.side", "Plan: across (D + 2 margin)",
                             ch["side"], "m", [kiln_d, margin])
    P["H"] = pv.derived("kiln_inlet_chamber.height", "Height: floor level to the throat's top",
                        ch["height"], "m", [kiln_d, margin])
    P["D_throat"] = pv.derived("kiln_inlet_chamber.D_throat", "Throat (outlet to the calciner) diameter",
                               ch["D_throat"], "m", [flow, temp, vel, lod])
    P["ramp_wall_deg"] = pv.derived("kiln_inlet_chamber.ramp_wall", "Ramp to the throat's left wall (90 - ramp)",
                                    90.0 - ch["ramp_deg"], "deg", [ramp])
    sec_deps = [kiln_d, slope, margin, ramp, foot, flow, temp, vel, lod]
    P["h_left"] = pv.derived("kiln_inlet_chamber.h_left", "Left wall: ramp's top to the roof",
                             ch["roof_left"][1] - ch["ramp_top"][1], "m", sec_deps)
    P["L_stub"] = pv.derived("kiln_inlet_chamber.L_stub", "Kiln tube's stub, along its axis",
                             ch["L_stub"], "m", [kiln_d, stub])
    P["volume"] = pv.derived("kiln_inlet_chamber.volume", "Volume (section prism + throat + stub)", ch["volume"], "m3",
                             sec_deps + [stub])
    doc = P["a_plan"].doc
    P["u_ports"] = pv.unknown("kiln_inlet_chamber.ports", "Burner, door and inspection ports", f"{doc}: not modelled")
    P["u_bypass"] = pv.unknown("kiln_inlet_chamber.bypass", "Gas bypass take-off", f"{doc}: no source")
    P["u_meal"] = pv.unknown("kiln_inlet_chamber.meal_entry", "Meal entry (injected in the solver)", f"{doc}: no source, not made")
    P["u_shell"] = pv.unknown("kiln_inlet_chamber.shell", "Casing / refractory thickness", f"{doc}: no structure modelled")
    P["u_material"] = pv.unknown("kiln_inlet_chamber.material", "Material", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
