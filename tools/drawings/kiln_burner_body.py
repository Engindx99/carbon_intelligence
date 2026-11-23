"""The whole kiln burner (JETFLEX 2.0) as simple envelopes: every value
geometry/macros/drawings.bas shows or lists on the kiln_burner_body sheet,
with where it comes from (same scheme as kiln_rotax.py).

The solid is kiln_burner_body.SLDPRT (kiln_burner_body.bas;
plant_geometry.kiln_burner_body()): castable pipe, steel burner pipe,
flange, air connection head and inlets, expansion joint, coal inlet,
carriage beam -- not a CFD input (user, 22 Nov 2026). Every length is a
ratio of the tip's D read off the Fuller brochure's side view, scaled by
the channel solid's D_tip (kiln_burner sheet).
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

DIMENSIONED = ("L_total", "castable_L", "tip_ring_L", "head_L", "D_castable", "flange_D")

ALSO = {}

ORDER = (
    "D_tip", "tip_ring_L", "castable_L", "D_castable", "D_pipe", "pipe_t",
    "flange_D", "head_L", "D_head", "bellows_L", "coal_L", "D_coal_inlet",
    "inlet1_D", "inlet2_D", "beam_H", "beam_L", "L_total",
    "u_inside", "u_inlets", "u_carriage",
)


def params(g, name="kiln_burner_body"):
    """{short key: Param} for the whole burner (name is the sheet's, unused)."""
    r = pg.kiln_burner_body(g)
    ch = pg.kiln_burner(g)
    P = {}

    def y(key):
        return pv.primary(g, f"kiln_burner.body_{key}", key, key=f"kiln_burner.body_{key}")

    split = [pv.primary(g, f"kiln_burner.{k}", k, key=f"kiln_burner.{k}")
             for k in ("axial_pressure", "swirl_pressure", "n_axial", "axial_slot_area_over_D2", "kiln_air_flow",
                       "primary_air_fraction")]
    P["D_tip"] = pv.derived("kiln_burner.D_tip", "Tip outer D (kiln_burner sheet)", r["D_tip"], "m", split)
    D = [P["D_tip"]]

    def ratio(key, label, value, *names):
        P[key] = pv.derived(f"kiln_burner_body.{key}", label, value, "m", D + [y(n) for n in names])

    ratio("tip_ring_L", "Castable tip ring, long", -r["z_ring"], "tip_ring_L")
    ratio("castable_L", "Castable, tip to its back end", -r["z_castable"], "castable_L")
    ratio("D_castable", "Castable OD behind the tip ring", 2 * r["R_castable"], "castable_D")
    P["pipe_t"] = pv.primary(g, "kiln_burner.body_pipe_t", "Steel burner pipe wall", key="kiln_burner.body_pipe_t")
    P["D_pipe"] = pv.derived("kiln_burner_body.D_pipe", "Steel burner pipe OD (bore = axial plenum)",
                             2 * r["r_pipe"], "m", D + [P["pipe_t"]])
    by = {b["name"]: b for b in r["bodies"]}
    ratio("flange_D", "Mounting flange OD", 2 * by["flange"]["p"][6], "flange_D")
    ratio("head_L", "Air connection head, long", r["z_flange"] - r["z_head"], "head_L")
    ratio("D_head", "Air connection head OD", 2 * r["r_head"], "head_D")
    ratio("bellows_L", "Expansion joint, long", r["z_head"] - r["z_bellows"], "bellows_L")
    ratio("coal_L", "Solid fuel inlet pipe, long (drawn straight)", r["z_bellows"] - r["z_coal"], "coal_L")
    ratio("D_coal_inlet", "Solid fuel inlet pipe OD", 2 * by["coal_inlet"]["p"][6], "coal_D")
    ratio("inlet1_D", "Air inlet 1 OD (head side)", 2 * by["air_inlet_1"]["p"][6], "inlet1_D")
    ratio("inlet2_D", "Air inlet 2 OD (head side)", 2 * by["air_inlet_2"]["p"][6], "inlet2_D")
    ratio("beam_H", "Carriage beam, high", by["beam"]["p"][3] - by["beam"]["p"][2], "beam_H")
    ratio("beam_L", "Carriage beam, long (out of the picture)", by["beam"]["p"][5] - by["beam"]["p"][4], "beam_L")
    ratio("L_total", "Burner, coal inlet flange to tip", r["L_total"],
          "tip_ring_L", "castable_L", "collar_L", "flange_L", "head_L", "bellows_L", "coal_L")
    doc = P["pipe_t"].doc
    P["u_inside"] = pv.unknown("kiln_burner_body.inside", "Channels inside the pipe behind the tip's 1 m",
                               f"{doc}: not modelled (the CFD channels end at the plenums)")
    P["u_inlets"] = pv.unknown("kiln_burner_body.inlets", "Which inlet is axial, which swirl air",
                               f"{doc}: not shown")
    P["u_carriage"] = pv.unknown("kiln_burner_body.carriage", "Carriage rail, trolley, hoses, platform",
                                 f"{doc}: not modelled")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    del ch
    return P
