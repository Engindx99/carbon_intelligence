"""The cyclone's dimension table, read back out of its solid.

The generic B-rep queries live in geometry/measure.py because every
unit needs them. What is here is the one thing that is specific to a
cyclone: which recovered surface stands for which named dimension.
"""

from .. import measure


def measure_cyclone(envelope, spec):
    """(quantity, from_cad, from_spec, unit) rows for one cyclone.

    Whoever reads the table can see the two columns disagree without
    knowing anything about CadQuery.
    """

    bb = envelope.BoundingBox()
    radii = measure.cylinder_radii(envelope)
    angles = measure.cone_half_angles_deg(envelope)

    r_body = 0.5 * spec.D_body
    r_dipleg = 0.5 * spec.dipleg_diameter
    r_vf_in = 0.5 * spec.vortex_finder_diameter
    r_vf_out = r_vf_in + spec.vortex_finder_wall_thickness_m

    return [
        ("Total height", bb.zlen, spec.total_height, "m"),
        ("Datum (dipleg discharge)", bb.zmin, 0.0, "m"),
        ("Body radius", measure.nearest(radii, r_body), r_body, "m"),
        ("Dipleg radius", measure.nearest(radii, r_dipleg), r_dipleg, "m"),
        (
            "Vortex finder bore radius",
            measure.nearest(radii, r_vf_in),
            r_vf_in,
            "m",
        ),
        (
            "Vortex finder outer radius",
            measure.nearest(radii, r_vf_out),
            r_vf_out,
            "m",
        ),
        (
            "Cone half-angle",
            angles[0] if angles else float("nan"),
            spec.cone_half_angle_deg,
            "deg",
        ),
    ]
