"""
The analytic derivative of the reaction rate and of the reaction
heat, which physics.variable_flow_rows.apply_solid_energy_balance
moves onto the solid row's diagonal.

Two things are being checked, and the second is the one that
matters for stability:

  1. the derivative is the derivative -- central finite
     differences agree to the accuracy a second-order difference
     can deliver on a function this steep;
  2. it is NON-NEGATIVE everywhere. That is the sign Patankar's
     source-term rule requires (S_P = -dQ/dTs <= 0). If it ever
     went negative the linearisation would REMOVE diagonal
     dominance instead of adding it, and the solve would be less
     stable than the frozen-source form it replaces.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from chemistry.calcination import CalcinationModel
from chemistry.dehydroxylation import DehydroxylationModel


# Central differences on f with a step scaled to T. The rate
# spans orders of magnitude, so an absolute step that suits
# 900 K is wrong at 1600 K.
def central_difference(f, T, relative_step=1.0e-6):

    h = relative_step * T

    return (f(T + h) - f(T - h)) / (2.0 * h)


class RateDerivativeTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_matches_central_differences_across_the_window(self):
        """
        The analytic rate slope reproduces a central difference.

        Sampled inside the reaction window and above it, where
        the window is clipped and only the Arrhenius factor
        carries a slope.
        """

        for T in [
            1100.0,
            1150.0,
            1200.0,
            1250.0,
            1299.0,
            1350.0,
            1500.0,
            1800.0,
        ]:

            analytic = self.model.reaction_rate_derivative(T)

            numeric = central_difference(
                lambda t: float(self.model.reaction_rate(t)),
                T,
            )

            self.assertGreater(
                abs(numeric),
                0.0,
                msg=f"degenerate finite difference at {T} K",
            )

            self.assertAlmostEqual(
                analytic / numeric,
                1.0,
                places=4,
                msg=(
                    f"rate slope at {T} K: analytic {analytic:.6e} "
                    f"vs numeric {numeric:.6e}"
                ),
            )

    def test_is_zero_below_onset(self):
        """
        Below T_start the window clips to zero and so does its
        slope, so the rate has no response to temperature.
        """

        for T in [400.0, 800.0, 1000.0, self.model.T_start - 1.0]:

            self.assertEqual(
                self.model.reaction_rate_derivative(T),
                0.0,
                msg=f"expected a dead rate slope at {T} K",
            )

    def test_is_never_negative(self):
        """
        The sign the linearisation depends on, over a range
        wider than any cell the plant produces.
        """

        T = np.linspace(300.0, 2200.0, 4000)

        slope = self.model.reaction_rate_derivative(T)

        self.assertTrue(
            np.all(slope >= 0.0),
            msg=(
                "negative rate slope at "
                f"{T[np.argmin(slope)]:.1f} K"
            ),
        )

    def test_scalar_and_array_paths_agree(self):
        """
        The scalar fast path is the array path, not a variant
        of it. Same requirement reacted_mass carries.
        """

        temperatures = [
            500.0,
            1073.0,
            1100.0,
            1200.0,
            1400.0,
            1900.0,
        ]

        array = self.model.reaction_rate_derivative(
            np.array(temperatures)
        )

        for T, from_array in zip(temperatures, array):

            self.assertAlmostEqual(
                self.model.reaction_rate_derivative(T),
                float(from_array),
                delta=1.0e-15 + 1.0e-12 * abs(float(from_array)),
                msg=f"paths disagree at {T} K",
            )

    def test_dehydroxylation_derivative_is_also_consistent(self):
        """
        The derivative lives on ReactionBase, so every reaction
        that uses the base rate law gets it. Checked on a second
        model so the implementation cannot quietly depend on
        calcination's particular constants.
        """

        model = DehydroxylationModel()

        T = 0.5 * (model.T_start + model.T_end)

        analytic = model.reaction_rate_derivative(T)

        numeric = central_difference(
            lambda t: float(model.reaction_rate(t)),
            T,
        )

        self.assertAlmostEqual(
            analytic / numeric,
            1.0,
            places=4,
        )


class HeatDerivativeTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_matches_central_differences(self):
        """
        dQ/dT for a cell holding `available` kg/s of CaCO3 for
        `dt` seconds, against a central difference of the heat
        itself.
        """

        available = 20.3
        dt = 0.8

        def heat(T):
            return (
                self.model.reacted_mass(
                    available,
                    float(self.model.reaction_rate(T)),
                    dt,
                )
                * self.model.deltaH
            )

        for T in [1100.0, 1150.0, 1200.0, 1400.0, 1700.0]:

            analytic = self.model.reaction_heat_derivative(
                available,
                T,
                dt,
            )

            numeric = central_difference(heat, T)

            self.assertGreater(abs(numeric), 0.0)

            self.assertAlmostEqual(
                analytic / numeric,
                1.0,
                places=4,
                msg=(
                    f"heat slope at {T} K: analytic "
                    f"{analytic:.6e} vs numeric {numeric:.6e}"
                ),
            )

    def test_is_never_negative(self):
        """
        S >= 0 is what puts the slope on the diagonal with the
        right sign. Swept over temperature and over residence
        time, since dQ/dT carries dt*exp(-k dt) and that factor
        is where a sign error would hide.
        """

        for dt in [1.0e-3, 0.1, 1.0, 10.0, 300.0]:

            for T in np.linspace(300.0, 2200.0, 500):

                self.assertGreaterEqual(
                    self.model.reaction_heat_derivative(
                        20.3,
                        float(T),
                        dt,
                    ),
                    0.0,
                    msg=f"negative heat slope at {T:.1f} K, dt={dt}",
                )

    def test_vanishes_when_the_reaction_is_complete(self):
        """
        Once k*dt is large the cell has already converted
        everything it holds, so more temperature buys no more
        heat and the slope collapses. This is the limit that
        makes the linearisation harmless where the reaction is
        finished, and decisive where it is not.
        """

        available = 20.3
        T = 1400.0

        # Residence times are taken from the rate itself rather
        # than written down, so this stays a statement about
        # k*dt and survives a change of rate law.
        k = float(self.model.reaction_rate(T))

        short = self.model.reaction_heat_derivative(
            available,
            T,
            0.01 / k,
        )

        long = self.model.reaction_heat_derivative(
            available,
            T,
            100.0 / k,
        )

        self.assertGreater(short, 0.0)

        self.assertLess(long, 1.0e-6 * short)

    def test_is_zero_without_mass_or_time(self):

        self.assertEqual(
            self.model.reaction_heat_derivative(0.0, 1400.0, 1.0),
            0.0,
        )

        self.assertEqual(
            self.model.reaction_heat_derivative(20.3, 1400.0, 0.0),
            0.0,
        )

    def test_scales_linearly_with_available_mass(self):
        """
        `available` is held fixed inside the derivative, so it
        factors out exactly. This is what lets a caller build
        the per-cell slope from the per-cell inlet flow without
        re-deriving anything.
        """

        base = self.model.reaction_heat_derivative(1.0, 1200.0, 0.5)

        self.assertAlmostEqual(
            self.model.reaction_heat_derivative(7.5, 1200.0, 0.5),
            7.5 * base,
            delta=1.0e-9 * abs(7.5 * base),
        )


if __name__ == "__main__":
    unittest.main()
