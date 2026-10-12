"""The solid transit through the rotary kiln is Sullivan's, and it
was mis-stated three ways.

`physics.bed_motion_from_continuity` used to give

    tau = L sqrt(1.77 rho A / (D N tan(beta) m_dot_s))

built by closing

    tau = 1.77 L / (D N tan(beta) eta)      <- residence_time()
    eta = m_dot_s tau / (rho L A)           <- mass continuity

against each other. The arithmetic is right and the premise is
not. Sullivan, Maier & Ralston (1927), US Bureau of Mines TP 384:

    tau [min] = 1.77 L sqrt(theta) / (D N beta)

    theta = dynamic angle of repose   [DEGREES]
    beta  = kiln inclination          [DEGREES]
    N     = rotational speed          [rpm]

already GIVES the transit. It has no fill-fraction term, so there
was no loop to close: the fill fraction is what continuity returns
afterwards, not what the correlation needs beforehand. And the
repo's copy had also dropped sqrt(theta), put tan(beta) where a
number of degrees belongs -- 180/pi = 57.3 at these angles -- and
handed Sullivan's MINUTES to callers that consume seconds.

The degrees-vs-tangent point is the one that is easy to get wrong
and easy to check, so it is checked here rather than asserted:
three industry restatements of the same correlation have to agree,
and they only do if beta is in degrees.
"""

import math
import unittest

import numpy as np

import main
from physics.physics import rotary_bed_motion


REPOSE = 40.0
SULLIVAN = 1.77

# 180/pi -- the small-angle conversion from tan(beta) to beta in
# degrees, and the entire reason the two published constants below
# differ by the factor they do.
RAD_PER_DEG = 180.0 / math.pi


class TheCorrelationIsTheLiteratureOneTest(unittest.TestCase):

    def test_beta_is_in_degrees_not_a_tangent(self):
        """The US Bureau of Mines form is quoted against the slope
        as a FRACTION and in revolutions per hour:

            T [min] = 11.4 L(ft) / (RPH * Dia(ft) * S),  S = ft/ft

        The feet cancel in L/Dia and RPH = 60 N, so in metres and
        rpm it is 0.19 L/(D N tan beta). If beta belonged in the
        degree-form as a tangent too, that 0.19 would have to equal
        the degree-form's 11.2 -- and it does, once multiplied by
        180/pi. That factor IS the conversion, which is what makes
        this a proof rather than a coincidence.
        """

        bom_metric = 11.4 / 60.0                 # = 0.19
        degree_form = 11.2                       # cemnet, "Kiln Speed"

        self.assertAlmostEqual(bom_metric, 0.19, places=3)
        self.assertAlmostEqual(
            bom_metric * RAD_PER_DEG, degree_form, delta=0.35
        )

    def test_the_published_constants_imply_one_repose_angle(self):
        """Each industry shorthand folds sqrt(theta) into its
        constant, so solving back for theta says whether they are
        describing the same material. Two land on 38-40 deg, which
        is what the cement literature states for raw material."""

        for constant, expected in ((11.2, 40.0), (11.4 / 60.0 * RAD_PER_DEG, 37.8)):
            theta = (constant / SULLIVAN) ** 2
            self.assertAlmostEqual(theta, expected, delta=0.3)

        # And the value this model configures reproduces the
        # most-used constant to 0.1 %.
        self.assertAlmostEqual(
            SULLIVAN * math.sqrt(REPOSE), 11.2, delta=0.02
        )

    def test_it_matches_a_published_worked_example(self):
        """L = 20 m, theta = 36 deg, beta = 3 deg, D = 1.6 m,
        N = 0.182 rpm  ->  243.13 min. Reproduced through the
        repo's own function, which means the units, the operand
        order and the constant all have to be right at once."""

        tau, _, _ = rotary_bed_motion(
            L=20.0, D=1.6, slope_deg=3.0, rpm=0.182,
            repose_deg=36.0,
            # The worked example is a transit time only; the flow
            # and the bore are picked to keep the fill in range,
            # which cannot affect tau -- that is the whole point.
            m_dot_s=1.0, rho_bulk=1100.0,
            A_cross=math.pi * 1.6 ** 2 / 4.0, eps=1e-9,
        )

        self.assertAlmostEqual(tau / 60.0, 243.13, delta=0.02)

    def test_the_answer_is_in_seconds(self):
        """Sullivan returns minutes and every caller reads
        seconds. The conversion is at the source, so this is the
        regression for it."""

        tau, u_s, _ = rotary_bed_motion(
            L=60.0, D=4.5, slope_deg=1.2603, rpm=3.5,
            repose_deg=REPOSE, m_dot_s=18.02, rho_bulk=1100.0,
            A_cross=math.pi * 4.5 ** 2 / 4.0, eps=1e-9,
        )

        minutes = SULLIVAN * 60.0 * math.sqrt(REPOSE) / (
            4.5 * 3.5 * 1.2603
        )

        self.assertAlmostEqual(tau, 60.0 * minutes, places=6)
        self.assertAlmostEqual(u_s, 60.0 / tau, places=12)


