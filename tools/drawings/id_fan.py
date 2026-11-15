"""The ID fan's drawing values (one string's preheater ID fan: rotor,
volute, inlet box and cone): every value geometry/macros/drawings.bas
shows or lists, with where it comes from and how far to trust it (same
scheme as cyclone.py).

The solid is id_fan.SLDPRT (id_fan.bas), three bodies: y along the fan's
axis (the hub's plane y = 0, the eye at y = b1), x horizontal (the
discharge runs to -x at the top), z up; the impeller turns from +x
towards +z.
"""

from geometry import plant_geometry as pg

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the CFD solid really has: the outlet face's edges (width
# B, height), the inlet box's face edges, and on the rotor alone the eye's
# and the tip's circles (D1, D2) and the rim's axial width b2 (circle
# centres on the axis). b1 is listed only: the shroud rises from the eye
# to the tip (b2 > b1), so the eye's circle is hidden in every outside view. The spiral, the blade arcs and the angles have
# no straight or circular edge to measure: listed only.
DIMENSIONED = ("D2", "D1", "b2", "B", "h_stub", "H_box", "depth_box")

ALSO = {}

# Table order on the sheet.
ORDER = (
    "D2", "D1", "b1", "b2", "z", "beta1", "beta2", "blade_t", "blade_arc_R",
    "B", "r3", "nose_R", "spiral_deg", "r_end", "h_stub", "l_stub", "gamma", "r_mrf",
    "D_cone", "L_cone", "H_box", "depth_box", "reach_box",
    "q", "dp", "speed", "u_out", "V_rotor", "V_volute", "V_inlet",
    "u_casing", "u_shaft", "u_damper", "u_gaps", "u_material",
)


