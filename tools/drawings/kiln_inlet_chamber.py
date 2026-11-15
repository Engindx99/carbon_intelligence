"""The kiln inlet chamber's drawing values (the gas volume between the
kiln's mouth and the calciner's throat): every value
geometry/macros/drawings.bas shows or lists, with where it comes from and
how far to trust it (same scheme as cyclone.py).

The solid is kiln_inlet_chamber.SLDPRT (kiln_inlet_chamber.bas): x from the
calciner axis (the kiln's mouth on the +x wall), y across (the axis at
y = 0), z up from the chamber floor level (the ramp's foot on the +x wall
is h_lip above it, the flat roof at z = H).
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has.
# (H and h_lip are listed only: the floor level z = 0 is a reference, the
# solid has no edge there; the kiln's wall from the ramp's foot to the roof
# is h_wall, an edge it does have.)
DIMENSIONED = ("a_plan", "h_wall", "D_throat", "D_mouth", "ramp_deg")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "a_plan", "H", "h_wall", "D_throat", "D_mouth", "margin", "clear", "h_lip", "ramp_deg", "volume",
    "u_ports", "u_bypass", "u_meal", "u_shell", "u_material",
)


def params(g, name="kiln_inlet_chamber"):
    """{short key: Param} for the kiln inlet chamber (name is the sheet's, unused)."""
    ch = pg.kiln_inlet_chamber(g)
    P = {}
    kiln_d = pv.primary(g, "kiln.D", "Kiln mouth diameter (the kiln's effective D)", key="kiln.D")
    margin = pv.primary(g, "layout.chamber_margin", "Margin round the kiln (plan = D + 2 margin)",
                        key="layout.chamber_margin")
    clear = pv.primary(g, "kiln_inlet_chamber.mouth_clearance", "Mouth clearance to the ramp's foot",
                       key="kiln_inlet_chamber.mouth_clearance")
    flow = pv.primary(g, "calciner.throat_gas_flow", "Kiln gas flow")
    temp = pv.primary(g, "calciner.throat_gas_T", "Kiln gas temperature")
    vel = pv.primary(g, "calciner.throat_velocity", "Throat velocity")
    lod = pv.primary(g, "calciner.throat_length_over_D", "Throat length over D")
    P["D_mouth"] = kiln_d
    P["margin"] = margin
    P["clear"] = clear
    P["a_plan"] = pv.derived("kiln_inlet_chamber.side", "Plan: side of the square (D + 2 margin)",
                             ch["side"], "m", [kiln_d, margin])
    P["H"] = pv.derived("kiln_inlet_chamber.height", "Height: floor level to the flat roof (= the plan's side)",
                        ch["height"], "m", [kiln_d, margin])
    P["D_throat"] = pv.derived("kiln_inlet_chamber.D_throat", "Throat (outlet to the calciner) diameter",
                               ch["D_throat"], "m", [flow, temp, vel, lod])
    P["h_lip"] = pv.derived("kiln_inlet_chamber.h_lip", "Ramp's foot on the kiln's wall, over the floor level",
                            ch["h_lip"], "m", [kiln_d, margin, clear])
    P["h_wall"] = pv.derived("kiln_inlet_chamber.h_wall", "Kiln's wall: ramp's foot to the roof (H - h_lip)",
                             ch["height"] - ch["h_lip"], "m", [kiln_d, margin, clear])
    P["ramp_deg"] = pv.derived("kiln_inlet_chamber.ramp_slope", "Floor ramp's slope (foot to the far top corner)",
                               ch["ramp_slope"], "deg", [kiln_d, margin, clear])
    vol = 0.5 * ch["side"] * (ch["height"] - ch["h_lip"]) * ch["side"]
    P["volume"] = pv.derived("kiln_inlet_chamber.volume", "Volume (to the roof)", vol, "m3",
                             [kiln_d, margin, clear])
    doc = P["a_plan"].doc
    P["u_ports"] = pv.unknown("kiln_inlet_chamber.ports", "Burner, door and inspection ports", f"{doc}: not modelled")
    P["u_bypass"] = pv.unknown("kiln_inlet_chamber.bypass", "Gas bypass take-off", f"{doc}: no source")
    P["u_meal"] = pv.unknown("kiln_inlet_chamber.meal_entry", "Meal entry (injected in the solver)", f"{doc}: no source, not made")
    P["u_shell"] = pv.unknown("kiln_inlet_chamber.shell", "Casing / refractory thickness", f"{doc}: no structure modelled")
    P["u_material"] = pv.unknown("kiln_inlet_chamber.material", "Material", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
