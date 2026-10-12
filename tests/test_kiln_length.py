"""The rotary tube has ONE length and ONE bore, and they belong to
it alone.

`plant.length: 60.0  # burning zone length` was consumed by the
burning zone ALONE, with `transition.length: 25.0` on top, so the
tube was 85 m. `kiln.length` is now the whole tube and the burning
zone is the remainder, so the two cannot disagree.

`kiln.diameter` is the same idea for the bore. Every zone used to
carry its own literal 4.2, which is how five separate pieces of
equipment came to share one number by accident. The two ROTATING
zones -- burning and transition -- now read the config; the
calciner, preheater and cooler keep their literals, because a
vertical riser, a cyclone string and a grate are not this tube and
must not follow it when it moves.

WHAT L/D MEANS HERE. It is a statement about the ROTARY KILN, and
about kiln TYPE. With fuel.kiln_fraction = 0.40 this plant burns
60% of its fuel in a separate static calciner, which is what lets
the rotary tube be short: US4425092 puts the rotary kiln of such a
plant below 14:1. It says nothing about the precalciner vessel.

  tube  bore   L/D    what it is
  85.0   4.2  20.24   long-dry/wet territory -- wrong kiln type
  60.0   4.2  14.29   misses the < 14:1 criterion
  60.0   4.5  13.33   the 2500-era twin
  74.0   4.8  15.42   committed: the 5000 t/d plant's PF5000 kiln

THE 5000 t/d PLANT (user decision, 12 Oct 2026). Two identical
2500 t/d strings share one kiln, the published PF5000 one, taken by
the 2500 line's rule (geometry/kiln/kiln.md): shell 4.8 m as the
bore, 74 m, 3 %. Its L/D of 15.42 is past the < 14:1 criterion the
4.5 x 60 m tube was chosen against, and inside the patent's 15:1-17:1
for a conventional preheater kiln. The published line is what it
is; the criterion is a design preference this plant does not meet,
and the tests below say so rather than hide it. The transition
keeps the old 25/60 share of the tube: 30.83 m.

WhatItMovedTest and TheClinkerGotWorseTest are records of the
2500-era tube and are kept as history.
"""

import math
import unittest

import main


class TheTubeHasOneLengthTest(unittest.TestCase):

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")

    def test_kiln_length_is_the_whole_tube(self):

        kiln = self.cfg["kiln"]["length"]
        transition = self.cfg["transition"]["length"]

        self.assertAlmostEqual(kiln, 74.0)
        self.assertAlmostEqual(transition, 30.83)

        burning = main.Burning(
            N=self.cfg["plant"]["N"],
            L=kiln,
            cfg=self.cfg,
        )

        self.assertAlmostEqual(burning.L, kiln - transition)
        self.assertAlmostEqual(burning.L, 43.17)

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
        cfg["transition"]["length"] = cfg["kiln"]["length"]

        with self.assertRaises(ValueError) as caught:
            main.Burning(N=20, L=cfg["kiln"]["length"], cfg=cfg)

        self.assertIn("must be positive", str(caught.exception))

    def test_plant_length_is_gone(self):
        """It meant the burning zone while sitting in a section
        named for the whole pyroprocess. Leaving it readable would
        let both spellings coexist."""

        self.assertNotIn("length", self.cfg["plant"])


