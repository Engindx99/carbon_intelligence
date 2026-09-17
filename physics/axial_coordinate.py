import numbers
from dataclasses import dataclass

import numpy as np


# ======================================================
# GLOBAL AXIAL COORDINATE
#
# One continuous coordinate z [m] along the SOLID flow path:
#
#   z = 0  : raw meal feed inlet of the preheater (Stage 5)
#   z = L  : clinker discharge of the cooler
#
# Units are laid end to end in solid flow order; gas travels
# in -z. Each unit keeps its own local mesh (L, N, dz); this
# module only places those meshes on the shared axis and does
# not feed back into any solver.
#
# The preheater is a cascade of lumped cyclone stages, so its
# segment is an equivalent solid path length (the same L that
# sizes the stage volumes), split into N equal stage segments.
# ======================================================

SOLID_FLOW_ZONE_ORDER = (
    "preheater",
    "calciner",
    "transition",
    "burning",
    "cooler",
)

# Zones whose state arrays are indexed against the solid flow
# (solid moves from index N-1 to index 0).
SOLID_INDEX_REVERSED_ZONES = ("preheater",)


@dataclass(frozen=True)
class AxialSegment:

    zone: str
    z_start: float                  # m
    L: float                        # m
    N: int
    solid_index_reversed: bool = False

    @property
    def z_end(self):
        return self.z_start + self.L

    @property
    def dz(self):
        return self.L / self.N

    @property
    def z_faces(self):
        # N+1 cell faces, increasing along the solid path [m]
        return self.z_start + np.arange(self.N + 1) * self.dz

    @property
    def z_centers(self):
        # N cell centres, increasing along the solid path [m]
        return self.z_start + (np.arange(self.N) + 0.5) * self.dz

    @property
    def z_at_index(self):
        # Cell centre of state-array index i [m], in array order
        z = self.z_centers
        return z[::-1] if self.solid_index_reversed else z


def build_axial_layout(
    lengths,
    cell_counts,
    reversed_zones=SOLID_INDEX_REVERSED_ZONES,
):

    layout = {}
    z_start = 0.0

    for zone in SOLID_FLOW_ZONE_ORDER:

        if zone not in lengths or zone not in cell_counts:
            raise ValueError(f"axial layout: missing length or cell count for '{zone}'")

        L = float(lengths[zone])
        N = cell_counts[zone]

        if not np.isfinite(L) or L <= 0.0:
            raise ValueError(f"axial layout: '{zone}' length must be > 0 m, got {L}")

        if isinstance(N, bool) or not isinstance(N, numbers.Integral) or N < 1:
            raise ValueError(f"axial layout: '{zone}' cell count must be an integer >= 1, got {N}")

        segment = AxialSegment(
            zone=zone,
            z_start=z_start,
            L=L,
            N=int(N),
            solid_index_reversed=zone in reversed_zones,
        )

        layout[zone] = segment
        z_start = segment.z_end

    return layout


def total_length(layout):

    return layout[SOLID_FLOW_ZONE_ORDER[-1]].z_end
