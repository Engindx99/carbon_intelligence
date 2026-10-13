"""Every zone of the twin computes over its equipment's fluid volume
(geometry/fluid_volumes.md).

Each documented volume below is re-derived here from the dimensions
in its geometry doc, not read back from the model, and the zone's
own cells must add up to it. Rows the twin does not meet yet are
marked expectedFailure: they are the plan's open steps, and an
unexpected success is the signal to remove the mark.

The plant is two identical 2500 t/d strings solved as one string
at the total flow, so per-string equipment counts twice.
"""

import math
import unittest

import numpy as np

import main
from tests.twin_harness import REPO_ROOT


STRINGS = 2


def _cylinder(D, L):
    return math.pi * D**2 / 4.0 * L


def _cyclone(D, h_body, h_cone, D_dust):
    """Body + cone (frustum down to the dust outlet)."""
    R, r = D / 2.0, D_dust / 2.0
    return math.pi * R**2 * h_body + math.pi * h_cone / 3.0 * (
        R**2 + R * r + r**2
    )


# geometry/preheater/riser_R*.md: published bore x FLS h_tot
RISER = {
    1: _cylinder(3.07, 21.38),
    2: _cylinder(3.35, 19.38),
    3: _cylinder(3.45, 20.37),
    4: _cylinder(3.60, 19.87),
}

# geometry/preheater/cyclone_C*.md, body + cone. C2-C4 on the CFD
# body (h = D, user decision 13 Oct 2026), C5 = C4 x 6.50/6.30.
CYCLONE = {
    1: _cyclone(4.32, 6.79, 4.65, 0.40),
    2: _cyclone(6.30, 6.30, 7.30, 0.81),
    3: _cyclone(6.30, 6.30, 7.30, 0.81),
    4: _cyclone(6.30, 6.30, 7.30, 0.81),
    5: _cyclone(6.50, 6.50, 7.532, 0.836),
}
CYCLONES_PER_STRING = {1: 2, 2: 1, 3: 1, 4: 1, 5: 1}

# Twin stage i (0-based) is C(5 - i), fed by the riser below it;
# C5 is fed by a gooseneck branch, which belongs to the calciner.
PREHEATER_STAGES = [
    STRINGS * (
        RISER.get(c, 0.0) + CYCLONES_PER_STRING[c] * CYCLONE[c]
    )
    for c in (5, 4, 3, 2, 1)
]

# geometry/calciner/calciner.md: 65 deg cone + cylinder
CALCINER = 1009.71
# geometry/preheater/gooseneck.md
GOOSENECK = 833.768

# geometry/kiln/kiln.md
KILN_D, KILN_L = 4.8, 74.0
# geometry/cooler/cooler.md
COOLER_BOX = 29.90 * 4.0 * 3.0

RTOL = 1e-3


def _cfg():
    return main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")


class TheDocumentedVolumesTest(unittest.TestCase):
    """The re-derivations agree with the numbers the docs print."""

    def test_the_cyclone_docs(self):
        self.assertAlmostEqual(CYCLONE[1], 124.54, delta=0.01)
        self.assertAlmostEqual(CYCLONE[4], 283.2, delta=0.1)
        self.assertAlmostEqual(CYCLONE[5], 311.0, delta=0.1)

    def test_the_preheater_stages(self):
        self.assertAlmostEqual(PREHEATER_STAGES[0], 622.0, delta=0.5)
        self.assertAlmostEqual(PREHEATER_STAGES[1], 970.9, delta=0.5)
        self.assertAlmostEqual(PREHEATER_STAGES[4], 814.7, delta=0.5)
        self.assertAlmostEqual(sum(PREHEATER_STAGES), 4262.9, delta=0.5)

    def test_the_tube(self):
        self.assertAlmostEqual(_cylinder(KILN_D, KILN_L), 1339.07, delta=0.01)


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
            _cylinder(KILN_D, L_t),
            delta=RTOL * _cylinder(KILN_D, L_t),
        )
        self.assertAlmostEqual(
            self._volume(transition, self.N) + self._volume(burning, self.N),
            _cylinder(KILN_D, KILN_L),
            delta=RTOL * _cylinder(KILN_D, KILN_L),
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

    @unittest.expectedFailure  # plan step 3
    def test_the_calciner_and_gooseneck(self):
        calciner = main.Calciner(
            N=self.N, L=self.cfg["calciner"]["length"], cfg=self.cfg
        )
        doc = CALCINER + GOOSENECK
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