class TheBoreBelongsToTheRotatingTubeTest(unittest.TestCase):
    """The point the user raised: the kiln's length and L/D size
    the ROTARY KILN. No static equipment may follow them."""

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")
        self.N = self.cfg["plant"]["N"]

    def _zone(self, cls, length_key):
        return cls(
            N=self.N,
            L=self.cfg[length_key]["length"],
            cfg=self.cfg,
        )

    def test_the_two_rotating_zones_share_the_configured_bore(self):
        """They are one tube, so one bore."""

        D = self.cfg["kiln"]["diameter"]
        self.assertAlmostEqual(D, 4.8)

        burning = main.Burning(
            N=self.N, L=self.cfg["kiln"]["length"], cfg=self.cfg
        )
        transition = self._zone(main.Transition, "transition")

        self.assertAlmostEqual(burning.D, D)
        self.assertAlmostEqual(transition.D, D)

    def test_the_static_equipment_does_not_follow_the_kiln(self):
        """A vertical riser, a cyclone string and a grate. Moving
        the kiln's bore must not resize any of them. The calciner
        reads its own PF5000 bore and the preheater is still a
        4.2 m placeholder (Faz 6 item 2); the cooler is a grate box
        with no bore at all (geometry/cooler/cooler.md)."""

        for cls, key, D in (
            (main.Calciner, "calciner", 6.74),
            (main.Preheater, "preheater", 4.2),
        ):
            self.assertAlmostEqual(
                self._zone(cls, key).D, D, msg=cls.__name__
            )

        cooler = self._zone(main.Cooler, "cooler")

        self.assertFalse(hasattr(cooler, "D"))
        self.assertAlmostEqual(cooler.width, 4.0)
        self.assertAlmostEqual(cooler.casing_height, 3.0)

    def test_changing_the_kiln_bore_moves_only_the_kiln(self):

        cfg = main.load_cfg("configs/twin_cfg.yaml")
        cfg["kiln"]["diameter"] = 4.0

        burning = main.Burning(
            N=self.N, L=cfg["kiln"]["length"], cfg=cfg
        )
        transition = main.Transition(
            N=self.N, L=cfg["transition"]["length"], cfg=cfg
        )
        calciner = main.Calciner(
            N=self.N, L=cfg["calciner"]["length"], cfg=cfg
        )

        self.assertAlmostEqual(burning.D, 4.0)
        self.assertAlmostEqual(transition.D, 4.0)
        self.assertAlmostEqual(calciner.D, 6.74)

    def test_the_cross_section_follows_the_configured_bore(self):
        """Not just the attribute -- the geometry built from it."""

        burning = main.Burning(
            N=self.N, L=self.cfg["kiln"]["length"], cfg=self.cfg
        )

        self.assertAlmostEqual(
            burning.A_cross,
            math.pi * self.cfg["kiln"]["diameter"] ** 2 / 4.0,
            places=9,
        )


class TheRatioIsAPrecalcinerPlantsKilnTest(unittest.TestCase):

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")
        self.L = self.cfg["kiln"]["length"]
        self.D = self.cfg["kiln"]["diameter"]

    def test_the_plant_is_configured_as_a_precalciner(self):
        """Which is what makes the short-kiln band the right one:
        most of the fuel fires in static equipment, so the rotary
        tube does not have to do the calcining."""

        self.assertLess(self.cfg["fuel"]["kiln_fraction"], 0.5)

    def test_the_kiln_is_the_published_5000_t_d_one(self):

        self.assertAlmostEqual(self.L, 74.0)
        self.assertAlmostEqual(self.D, 4.8)
        self.assertAlmostEqual(self.L / self.D, 15.42, delta=0.01)

    def test_it_misses_the_short_kiln_criterion_and_says_so(self):
        """US4425092: below 14:1 for the rotary kiln of a
        precalciner plant, 15:1-17:1 for a conventional preheater
        kiln. The published 5000 t/d line sits in the second band."""

        self.assertGreater(self.L / self.D, 14.0)
        self.assertLess(self.L / self.D, 17.0)

    def test_the_2500_era_tube_met_it(self):
        """Recorded: 4.5 x 60 m was chosen against the criterion,
        which the 4.2 m bore at 60 m would have missed."""

        self.assertLess(60.0 / 4.5, 14.0)
        self.assertGreater(60.0 / 4.2, 14.0)

    def test_the_old_tube_was_the_wrong_kiln_type(self):

        old = (60.0 + 25.0) / 4.2

        self.assertAlmostEqual(old, 20.24, delta=0.01)
        self.assertGreater(old, 17.0)


class WhatItMovedTest(unittest.TestCase):
    """Pinned so the next reader does not re-measure it.

    Measured at nodes_per_stage=1. Still out of band afterwards,
    and said here rather than left to be discovered: the kiln
    discharge wants (1600, 1780) and does not respond to motion at
    all -- it sits at 1481-1531 K across the ENTIRE stated search
    box. That is a fuel question, not a geometry one.
    """

    # 46.2 m, 4.2 m bore, 5.24 % slope, 1.5 rpm, on the transit
    # correlation as it was.
    BEFORE = {
        "Ts_burning_max": 1771.16,
        "secondary_air": 1085.57,
        "kiln_discharge": 1524.09,
        "transit_min": 51.85,
    }
    # 60 m, 4.5 m bore, 2.2 %, 3.5 rpm, Sullivan's correlation.
    AFTER = {
        "Ts_burning_max": 1758.78,
        "secondary_air": 1054.33,
        "kiln_discharge": 1480.89,
        "transit_min": 33.84,
    }

    LIQUIDUS = 1773.0

    def test_the_residence_band_is_reached_for_the_first_time(self):
        """25-35 min. The previous kiln read 51.85 and was judged
        unable to reach the band at any length -- a conclusion
        that was an artifact of the correlation."""

        self.assertGreater(self.BEFORE["transit_min"], 35.0)

        self.assertGreaterEqual(self.AFTER["transit_min"], 25.0)
        self.assertLessEqual(self.AFTER["transit_min"], 35.0)

    def test_secondary_air_stays_in_its_band(self):
        """It entered the band with the cooler work and must not
        be given back here."""

        self.assertGreaterEqual(self.AFTER["secondary_air"], 1050.0)
        self.assertLessEqual(self.AFTER["secondary_air"], 1350.0)

    def test_the_liquidus_margin_improved_but_is_still_thin(self):
        """1.8 K before, 14.2 K now. Better, and still not a lot
        for a model that has to take a disturbance."""

        before = self.LIQUIDUS - self.BEFORE["Ts_burning_max"]
        after = self.LIQUIDUS - self.AFTER["Ts_burning_max"]

        self.assertAlmostEqual(before, 1.84, delta=0.02)
        self.assertAlmostEqual(after, 14.22, delta=0.02)

        self.assertGreater(after, before)
        self.assertLess(after, 25.0)

    def test_the_kiln_discharge_is_still_out_of_band(self):
        """And got slightly worse, which is worth stating plainly:
        the transit band and the discharge band pull opposite
        ways, and motion cannot serve both."""

        self.assertLess(self.AFTER["kiln_discharge"], 1600.0)
        self.assertLess(
            self.AFTER["kiln_discharge"],
            self.BEFORE["kiln_discharge"],
        )


