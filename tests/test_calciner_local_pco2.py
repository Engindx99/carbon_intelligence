"""
The calciner's local CO2 back-pressure.

CalcinationModel rates each riser cell against the CO2 partial pressure
of its own outlet gas (the gas entering the riser plus everything the
meal releases up to and including that cell) instead of the fixed
representative co2_partial_pressure, which the counter-current kiln
zones still use. These pin:

- the default (p_CO2=None) is the fixed constant, bit for bit;
- the chord in reaction_heat_slope is anchored at T_eq of the p it is
  given, an exact zero of the rate at that p;
- a gas with no CO2 holds nothing back;
- a co-current march: p rises cell by cell, and the last cell's p is
  the mole fraction of the gas that leaves.
"""
import math
import unittest

import numpy as np

from chemistry.calcination import CalcinationModel
from physics.gas_thermo import add, air, burn_in, mole_fraction, MOLAR_MASS
from physics.physics import FUEL_COMPOSITION
from pyroprocess.globalstate import GlobalState


class OptionalBackPressureTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_none_is_the_fixed_constant(self):
        m = self.model
        p = m.co2_partial_pressure
        for T in (1050.0, 1100.0, 1150.0):
            with self.subTest(T=T):
                self.assertEqual(m.reaction_rate(T), m.reaction_rate(T, p))
                self.assertEqual(
                    m.reaction_rate_derivative(T),
                    m.reaction_rate_derivative(T, p),
                )
                self.assertEqual(
                    m.reaction_heat_slope(10.0, T, 0.2),
                    m.reaction_heat_slope(10.0, T, 0.2, p),
                )
        self.assertEqual(
            m.rate_vanishing_temperature(),
            m.rate_vanishing_temperature(p),
        )
        T = np.array([1050.0, 1100.0, 1150.0])
        np.testing.assert_array_equal(m.reaction_rate(T), m.reaction_rate(T, p))

    def test_vanishing_temperature_is_an_exact_zero_at_its_p(self):
        m = self.model
        for p in (0.10, 0.25, 0.33):
            with self.subTest(p=p):
                T_v = m.rate_vanishing_temperature(p)
                self.assertAlmostEqual(T_v, m.equilibrium_temperature(p), places=9)
                self.assertEqual(m.reaction_rate(T_v - 1e-9, p), 0.0)
                self.assertGreater(m.reaction_rate(T_v + 1.0, p), 0.0)

    def test_richer_gas_holds_the_reaction_off(self):
        m = self.model
        T = 1100.0
        self.assertGreater(m.reaction_rate(T, 0.25), m.reaction_rate(T, 0.33))
        self.assertGreater(
            m.rate_vanishing_temperature(0.33),
            m.rate_vanishing_temperature(0.25),
        )

    def test_no_co2_holds_nothing_back(self):
        m = self.model
        T = 1000.0
        arrhenius = m.prefactor * math.exp(-m.activation_energy / (m.R * T))
        self.assertAlmostEqual(m.reaction_rate(T, 0.0), arrhenius, places=12)
        self.assertEqual(m.rate_vanishing_temperature(0.0), -math.inf)
        slope = m.reaction_heat_slope(10.0, T, 0.2, 0.0)
        self.assertTrue(math.isfinite(slope))
        self.assertGreaterEqual(slope, 0.0)

    def test_negative_p_is_refused(self):
        with self.assertRaises(ValueError):
            self.model.reaction_rate(1100.0, -0.1)


class CellBackPressureTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_extent_is_consistent_with_its_own_gas(self):
        m = self.model
        n_up, n_CO2 = 3000.0, 600.0           # mol/s, y 0.20
        m_in, T, tau = 50.0, 1110.0, 0.2
        p = m.cell_back_pressure(m_in, T, tau, n_CO2, n_up)
        reacted = m_in * -math.expm1(-m.reaction_rate(T, p) * tau)
        n_c = reacted * m.CO2_ratio / MOLAR_MASS["CO2"]
        self.assertAlmostEqual(p, (n_CO2 + n_c) / (n_up + n_c), places=9)
        # Its own CO2 raises the back-pressure above the incoming gas.
        self.assertGreater(p, n_CO2 / n_up)

    def test_below_the_incoming_equilibrium_nothing_reacts(self):
        m = self.model
        n_up, n_CO2 = 3000.0, 900.0           # y 0.30
        T = m.equilibrium_temperature(0.30) - 5.0
        p = m.cell_back_pressure(50.0, T, 0.2, n_CO2, n_up)
        self.assertAlmostEqual(p, 0.30, places=12)


class CoCurrentMarchTest(unittest.TestCase):

    N = 20

    def _state(self):
        state = GlobalState(N=self.N)
        state.Ts_calciner = np.linspace(1150.0, 1100.0, self.N)
        state.m_dot_s_calciner = 96.0
        state.m_dot_H2O_generated_cells = np.full(self.N, 0.002)
        return state

    def _gas_in(self):
        kiln = add(air(33.0), {"CO2": 8.0, "H2O": 0.5})
        return burn_in(add(kiln, air(44.0)), 3.17, FUEL_COMPOSITION)

    def test_p_rises_and_matches_the_leaving_gas(self):
        m = CalcinationModel()
        state = self._state()
        gas_in = self._gas_in()
        state = m.apply(
            state, 1.5, 10.0,
            m_dot_CaCO3_in=69.0, commit_phases=False, gas_in=gas_in,
        )
        p = np.asarray(state.Calciner_p_CO2_cells)
        self.assertTrue(np.all(np.diff(p) >= 0.0))
        self.assertGreater(p[0], mole_fraction(gas_in, "CO2"))

        released = float(np.sum(state.m_dot_CaCO3_reacted_cells)) * m.CO2_ratio
        gas_out = add(
            gas_in,
            {"CO2": released, "H2O": float(np.sum(state.m_dot_H2O_generated_cells))},
        )
        self.assertAlmostEqual(p[-1], mole_fraction(gas_out, "CO2"), places=9)

    def test_no_gas_keeps_the_constant(self):
        m = CalcinationModel()
        state = m.apply(
            self._state(), 1.5, 10.0,
            m_dot_CaCO3_in=69.0, commit_phases=False,
        )
        np.testing.assert_array_equal(
            state.Calciner_p_CO2_cells,
            np.full(self.N, m.co2_partial_pressure),
        )


if __name__ == "__main__":
    unittest.main()