class TheFillFractionIsAnOutputTest(unittest.TestCase):

    KWARGS = dict(
        L=60.0, D=4.5, slope_deg=1.2603, rpm=3.5, repose_deg=REPOSE,
        rho_bulk=1100.0, A_cross=math.pi * 4.5 ** 2 / 4.0, eps=1e-9,
    )

    def test_the_transit_does_not_depend_on_the_flow(self):
        """The old closure made tau a function of m_dot_s through
        the continuity leg. Sullivan's does not: feed rate changes
        how DEEP the bed is, not how fast it walks."""

        taus = [
            rotary_bed_motion(m_dot_s=m, **self.KWARGS)[0]
            for m in (10.0, 18.02, 30.0)
        ]

        for tau in taus[1:]:
            self.assertAlmostEqual(tau, taus[0], places=9)

    def test_the_fill_follows_continuity_exactly(self):

        m_dot = 18.02
        tau, u_s, fill = rotary_bed_motion(
            m_dot_s=m_dot, **self.KWARGS
        )

        self.assertAlmostEqual(
            fill,
            m_dot / (
                self.KWARGS["rho_bulk"] * u_s * self.KWARGS["A_cross"]
            ),
            places=12,
        )

        # Proportional to the flow, which is the statement the old
        # closure could not make because the flow was also setting
        # the transit.
        _, _, double = rotary_bed_motion(
            m_dot_s=2.0 * m_dot, **self.KWARGS
        )
        self.assertAlmostEqual(double, 2.0 * fill, places=12)

    def test_u_s_does_not_depend_on_length(self):
        """tau scales with L, so u_s = L/tau does not. This is why
        handing the correlation the BURNING ZONE's length rather
        than the whole tube's changes nothing about the velocity
        the two zones share."""

        speeds = []
        for L in (21.2, 35.0, 60.0):
            kwargs = dict(self.KWARGS, L=L)
            speeds.append(
                rotary_bed_motion(m_dot_s=18.02, **kwargs)[1]
            )

        for u in speeds[1:]:
            self.assertAlmostEqual(u, speeds[0], places=12)


class TheGuardsTest(unittest.TestCase):

    BASE = dict(
        L=60.0, D=4.5, slope_deg=1.2603, rpm=3.5, repose_deg=REPOSE,
        m_dot_s=18.02, rho_bulk=1100.0,
        A_cross=math.pi * 4.5 ** 2 / 4.0, eps=1e-9,
    )

    def test_a_level_kiln_is_rejected(self):

        with self.assertRaises(ValueError) as caught:
            rotary_bed_motion(**dict(self.BASE, slope_deg=0.0))

        self.assertIn("positive inclination", str(caught.exception))

    def test_a_repose_angle_outside_the_fitted_range_is_rejected(self):
        """15-55 deg is where the correlation was fitted. Outside
        it the sqrt(theta) grouping is an extrapolation, and the
        caller is told rather than handed a number."""

        for theta in (5.0, 80.0):
            with self.assertRaises(ValueError) as caught:
                rotary_bed_motion(**dict(self.BASE, repose_deg=theta))
            self.assertIn("15-55 deg", str(caught.exception))

        for theta in (15.0, 40.0, 55.0):
            rotary_bed_motion(**dict(self.BASE, repose_deg=theta))

    def test_an_impossible_fill_is_rejected(self):
        """A bed that will not fit the bore is a statement about
        the plant, not a number to clamp."""

        with self.assertRaises(ValueError) as caught:
            rotary_bed_motion(**dict(self.BASE, m_dot_s=1.0e5))

        self.assertIn("fill fraction out of range", str(caught.exception))