class TheClinkerGotWorseTest(unittest.TestCase):
    """THE COST OF THIS CHANGE, pinned so it cannot be forgotten.

    A COMPENSATING ERROR WAS REMOVED AND THE ERROR IT WAS HIDING IS
    NOW VISIBLE. The old correlation gave this kiln 51.85 min of
    transit where Sullivan's gives 33.84, so every residence-driven
    reaction had ~1.5x the time it should have had, and the
    chemistry was leaning on it. With the transit corrected, the
    clinker is measurably worse:

      kg/s at the cooler outlet      46.2 m tube    60 m tube
        CaCO3, never calcined            2.5073       4.5833
        C3S, the alite                   1.1502       0.5765
        C2S                              5.7882       4.6854

    That is a quarter of the "clinker" leaving as raw limestone.
    It is NOT an argument for putting the correlation back --
    keeping a verifiably wrong transit to protect a number that
    was right for the wrong reason is the exact
    compensating-error pattern chemistry/calcination.py already
    documents being dismantled.

    IT IS AN ARGUMENT ABOUT WHERE CALCINATION BELONGS. It belongs
    in the calciner, and the calciner is not doing it: at the
    calciner outlet 15.42 of 21.0 kg/s of CaCO3 is still CaCO3, so
    the vessel that should finish ~90% of the job finishes ~26%
    and hands the rest to a kiln that no longer has the time. Two
    reasons, both already identified and neither fixed here:

      1. The calciner is modelled as a ROTATING, inclined cylinder
         and gets a 1340 s solids transit where a vertical riser
         gives ~5 s. Wrong equipment, and the error does not even
         help -- 22 minutes still only reaches 26%.
      2. Its kinetics are ~5 orders of magnitude too slow
         (committed pair 42.5 1/s, 150 kJ/mol). The literature
         pair is patched and still unlandable: it diverges the
         outer solve at sweep 3 with Ts_burning 4674 K, on the old
         geometry and this one alike, so it is independent of
         everything this commit touches.
    """

    CLINKER = {
        # zone outlet, kg/s
        "CaCO3": (2.5073, 4.5833),
        "C3S": (1.1502, 0.5765),
        "C2S": (5.7882, 4.6854),
    }
    CALCINER_OUT_CaCO3 = (14.0230, 15.4169)

    def test_the_uncalcined_carry_over_nearly_doubled(self):

        before, after = self.CLINKER["CaCO3"]

        self.assertGreater(after, before)
        self.assertAlmostEqual(after / before, 1.83, delta=0.01)

    def test_the_alite_halved(self):
        """C3S is what makes cement cement."""

        before, after = self.CLINKER["C3S"]

        self.assertLess(after, 0.55 * before)

    def test_the_calciner_is_where_this_actually_fails(self):
        """It was already failing before this commit -- the kiln
        was covering for it, and now it cannot."""

        before, after = self.CALCINER_OUT_CaCO3

        # Barely moved: the calciner's own shortfall is not what
        # this commit changed.
        self.assertLess(abs(after - before) / before, 0.11)

        # And it is large in both. ~21 kg/s of CaCO3 enters.
        self.assertGreater(before, 13.0)
        self.assertGreater(after, 13.0)


if __name__ == "__main__":
    unittest.main()
