"""The calciner's drawing values (the ILC vessel, its throat, Y gooseneck,
tertiary air duct, meal and fuel pipes): every value
geometry/macros/drawings.bas shows or lists, with where it comes from and
how far to trust it (same scheme as cyclone.py).

The solid is calciner.SLDPRT (calciner.bas): z = 0 at the throat's foot.
"""

import math

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has.
# (D_neck, the arms' outlet height and the width over the outlet faces are in the table only:
# the neck has no full circle among its edges, the others rest on the layout's schematic C5 height)
DIMENSIONED = (
    "D_throat", "L_throat", "H_cone", "D_vessel", "H_cylinder", "H_vessel",
    "D_leg", "D_fuel", "D_TA", "ta_x", "D_feed",
    "box_rise",
)

ALSO = {}

# Table order on the sheet.
ORDER = (
    "D_throat", "L_throat", "H_cone", "D_vessel", "H_cylinder", "H_vessel",
    "D_neck", "neck_slope", "neck_piece", "neck_level", "channel", "D_leg", "arm_angle", "arm_run",
    "y_off", "x_leg", "leg_end_z", "width", "top",
    "D_TA", "ta_y", "ta_z", "ta_x", "D_feed", "D_fuel", "fuel_slope",
    "box_width", "box_back_h", "box_height", "box_rise",
    "volume", "wet_area",
    "u_wall", "u_material", "u_flange", "u_support", "u_burner",
)


