"""Every zone of the twin computes over its equipment's fluid volume
(geometry/fluid_volumes.md), the volume its one geometry source gives.

The volumes and wall areas are derived in geometry/plant_geometry.py
from geometry/plant_geometry.yaml (single-source rule, user decision
13-14 Oct 2026); the zones' own cells must add up to them. The
derivations themselves are held to the documented figures in
tests/test_plant_geometry.py.

The plant is two identical 2500 t/d strings solved as one string at
the total flow, so per-string equipment counts twice.
"""

import math
import unittest

import numpy as np

import main
from geometry import plant_geometry as pg
from tests.twin_harness import REPO_ROOT


G = pg.load()
STRINGS = pg.v(G["plant"]["strings"])

# Twin stage i (0-based) is C(4 - i) with the riser below it: R4..R2
# the CFD outlet pipes of C5..C3, R1 C2's outlet, R1 and the twin
# branches (user decision, 14 Oct 2026).
RISER = {k: pg.stage_riser(G, k) for k in (2, 3, 4)}
RISER[1] = pg.r1_path(G)
CYCLONE = {s: pg.cyclone(G, f"C{s}") for s in range(1, 6)}

PREHEATER_STAGES = [
    STRINGS * (RISER[c]["volume"] + CYCLONE[c]["per_string"] * CYCLONE[c]["volume"])
    for c in (4, 3, 2, 1)
]
PREHEATER_WALLS = [
    STRINGS * (RISER[c]["wall_area"] + CYCLONE[c]["per_string"] * CYCLONE[c]["wet_area"])
    for c in (4, 3, 2, 1)
]

# The calciner zone: the vessel above the meal feed, the gooseneck to the
# C5 inlets, the C5s
C5_ALL = STRINGS * CYCLONE[5]["per_string"] * CYCLONE[5]["volume"]
CALCINER = pg.calciner_above_feed(G)["volume"]
GOOSENECK = pg.gooseneck_plant(G)["volume"]

KILN = pg.kiln(G)
COOLER_BOX = pg.cooler(G)["box_volume"]

RTOL = 1e-3


def _cylinder(D, L):
    return math.pi * D**2 / 4.0 * L


def _cfg():
    return main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")


class EveryZoneComputesOverItsVolumeTest(unittest.TestCase):

    def setUp(self):
        self.cfg = _cfg()
        self.N = self.cfg["plant"]["N"]

    def _cells(self, zone, cells):
        return np.broadcast_to(np.asarray(zone.V_cell, dtype=float), (cells,))

    def _volume(self, zone, cells):
        return float(self._cells(zone, cells).sum())

    def test_the_kiln_tube(self):
        transition = main.Transition(
            N=self.N, L=self.cfg["transition"]["length"], cfg=self.cfg
        )
        burning = main.Burning(
            N=self.N, L=self.cfg["kiln"]["length"], cfg=self.cfg
        )
        L_t = self.cfg["transition"]["length"]

        self.assertAlmostEqual(
            self._volume(transition, self.N),
            _cylinder(KILN["D"], L_t),
            delta=RTOL * _cylinder(KILN["D"], L_t),
        )
        self.assertAlmostEqual(
            self._volume(transition, self.N) + self._volume(burning, self.N),
            KILN["volume"],
            delta=RTOL * KILN["volume"],
        )

    def test_the_cooler_casing(self):
        cooler = main.Cooler(
            N=self.N, L=self.cfg["cooler"]["length"], cfg=self.cfg
        )
        box = cooler.L * cooler.width * cooler.casing_height
        self.assertAlmostEqual(box, COOLER_BOX, delta=RTOL * COOLER_BOX)

    def test_the_preheater_stages(self):
        preheater = main.Preheater(
            L=self.cfg["preheater"]["length"],
            nodes_per_stage=self.cfg["preheater"]["nodes_per_stage"],
            cfg=self.cfg,
        )
        V = self._cells(preheater, len(preheater.stages))
        for i, (twin, doc) in enumerate(zip(V, PREHEATER_STAGES)):
            with self.subTest(stage=i + 1):
                self.assertAlmostEqual(twin, doc, delta=RTOL * doc)
        A = np.broadcast_to(np.asarray(preheater.A_wall_cell, dtype=float), V.shape)
        for i, (twin, doc) in enumerate(zip(A, PREHEATER_WALLS)):
            with self.subTest(stage_wall=i + 1):
                self.assertAlmostEqual(twin, doc, delta=RTOL * doc)

    def test_the_calciner_and_gooseneck(self):
        calciner = main.Calciner(
            N=self.N, L=self.cfg["calciner"]["length"], cfg=self.cfg
        )
        # The calciner zone runs from its inlet through the
        # gooseneck to the C5s, its outlet cyclones.
        doc = CALCINER + GOOSENECK + C5_ALL
        cells = np.size(calciner.V_cell) if np.ndim(calciner.V_cell) else self.N
        self.assertAlmostEqual(
            self._volume(calciner, cells),
            doc,
            delta=RTOL * doc,
        )


class EquipmentWithoutAVolumeTest(unittest.TestCase):
    """Pure handoffs in the twin, for want of a source. Listed here so
    'every piece of equipment' is a checked claim, not a hope; adding
    one as a zone means moving it out of this list."""

    def test_the_ledger_lists_them(self):
        text = (REPO_ROOT / "geometry" / "fluid_volumes.md").read_text(
            encoding="utf-8"
        )
        for name in (
            "Tersiyer hava kanalı",
            "Fırın başlığı",
            "Fırın giriş odası",
            "Soğutucu vent'i",
            "Farin boruları",
        ):
            with self.subTest(equipment=name):
                self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
