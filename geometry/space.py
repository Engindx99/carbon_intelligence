"""Distances between centre-lines in space, for any unit with ducts.

WHY A FLUID VOLUME CARES. The solid this package builds is the WETTED
envelope -- its volume is the gas volume -- and the tower is the union
of the vessels and the ducts. A union cannot tell an intended junction
from an accidental crossing: two passages that overlap anywhere become
one passage, so the CFD domain silently gains a short circuit between
a gas riser and a meal line that in the plant are separated by steel.
Nothing downstream notices, because the fuse still returns one solid
and one solid is what "the tower connects" is read from. This module
is what notices.

It is not about erection room, flanges or access. A gap of a few
centimetres outside the domain costs a CFD mesh nothing, because the
gap is not meshed. Interference costs it the topology.

`geometry/plan.py` answers "how close do these two things come when you
look down on them", and that is the right question for deciding where a
vessel stands. It is the WRONG question for two ducts. Two pipes can
share a patch of plan and miss each other by twenty metres of height,
and two pipes can be far apart in plan at the level where one of them
actually is. Asking the plan question about ducts is how the preheater
came to have four collisions nobody could see:

    the dipleg drop from stage n ran straight through the elbow that
    turns riser n+1 into the mouth of stage n+1, 1.657 m of interference
    each, and then joined that same riser properly nine metres lower

-- so the meal line crossed its riser TWICE. Every plan check passed,
because in plan the two really are close and are SUPPOSED to be: they
join. The fusion passed too, because a duct that runs through the duct
it joins still fuses into one solid. Only a distance that knows about z
can tell the joint from the collision.

PURE PYTHON, no CAD kernel, like `plan`. The check has to run in the
same environment as the twin, and it has to run on centre-lines rather
than on built solids, because it is what decides whether building them
is worth trying.

Everything here is 3-D. Points are (x, y, z) triples.
"""

import math


def segment_segment_distance(a, b, c, d):
    """Shortest distance between segments [a, b] and [c, d] in space.

    Exact, not sampled. The two infinite lines have a unique closest
    pair unless they are parallel; clamping those parameters to [0, 1]
    and then re-projecting each clamped endpoint onto the other segment
    is what makes it right for SEGMENTS, which is the case that matters
    here -- duct legs are short and their nearest approach is usually at
    an end.
    """

    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = d[0] - c[0], d[1] - c[1], d[2] - c[2]
    wx, wy, wz = a[0] - c[0], a[1] - c[1], a[2] - c[2]

    uu = ux * ux + uy * uy + uz * uz
    uv = ux * vx + uy * vy + uz * vz
    vv = vx * vx + vy * vy + vz * vz
    uw = ux * wx + uy * wy + uz * wz
    vw = vx * wx + vy * wy + vz * wz

    denominator = uu * vv - uv * uv

    if denominator > 1.0e-12 * uu * vv:
        s = (uv * vw - vv * uw) / denominator
        t = (uu * vw - uv * uw) / denominator
    else:
        # Parallel: any s does, so start from one end and let the
        # clamping below find the overlap.
        s, t = 0.0, (vw / vv if vv > 0.0 else 0.0)

    s = 0.0 if s < 0.0 else (1.0 if s > 1.0 else s)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

    # Re-project each clamped point onto the other segment, or a
    # clamped pair that is not actually the closest pair survives.
    for _pass in range(2):

        p = (a[0] + s * ux, a[1] + s * uy, a[2] + s * uz)
        t = _project(p, c, (vx, vy, vz), vv)

        q = (c[0] + t * vx, c[1] + t * vy, c[2] + t * vz)
        s = _project(q, a, (ux, uy, uz), uu)

    p = (a[0] + s * ux, a[1] + s * uy, a[2] + s * uz)
    q = (c[0] + t * vx, c[1] + t * vy, c[2] + t * vz)

    return math.dist(p, q)


def _project(point, origin, direction, span):
    """Where `point` lands on a segment, as a fraction clamped to it."""

    if span <= 0.0:
        return 0.0

    t = sum(
        (point[i] - origin[i]) * direction[i] for i in range(3)
    ) / span

    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)


def point_segment_distance(point, a, b):
    """Shortest distance from a point to a segment [a, b] in space."""

    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    span = dx * dx + dy * dy + dz * dz

    t = _project(point, a, (dx, dy, dz), span)

    return math.dist(point, (a[0] + t * dx, a[1] + t * dy, a[2] + t * dz))


def legs(path):
    """A polyline's segments, as (index, start, end)."""

    return [
        (index, first, second)
        for index, (first, second) in enumerate(zip(path, path[1:]))
    ]


JOIN_TOLERANCE = 1.0e-6


def is_junction(first, i, second, j, tolerance=JOIN_TOLERANCE):
    """Do LEG i of `first` and LEG j of `second` meet at a path's end?

    PER LEG, NEVER PER PATH, and that distinction is the whole point.
    A whitelist keyed on a pair of names says "these two are allowed
    to touch" and then cannot say WHERE, so it excuses the junction
    and the crossing alike. Saying it per PATH -- "these two paths
    meet at an end somewhere" -- is the same mistake spelt
    geometrically: the meal line really does end on its riser, and
    that fact would excuse it for passing through the same riser nine
    metres higher up on the way. Only the leg that actually CARRIES
    the end is a junction; every other approach between the two is a
    crossing, whatever their names.

    Every real junction in a preheater is the end of a duct landing on
    another: a riser leaves an outlet and enters a mouth, a meal line
    leaves a dipleg and lands on a riser. So the test is that an end
    of one path lies on the other path's leg AND belongs to the leg
    being excused.
    """

    for index, end in ((0, first[0]), (len(first) - 2, first[-1])):
        if i == index and point_segment_distance(
                end, second[j], second[j + 1]) <= tolerance:
            return True

    for index, end in ((0, second[0]), (len(second) - 2, second[-1])):
        if j == index and point_segment_distance(
                end, first[i], first[i + 1]) <= tolerance:
            return True

    return False


def interferences(ducts, clearance=0.0):
    """Every pair of duct legs too close, junctions excepted.

    `ducts` is [(name, path, diameter)]. Two flow passages that come
    closer than their two bores allow are not two passages any more:
    the union that the fluid volume is built as merges them, and the
    CFD domain gains a short circuit between, say, a gas riser and a
    meal line that in the plant are separated by steel.

    Yields (name_a, i, name_b, j, gap) with `gap` the distance left
    between the two BORES -- negative is interference. Exact in 3-D,
    because the question is 3-D: two ducts can share a patch of plan
    and miss each other by twenty metres of height.
    """

    out = []

    for index, (name_a, path_a, bore_a) in enumerate(ducts):
        for name_b, path_b, bore_b in ducts[index + 1:]:

            need = 0.5 * bore_a + 0.5 * bore_b + clearance

            for i, a0, a1 in legs(path_a):
                for j, b0, b1 in legs(path_b):

                    if is_junction(path_a, i, path_b, j):
                        continue

                    gap = segment_segment_distance(a0, a1, b0, b1) - need

                    if gap < 0.0:
                        out.append((name_a, i, name_b, j, gap))

    return out
