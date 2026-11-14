"""The grate cooler's drawing values (the fluid box above the grate): every
value geometry/macros/drawings.bas shows or lists, with where it comes from
and how far to trust it (same scheme as cyclone.py).

The solid is cooler.SLDPRT (cooler.bas): x along the grate (x = 0 at the
hot end), y across, z up from the grate plane.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has.
DIMENSIONED = ("L_cool", "w_cool", "H_cool", "segment", "hood")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "grate_area", "w_cool", "L_cool", "H_cool", "segments", "segment", "hood_segments", "hood",
    "volume", "wall_area",
    "u_vent", "u_plate", "u_crusher", "u_chute", "u_wall", "u_material",
)


def params(g, name="cooler"):
    """{short key: Param} for the cooler (name is the sheet's, unused)."""
    c = pg.cooler(g)
    P = {}
    P["grate_area"] = pv.primary(g, "cooler.grate_area", "Grate area (PF5000)", key="cooler.grate_area")
    P["w_cool"] = pv.primary(g, "cooler.width", "Grate width", key="cooler.width")
    P["L_cool"] = pv.derived("cooler.L", "Grate length (area / width)", c["length"], "m",
                             [P["grate_area"], P["w_cool"]])
    P["H_cool"] = pv.primary(g, "cooler.casing_height", "Height, grate to roof", key="cooler.casing_height")
    P["segments"] = pv.primary(g, "cooler.segments", "Undergrate air segments (FLS)", key="cooler.segments")
    P["segment"] = pv.derived("cooler.segment_L", "One segment: length", c["segment_L"], "m",
                              [P["L_cool"], P["segments"]])
    P["hood_segments"] = pv.primary(g, "cooler.hood_segments", "Segments under the hood's opening (hot end)",
                                    key="cooler.hood_segments")
    P["hood"] = pv.derived("cooler.hood_L", "Hood opening: length from the hot end", c["hood_L"], "m",
                           [P["segment"], P["hood_segments"]])
    P["volume"] = pv.derived("cooler.volume", "Volume (box, bed included)", c["box_volume"], "m3",
                             [P["L_cool"], P["w_cool"], P["H_cool"]])
    P["wall_area"] = pv.derived("cooler.wall_area", "Wall area (sides, ends, roof but the hood)", c["wall_area"], "m2",
                                [P["L_cool"], P["w_cool"], P["H_cool"], P["hood"]])
    doc = P["grate_area"].doc
    P["u_vent"] = pv.unknown("cooler.vent", "Vent outlet (cold end): place and size", f"{doc}: no source, not made")
    P["u_plate"] = pv.unknown("cooler.plates", "Grate plates / compartment walls", f"{doc}: not modelled")
    P["u_crusher"] = pv.unknown("cooler.crusher", "Clinker crusher", f"{doc}: not modelled")
    P["u_chute"] = pv.unknown("cooler.chute", "Clinker chute from the kiln", f"{doc}: not modelled")
    P["u_wall"] = pv.unknown("cooler.shell", "Casing / refractory thickness", f"{doc}: no structure modelled")
    P["u_material"] = pv.unknown("cooler.material", "Material", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
