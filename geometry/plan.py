"""Distances in plan, for any unit that has to keep two things apart.

A tower's layout is decided in plan: whether a duct clears a vessel,
whether two vessels clear each other, how far a column has to stand
back. Those are all the same question -- how close do these two things
come when you look down on them -- and it is answered here once.

PURE PYTHON, no CAD kernel. The layout arithmetic that decides where
things go must run in the same environment as the twin, so that a
clearance can be checked without installing anything. The 3-D
collision check on the built solids is a different test answering a
different question: this one says whether a layout CAN be built, that
one says whether what was built is what the layout said.

Everything here is 2-D. Segments are (x, y) pairs; polygons are lists
of (x, y) that need not be closed -- the last vertex is joined back to
the first.
"""

import math


def point_segment_distance(point, a, b):
    """Shortest distance from a point to a segment [a, b]."""

    ax, ay = a
    bx, by = b
    px, py = point

    dx = bx - ax
    dy = by - ay

    span = dx * dx + dy * dy

    if span <= 0.0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * dx + (py - ay) * dy) / span
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def segments_cross(a, b, c, d):
    """True if [a, b] and [c, d] properly cross.

    Touching at an endpoint or lying along each other counts as not
    crossing; those cases are caught by the distance being zero, which
    is what the callers actually test.
    """

    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    d1 = side(a, b, c)
    d2 = side(a, b, d)
    d3 = side(c, d, a)
    d4 = side(c, d, b)

    return ((d1 > 0.0) != (d2 > 0.0)) and ((d3 > 0.0) != (d4 > 0.0))


def segment_segment_distance(a, b, c, d):
    """Shortest distance between two segments; 0 if they cross."""

    if segments_cross(a, b, c, d):
        return 0.0

    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def polyline_polyline_distance(first, second):
    """Shortest distance between two polylines."""

    return min(
        segment_segment_distance(a, b, c, d)
        for a, b in zip(first, first[1:])
        for c, d in zip(second, second[1:])
    )


def point_in_polygon(point, polygon):
    """Ray-crossing test. On the boundary is unspecified, as always."""

    px, py = point
    inside = False

    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):

        if (ay > py) != (by > py):

            x = ax + (py - ay) * (bx - ax) / (by - ay)

            if px < x:
                inside = not inside

    return inside


def polygon_point_distance(polygon, point):
    """Distance from a polygon to a point; NEGATIVE if it is inside.

    The sign is what makes this usable as a clearance: a caller can
    compare it against a required gap without first asking whether the
    point is in or out.
    """

    edge = min(
        point_segment_distance(point, a, b)
        for a, b in zip(polygon, polygon[1:] + polygon[:1])
    )

    return -edge if point_in_polygon(point, polygon) else edge


def polygon_segment_distance(polygon, a, b):
    """Distance from a polygon to a segment; 0 if the segment enters."""

    if point_in_polygon(a, polygon) or point_in_polygon(b, polygon):
        return 0.0

    return min(
        segment_segment_distance(a, b, p, q)
        for p, q in zip(polygon, polygon[1:] + polygon[:1])
    )


def polygon_polyline_distance(polygon, polyline):
    """Distance from a polygon to a polyline; 0 if the line enters."""

    return min(
        polygon_segment_distance(polygon, a, b)
        for a, b in zip(polyline, polyline[1:])
    )


def polygons_distance(first, second):
    """Distance between two polygons; 0 if they overlap at all."""

    if any(point_in_polygon(p, second) for p in first):
        return 0.0

    if any(point_in_polygon(p, first) for p in second):
        return 0.0

    return min(
        segment_segment_distance(a, b, c, d)
        for a, b in zip(first, first[1:] + first[:1])
        for c, d in zip(second, second[1:] + second[:1])
    )


def translate(polygon, dx, dy):
    return [(x + dx, y + dy) for x, y in polygon]


def rotate(polygon, angle_deg):
    """About the origin."""

    c = math.cos(math.radians(angle_deg))
    s = math.sin(math.radians(angle_deg))

    return [(c * x - s * y, s * x + c * y) for x, y in polygon]
