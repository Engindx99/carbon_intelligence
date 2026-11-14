"""The rotary kiln's drawing values (the tube: inner diameter, length,
slope, the transition / burning split): every value
geometry/macros/drawings.bas shows or lists, with where it comes from and
how far to trust it (same scheme as cyclone.py).

The solid is kiln.SLDPRT (kiln.bas): the axis is z, the back end (the
kiln inlet chamber's side) at z = 0, the hood end at z = L. The slope is
an installation attribute and is not built into the solid.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has. The slope and the zones have no
# edge in the solid: the table only.
DIMENSIONED = ("D_kiln", "L_kiln")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "D_kiln", "L_kiln", "slope", "transition_L", "burning_L",
    "volume", "wall_area",
    "u_wall", "u_material", "u_tyre", "u_drive", "u_seal",
)


def params(g, name="kiln"):
    """{short key: Param} for the kiln (name is the sheet's, unused)."""
    k = pg.kiln(g)
    P = {}
    P["D_kiln"] = pv.primary(g, "kiln.D", "Kiln inner diameter (effective)", key="kiln.D")
    P["L_kiln"] = pv.primary(g, "kiln.L", "Kiln length", key="kiln.L")
    P["slope"] = pv.primary(g, "kiln.slope", "Slope (installed, not built into the solid)", key="kiln.slope")
    P["transition_L"] = pv.primary(g, "kiln.transition_L", "Transition zone from the back end (model split)",
                                   key="kiln.transition_L")
    P["burning_L"] = pv.derived("kiln.burning_L", "Burning zone (model split)", k["burning_L"], "m",
                                [P["L_kiln"], P["transition_L"]])
    P["volume"] = pv.derived("kiln.volume", "Volume (tube)", k["volume"], "m3", [P["D_kiln"], P["L_kiln"]])
    P["wall_area"] = pv.derived("kiln.wall_area", "Wetted area (tube)", k["wall_area"], "m2",
                                [P["D_kiln"], P["L_kiln"]])
    doc = P["D_kiln"].doc
    P["u_wall"] = pv.unknown("kiln.shell", "Shell / refractory thickness",
                             f"{doc}: CFD fluid volume, no structure modelled")
    P["u_material"] = pv.unknown("kiln.material", "Material", f"{doc}: no source")
    P["u_tyre"] = pv.unknown("kiln.tyres", "Tyres / support rollers", f"{doc}: no source")
    P["u_drive"] = pv.unknown("kiln.drive", "Drive / girth gear", f"{doc}: no source")
    P["u_seal"] = pv.unknown("kiln.seals", "Inlet and outlet seals", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
