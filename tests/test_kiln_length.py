"""The rotary tube has ONE length, and it is 46.2 m.

`plant.length: 60.0  # burning zone length` was consumed by the
burning zone alone, with `transition.length: 25.0` on top. The
rotary tube was therefore 85 m at D = 4.2 m, i.e. L/D = 20.2.

L/D is what says whether a kiln is the right kiln. This plant sets
`fuel.kiln_fraction = 0.40`, so 60% of the fuel burns in the
calciner and it is an in-line calciner (ILC) plant. A precalciner
kiln is SHORT: US4425092 puts it below 14:1 and preferably at
7:1-11:1, against 15:1-17:1 for a conventional cyclone-preheater
kiln with no precalciner. 20.2 was not merely long -- it was the
wrong kiln type, long-dry/wet territory, on a plant configured as
a precalciner.

Now `kiln.length` is the whole tube and the burning zone is the
remainder after `transition.length`, so the two cannot disagree
about how long the kiln is. Changing `transition.length` used to
silently lengthen the tube; now it only moves the internal split.

MEASURED, nodes_per_stage=1, across the whole sweep:

  tube   L/D    Ts_burning max   secondary air   kiln discharge
  85.0  20.24      1622.64 K        948.69 K       1295.42 K
  60.0  14.29      1703.51 K       1020.02 K       1415.94 K
  46.2  11.00      1771.16 K       1085.57 K       1524.09 K
  37.8   9.00      1832.07 K       1148.30 K       1625.04 K

The kiln's discharge end is its coldest section -- the bed peaks
mid-kiln and is re-cooled against incoming secondary air over the
last cells -- so less of that re-cooling, and less shell to lose
through, both push the discharge up.

WHY IT STOPS AT 11 AND NOT AT 9. At L/D 9 the bed reaches 1832 K
and breaks BOUNDS["Ts_any_zone_max"] = 1773 K, the clinker
liquidus. The lower half of the literature's own preferred range
is incompatible with this model's physical bound, so 11 is
simultaneously the literature value and the furthest this plant
can go without violating one. Bounded, not fitted.

AND IT IS TIGHT: 1771.16 K leaves 1.8 K of margin to the liquidus.
"""

import math
import unittest

import main


VESSEL_D = 4.2


class TheTubeHasOneLengthTest(unittest.TestCase):

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")

    def test_kiln_length_is_the_whole_tube(self):

        kiln = self.cfg["kiln"]["length"]
        transition = self.cfg["transition"]["length"]

        self.assertAlmostEqual(kiln, 46.2)
        self.assertAlmostEqual(transition, 25.0)

        burning = main.Burning(
            N=self.cfg["plant"]["N"],
            L=kiln,
            cfg=self.cfg,
        )

        self.assertAlmostEqual(burning.L, kiln - transition)
        self.assertAlmostEqual(burning.L, 21.2)

    def test_moving_the_split_does_not_lengthen_the_tube(self):
        """The regression. Before this, transition.length was
        added to a separately configured burning length, so
        editing it changed how long the kiln was."""

        for transition in (15.0, 25.0, 30.0):

            cfg = main.load_cfg("configs/twin_cfg.yaml")
            cfg["transition"]["length"] = transition

            burning = main.Burning(
                N=cfg["plant"]["N"],
                L=cfg["kiln"]["length"],
                cfg=cfg,
            )

            self.assertAlmostEqual(
                burning.L + transition,
                cfg["kiln"]["length"],
            )

    def test_a_split_that_leaves_no_kiln_is_rejected(self):

        cfg = main.load_cfg("configs/twin_cfg.yaml")
        cfg["transition"]["length"] = 46.2

        with self.assertRaises(ValueError) as caught:
            main.Burning(N=20, L=46.2, cfg=cfg)

        self.assertIn("must be positive", str(caught.exception))

    def test_plant_length_is_gone(self):
        """It meant the burning zone while sitting in a section
        named for the whole pyroprocess. Leaving it readable would
        let both spellings coexist."""

        self.assertNotIn("length", self.cfg["plant"])


