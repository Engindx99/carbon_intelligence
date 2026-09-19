"""T_gas_from_h: the enthalpy -> temperature inversion, and the
silent clamp that used to sit on both ends of it.

The clamp was not a harmless convenience. On the
literature-kinetics tree it destroyed 7.281181e5 W at the
burning -> transition gas handoff, which was precisely the
residual by which two of the fourteen balances were failing.
These tests pin the raise, and pin the measured case that
exposed it.
"""

import math
import unittest

from physics.physics import cp_gas, h_gas, T_gas_from_h


T_REF = 298.15


class RoundTripTest(unittest.TestCase):

    def test_inverts_h_gas_over_the_working_range(self):

        for T in (300.0, 500.0, 900.0, 1500.0, 2200.0, 3000.0, 3900.0):

            h = h_gas(T, T_REF)
            back = T_gas_from_h(h, T_REF, T_REF, 4000.0)

            self.assertAlmostEqual(back, T, places=6)

    def test_the_bounds_themselves_are_exact_answers(self):
        """Raising must not reject the window's own endpoints."""

        self.assertAlmostEqual(
            T_gas_from_h(h_gas(4000.0, T_REF), T_REF, T_REF, 4000.0),
            4000.0,
            places=9,
        )
        self.assertAlmostEqual(
            T_gas_from_h(h_gas(T_REF, T_REF), T_REF, T_REF, 4000.0),
            T_REF,
            places=9,
        )


class OutOfWindowRaisesTest(unittest.TestCase):

    def test_above_the_window(self):

        h = h_gas(4000.0, T_REF) * 1.01

        with self.assertRaises(ValueError) as caught:
            T_gas_from_h(h, T_REF, T_REF, 4000.0)

        self.assertIn("above the inversion window", str(caught.exception))

    def test_below_the_window(self):

        h = h_gas(T_REF, T_REF) - 1.0e5

        with self.assertRaises(ValueError) as caught:
            T_gas_from_h(h, T_REF, T_REF, 4000.0)

        self.assertIn("below the inversion window", str(caught.exception))

    # ------------------------------------------------------
    # The measured case. Reproduced from the converged
    # literature-kinetics plant at nodes_per_stage=1:
    #   m_dot_g                    = 14.9204 kg/s
    #   Hgas_transition_in/m_dot_g = 4.728007e6 J/kg
    #   h_gas(4000 K)              = 4.679207e6 J/kg
    # The gas wanted 4037.9 K, the window stopped at 4000.0,
    # and the difference times the flow is the balance
    # residual to every digit.
    # ------------------------------------------------------
    def test_the_transition_handoff_case_is_rejected_not_clamped(self):

        m_dot_g = 14.9204
        h_target = 4.728007e6

        h_bound = h_gas(4000.0, T_REF)

        self.assertGreater(h_target, h_bound)

        leak_W = (h_target - h_bound) * m_dot_g

        # The failing Transition and Pyroprocess balances.
        self.assertAlmostEqual(leak_W, 7.281181e5, delta=2.0e2)

        with self.assertRaises(ValueError):
            T_gas_from_h(h_target, T_REF, T_REF, 4000.0)

    def test_the_true_temperature_is_recoverable_with_a_wider_window(self):
        """Widening is NOT the fix, but it shows what was lost."""

        T = T_gas_from_h(4.728007e6, T_REF, T_REF, 6000.0)

        self.assertAlmostEqual(T, 4037.9, delta=0.1)


class MonotonicityCaveatTest(unittest.TestCase):
    """h_gas is the analytic cubic integral of cp_gas.

    cp_gas floors at 1050 J/(kg K); h_gas does NOT carry that
    floor, so the inverse stops being unique far above the
    working range. This pins where the docstring's promise
    actually holds, so nobody widens T_max past it casually.
    """

    def test_h_gas_increases_through_the_documented_range(self):

        previous = None

        for T in range(300, 8001, 100):

            h = h_gas(float(T), T_REF)

            if previous is not None:
                self.assertGreater(h, previous, f"at {T} K")

            previous = h

    @staticmethod
    def _unfloored_cp(T):
        return 1050.0 + 0.18 * T - 3.0e-5 * T * T

    def test_cp_gas_floors_where_the_polynomial_falls_below_it(self):

        # At 7000 K the polynomial is already under the floor,
        # so cp_gas returns the floor while h_gas -- the
        # analytic integral -- keeps following the polynomial.
        self.assertLess(self._unfloored_cp(7000.0), 1050.0)
        self.assertAlmostEqual(cp_gas(7000.0), 1050.0, places=6)

    def test_the_integrand_turns_negative_far_above_the_range(self):
        """Where h_gas stops being invertible at all.

        3e-5 T^2 - 0.18 T - 1050 = 0 puts the crossing near
        9633 K. That is the real ceiling on any widening of
        T_max, and it is 2.4x above the 4000 K window -- so the
        window is a modelling choice, not a numerical necessity,
        which is exactly why silently clamping at it was
        indefensible.
        """

        crossing = (
            0.18 + math.sqrt(0.18 ** 2 + 4.0 * 3.0e-5 * 1050.0)
        ) / (2.0 * 3.0e-5)

        self.assertAlmostEqual(crossing, 9633.0, delta=5.0)

        self.assertGreater(self._unfloored_cp(crossing - 100.0), 0.0)
        self.assertLess(self._unfloored_cp(crossing + 100.0), 0.0)


if __name__ == "__main__":
    unittest.main()
