"""Primitive B-rep solids, the only place geometry/ touches CadQuery.

z is vertical, lengths in metres. The catalogue, the properties and
the report never import this module, so they run without CadQuery.
"""

import cadquery as cq
from cadquery import Vector


UP = Vector(0, 0, 1)


def cylinder(D, length, z0=0.0):
    """Vertical cylinder on the z axis from z0 to z0 + length."""

    return cq.Solid.makeCylinder(0.5 * D, length, Vector(0, 0, z0), UP)


def frustum(D_bottom, D_top, length, z0=0.0):
    """Vertical truncated cone on the z axis from z0 to z0 + length."""

    return cq.Solid.makeCone(0.5 * D_bottom, 0.5 * D_top, length, Vector(0, 0, z0), UP)


def tube(D_outer, D_inner, length, z0=0.0):
    """Vertical annular tube on the z axis from z0 to z0 + length."""

    return cylinder(D_outer, length, z0).cut(cylinder(D_inner, length, z0))


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box between the given bounds."""

    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, Vector(x0, y0, z0))


def fuse(*solids):
    """One solid from overlapping solids."""

    out = solids[0]

    for s in solids[1:]:
        out = out.fuse(s)

    return out.clean()
