"""The kiln's mechanical parts after FLS ROTAX-2: every value
geometry/macros/drawings.bas shows or lists on the kiln_rotax sheet, with
where it comes from (same scheme as kiln.py).

The solid is kiln_rotax.SLDPRT (kiln_rotax.bas; plant_geometry.kiln_rotax()
lays every body out): tyres with tangential suspension, roller stations,
friction drive, thrust device, seals, cooling fans, piers, walkway, as
simple envelopes (user, 22 Nov 2026: the kiln's dimensions stay, only these
parts are added). The kiln's shell is drawn as a phantom outline from the
kiln's own numbers; it is not in this solid. Not a fabrication drawing.
FLS publishes no ROTAX-2 size: the values are image ratios, literature or
schematic (plant_geometry.yaml kiln_rotax); schematic values are listed,
never dimensioned.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the solid has.
DIMENSIONED = ("tyre_span", "tyre_width", "tyre_section_L", "D_tyre", "tyre_thickness", "D_roller")

ALSO = {}

ORDER = (
    "tyre_inlet_at", "z_tyre_inlet", "tyre_outlet_at", "z_tyre_outlet", "tyre_span",
    "tyre_width", "tyre_thickness", "tyre_gap", "D_tyre", "tyre_section_t", "tyre_section_L", "bracket_n",
    "roller_over_tyre", "roller_angle", "D_roller", "w_roller",
    "pier_top", "ground_inlet", "ground_outlet",
    "gearbox_D", "motor_size", "htd_D",
    "inlet_seal_depth", "outlet_seal_depth",
    "fan_n", "fan_D", "fan_clearance", "walkway_width",
    "u_power", "u_seal", "u_foundation",
)


def params(g, name="kiln_rotax"):
    """{short key: Param} for the ROTAX-2 parts (name is the sheet's, unused)."""
    r = pg.kiln_rotax(g)
    P = {}

    def yp(key, label):
        P[key] = pv.primary(g, f"kiln_rotax.{key}", label, key=f"kiln_rotax.{key}")
        return P[key]

    L = pv.primary(g, "kiln.L", "Kiln length", key="kiln.L")
    D = pv.primary(g, "kiln.D", "Kiln bore", key="kiln.D")
    t_sh = pv.primary(g, "kiln.shell_t", "Shell plate", key="kiln.shell_t")
    t_br = pv.primary(g, "kiln.lining_t", "Brick ring", key="kiln.lining_t")
    slope = pv.primary(g, "kiln.slope", "Slope", key="kiln.slope")
    axis_z = pv.primary(g, "layout.kiln_axis_z", "Kiln axis over the ground, back end", key="layout.kiln_axis_z")
    shell = [D, t_br, t_sh]

    yp("tyre_inlet_at", "Inlet tyre along L (ROTAX-2 image)")
    P["z_tyre_inlet"] = pv.derived("kiln_rotax.z_tyre_inlet", "Inlet tyre centre from the back end",
                                   r["z_tyre_inlet"], "m", [P["tyre_inlet_at"], L])
    yp("tyre_outlet_at", "Outlet tyre along L (ROTAX-2 image)")
    P["z_tyre_outlet"] = pv.derived("kiln_rotax.z_tyre_outlet", "Outlet tyre centre from the back end",
                                    r["z_tyre_outlet"], "m", [P["tyre_outlet_at"], L])
    P["tyre_span"] = pv.derived("kiln_rotax.tyre_span", "Tyre span (7.3 x shell D, past about 7 D)",
                                r["tyre_span"], "m", [P["tyre_inlet_at"], P["tyre_outlet_at"], L])
    yp("tyre_width", "Tyre width")
    yp("tyre_thickness", "Tyre radial thickness")
    yp("tyre_gap", "Shell to tyre bore (tangential suspension)")
    P["D_tyre"] = pv.derived("kiln_rotax.D_tyre", "Tyre outer D", r["D_tyre"], "m",
                             shell + [P["tyre_gap"], P["tyre_thickness"]])
    yp("tyre_section_t", "Shell under the tyre (triple plate)")
    yp("tyre_section_L", "Tyre section length")
    yp("bracket_n", "Suspension brackets per tyre")
    yp("roller_over_tyre", "Roller D / tyre D (TAPPI 2019)")
    yp("roller_angle", "Roller from the vertical (60 deg pair)")
    P["D_roller"] = pv.derived("kiln_rotax.D_roller", "Support roller D", r["D_roller"], "m",
                               [P["roller_over_tyre"], P["D_tyre"]])
    extra = pv.primary(g, "kiln_rotax.roller_extra_width", "Roller wider than the tyre",
                       key="kiln_rotax.roller_extra_width")
    P["w_roller"] = pv.derived("kiln_rotax.w_roller", "Support roller width", r["w_roller"], "m",
                               [P["tyre_width"], extra])
    stack = [pv.primary(g, f"kiln_rotax.{k}", k, key=f"kiln_rotax.{k}") for k in ("bearing_size", "frame_t")]
    P["pier_top"] = pv.derived("kiln_rotax.y_pier_top", "Pier top under the kiln axis", r["y_pier_top"], "m",
                               [P["D_roller"], P["D_tyre"], P["roller_angle"]] + stack)
    P["ground_inlet"] = pv.derived("kiln_rotax.ground_inlet", "Ground under the axis, inlet pier",
                                   r["ground_inlet"], "m", [axis_z, slope, P["tyre_inlet_at"], L])
    P["ground_outlet"] = pv.derived("kiln_rotax.ground_outlet", "Ground under the axis, outlet pier",
                                    r["ground_outlet"], "m", [axis_z, slope, P["tyre_outlet_at"], L])
    yp("gearbox_D", "Drive gearbox D (2, inlet station)")
    yp("motor_size", "Main motor size (2, inlet station)")
    yp("htd_D", "Hydraulic thrust roller D")
    yp("inlet_seal_depth", "Inlet seal housing, radial")
    yp("outlet_seal_depth", "Outlet seal housing, radial")
    yp("fan_n", "Shell cooling fans (ROTAX-2 image)")
    yp("fan_D", "Cooling fan D")
    yp("fan_clearance", "Fan outlet to the surface it cools")
    yp("walkway_width", "Walkway width")
    doc = P["tyre_width"].doc
    P["u_power"] = pv.unknown("kiln_rotax.drive_power", "Drive motor power, speed range", f"{doc}: no source")
    P["u_seal"] = pv.unknown("kiln_rotax.seal_detail", "Seal blocks, wire ropes, cooling air", f"{doc}: no source")
    P["u_foundation"] = pv.unknown("kiln_rotax.foundation", "Foundations, platforms, stairs, railings",
                                   f"{doc}: not modelled")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
