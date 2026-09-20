"""Ducts, for any unit that has to connect two things.

A pipe here is a circular bore swept along a polyline centre-line:
cylinders for the straight runs, and a sphere of the same radius fused
at each interior corner so the elbow closes and the whole run comes
back as ONE solid rather than as segments that merely touch at a point.

That is crude next to a real bend, and deliberately so. At this stage
the question is WHERE things connect, not what the pipe stress is, and
a mitred elbow made of primitives has an analytic volume, no sweep
frame to twist and no loft to self-intersect.

The centre-lines come from a unit's own layout module, which computes
them without a CAD kernel. This module only turns points into solids.
"""

import cadquery as cq
from cadquery import Vector


def pipe(path, diameter):
    """One solid along `path`, a list of (x, y, z) in metres."""

    if len(path) < 2:
        raise ValueError(f"a pipe needs at least two points, got {len(path)}")

    if diameter <= 0.0:
        raise ValueError(f"pipe diameter must be positive, got {diameter}")

    radius = 0.5 * diameter
    bodies = []

    for a, b in zip(path, path[1:]):

        direction = Vector(b[0] - a[0], b[1] - a[1], b[2] - a[2])
        length = direction.Length

        if length <= 0.0:
            raise ValueError(
                f"duct centre-line has a zero-length segment at {a}"
            )

        bodies.append(
            cq.Solid.makeCylinder(
                radius, length, Vector(*a), direction.normalized()
            )
        )

    for corner in path[1:-1]:
        bodies.append(
            cq.Solid.makeSphere(
                radius,
                Vector(*corner),
                angleDegrees1=-90,
                angleDegrees2=90,
                angleDegrees3=360,
            )
        )

    solid = bodies[0]

    for body in bodies[1:]:
        solid = solid.fuse(body)

    return solid.clean()


def path_length(path):
    """Centre-line length [m]."""

    return sum(
        sum((b[i] - a[i]) ** 2 for i in range(3)) ** 0.5
        for a, b in zip(path, path[1:])
    )