class TheRatioIsAPrecalcinerKilnTest(unittest.TestCase):
    """L/D is the acceptance test, and it is a statement about
    kiln TYPE, not a tuned number."""

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")
        self.L = self.cfg["kiln"]["length"]

    def test_the_plant_is_configured_as_a_precalciner(self):
        """Which is what makes the short-kiln band the right one."""

        self.assertLess(self.cfg["fuel"]["kiln_fraction"], 0.5)

    def test_the_ratio_is_inside_the_precalciner_band(self):

        self.assertAlmostEqual(self.L / VESSEL_D, 11.00, delta=0.01)

        # US4425092: below 14:1, preferably 7:1-11:1.
        self.assertLess(self.L / VESSEL_D, 14.0)
        self.assertGreaterEqual(self.L / VESSEL_D, 7.0)

    def test_the_old_tube_was_the_wrong_kiln_type(self):

        old = (60.0 + 25.0) / VESSEL_D

        self.assertAlmostEqual(old, 20.24, delta=0.01)

        # Past even the conventional preheater kiln range, on a
        # plant burning 60% of its fuel in the calciner.
        self.assertGreater(old, 17.0)

    def test_the_shell_area_the_change_removes(self):

        old_area = math.pi * VESSEL_D * 85.0
        new_area = math.pi * VESSEL_D * self.L

        self.assertAlmostEqual(new_area / old_area - 1.0, -0.456, delta=0.001)


class WhatItMovedTest(unittest.TestCase):
    """Pinned so the next reader does not re-measure it.

    Still out of band afterwards, and said so here rather than
    left to be discovered: the kiln discharge wants (1600, 1780)
    and reaches 1524.09 K.
    """

    BEFORE = {
        "Ts_burning_max": 1622.64,
        "secondary_air": 948.69,
        "kiln_discharge": 1295.42,
    }
    AFTER = {
        "Ts_burning_max": 1771.16,
        "secondary_air": 1085.57,
        "kiln_discharge": 1524.09,
    }

    # The next step down the literature's range, which this does
    # NOT take, and the bound that stops it.
    AT_LD_9 = {"Ts_burning_max": 1832.07, "secondary_air": 1148.30}
    LIQUIDUS = 1773.0

    def test_every_gate_quantity_moved_the_right_way(self):

        for key in self.BEFORE:
            self.assertGreater(self.AFTER[key], self.BEFORE[key], key)

    def test_the_burning_zone_is_now_a_plausible_one(self):
        """Real burning zones run a bed around 1700-1750 K, under
        the 1773 K liquidus. 1622 K was cold for a kiln making
        C3S."""

        self.assertGreater(self.AFTER["Ts_burning_max"], 1650.0)
        self.assertLess(self.AFTER["Ts_burning_max"], 1773.0)

    def test_secondary_air_finally_reaches_its_band(self):
        """586.06 lumped -> 717.81 cross-flow -> 948.69 with the
        right contact area -> 1085.57 here. The gate this whole
        line of work was aimed at."""

        self.assertGreaterEqual(self.AFTER["secondary_air"], 1050.0)
        self.assertLessEqual(self.AFTER["secondary_air"], 1350.0)

    def test_going_further_would_break_the_liquidus(self):

        self.assertLess(self.AFTER["Ts_burning_max"], self.LIQUIDUS)
        self.assertGreater(self.AT_LD_9["Ts_burning_max"], self.LIQUIDUS)

    def test_the_margin_to_the_liquidus_is_uncomfortably_thin(self):
        """Recorded rather than smoothed over: a model sitting on
        a limit has nothing left for a disturbance."""

        self.assertLess(
            self.LIQUIDUS - self.AFTER["Ts_burning_max"], 5.0
        )

    def test_the_kiln_discharge_is_still_out_of_band(self):

        self.assertLess(self.AFTER["kiln_discharge"], 1600.0)


if __name__ == "__main__":
    unittest.main()