def params(g, name="id_fan"):
    """{short key: Param} for the ID fan (name is the sheet's, unused)."""
    f = pg.id_fan(g)
    P = {}

    def prim(field, label):
        return pv.primary(g, f"id_fan.{field}", label, key=f"id_fan.{field}")

    duty = [prim("exhaust_flow_per_string", "Exhaust flow"), prim("exhaust_T", "Exhaust temperature"),
            prim("exhaust_molar_mass", "Molar mass"), prim("inlet_underpressure", "Inlet underpressure")]
    dp = prim("total_pressure", "Total pressure rise")
    psi = prim("pressure_coefficient", "Pressure coefficient")
    speed = prim("speed", "Speed")
    eye = prim("eye_ratio", "Eye ratio D1/D2")
    beta2 = prim("blade_outlet_angle", "Blade outlet angle")
    kz = prim("blade_number_coeff", "Blade number coefficient")
    t = prim("blade_thickness", "Blade thickness")
    inc = prim("incidence", "Incidence")
    eta_h = prim("hydraulic_efficiency", "Hydraulic efficiency")
    wb = prim("volute_width_ratio", "Volute width / b2")
    gap = prim("tongue_gap_ratio", "Tongue gap / D2")
    nose = prim("tongue_radius_ratio", "Tongue nose radius / D2")
    mrf = prim("mrf_gap_fraction", "MRF rim share of the gap")
    stub = prim("outlet_stub_ratio", "Discharge length / height")
    cone_in = prim("cone_inlet_ratio", "Cone mouth / D1")
    plate = prim("side_plate_gap", "Front plate gap")
    c_out = prim("volute_outlet_velocity", "Volute outlet velocity")
    gam = prim("discharge_angle", "Discharge angle up from the horizontal")
    box_a = prim("inlet_box_area_ratio", "Box face / eye area")
    box_h = prim("inlet_box_height_ratio", "Box height / cone mouth")
    box_r = prim("inlet_box_reach_ratio", "Box reach / cone mouth")

    d2_in = duty + [dp, psi, speed]
    imp = d2_in + [eye, beta2, kz, t, inc, eta_h]
    vol = imp + [wb, gap, nose, c_out]

    P["D2"] = pv.derived("id_fan.D2", "Impeller diameter D2 (tip speed / pi n)", f["D_impeller"], "m", d2_in)
    P["D1"] = pv.derived("id_fan.D1", "Eye diameter D1 (0.70 D2)", f["D_inlet"], "m", d2_in + [eye])
    P["b1"] = pv.derived("id_fan.b1", "Blade height at the eye b1 (c_m1 = c0)", f["b1"], "m", d2_in + [eye])
    P["b2"] = pv.derived("id_fan.b2", "Outlet width b2 (Euler, Wiesner slip, continuity)", f["b2"], "m", imp)
    P["z"] = pv.derived("id_fan.z", "Blades z = 8.5 sin(beta2) / (1 - D1/D2)", f["z"], "-", [kz, beta2, eye])
    P["beta1"] = pv.derived("id_fan.beta1", "Blade inlet angle beta1 (from the tangent)", round(f["beta1"], 2), "deg", imp)
    P["beta2"] = beta2
    P["blade_t"] = t
    P["blade_arc_R"] = pv.derived("id_fan.blade_arc_R", "Blade: single circular arc, radius", f["blade_arc_R"], "m", imp)
    P["B"] = pv.derived("id_fan.B", "Volute width B (3 b2)", f["B"], "m", imp + [wb])
    P["r3"] = pv.derived("id_fan.r3", "Tongue circle r3 (r2 + 0.075 D2)", f["r3"], "m", d2_in + [gap])
    P["nose_R"] = pv.derived("id_fan.nose_R", "Tongue nose radius", f["tongue_radius"], "m", d2_in + [nose])
    P["spiral_deg"] = pv.derived("id_fan.spiral", "Log spiral angle (outlet at 30 m/s)", round(f["spiral_angle"], 2), "deg", vol)
    P["r_end"] = pv.derived("id_fan.r_end", "Spiral end radius", f["r_end"], "m", vol)
    P["h_stub"] = pv.derived("id_fan.h_stub", "Outlet height (spiral end cos(alpha) - 2 nose R)", f["h_stub"], "m", vol)
    P["l_stub"] = pv.derived("id_fan.l_stub", "Straight discharge length", f["l_stub"], "m", vol + [stub])
    P["r_mrf"] = pv.derived("id_fan.r_mrf", "Rotating (MRF) zone radius", f["r_mrf"], "m", d2_in + [gap, mrf])
    P["D_cone"] = pv.derived("id_fan.D_cone", "Inlet cone mouth diameter", f["D_cone"], "m", d2_in + [eye, cone_in])
    P["L_cone"] = pv.derived("id_fan.L_cone", "Inlet cone length (eye to the box, through the plate)", f["L_cone"], "m",
                             imp + [wb, plate])
    P["gamma"] = gam
    P["H_box"] = pv.derived("id_fan.H_box", "Inlet box height (z)", f["H_box"], "m", d2_in + [eye, cone_in, box_h])
    P["depth_box"] = pv.derived("id_fan.depth_box", "Inlet box depth (y): face area 1.75 x eye", f["depth_box"], "m",
                                d2_in + [eye, cone_in, box_h, box_a])
    P["reach_box"] = pv.derived("id_fan.reach_box", "Inlet box face from the axis (x)", f["reach_box"], "m",
                                d2_in + [eye, cone_in, box_r])
    P["q"] = pv.derived("id_fan.q", "Volume flow at the inlet (one string)", round(f["q"], 2), "m3/s", duty)
    P["dp"] = dp
    P["speed"] = speed
    P["u_out"] = pv.derived("id_fan.u_out", "Outlet velocity", round(f["u_out"], 1), "m/s", vol)
    P["V_rotor"] = pv.derived("id_fan.V_rotor", "Volume: rotating zone (bladed)", f["V_rotor_bladed"], "m3", imp + [mrf])
    P["V_volute"] = pv.derived("id_fan.V_volute", "Volume: volute + discharge", f["V_volute"], "m3", vol + [mrf, stub])
    P["V_inlet"] = pv.derived("id_fan.V_inlet", "Volume: inlet cone + box", f["V_cone"] + f["V_box"], "m3",
                              imp + [wb, plate, cone_in, box_a, box_h, box_r])
    doc = P["D2"].doc
    P["u_casing"] = pv.unknown("id_fan.casing", "Casing / plate thickness", f"{doc}: fluid volume only")
    P["u_shaft"] = pv.unknown("id_fan.shaft", "Shaft, hub boss, bearings", f"{doc}: not modelled")
    P["u_damper"] = pv.unknown("id_fan.damper", "Inlet damper / IGV (VFD assumed)", f"{doc}: not modelled")
    P["u_gaps"] = pv.unknown("id_fan.gaps", "Seal gap cone-shroud, disc cavities", f"{doc}: not in the flow path")
    P["u_material"] = pv.unknown("id_fan.material", "Material, wear liners", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