class TheConfiguredKilnTest(unittest.TestCase):
    """What the committed config actually turns."""

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")
        self.burning = main.Burning(
            N=self.cfg["plant"]["N"],
            L=self.cfg["kiln"]["length"],
            cfg=self.cfg,
        )

    def test_the_slope_is_configured_as_a_percent(self):
        """Not degrees. `inclination_deg: 3.0` meant 5.24 %, which
        is outside the 2-4 % a cement kiln is laid on -- the unit
        confusion Sullivan's degrees invite."""

        self.assertNotIn("inclination_deg", self.cfg["motion"])

        pct = self.cfg["motion"]["inclination_pct"]
        self.assertGreaterEqual(pct, 2.0)
        self.assertLessEqual(pct, 4.0)

        self.assertAlmostEqual(
            self.burning.slope_deg,
            math.degrees(math.atan(pct / 100.0)),
            places=12,
        )

    def test_a_slope_given_in_degrees_by_mistake_is_still_a_percent(self):
        """There is no silent reinterpretation: 3.0 now means
        3.0 %, which is 1.72 deg, not 3 deg. Pinned so that a
        future reader editing this value knows which it is."""

        cfg = main.load_cfg("configs/twin_cfg.yaml")
        cfg["motion"]["inclination_pct"] = 3.0

        burning = main.Burning(
            N=cfg["plant"]["N"], L=cfg["kiln"]["length"], cfg=cfg
        )

        self.assertAlmostEqual(burning.slope_deg, 1.718358, places=5)

    def test_the_speed_is_inside_the_stated_range(self):

        motion = self.cfg["motion"]

        # The PF5000 drive (geometry/kiln/kiln.md).
        self.assertEqual(motion["rpm_min"], 0.6)
        self.assertEqual(motion["rpm_max"], 4.0)
        self.assertGreaterEqual(motion["rpm_default"], motion["rpm_min"])
        self.assertLessEqual(motion["rpm_default"], motion["rpm_max"])

    def test_the_tube_transit_is_in_the_precalciner_band(self):
        """25-35 min. THE constraint this operating point was
        chosen against, and the reason the slope and the speed are
        what they are."""

        b = self.burning

        _, u_s, fill = rotary_bed_motion(
            L=b.L, D=b.D, slope_deg=b.slope_deg, rpm=b.rpm_default,
            repose_deg=b.repose_deg,
            # The clinker, which is what state.m_dot_s carries: the
            # 5000 t/d plant's, from tests/data/twin_state_reference.json.
            m_dot_s=69.50, rho_bulk=b.rho_s, A_cross=b.A_cross,
            eps=b.eps,
        )

        transit_min = self.cfg["kiln"]["length"] / u_s / 60.0

        # The PF5000 tube, 74 m x 4.8 m at 3 % and 3.5 rpm. The
        # 2500-era 60 m x 4.5 m tube at 2.2 % read 33.84 min.
        self.assertAlmostEqual(transit_min, 28.70, delta=0.02)
        self.assertGreaterEqual(transit_min, 25.0)
        self.assertLessEqual(transit_min, 35.0)

        # And the bed it implies. A cement kiln usually runs 5-17 %.
        # The 2500-era tube carried 18 kg/s of clinker at 3.49 %, a
        # bore sized for two to three times that; the 5000 t/d plant
        # fills the PF5000 tube into the band.
        self.assertAlmostEqual(100.0 * fill, 8.12, delta=0.02)
        self.assertGreater(100.0 * fill, 5.0)
        self.assertLess(100.0 * fill, 17.0)

    def test_the_old_tube_was_half_an_hour_slower(self):
        """46.2 m at 4.2 m, 5.24 % and 1.5 rpm read 51.85 min and
        was judged unable to reach the band at any length. That
        conclusion was an artifact of the correlation."""

        cfg = main.load_cfg("configs/twin_cfg.yaml")
        cfg["kiln"]["length"] = 46.2
        cfg["kiln"]["diameter"] = 4.2
        cfg["motion"]["inclination_pct"] = 100.0 * math.tan(
            math.radians(3.0)
        )
        cfg["motion"]["rpm_min"] = 1.0
        cfg["motion"]["rpm_default"] = 1.5

        b = main.Burning(N=cfg["plant"]["N"], L=46.2, cfg=cfg)

        _, u_s, _ = rotary_bed_motion(
            L=b.L, D=b.D, slope_deg=b.slope_deg, rpm=1.5,
            repose_deg=b.repose_deg, m_dot_s=18.02,
            rho_bulk=b.rho_s, A_cross=b.A_cross, eps=b.eps,
        )

        self.assertAlmostEqual(46.2 / u_s / 60.0, 27.36, delta=0.05)


if __name__ == "__main__":
    unittest.main()
