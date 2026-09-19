"""
The reaction-sink linearisation on the solid energy row.

Until now nothing tested this at all: `dQ_dTs` and `slope_cells`
appeared in no test file, so the only thing exercising the device
was the plant solve itself. That is how the first attempt at the
literature calcination rate got as far as a crashed plant before
anyone noticed the slope was wrong -- the failure is visible in a
single cell, and this file is where it should be caught.

Three properties, in the order they matter:

  1. THE CANCELLATION IDENTITY. The diagonal-and-b pair that
     `apply_solid_energy_balance` builds must reconstruct the sink
     exactly at Ts == Ts*, whatever S is. This is what lets the
     slope be chosen for stability rather than accuracy, and it is
     why the converged answer cannot depend on it.
  2. THE SLOPE IS NEVER WEAKER THAN THE TANGENT, and never
     negative. A negative slope would remove diagonal dominance
     instead of adding it.
  3. THE CELL BEHAVES. A heat-starved cell settles on the plateau
     absorbing what it has; a heat-rich cell reaches the same
     fixed point the tangent would.
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
from physics.variable_flow_rows import apply_solid_energy_balance


# A one-cell solid row with everything but the sink switched off,
# so what the assertions see is the linearisation and nothing
# else. Returns the coefficient on Ts and the value in b.
def solid_row(Q_reaction_cell, dQ_dTs_cell, Ts_star_cell, Ts_in=1000.0):

    N = 1
    A = np.zeros((3 * N, 3 * N))
    b = np.zeros(3 * N)

    apply_solid_energy_balance(
        A,
        b,
        row=0,
        i=0,
        N=N,
        Cs_out=0.0,
        Cs_in=0.0,
        T_ref=0.0,
        dm_gas=0.0,
        cp_gas_s=0.0,
        h_const_s=0.0,
        V_cell=0.0,
        K_gs=0.0,
        K_ws=0.0,
        radiation_solid_source=0.0,
        Q_reaction_cell=Q_reaction_cell,
        Ts_in=Ts_in,
        dQ_dTs_cell=dQ_dTs_cell,
        Ts_star_cell=Ts_star_cell,
    )

    # Ts is unknown index N + i == 1.
    return A[0, 1], b[0]


# The sink the row actually applies at a given Ts:
#   b holds -(Q(Ts*) - S Ts*) and the diagonal holds +S, so the
#   sink the balance sees is  S*Ts - b_sink_part.
def applied_sink(Q_reaction_cell, S, Ts_star, Ts):

    coeff, b = solid_row(Q_reaction_cell, S, Ts_star)

    return coeff * Ts - b


class CancellationIdentityTest(unittest.TestCase):
    """
    Q_eff(Ts*) == Q(Ts*) for ANY S. This is the whole licence for
    picking S on stability grounds, so it is checked over slopes
    spanning twenty orders of magnitude, including zero.
    """

    def test_reconstructs_the_sink_at_the_linearisation_point(self):

        Q = 3.612e7
        Ts_star = 1223.15

        # Bit-exact over fourteen orders of magnitude, measured.
        # The chord produces at most ~1.4e7 W/K in this plant, so
        # this range clears anything the model can ask for by
        # seven orders.
        for S in [
            0.0,
            1.0,
            1.0e3,
            2.667e5,
            1.0e7,
            1.0e10,
            1.0e14,
        ]:

            with self.subTest(S=S):

                self.assertEqual(
                    applied_sink(Q, S, Ts_star, Ts_star),
                    Q,
                    msg=f"sink not reconstructed at Ts* with S={S:.3e}",
                )

    def test_the_reconstruction_has_a_round_off_ceiling(self):
        """
        The identity is exact in arithmetic but not in doubles:
        b carries S*Ts*, and recovering Q from it costs
        log10(S*Ts*/Q) digits. Measured for Q = 3.6e7 at
        Ts* = 1223 K: exact through S = 1e14, 1.6e-5 relative at
        1e16, 7e-2 at 1e20.

        Recorded rather than avoided, because it is the one way
        the slope could be pushed too far -- a future anchor that
        made the chord span vanish would send S through this
        ceiling, and the symptom would be a sink quietly wrong by
        a few percent rather than an exception.
        """

        Q = 3.612e7
        Ts_star = 1223.15

        self.assertEqual(applied_sink(Q, 1.0e14, Ts_star, Ts_star), Q)

        degraded = applied_sink(Q, 1.0e20, Ts_star, Ts_star)

        self.assertNotEqual(degraded, Q)

        self.assertAlmostEqual(degraded / Q, 1.0, delta=0.1)

    def test_zero_slope_reproduces_the_frozen_source(self):
        """
        With S = 0 the row must be exactly what it was before the
        linearisation existed: the sink a plain constant in b.
        """

        Q = 1.234e6

        coeff, b = solid_row(Q, 0.0, 1500.0)

        self.assertEqual(coeff, 0.0)
        self.assertEqual(b, -Q)

    def test_slope_makes_the_sink_vanish_at_the_chord_anchor(self):
        """
        With S set to the chord, the applied sink is zero at the
        temperature where the reaction stops -- the statement the
        tangent cannot make.
        """

        model = CalcinationModel()

        T_vanish = model.rate_vanishing_temperature()
        Ts_star = T_vanish + 140.0
        Q = 3.6e7

        S = Q / (Ts_star - T_vanish)

        self.assertAlmostEqual(
            applied_sink(Q, S, Ts_star, T_vanish),
            0.0,
            delta=1.0e-6 * Q,
        )


class SlopeChoiceTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_slope_is_never_weaker_than_the_tangent(self):
        """
        reaction_heat_slope takes max(tangent, chord), so it can
        only ever damp more than the derivative alone. Swept over
        temperature and five decades of residence.
        """

        available = 20.3

        for dt in [1.0e-3, 0.1, 1.0, 66.0, 1.0e3]:

            for T in np.linspace(300.0, 2200.0, 200):

                T = float(T)

                tangent = self.model.reaction_heat_derivative(
                    available, T, dt
                )

                slope = self.model.reaction_heat_slope(
                    available, T, dt
                )

                self.assertGreaterEqual(
                    slope,
                    tangent - 1.0e-9 * max(abs(tangent), 1.0),
                    msg=f"slope below tangent at {T:.1f} K, dt={dt}",
                )

                self.assertGreaterEqual(
                    slope,
                    0.0,
                    msg=f"negative slope at {T:.1f} K, dt={dt}",
                )

    def test_slope_survives_where_the_tangent_dies(self):
        """
        The measurement that forced this change. Well above the
        stopping temperature the reaction has converted everything
        it holds, the heat saturates and the tangent collapses to
        nothing -- while the sink it is supposed to hold is at its
        maximum. The chord must not collapse with it.
        """

        available = 20.3
        T = self.model.rate_vanishing_temperature() + 400.0

        # Residence taken from the local rate so that k*dt = 100
        # whatever the rate law is. Writing a number here instead
        # would make the test a statement about today's kinetic
        # constants rather than about saturation.
        dt = 100.0 / float(self.model.reaction_rate(T))

        tangent = self.model.reaction_heat_derivative(available, T, dt)
        slope = self.model.reaction_heat_slope(available, T, dt)

        heat = (
            self.model.reacted_mass(
                available,
                float(self.model.reaction_rate(T)),
                dt,
            )
            * self.model.deltaH
        )

        # The reaction really is saturated here, otherwise this
        # test is not testing what it claims to.
        self.assertGreater(heat, 0.99 * available * self.model.deltaH)

        self.assertLess(tangent, 1.0e-6 * slope)

        self.assertGreater(slope, 0.0)

    def test_is_zero_without_mass_or_time(self):

        self.assertEqual(
            self.model.reaction_heat_slope(0.0, 1400.0, 1.0), 0.0
        )

        self.assertEqual(
            self.model.reaction_heat_slope(20.3, 1400.0, 0.0), 0.0
        )

    def test_falls_back_to_the_tangent_below_the_stopping_point(self):
        """
        At or below the vanishing temperature there is no chord to
        take -- Q is zero and so is its secant -- so the method
        must return the tangent rather than divide by a
        non-positive span.
        """

        T_vanish = self.model.rate_vanishing_temperature()

        for T in [T_vanish - 200.0, T_vanish - 1.0, T_vanish]:

            self.assertEqual(
                self.model.reaction_heat_slope(20.3, T, 66.0),
                self.model.reaction_heat_derivative(20.3, T, 66.0),
                msg=f"expected the tangent at {T:.1f} K",
            )

    def test_dehydroxylation_gets_the_same_device(self):
        """
        The chord lives on ReactionBase and anchors on
        rate_vanishing_temperature, which the window law supplies
        as T_start. So a second reaction inherits it without
        knowing anything about calcination's equilibrium.
        """

        model = DehydroxylationModel()

        self.assertEqual(
            model.rate_vanishing_temperature(),
            model.T_start,
        )

        T = model.T_start + 600.0

        self.assertGreaterEqual(
            model.reaction_heat_slope(1.0, T, 66.0),
            model.reaction_heat_derivative(1.0, T, 66.0),
        )


class CellFixedPointTest(unittest.TestCase):
    """
    One solid cell, balanced against a fixed heat supply:

        W_s (T - T_in) = Q_supply - Q_eff(T)

    iterated the way the plant iterates it -- chemistry at the
    previous temperature, then the energy equation. This is the
    smallest thing that reproduces the plant's failure mode, and
    it runs in milliseconds.
    """

    W_s = 20.3 * 850.0
    available = 20.3

    def setUp(self):
        self.model = CalcinationModel()

        T_vanish = self.model.rate_vanishing_temperature()

        # The calciner's own starting geometry, expressed
        # relative to the stopping temperature rather than as
        # absolute numbers: it initialises 135 K above the
        # plateau with the meal arriving ~12 K above it.
        self.T_hot_start = T_vanish + 135.0
        self.T_in = T_vanish + 12.0

        # Residence chosen so the reaction is SATURATED at that
        # starting temperature, k*tau = 100. That is the regime
        # the tangent cannot hold, and deriving it from the rate
        # keeps this a test about saturation rather than about
        # whichever kinetic constants are in force.
        self.tau = 100.0 / float(
            self.model.reaction_rate(self.T_hot_start)
        )

        # What full conversion would cost, and therefore what
        # "starved" and "rich" mean here.
        self.Q_full = self.available * self.model.deltaH

    def heat(self, T):

        return (
            self.model.reacted_mass(
                self.available,
                float(self.model.reaction_rate(T)),
                self.tau,
            )
            * self.model.deltaH
        )

    def solve_cell(self, T_in, Q_supply, T_start, use_chord, passes=60):

        T_star = T_start

        for _ in range(passes):

            Q = self.heat(T_star)

            S = (
                self.model.reaction_heat_slope(
                    self.available, T_star, self.tau
                )
                if use_chord
                else self.model.reaction_heat_derivative(
                    self.available, T_star, self.tau
                )
            )

            # W_s(T - T_in) = Q_supply - [Q + S(T - T_star)]
            T_star = (
                Q_supply - Q + S * T_star + self.W_s * T_in
            ) / (self.W_s + S)

        return T_star

    def test_heat_starved_cell_settles_and_conserves(self):
        """
        Far more reaction is kinetically possible than the cell
        can pay for. It must settle just above the stopping
        temperature, absorbing exactly the heat supplied -- not
        run away, and above all not go negative.
        """

        # ~14% of what full conversion costs -- the plant's own
        # ratio, ~5 MW present against ~36 MW demanded.
        Q_supply = 0.14 * self.Q_full

        T = self.solve_cell(
            self.T_in, Q_supply, self.T_hot_start, use_chord=True
        )

        T_vanish = self.model.rate_vanishing_temperature()

        self.assertGreater(T, T_vanish - 1.0)
        self.assertLess(T, T_vanish + 60.0)

        # Energy closes on the TRUE heat at the converged
        # temperature, not on the linearised stand-in.
        self.assertAlmostEqual(
            self.W_s * (T - self.T_in) + self.heat(T),
            Q_supply,
            delta=1.0e-6 * Q_supply,
        )

    def test_heat_starved_cell_goes_negative_without_the_chord(self):
        """
        The failure this whole change exists to remove. Kept as a
        test so that anyone who later replaces the chord with the
        tangent finds out here instead of from a crashed plant.
        """

        T = self.solve_cell(
            self.T_in,
            0.14 * self.Q_full,
            self.T_hot_start,
            use_chord=False,
            passes=1,
        )

        self.assertLess(T, 0.0)

    def test_heat_rich_cell_reaches_the_same_fixed_point(self):
        """
        The chord must not buy its robustness with a biased
        answer. Where the cell has heat to spare the reaction
        really does run to completion, and chord and tangent have
        to agree -- which is the cancellation identity showing up
        in the solved temperature.
        """

        T_in = self.T_hot_start
        Q_supply = 2.0 * self.Q_full

        chord = self.solve_cell(
            T_in, Q_supply, self.T_hot_start, use_chord=True
        )
        tangent = self.solve_cell(
            T_in, Q_supply, self.T_hot_start, use_chord=False
        )

        self.assertAlmostEqual(chord, tangent, delta=1.0e-6 * chord)

        self.assertAlmostEqual(
            self.W_s * (chord - T_in) + self.heat(chord),
            Q_supply,
            delta=1.0e-6 * Q_supply,
        )

    def test_converges_from_anywhere(self):
        """
        Robustness is the point, so the starting temperature is
        swept across and well beyond the operating range. Every
        start must reach the same place.
        """

        Q_supply = 0.14 * self.Q_full

        reference = self.solve_cell(
            self.T_in, Q_supply, self.T_hot_start, use_chord=True
        )

        T_vanish = self.model.rate_vanishing_temperature()

        for offset in [-200.0, -40.0, 0.0, 135.0, 400.0, 900.0, 1900.0]:

            T_start = T_vanish + offset

            with self.subTest(T_start=T_start):

                self.assertAlmostEqual(
                    self.solve_cell(
                        self.T_in, Q_supply, T_start, use_chord=True
                    ),
                    reference,
                    delta=1.0e-6 * reference,
                )


if __name__ == "__main__":
    unittest.main()