def params(g, name="calciner"):
    """{short key: Param} for the calciner (name is the sheet's, unused)."""
    cal = pg.calciner(g)
    inl = pg.calciner_inlets(g)
    gn = pg.gooseneck(g)
    P = {}

    flow = pv.primary(g, "calciner.throat_gas_flow", "Kiln gas flow")
    temp = pv.primary(g, "calciner.throat_gas_T", "Kiln gas temperature")
    vel = pv.primary(g, "calciner.throat_velocity", "Throat velocity")
    lod = pv.primary(g, "calciner.throat_length_over_D", "Throat length over D")
    cone = pv.primary(g, "calciner.cone_angle", "Cone wall angle")
    leg = pv.primary(g, "gooseneck.D_leg", "Gooseneck leg bore (published)")
    piece_k = pv.primary(g, "gooseneck.neck_piece_over_D_neck", "Inclined piece over the neck D")
    level_k = pv.primary(g, "gooseneck.neck_level_over_D_neck", "Level piece over the neck D")
    slope_k = pv.primary(g, "gooseneck.neck_slope", "Neck slope")
    arm_k = pv.primary(g, "gooseneck.arm_angle", "Arm angle to the vertical")
    armp_k = pv.primary(g, "gooseneck.arm_run_over_D_leg", "Arm level run over the leg D")
    chan_k = pv.primary(g, "gooseneck.channel_over_D_neck", "Vertical channel over the neck D")
    # the arms' level runs stand at C5's inlet axis, which the tertiary air duct's clearance over
    # C5's height sets (the layout's schematic clearance): the heights and x derived from it are not
    # better than schematic
    end_k = pv.primary(g, "layout.c5_over_tertiary_air", "C5 over the tertiary air duct")
    P["D_vessel"] = pv.primary(g, "calciner.D", "Vessel inner diameter D", key="calciner.D")
    P["H_vessel"] = pv.primary(g, "calciner.H", "Vessel height (cone + cylinder)", key="calciner.H")

    P["D_throat"] = pv.derived("calciner.D_throat", "Throat (kiln gas inlet) diameter",
                               cal["D_throat"], "m", [flow, temp, vel])
    P["L_throat"] = pv.derived("calciner.L_throat", "Throat length", cal["z_throat_top"], "m",
                               [P["D_throat"], lod])
    P["H_cone"] = pv.derived("calciner.H_cone", "Cone height", cal["h_cone"], "m",
                             [P["D_vessel"], P["D_throat"], cone])
    P["H_cylinder"] = pv.derived("calciner.H_cylinder", "Cylinder height", cal["h_cylinder"], "m",
                                 [P["H_vessel"], P["H_cone"]])
    # one neck of both legs' area: a user decision, so no better than a model value
    # one neck of both arms' area: a user decision, so no better than a model value
    P["D_neck"] = pv.derived("gooseneck.D_neck", "Gooseneck neck diameter (both arms' area)",
                             gn["D_neck"], "m", [leg, piece_k])
    P["neck_piece"] = pv.derived("gooseneck.piece", "Neck's inclined pieces (2): length", gn["piece"], "m",
                                 [P["D_neck"], piece_k, slope_k])
    P["neck_level"] = pv.derived("gooseneck.level", "Neck's level piece: length", gn["level"], "m",
                                 [P["D_neck"], level_k])
    P["D_leg"] = pv.primary(g, "gooseneck.D_leg", "Gooseneck arm bore", key="gooseneck.D_leg")
    P["neck_slope"] = slope_k
    P["channel"] = pv.derived("gooseneck.channel", "Vertical channel below the neck: length", gn["channel"], "m",
                              [P["D_neck"], chan_k])
    P["arm_angle"] = arm_k
    P["arm_run"] = pv.derived("gooseneck.arm_run", "Arms' level run to the outlet face: length", gn["arm_run"], "m",
                              [leg, armp_k])
    # the neck's first piece pierces the roof in front of the axis by what keeps its cap in the vessel
    P["y_off"] = pv.derived("gooseneck.y_off", "Channel and arms in front of the vessel axis",
                            gn["y_off"], "m", [P["neck_piece"], P["neck_level"], slope_k, P["D_vessel"], P["D_neck"]])
    ta_z_k = pv.derived("calciner.ta_z", "Tertiary air duct axis height", inl["tertiary_air"]["z"], "m",
                        [P["L_throat"], P["H_cone"],
                         pv.primary(g, "calciner.D_tertiary_air", "Tertiary air duct diameter"),
                         pv.primary(g, "calciner.tertiary_air_cone_clearance", "Duct over the cone's top")])
    P["leg_end_z"] = pv.derived("gooseneck.z_end", "Throat foot to the arms' level runs' axis (C5's inlet axis)",
                                gn["z_end"], "m", [ta_z_k, end_k])
    P["x_leg"] = pv.derived("gooseneck.x_leg", "Barrel axis to an arm's outlet face", gn["x_leg"], "m",
                            [leg, armp_k, arm_k, chan_k, P["D_neck"], P["leg_end_z"], P["H_vessel"], P["L_throat"]])
    P["width"] = pv.derived("gooseneck.width", "Overall width over the arms' outlet faces", 2.0 * gn["x_leg"],
                            "m", [P["x_leg"]])
    P["top"] = pv.derived("gooseneck.top", "Throat foot to the neck's crown", gn["crown"], "m",
                          [P["L_throat"], P["H_vessel"], P["neck_piece"], slope_k])

    ta = inl["tertiary_air"]
    ta_d = pv.primary(g, "calciner.D_tertiary_air", "Tertiary air duct diameter", key="calciner.D_tertiary_air")
    relief = pv.primary(g, "calciner.tertiary_air_wall_relief", "Duct's wall clear of the vessel's")
    clear = pv.primary(g, "calciner.tertiary_air_cone_clearance", "Duct over the cone's top")
    stub = pv.primary(g, "calciner.tertiary_air_stub_length", "Duct stub past the tangent plane")
    P["D_TA"] = ta_d
    P["ta_y"] = pv.derived("calciner.ta_offset", "Tertiary air duct axis off the vessel axis (tangential, x)",
                           ta["offset"], "m", [P["D_vessel"], ta_d, relief])
    P["ta_z"] = pv.derived("calciner.ta_z", "Tertiary air duct axis height", ta["z"], "m",
                           [P["L_throat"], P["H_cone"], ta_d, clear])
    P["ta_x"] = pv.derived("calciner.ta_face", "Vessel axis to the duct's face (y)", -ta["y_end"], "m",
                           [P["D_vessel"], stub])

    d_feed = pv.primary(g, "calciner.D_feed", "Meal pipe diameter (two)", key="calciner.D_feed")
    P["D_feed"] = d_feed
    P["D_fuel"] = pv.primary(g, "calciner.D_fuel", "Fuel pipe diameter (two)", key="calciner.D_fuel")
    P["fuel_slope"] = pv.primary(g, "calciner.fuel_slope", "Fuel pipes' slope to the horizontal",
                                 key="calciner.fuel_slope")

    # the dispersion boxes under the meal pipes (model values read off a manufacturer's image, calciner.md)
    mb = inl["meal"]
    wk = pv.primary(g, "dispersion_box.width_over_D_feed", "Dispersion box width over D_feed")
    P["box_width"] = pv.derived("calciner.box_width", "Dispersion box width (along the wall)", mb["width"], "m", [d_feed, wk])
    bhk = pv.primary(g, "dispersion_box.back_height_over_D_feed", "Box back face height over D_feed")
    P["box_back_h"] = pv.derived("calciner.box_back_h", "Dispersion box back face height", mb["back_h"], "m", [d_feed, bhk])
    sl = pv.primary(g, "dispersion_box.floor_slope_deg", "Box floor ramp to the horizontal")
    P["box_height"] = pv.derived("calciner.box_height", "Dispersion box open face height", mb["height"], "m",
                                 [P["box_back_h"], sl, pv.primary(g, "dispersion_box.depth_over_D_feed", "Box depth over D_feed")])
    P["box_rise"] = pv.primary(g, "dispersion_box.pipe_rise", "Meal pipe's rise over the box", key="calciner.box_rise")

    P["volume"] = pv.derived("calciner.volume", "Volume (cone + cylinder)", cal["vessel_volume"], "m3",
                             [P["D_vessel"], P["H_vessel"], P["D_throat"], cone])
    P["wet_area"] = pv.derived("calciner.wet_area", "Wetted area (cylinder, cone, roof ring)",
                               cal["vessel_wall_area"], "m2",
                               [P["D_vessel"], P["H_vessel"], P["D_throat"], cone, P["D_neck"]])

    doc = P["D_vessel"].doc
    P["u_wall"] = pv.unknown("calciner.shell", "Shell / refractory thickness",
                             f"{doc}: CFD fluid volume, no structure modelled")
    P["u_material"] = pv.unknown("calciner.material", "Material", f"{doc}: no source")
    P["u_flange"] = pv.unknown("calciner.flanges", "Flanges / nozzles / manholes", f"{doc}: no source")
    P["u_support"] = pv.unknown("calciner.supports", "Supports / hangers", f"{doc}: no source")
    P["u_burner"] = pv.unknown("calciner.burner", "Burner / fuel inlet fittings",
                               f"{doc}: the fuel pipes are bare inlet ducts, no burner geometry")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
