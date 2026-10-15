"""
Clay dehydroxylation: sourced kinetics, and the preheater releasing the
clay water before the calciner.

The previous kinetics (1e3 1/s, 120 kJ/mol behind a 723-973 K window)
released 0.04 of 1.87 kg/s, and the rest reached the clinker. These pin
the sourced replacement (Cheng et al. 2021, first-order at the same
t90) against what clay does, the oxide-route reaction enthalpy, and the
preheater's flow form conserving mass.
"""
import math
import unittest

import numpy as np

from chemistry.dehydroxylation import DehydroxylationModel
from chemistry.phases import raw_meal_solid_flow
from chemistry.reactions import ChemistryModel
from pyroprocess.globalstate import GlobalState


def t90(model, T):
    return math.log(10.0) / float(model.reaction_rate(T))


class SourcedKineticsTest(unittest.TestCase):

    def setUp(self):
        self.model = DehydroxylationModel()

    def test_first_order_matches_the_a23_t90(self):
        # A2/3: [-ln(1 - a)]^1.5 = k t. At a = 0.9 the first-order
        # rate must give the same time.
        k_a23 = 10.0 ** 9.44588 * math.exp(
            -self.model.activation_energy / (self.model.R * 1000.0)
        )
        t_a23 = math.log(10.0) ** 1.5 / k_a23
        self.assertAlmostEqual(t90(self.model, 1000.0), t_a23, places=9)

    def test_against_what_clay_does(self):
        m = self.model
        # Flash calcination: done within about a second at 800 C.
        self.assertLess(t90(m, 1073.15), 1.5)
        # The preheater's bottom stage (~1000 K, a few s of gas
        # residence) releases most of it.
        self.assertLess(t90(m, 1000.0), 10.0)
        # The top stage (~575 K) releases nothing.
        self.assertGreater(t90(m, 575.0), 1.0e6)

    def test_no_window_and_no_chord_anchor(self):
        m = self.model
        arrhenius = m.prefactor * math.exp(-m.activation_energy / (m.R * 1200.0))
        self.assertAlmostEqual(m.reaction_rate(1200.0), arrhenius, places=12)
        self.assertEqual(m.rate_vanishing_temperature(), -math.inf)

    def test_derivative_is_the_arrhenius_slope(self):
        m = self.model
        T, h = 1000.0, 1e-3
        numeric = (m.reaction_rate(T + h) - m.reaction_rate(T - h)) / (2 * h)
        self.assertAlmostEqual(
            m.reaction_rate_derivative(T) / numeric, 1.0, places=6
        )

    def test_oxide_route_enthalpy(self):
        # Robie & Hemingway (1995) standard enthalpies of formation.
        dH = (-1675.7 + 2 * -910.7 + 2 * -241.8) - (-4119.6)    # kJ/mol
        per_kg_water = dH * 1e3 / (2 * 0.0180153)
        self.assertAlmostEqual(self.model.deltaH / per_kg_water, 1.0, delta=0.01)


class PreheaterReleaseTest(unittest.TestCase):

    def _state(self, Ts):
        state = GlobalState(N=20)
        state.Ts_preheater = np.asarray(Ts, dtype=float)
        state.m_dot_s_preheater = 89.7
        return state

    def test_mass_moves_from_solid_to_gas(self):
        chem = ChemistryModel()
        state = self._state([1018.0, 907.0, 760.0, 575.0])
        state = chem.apply_preheater(state, np.full(4, 3.0))

        feed = raw_meal_solid_flow(89.7)
        flows = state.material_flows["preheater"]
        solid_out = sum(
            float(getattr(flows.solids, sp)[0]) for sp in feed
            if hasattr(flows.solids, sp)
        )
        gas = float(np.sum(flows.gases.H2O))

        self.assertAlmostEqual(solid_out + gas, sum(feed.values()), places=9)
        self.assertAlmostEqual(gas, state.m_dot_H2O_evaporated_preheater, places=12)

        released = state.m_dot_BoundH2O_reacted_preheater
        self.assertAlmostEqual(
            feed["Bound_H2O"] - float(flows.solids.Bound_H2O[0]),
            released,
            places=12,
        )
        # Most of the clay water leaves before the calciner.
        self.assertGreater(released / feed["Bound_H2O"], 0.8)

        self.assertAlmostEqual(
            state.Preheater_Q_sink,
            float(np.sum(state.Preheater_Q_sink_cells)),
            places=6,
        )
        self.assertAlmostEqual(
            state.Dehydroxylation_Q_sink_preheater,
            released * chem.dehydroxylation.deltaH,
            delta=1e-6 * state.Dehydroxylation_Q_sink_preheater,
        )


if __name__ == "__main__":
    unittest.main()
