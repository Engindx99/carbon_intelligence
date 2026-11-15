"""Belite follows the measured Jander law of Alonso, Fernandez &
Abanades, Ind. Eng. Chem. Res. 58 (2019) 5445 (chemistry/belite.py).

    [1 - (1 - X)^(1/3)]^2 = k t,   k = k0 exp(-Ea / R T)

X is the molar share of the meal's calcium in belite. Table 2,
raw meal RM1: k0 = 6.61e10 1/s, Ea = 325 kJ/mol.
"""

import math
import unittest

from chemistry.belite import BeliteModel

R = 8.314

# A calcined marl like Alonso's RM1: CaO ~42 %, SiO2 ~14 % (Table 1).
MEAL = {
    "CaO": 42.0, "SiO2": 14.0, "CaCO3": 0.0,
    "C2S": 0.0, "C3S": 0.0, "C3A": 0.0, "C4AF": 0.0,
    "Al2O3": 4.0, "Fe2O3": 2.0,
}

M = {"Ca": 0.04008, "Si": 0.02809}
CA_SHARE = {  # kg Ca per kg species
    "CaO": 0.04008 / 0.05608, "CaCO3": 0.04008 / 0.10009,
    "C2S": 2 * 0.04008 / 0.17224, "C3S": 3 * 0.04008 / 0.22832,
}
SI_SHARE = {
    "SiO2": 0.02809 / 0.06008, "C2S": 0.02809 / 0.17224,
    "C3S": 0.02809 / 0.22832,
}


def _element(flow, share):
    return sum(flow.get(k, 0.0) * v for k, v in share.items())


def _X(model, flow):
    return model._conversion(flow, model._calcium_moles(flow))


def _react(T, t, steps=1):
    model = BeliteModel()
    flow = dict(MEAL)
    k = float(model.reaction_rate(T))
    for _ in range(steps):
        model.react_flow(flow, T, t / steps, k)
    return model, flow


class TheLawIsTable2Test(unittest.TestCase):

    def test_parameters(self):
        model = BeliteModel()
        self.assertEqual(model.prefactor, 6.61e10)
        self.assertEqual(model.activation_energy, 3.25e5)

    def test_closed_form(self):
        """X after t is the Jander inverse of k t, from X = 0."""
        T, t = 1163.15, 240.0
        k = 6.61e10 * math.exp(-3.25e5 / (R * T))
        X_expected = 1.0 - (1.0 - math.sqrt(k * t)) ** 3
        model, flow = _react(T, t)
        self.assertAlmostEqual(_X(model, flow), X_expected, places=9)

    def test_reproduces_the_paper(self):
        """RM1 reaches X ~ 0.5 at 890 C "in barely 4 min" (Fig. 6a)."""
        model, flow = _react(890.0 + 273.15, 240.0)
        self.assertGreater(_X(model, flow), 0.45)
        self.assertLess(_X(model, flow), 0.55)


class TheIntegralIsExactTest(unittest.TestCase):

    def test_split_invariance(self):
        """The conversion is read off the composition, so 240 steps of
        1 s land where one step of 240 s does."""
        m1, f1 = _react(1163.15, 240.0, steps=1)
        m2, f2 = _react(1163.15, 240.0, steps=240)
        self.assertAlmostEqual(_X(m1, f1), _X(m2, f2), places=10)

    def test_elements_and_mass_are_conserved(self):
        _, flow = _react(1250.0, 600.0)
        self.assertAlmostEqual(sum(flow.values()), sum(MEAL.values()), places=10)
        self.assertAlmostEqual(_element(flow, CA_SHARE), _element(MEAL, CA_SHARE), places=10)
        self.assertAlmostEqual(_element(flow, SI_SHARE), _element(MEAL, SI_SHARE), places=10)

    def test_alite_does_not_move_X_back(self):
        """C2S + CaO -> C3S keeps the silicon combined."""
        model, flow = _react(1163.15, 240.0)
        X = _X(model, flow)
        moved = 0.5 * flow["C2S"]
        flow["C2S"] -= moved
        flow["CaO"] -= moved * 0.05608 / 0.17224
        flow["C3S"] += moved * 0.22832 / 0.17224
        self.assertAlmostEqual(_X(model, flow), X, places=10)

    def test_silica_is_the_ceiling(self):
        """At kiln temperatures the reaction ends when SiO2 is gone,
        never beyond."""
        _, flow = _react(1700.0, 3600.0)
        self.assertGreaterEqual(flow["SiO2"], 0.0)
        self.assertLess(flow["SiO2"], 1e-9 * MEAL["SiO2"])
        self.assertGreaterEqual(flow["CaO"], 0.0)


class TheSubstepRateIsBoundedTest(unittest.TestCase):

    def test_finite_when_the_silica_runs_out(self):
        model = BeliteModel()
        flow = dict(MEAL)
        r = model.substep_rate(flow, float(model.reaction_rate(1700.0)), 100.0)
        self.assertTrue(math.isfinite(r))
        self.assertAlmostEqual(r, -math.log(1e-6) / 100.0, places=9)

    def test_zero_without_silica(self):
        model = BeliteModel()
        flow = dict(MEAL, SiO2=0.0)
        self.assertEqual(model.substep_rate(flow, 1.0, 10.0), 0.0)


if __name__ == "__main__":
    unittest.main()
