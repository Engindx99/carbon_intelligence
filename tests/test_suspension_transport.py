"""The two vessels that are not packed beds and do not rotate.

A precalciner is a vertical riser and a cyclone preheater is a
string of ducts and separators. In both, the meal is carried by
the process gas: its velocity is the gas velocity less the slip
its own weight costs it, and the suspension density follows from
continuity afterwards. There is no fill fraction to configure and
no transit correlation to fit -- it is transport.

WHAT THIS REPLACES. Both vessels carried `fill_fraction = 0.10`,
a settled-heap packing applied to a dispersion, and the calciner
additionally ran a ROTARY KILN transit correlation at a
hard-coded 3 degree inclination and 3 rpm while reading the
kiln's own speed off the state. Measured against the plant
specification:

    vessel              modelled     specification
    preheater, total     342.9 s      30-60 s
    precalciner          670.1 s      2-5 s

The calciner was 134x over. It is not a rotating cylinder; it is
not inclined; and 22 minutes of hold-up still only finished ~26%
of the calcination, so the error was not even buying anything.

THE ANSWER DOES NOT DEPEND ON THE PARTICLE SIZE, which is the
one genuinely uncertain input here. Cement raw meal is ground to
12-14% residue on 90 um, so the particles are tens of microns and
the slip is a fraction of a percent of the gas velocity.
MEASURED on the converged calciner stream:

    d_p      u_t          slip      transit
    10 um    0.0028 m/s   0.023 %    2.02 s
    25 um    0.0175 m/s   0.142 %    2.03 s
    50 um    0.0701 m/s   0.567 %    2.03 s
    90 um    0.2271 m/s   1.838 %    2.06 s

Every defensible meal size lands in the same place, and inside
the 2-5 s band. That plateau is what makes this a mechanism being
corrected rather than a parameter being fitted -- the same
argument the cooler's NTU plateau carries.
"""

import math
import unittest

from physics.physics import (
    G_ACCEL,
    mu_gas,
    stokes_terminal_velocity,
    suspension_transport,
)


# Limestone and clay. The PARTICLE density, not the ~1100 kg/m3
# bulk density the zones carry as rho_s -- bulk density already
# contains the void fraction of a settled heap, which means
# nothing for a particle falling through gas.
RHO_PARTICLE = 2700.0


class StokesTest(unittest.TestCase):

    def test_it_is_the_textbook_expression(self):

        d_p, rho_g, mu = 25.0e-6, 0.2456, 5.245e-5

        self.assertAlmostEqual(
            stokes_terminal_velocity(d_p, RHO_PARTICLE, rho_g, mu),
            (RHO_PARTICLE - rho_g) * G_ACCEL * d_p ** 2 / (18.0 * mu),
            places=12,
        )

    def test_it_goes_as_the_square_of_the_diameter(self):

        args = (RHO_PARTICLE, 0.2456, 5.245e-5)

        single = stokes_terminal_velocity(25.0e-6, *args)
        double = stokes_terminal_velocity(50.0e-6, *args)

        self.assertAlmostEqual(double / single, 4.0, places=9)

    def test_leaving_the_stokes_regime_is_refused(self):
        """Re_p < 1 is where the linear drag holds. d_p is
        configurable, so this is checked rather than assumed --
        past it the expression OVERSTATES the settling velocity,
        which would understate the transit."""

        with self.assertRaises(ValueError) as caught:
            # A millimetre nodule, not meal.
            stokes_terminal_velocity(
                1.0e-3, RHO_PARTICLE, 0.2456, 5.245e-5
            )

        self.assertIn("Reynolds", str(caught.exception))

        # The meal sizes that matter are far inside it.
        for d_p in (10.0e-6, 25.0e-6, 50.0e-6, 90.0e-6):
            u_t = stokes_terminal_velocity(
                d_p, RHO_PARTICLE, 0.2456, 5.245e-5
            )
            reynolds = 0.2456 * u_t * d_p / 5.245e-5
            self.assertLess(reynolds, 0.1, f"d_p={d_p}")

    def test_a_particle_lighter_than_the_gas_is_refused(self):

        with self.assertRaises(ValueError) as caught:
            stokes_terminal_velocity(25.0e-6, 0.1, 0.2456, 5.245e-5)

        self.assertIn("does not settle", str(caught.exception))


