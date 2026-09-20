"""The cooler's gas-solid area came from the wrong diameter.

`physics.interfacial_areas` computes a_gs as the packed-bed
specific surface 6(1-eps)/d_p. The d_p in that correlation is the
PARTICLE diameter. The cooler passed its 4.2 m VESSEL diameter.

This is not a correlation choice, it is a dimensional
substitution, and the repo already says so in its own words at
pyroprocess/burning/heat_transfer.py:133-138 -- the kiln hit the
same thing and replaced the call with bed_segment_geometry. The
cooler still carried it.

WHY THIS IS NOT A FITTED PARAMETER, and how to check rather than
believe that. Per-cell NTU was 1.20, so the cooling air got barely
halfway to the local bed temperature before leaving. Correcting
d_p moves the plant onto a PLATEAU where the answer stops
depending on the number. MEASURED on the converged plant by
scaling a_gs directly:

    a_gs x     NTU    secondary air   clinker discharge
       1      1.20       717.81 K         462.06 K
      10     12.29       912.55 K         363.94 K
      25     30.79       934.47 K         356.89 K
     100    123.34       946.13 K         353.41 K

A ten-fold change in area moves secondary air 33.6 K. Every
defensible clinker nodule size -- the grate passes up to ~25 mm
and nodules run 10-25 mm -- is a 170x to 420x correction, far onto
that plateau.

WHAT IT DOES NOT FIX, stated here so nobody reads the commit as a
success: secondary air reaches 948.69 K against
BOUNDS["secondary_air"] = (1050, 1350). Still out of band, by
about 100 K. The cooler was necessary and is not sufficient.
"""

import unittest

from physics.physics import interfacial_areas


EPSILON_BED = 0.35
VESSEL_D = 4.2
K_INTERFACIAL = 1.0

# configs/twin_cfg.yaml cooler.particle_diameter_m
D_PARTICLE = 0.015


def _areas(d_particle=None):
    return interfacial_areas(
        D=VESSEL_D,
        epsilon_bed=EPSILON_BED,
        k_interfacial=K_INTERFACIAL,
        d_particle=d_particle,
    )


class TheAreaUsesTheParticleTest(unittest.TestCase):

    def test_a_gs_is_the_packed_bed_specific_surface(self):

        a_gs, _ = _areas(D_PARTICLE)

        self.assertAlmostEqual(
            a_gs,
            6.0 * (1.0 - EPSILON_BED) / D_PARTICLE,
            places=9,
        )
        self.assertAlmostEqual(a_gs, 260.0, places=6)

    def test_the_vessel_diameter_gave_a_number_two_orders_too_small(self):

        vessel_a_gs, _ = _areas(None)

        self.assertAlmostEqual(vessel_a_gs, 0.9286, delta=1.0e-4)
        self.assertGreater(_areas(D_PARTICLE)[0] / vessel_a_gs, 100.0)

    def test_the_wall_area_is_a_perimeter_and_does_not_follow(self):
        """a_ws is solid->WALL contact. Scaling it with the
        particle size would put more wall contact area in the zone
        than the vessel physically has wall."""

        self.assertAlmostEqual(
            _areas(D_PARTICLE)[1],
            _areas(None)[1],
            places=12,
        )
        self.assertAlmostEqual(_areas(D_PARTICLE)[1], 0.5571, delta=1e-4)

    def test_the_default_is_bit_identical_to_the_old_behaviour(self):
        """Every zone that has not been revisited -- calciner,
        preheater -- calls this without d_particle and must not
        move. The same substitution is present there and is a
        different question and a different commit."""

        a_gs, a_ws = _areas(None)

        self.assertEqual(a_gs, 6.0 * (1.0 - EPSILON_BED) / VESSEL_D)
        self.assertEqual(a_ws, 0.6 * a_gs)


class TheAnswerSitsOnAPlateauTest(unittest.TestCase):
    """The anti-tuning test.

    Rows measured on the converged plant at nodes_per_stage=1 by
    scaling cooler.a_gs directly, so the plant's own recuperation
    feedback is included rather than a standalone cooler estimate.
    """

    SWEEP = (
        # (a_gs multiplier, per-cell NTU, secondary air K, clinker out K)
        (1.0, 1.20, 717.81, 462.06),
        (2.0, 2.42, 802.53, 410.57),
        (5.0, 6.12, 879.70, 375.76),
        (10.0, 12.29, 912.55, 363.94),
        (25.0, 30.79, 934.47, 356.89),
        (100.0, 123.34, 946.13, 353.41),
    )

    def test_the_committed_diameter_is_past_the_knee(self):

        correction = _areas(D_PARTICLE)[0] / _areas(None)[0]

        self.assertGreater(correction, 100.0)

    def test_ten_fold_in_area_moves_secondary_air_under_fifty_kelvin(self):

        by_factor = {row[0]: row for row in self.SWEEP}

        spread = abs(by_factor[100.0][2] - by_factor[10.0][2])

        self.assertAlmostEqual(spread, 33.58, delta=0.1)
        self.assertLess(spread, 50.0)

    def test_every_defensible_nodule_size_lands_on_the_plateau(self):
        """Nodules run 10-25 mm and a grate passes up to ~25 mm.
        Even 5 mm dust and 40 mm oversize clear the knee."""

        vessel = _areas(None)[0]

        for d_p in (0.005, 0.010, 0.015, 0.025, 0.040):
            self.assertGreater(_areas(d_p)[0] / vessel, 20.0)

    def test_the_uncorrected_plant_was_NOT_on_the_plateau(self):
        """Which is why this had to be fixed rather than left:
        at NTU 1.20 the reported air temperature was a function of
        a vessel diameter that has no business being in it."""

        self.assertLess(self.SWEEP[0][1], 2.0)

        knee = abs(self.SWEEP[1][2] - self.SWEEP[0][2])

        self.assertGreater(knee, 80.0)


class WhatIsStillWrongTest(unittest.TestCase):
    """Pinned so the next reader does not have to re-measure it."""

    SECONDARY_AIR_ACHIEVED = 948.69
    BAND = (1050.0, 1350.0)

    def test_secondary_air_is_still_out_of_band(self):

        self.assertLess(self.SECONDARY_AIR_ACHIEVED, self.BAND[0])
        self.assertGreater(
            self.BAND[0] - self.SECONDARY_AIR_ACHIEVED, 90.0
        )

    def test_but_it_is_most_of_the_way_from_where_it_started(self):
        """586.06 K lumped, 717.81 K cross-flow, 948.69 K here.
        The cooler was necessary; it is not sufficient."""

        self.assertGreater(self.SECONDARY_AIR_ACHIEVED - 586.06, 350.0)


if __name__ == "__main__":
    unittest.main()
