"""The preheater tower: which lines can be assembled, and why not.

A single-string tower as one continuous fluid volume needs, from the
catalogue:

    C1..C5      every cyclone dimension (properties.CYCLONE_FIELDS)
    R1..R4      diameter and length of each riser
    gooseneck   diameter and length (calciner -> C5)
    calciner    diameter and length

and, beyond the catalogue, a riser shape. The shape is open: the FLS
paper's text and its equations disagree (SOURCES.md, "Açık
belirsizlikler"), so no riser solid exists and none is assumed.

This module does not complete missing geometry. It lists what is
missing and refuses. No catalogue line is complete today:

    1500, 2500  riser lengths and the gooseneck length have no source
                (1500 also has no gooseneck diameter)
    5000        as 1500, and it is a double string, which the first
                tower builder does not take on
    FLS         no gooseneck at all

Not part of the tower, by decision (SOURCES.md): no tertiary air duct,
since the calciner base is the single inlet, and no meal pipes.

LAYOUT. Where the cyclones stand relative to each other is not an
equipment dimension either, and it is kept apart from the catalogue
in LayoutParams. It has no values yet: they will be set in the config
when a line becomes complete, and no layout is solved or optimised.
"""

from dataclasses import dataclass

from geometry.properties import CYCLONE_FIELDS


@dataclass(frozen=True)
class LayoutParams:
    """Topology choices of the tower model, not plant dimensions.

    cyclone_axis_offset_over_D
        horizontal distance between the axes of consecutive stages,
        x the lower stage's effective D
    riser_elbow_radius_over_D
        centre-line radius of a riser's bends, x the riser's D
    c1_split_angle_deg
        angle between the branches where R1 splits to a multi-cyclone C1
    """

    cyclone_axis_offset_over_D: float
    riser_elbow_radius_over_D: float
    c1_split_angle_deg: float


RISER_SHAPE_OPEN = (
    "riser shape is unresolved (SOURCES.md, Açık belirsizlikler); "
    "no riser solid is built"
)


class TowerIncomplete(ValueError):
    """The tower cannot be assembled from what the catalogue has."""

    def __init__(self, line_key, missing, blockers):
        self.missing = tuple(missing)
        self.blockers = tuple(blockers)

        parts = []

        if self.missing:
            parts.append("missing " + ", ".join(self.missing))

        parts += list(self.blockers)

        super().__init__(f"tower of line {line_key}: " + "; ".join(parts))


def required_fields(line):
    """Every catalogue field a single-string tower of `line` needs."""

    paths = []

    for c in line.cyclones:
        paths += [(f"C{c.stage}", c, n) for n in CYCLONE_FIELDS]

    for d in line.ducts:
        paths += [(d.name, d, n) for n in ("D", "length")]

    paths += [("gooseneck", line.gooseneck, n) for n in ("D", "length")]
    paths += [("calciner", line.calciner, n) for n in ("D", "length")]

    return paths


def missing_for_tower(line):
    """The required fields `line` has no value for, as 'part.field'."""

    return [
        f"{prefix}.{name}"
        for prefix, part, name in required_fields(line)
        if getattr(part, name) is None
    ]


def tower_blockers(line):
    """What stops the tower besides missing fields."""

    blockers = []

    if line.strings != 1:
        blockers.append(
            f"{line.strings} strings: the first tower builder takes a single string only"
        )

    blockers.append(RISER_SHAPE_OPEN)

    return blockers


def build_tower(line, cfd, layout):
    """The tower's fluid volume, or TowerIncomplete saying why not.

    Never reached today: every catalogue line is refused above. The
    assembly is written when a line is complete, not before.
    """

    missing = missing_for_tower(line)
    blockers = tower_blockers(line)

    if missing or blockers:
        raise TowerIncomplete(line.key, missing, blockers)

    raise NotImplementedError("tower assembly is not written: no line is complete")