class TheCalcinerStreamTest(unittest.TestCase):
    """The converged calciner gas, from the committed fixture."""

    # m_dot_g_transition + m_dot_air_calciner + m_dot_fuel_calciner
    M_DOT_G = 42.0647
    M_DOT_S = 26.3910
    T_GAS = 1489.0
    D = 4.2
    L = 25.0

    def setUp(self):
        self.A = math.pi * self.D ** 2 / 4.0
        # Ideal gas on the representative molar mass the zones use.
        self.rho_g = 101325.0 * 0.030 / (8.314 * self.T_GAS)
        self.mu = mu_gas(self.T_GAS)

    def _transit(self, d_p):
        u_s, u_g, u_t, frac = suspension_transport(
            m_dot_g=self.M_DOT_G, m_dot_s=self.M_DOT_S,
            rho_g=self.rho_g, A_cross=self.A, d_p=d_p,
            rho_particle=RHO_PARTICLE, mu=self.mu, eps=1e-9,
        )
        return self.L / u_s, u_g, u_t, frac

    def test_the_transit_is_inside_the_ilc_band(self):
        """2-5 s. The vessel used to hold the meal for 670."""

        transit, _, _, _ = self._transit(25.0e-6)

        self.assertAlmostEqual(transit, 2.03, delta=0.02)
        self.assertGreaterEqual(transit, 2.0)
        self.assertLessEqual(transit, 5.0)

        self.assertGreater(670.1 / transit, 100.0)

    def test_the_particle_size_does_not_decide_it(self):
        """The plateau. Every defensible meal size lands within
        2 % of the same transit, so the one uncertain input here
        cannot be used to steer the answer."""

        transits = [
            self._transit(d)[0]
            for d in (10.0e-6, 25.0e-6, 50.0e-6, 90.0e-6)
        ]

        self.assertLess(max(transits) / min(transits) - 1.0, 0.03)

        for transit in transits:
            self.assertGreaterEqual(transit, 2.0)
            self.assertLessEqual(transit, 5.0)

    def test_the_slip_is_a_fraction_of_a_percent(self):
        """Which is the physical content of pneumatic conveying:
        the meal goes where the gas goes. It is also why these
        vessels hold solids for SECONDS while a rotary kiln holds
        its bed for half an hour."""

        _, u_g, u_t, _ = self._transit(25.0e-6)

        self.assertAlmostEqual(u_g, 12.36, delta=0.02)
        self.assertLess(100.0 * u_t / u_g, 0.2)

    def test_the_suspension_is_dilute(self):
        """~6e-5 by volume, against the 0.10 the packed-bed
        treatment asserted -- three orders of magnitude apart, and
        the reason the hold-up was so wrong."""

        _, _, _, frac = self._transit(25.0e-6)

        self.assertLess(frac, 1.0e-4)
        self.assertGreater(frac, 1.0e-5)
        self.assertLess(frac, 0.10 / 1000.0)

    def test_continuity_closes_on_the_particle_density(self):

        u_s, _, _, frac = suspension_transport(
            m_dot_g=self.M_DOT_G, m_dot_s=self.M_DOT_S,
            rho_g=self.rho_g, A_cross=self.A, d_p=25.0e-6,
            rho_particle=RHO_PARTICLE, mu=self.mu, eps=1e-9,
        )

        self.assertAlmostEqual(
            frac,
            self.M_DOT_S / (RHO_PARTICLE * u_s * self.A),
            places=12,
        )

    def test_a_gas_too_slow_to_lift_the_meal_is_refused(self):
        """Not clamped. A vessel that would fill is a statement
        about the plant."""

        with self.assertRaises(ValueError) as caught:
            suspension_transport(
                m_dot_g=0.01, m_dot_s=self.M_DOT_S,
                rho_g=self.rho_g, A_cross=self.A, d_p=90.0e-6,
                rho_particle=RHO_PARTICLE, mu=self.mu, eps=1e-9,
            )

        self.assertIn("cannot carry the solids", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
