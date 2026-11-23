"""The kiln burner (JETFLEX 2.0): every value geometry/macros/drawings.bas
shows or lists on the kiln_burner sheet, with where it comes from (same
scheme as kiln_rotax.py).

The solid is kiln_burner.SLDPRT (kiln_burner.bas; plant_geometry.
kiln_burner() lays every body out): the burner's three channels up to its
tip -- the coal pipe, the axial air plenum and slots, the swirl air plenum
and inclined holes -- a CFD flow volume (user, 22 Nov 2026). FLS publishes
no size: the tip's layout is the brochure's (image ratios), scaled so the
slots pass the twin's axial air at the JETFLEX manual's pressure.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the solid has.
DIMENSIONED = ("D_coal", "D_swirl_out", "D_axial_out", "L_coal", "plenum_L", "plate_t")

ALSO = {}

ORDER = (
    "thermal_MW", "m_pa", "m_axial", "m_swirl", "m_transport",
    "axial_pressure", "swirl_pressure", "u_axial", "u_swirl", "momentum_per_MW",
    "D_tip", "D_coal", "y_coal", "u_coal", "L_coal",
    "n_axial", "slot_l", "slot_w", "slot_tilt", "r_slots",
    "n_swirl", "hole_a", "swirl_angle", "r_holes",
    "D_swirl_in", "D_swirl_out", "D_axial_in", "D_axial_out", "plenum_L", "plate_t",
    "u_lance", "u_nozzle_angle", "u_insertion",
)


def params(g, name="kiln_burner"):
    """{short key: Param} for the burner (name is the sheet's, unused)."""
    r = pg.kiln_burner(g)
    P = {}

    def yp(key, label):
        P[key] = pv.primary(g, f"kiln_burner.{key}", label, key=f"kiln_burner.{key}")
        return P[key]

    def y(key, label):           # an input not in the table
        return pv.primary(g, f"kiln_burner.{key}", label, key=f"kiln_burner.{key}")

    fuel, lhv = y("fuel_flow", "Kiln fuel"), y("fuel_LHV", "LHV")
    air, share = y("kiln_air_flow", "Kiln air"), y("primary_air_fraction", "Primary air share")
    T0, load = y("primary_air_T", "Primary air T"), y("transport_loading", "Coal loading")
    ratios = [y(k, k) for k in ("n_axial", "axial_slot_area_over_D2", "n_swirl", "swirl_hole_area_over_D2")]

    P["thermal_MW"] = pv.derived("kiln_burner.thermal_MW", "Thermal input (twin kiln fuel x LHV)",
                                 r["thermal_MW"], "MW", [fuel, lhv])
    P["m_pa"] = pv.derived("kiln_burner.m_pa", "Primary air, axial + swirl (twin share)",
                           r["m_pa"], "kg/s", [air, share])
    yp("axial_pressure", "Axial air pressure (JETFLEX manual)")
    yp("swirl_pressure", "Swirl air pressure (JETFLEX manual)")
    yp("swirl_angle", "Swirl holes off the axis")
    jets = [P["axial_pressure"], P["swirl_pressure"], T0]
    split = [P["m_pa"], P["swirl_angle"]] + jets + ratios
    P["m_axial"] = pv.derived("kiln_burner.m_axial", "Axial air (split by the open areas)",
                              r["m_axial"], "kg/s", split)
    P["m_swirl"] = pv.derived("kiln_burner.m_swirl", "Swirl air", r["m_swirl"], "kg/s", split)
    P["m_transport"] = pv.derived("kiln_burner.m_transport", "Coal conveying air (fuel / loading)",
                                  r["m_transport"], "kg/s", [fuel, load])
    P["u_axial"] = pv.derived("kiln_burner.u_axial", "Axial jet (isentropic)", r["u_axial"], "m/s",
                              [P["axial_pressure"], T0])
    P["u_swirl"] = pv.derived("kiln_burner.u_swirl", "Swirl jet (isentropic)", r["u_swirl"], "m/s",
                              [P["swirl_pressure"], T0])
    P["momentum_per_MW"] = pv.derived("kiln_burner.momentum_per_MW", "Momentum sum m u (FLS 7-11)",
                                      r["momentum_per_MW"], "N/MW", split + [fuel, lhv])
    P["D_tip"] = pv.derived("kiln_burner.D_tip", "Tip outer D (scale: slots pass the axial air)",
                            r["D_tip"], "m", split)
    scale = [P["D_tip"]]
    P["n_axial"] = yp("n_axial", "Axial air slots (brochure)")
    P["n_swirl"] = yp("n_swirl", "Swirl air holes (brochure)")
    dc = y("coal_pipe_D_over_D", "Coal pipe D / tip D")
    P["D_coal"] = pv.derived("kiln_burner.D_coal", "Solid fuel pipe bore", r["D_coal"], "m", scale + [dc])
    P["y_coal"] = pv.derived("kiln_burner.y_coal", "Solid fuel pipe above the tip axis", r["y_coal"], "m",
                             scale + [y("coal_pipe_offset_over_D", "offset")])
    P["u_coal"] = pv.derived("kiln_burner.u_coal", "Coal pipe velocity (check: 33 m/s lit.)",
                             r["u_coal"], "m/s", [P["m_transport"], P["D_coal"]])
    P["L_coal"] = pv.derived("kiln_burner.L_coal", "Coal pipe in the solid (5 D)", r["L_coal"], "m",
                             [P["D_coal"], y("coal_pipe_L_over_D", "L / D")])
    slot = scale + [y("axial_slot_aspect", "aspect"), P["n_axial"]]
    P["slot_l"] = pv.derived("kiln_burner.slot_l", "Axial slot, long side", r["slot_l"], "m", slot)
    P["slot_w"] = pv.derived("kiln_burner.slot_w", "Axial slot, short side", r["slot_w"], "m", slot)
    yp("axial_slot_tilt", "Slot's long side off the tangent")
    P["slot_tilt"] = P.pop("axial_slot_tilt")
    P["r_slots"] = pv.derived("kiln_burner.r_slots", "Slot ring radius", r["r_slots"], "m",
                              scale + [y("axial_ring_r_over_D", "r / D")])
    P["hole_a"] = pv.derived("kiln_burner.hole_a", "Swirl hole side (normal to it)", r["hole_a"], "m",
                             split)
    P["r_holes"] = pv.derived("kiln_burner.r_holes", "Swirl hole ring radius (tip plane)", r["r_holes"], "m",
                              scale + [y("swirl_ring_r_over_D", "r / D")])
    clr = y("plenum_clearance", "Plenum clearance")
    sw0, sw1 = r["swirl_plenum"]
    ax0, ax1 = r["axial_plenum"]
    P["D_swirl_in"] = pv.derived("kiln_burner.D_swirl_in", "Swirl plenum inner D", 2 * sw0, "m",
                                 [P["r_holes"], P["hole_a"], clr])
    P["D_swirl_out"] = pv.derived("kiln_burner.D_swirl_out", "Swirl plenum outer D", 2 * sw1, "m",
                                  [P["r_holes"], P["hole_a"], clr])
    P["D_axial_in"] = pv.derived("kiln_burner.D_axial_in", "Axial plenum inner D", 2 * ax0, "m",
                                 [P["r_slots"], P["slot_l"], clr])
    P["D_axial_out"] = pv.derived("kiln_burner.D_axial_out", "Axial plenum outer D", 2 * ax1, "m",
                                  [P["r_slots"], P["slot_l"], clr])
    yp("plenum_L", "Plenums (the solid's air inlets)")
    yp("plate_t", "Front plate the openings run through")
    doc = P["plate_t"].doc
    P["u_lance"] = pv.unknown("kiln_burner.lance", "Fuel lance, igniter, flame scanner (closed here)",
                              f"{doc}: no flow path in this solid")
    P["u_nozzle_angle"] = pv.unknown("kiln_burner.nozzle_angle", "Axial nozzles' fixed angle, swirl sense",
                                     f"{doc}: not published (axial 0 deg, anticlockwise: model)")
    P["u_insertion"] = pv.unknown("kiln_burner.insertion", "Burner position in the kiln (depth, offset)",
                                  f"{doc}: for the flame domain")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
