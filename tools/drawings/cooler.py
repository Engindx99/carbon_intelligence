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
DIMENSIONED = ("L_cool", "w_cool", "H_cool", "segment", "hood", "bed_h", "vent_D", "vent_L")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "grate_area", "w_cool", "L_cool", "H_cool", "segments", "segment", "hood_segments", "hood",
    "cis_angle", "cis_rise", "bed_h", "vent_D", "vent_x", "vent_L",
    "hrb_rollers", "hrb_pitch", "hrb_L",
    "volume_bed", "volume_fb", "volume",
    "u_plate", "u_chute", "u_wall", "u_material",
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
    f = pg.cooler_cfd(g)
    P["cis_angle"] = pv.primary(g, "cooler.cis_angle", "Inlet grate (CIS): slope", key="cooler.cis_angle")
    P["cis_rise"] = pv.derived("cooler.cis_rise", "Inlet grate: height at the hot end (one segment long)",
                               c["cis_rise"], "m", [P["cis_angle"], P["segment"]])
    P["bed_h"] = pv.derived("cooler.bed_h", "Clinker bed depth (the FLS design bed)", c["bed_h"], "m",
                            [P["w_cool"]])
    P["vent_D"] = pv.derived("cooler.vent_D", "Vent duct bore (vent air at 250 degC, 13 m/s)", f["vent_D"], "m",
                             [pv.primary(g, "cooler.vent_velocity", "Vent duct velocity", key="cooler.vent_velocity")])
    P["vent_x"] = pv.derived("cooler.vent_x", "Vent duct axis from the hot end", f["vent_x"], "m", [P["L_cool"], P["vent_D"]])
    P["vent_L"] = pv.derived("cooler.vent_L", "Vent duct run off the roof (3 D)", f["vent_L"], "m", [P["vent_D"]])
    P["hrb_rollers"] = pv.primary(g, "cooler.hrb_rollers", "Clinker outlet: roller breaker (HRB) rollers",
                                  key="cooler.hrb_rollers")
    P["hrb_pitch"] = pv.primary(g, "cooler.hrb_pitch", "HRB roller pitch", key="cooler.hrb_pitch")
    P["hrb_L"] = pv.derived("cooler.hrb_L", "HRB deck past the grate's end (freeboard over it)", f["hrb_L"], "m",
                            [P["hrb_rollers"], P["hrb_pitch"]])
    P["volume_bed"] = pv.derived("cooler.bed_volume", "Bed body (porous zone)", f["bed_volume"], "m3",
                                 [P["L_cool"], P["w_cool"], P["bed_h"]])
    P["volume_fb"] = pv.derived("cooler.freeboard_volume", "Freeboard body (vent duct included)", f["freeboard_volume"], "m3",
                                [P["L_cool"], P["w_cool"], P["H_cool"], P["vent_D"], P["hrb_L"]])
    P["volume"] = pv.derived("cooler.volume", "CFD volume (bed + freeboard)", f["volume"], "m3",
                             [P["volume_bed"], P["volume_fb"]])
    doc = P["grate_area"].doc
    P["u_plate"] = pv.unknown("cooler.plates", "Grate plates / compartment walls", f"{doc}: not modelled")
    P["u_chute"] = pv.unknown("cooler.chute", "Clinker chute from the kiln", f"{doc}: not modelled")
    P["u_wall"] = pv.unknown("cooler.shell", "Casing / refractory thickness", f"{doc}: no structure modelled")
    P["u_material"] = pv.unknown("cooler.material", "Material", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
