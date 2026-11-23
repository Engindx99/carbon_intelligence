"""The flame zone's CFD volume: every value geometry/macros/drawings.bas
shows or lists on the kiln_flame sheet, with where it comes from (same
scheme as kiln_burner.py).

The solid is kiln_flame.SLDPRT (kiln_flame.bas; plant_geometry.
kiln_flame() lays every body out): the kiln hood, the kiln's bore over the
burning zone, the cooler's two hood segments under the hood's floor, the
tertiary air duct's mouth on its roof, the burner's channels placed with
their tip 0.25 m inside the kiln, the burner itself cut out (user,
23 Nov 2026: placement + hood + flame CFD volume; CFD runs later).

The hood's width and height rest on schematic values (the outlet seal's
depth, the cooler's drop under the kiln): listed, not dimensioned.
"""

import math

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the solid has.
DIMENSIONED = ("hood_depth", "segment_L", "D_bore", "D_ta", "tip_to_cut")

ALSO = {}

ORDER = (
    "m_air", "area", "area_min", "u", "u_hot",
    "R_seal", "seal_clearance", "hood_W", "hood_H", "hood_depth", "segment_L", "flame_stub_L",
    "D_ta", "h_ta", "D_bore", "L_flame",
    "burner_insertion", "burner_offset_x", "burner_offset_y", "burner_tilt_deg",
    "tip_to_cut", "castable_past_front",
    "u_bed", "u_doors",
)


def params(g, name="kiln_flame"):
    """{short key: Param} for the flame volume (name is the sheet's, unused)."""
    hd, kl, co = pg.kiln_hood(g), pg.kiln(g), pg.cooler(g)
    pl, f = pg.kiln_burner_placement(g), pg.kiln_flame(g)
    P = {}

    def y(dotted, label, key=None):
        return pv.primary(g, dotted, label, key=key or dotted)

    sec = [y("kiln_burner.kiln_air_flow", "Kiln air"), y("kiln_burner.primary_air_fraction", "Primary share"),
           y("kiln_hood.seal_air_fraction", "Seal leak share")]
    T_sec = y("kiln_hood.secondary_air_T", "Secondary air T")
    ta_m, ta_T = y("calciner.tertiary_air_flow", "Tertiary air"), y("calciner.tertiary_air_T", "Tertiary air T")
    vmin = y("kiln_hood.air_velocity_min", "Hood air velocity, min (literature)")
    vmax = y("kiln_hood.air_velocity_max", "Hood air velocity, max (literature)")
    depth_in = [y("cooler.grate_area", "Grate area"), y("cooler.width", "Cooler width"),
                y("cooler.segments", "Segments"), y("cooler.hood_segments", "Hood segments")]
    seal = [y("kiln_rotax.outlet_seal_depth", "Outlet seal depth"), y("kiln.D", "Kiln D")]
    drop = y("layout.cooler_drop", "Kiln axis over the cooler roof")

    P["m_air"] = pv.derived("kiln_flame.m_air", "Air through the hood (secondary + tertiary)",
                            hd["m"], "kg/s", sec + [ta_m])
    P["seal_clearance"] = y("kiln_hood.seal_clearance", "Back wall round the seal, clearance",
                            key="kiln_hood.seal_clearance")
    P["R_seal"] = pv.derived("kiln_flame.R_seal", "Outlet seal's outer radius (kiln_rotax)",
                             hd["R_seal"], "m", seal)
    P["hood_W"] = pv.derived("kiln_flame.hood_W", "Hood inner width (seal + clearance, both sides)",
                             hd["W"], "m", [P["R_seal"], P["seal_clearance"]])
    P["hood_H"] = pv.derived("kiln_flame.hood_H", "Hood inner height (cooler roof to the roof)",
                             hd["H"], "m", [P["R_seal"], P["seal_clearance"], drop])
    P["hood_depth"] = pv.derived("kiln_flame.hood_depth", "Hood depth (the cooler's two hood segments)",
                                 hd["depth"], "m", depth_in)
    P["segment_L"] = pv.derived("kiln_flame.segment_L", "Cooler segment under the hood, long",
                                co["segment_L"], "m", depth_in)
    P["flame_stub_L"] = y("kiln_hood.flame_stub_L", "Inlet / outlet stubs (segment 2: twice)",
                          key="kiln_hood.flame_stub_L")
    P["area"] = pv.derived("kiln_flame.area", "Hood section, width x height", hd["area"], "m2",
                           [P["hood_W"], P["hood_H"]])
    P["area_min"] = pv.derived("kiln_flame.area_min", "Section the velocity limit needs", hd["area_min"], "m2",
                               [P["m_air"], ta_T, vmax])
    P["u"] = pv.derived("kiln_flame.u", "Hood air velocity at the tertiary air T (4-10 m/s)",
                        hd["u"], "m/s", [P["m_air"], ta_T, P["area"], vmin, vmax])
    P["u_hot"] = pv.derived("kiln_flame.u_hot", "Hood air velocity at the secondary air T", hd["u_hot"], "m/s",
                            [P["m_air"], T_sec, P["area"], vmin, vmax])
    dta = y("calciner.D_tertiary_air", "Tertiary air duct D")
    P["D_ta"] = pv.derived("kiln_flame.D_ta", "Tertiary air mouth on the roof (the duct's D)",
                           2.0 * f["r_ta"], "m", [dta])
    P["h_ta"] = pv.derived("kiln_flame.h_ta", "Its axis from the back wall (over segment 2)",
                           f["h_ta"], "m", depth_in)
    P["D_bore"] = y("kiln.D", "Kiln bore D (the kiln sheet)", key="kiln.D")
    P["L_flame"] = pv.derived("kiln_flame.L_flame", "Bore in the volume (the twin's burning zone)",
                              f["L_flame"], "m", [y("kiln.L", "Kiln L"), y("kiln.transition_L", "Transition zone")])
    for k, label in (("burner_insertion", "Burner tip inside the kiln mouth"),
                     ("burner_offset_x", "Burner off the kiln axis, across"),
                     ("burner_offset_y", "Burner off the kiln axis, up"),
                     ("burner_tilt_deg", "Burner off the kiln axis, tilt")):
        P[k] = y(f"kiln_hood.{k}", label, key=f"kiln_hood.{k}")
    P["tip_to_cut"] = pv.derived("kiln_flame.tip_to_cut", "Burner tip to the kiln gas outlet",
                                 pl["tip"][2] - f["z_cut"], "m", [P["L_flame"], P["burner_insertion"]])
    body = [y("kiln_burner.body_castable_L", "castable_L"), y("kiln_burner.body_tip_ring_L", "tip_ring_L")]
    P["castable_past_front"] = pv.derived("kiln_flame.castable_past_front",
                                          "Burner castable past the hood's front wall (> 0: no bare steel)",
                                          pl["castable_past_front"], "m",
                                          body + [P["burner_insertion"], P["hood_depth"]])
    doc = P["seal_clearance"].doc
    P["u_bed"] = pv.unknown("kiln_flame.bed", "Clinker bed in the kiln and on the grate",
                            f"{doc}: not in the volume (as kiln.SLDPRT)")
    P["u_doors"] = pv.unknown("kiln_flame.doors", "Hood doors, seal leaks, refractory detail",
                              f"{doc}: not modelled")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    assert math.isclose(P["tip_to_cut"].value, kl["burning_L"] - P["burner_insertion"].value)
    return P
