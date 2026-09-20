"""Reading dimensions back OUT of a finished solid.

Shared by every unit. The point is that none of it trusts the builder:
it queries the B-rep and reports what is actually there, so a unit's
verification compares its spec against the geometry rather than against
the code that was supposed to produce it.

HOW A DIMENSION IS RECOVERED
----------------------------
Not from the bounding box, which only sees the outside. OCCT keeps the
analytic surface behind every face, so a cylindrical face still knows
its own radius and a conical face still knows its own half-angle:

    face.geomType()  ->  'PLANE' | 'CYLINDER' | 'CONE' | 'BSPLINE'
    BRepAdaptor_Surface(face.wrapped).Cylinder().Radius()
    BRepAdaptor_Surface(face.wrapped).Cone().SemiAngle()

That is worth knowing when choosing how to draw something: a frustum
made with `makeCone` keeps an analytic conical surface and its angle
can be read back, while the same frustum made with `loft` becomes a
B-spline and its angle cannot be recovered at all.

Heights come from the z of the planar faces, again not from the box.
"""

import math

from OCP.BRepAdaptor import BRepAdaptor_Surface


TOL = 1.0e-7


def _dedupe(values, tol=TOL):
    """Collapse values that agree to `tol`, keeping them sorted."""

    out = []

    for v in sorted(values):
        if not out or abs(v - out[-1]) > tol:
            out.append(v)

    return out


def cylinder_radii(shape):
    """Every distinct cylindrical radius in the solid [m]."""

    radii = [
        BRepAdaptor_Surface(f.wrapped).Cylinder().Radius()
        for f in shape.Faces()
        if f.geomType() == "CYLINDER"
    ]

    return _dedupe(radii)


def cone_half_angles_deg(shape):
    """Every distinct conical half-angle in the solid [deg]."""

    angles = [
        math.degrees(abs(BRepAdaptor_Surface(f.wrapped).Cone().SemiAngle()))
        for f in shape.Faces()
        if f.geomType() == "CONE"
    ]

    return _dedupe(angles, tol=1.0e-6)


def planar_face_heights(shape):
    """z of every face whose plane is horizontal [m].

    These are a vessel's decks -- a discharge, a roof, a floor -- and
    heights are differences between them.
    """

    heights = []

    for f in shape.Faces():

        if f.geomType() != "PLANE":
            continue

        normal = f.normalAt()

        if abs(abs(normal.z) - 1.0) > 1.0e-9:
            continue

        heights.append(f.Center().z)

    return _dedupe(heights)


def topology(shape):
    """The 'no stray bodies' facts, as numbers."""

    return {
        "solids": len(shape.Solids()),
        "shells": len(shape.Shells()),
        "faces": len(shape.Faces()),
        "valid": bool(shape.isValid()),
        "volume": float(shape.Volume()),
        "area": float(shape.Area()),
    }


def nearest(values, target):
    """The value closest to `target`, or nan when there are none."""

    if not values:
        return float("nan")

    return min(values, key=lambda v: abs(v - target))


def format_measurements(rows):
    """A (quantity, from_cad, from_spec, unit) table as text."""

    out = [
        f"  {'quantity':<28}{'from CAD':>12}{'from spec':>12}  unit",
        "  " + "-" * 58,
    ]

    for name, cad, spec_value, unit in rows:
        out.append(f"  {name:<28}{cad:>12.5f}{spec_value:>12.5f}  {unit}")

    return "\n".join(out)
