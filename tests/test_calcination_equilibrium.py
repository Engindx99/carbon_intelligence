"""
CaCO3 decomposition equilibrium closure.

These pin the two anchors the closure is built from and the tabulated
decomposition curve it has to reproduce. A replacement for
CalcinationModel.equilibrium_pressure must clear the same table.
"""
import math
import unittest

from chemistry.calcination import CalcinationModel


# Tabulated equilibrium CO2 pressure over CaCO3 [atm].
# Spans four orders of magnitude, which is what makes this a test of
# the dH/dS pair rather than of a single point.
DECOMPOSITION_CURVE = {
    873.0: 0.0024,
    973.0: 0.028,
    1073.0: 0.22,
    1173.0: 1.04,
    1273.0: 3.9,
}

# Worst deviation over the table above. The closure is a two-parameter
# thermodynamic form, not a fit, so it is not expected to be exact --
# but it must stay this close, or the anchors have drifted.
MAX_DEVIATION = 0.20


class EquilibriumPressureTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_molar_enthalpy_matches_the_reaction_deltaH(self):
        # The molar value must be derived from this model's own
        # deltaH, not stated independently, or the two can drift.
        self.assertAlmostEqual(
            self.model.dH_molar,
            self.model.deltaH * self.model.M_CaCO3,
            places=9,
        )
        # Open calciner literature quotes 179.4 kJ/mol.
        self.assertAlmostEqual(
            self.model.dH_molar / 1000.0, 179.4, delta=2.0
        )

    def test_one_atmosphere_at_the_anchor_temperature(self):
        p = self.model.equilibrium_pressure(
            self.model.T_equilibrium_1atm
        )
        self.assertAlmostEqual(p, 1.0, places=6)

    def test_reproduces_the_decomposition_curve(self):
        for T, tabulated in DECOMPOSITION_CURVE.items():
            with self.subTest(T=T):
                modelled = self.model.equilibrium_pressure(T)
                deviation = abs(modelled - tabulated) / tabulated
                self.assertLess(
                    deviation,
                    MAX_DEVIATION,
                    f"T={T} K: {modelled:.5g} vs {tabulated:.5g} atm "
                    f"({100.0 * deviation:.1f}% off)",
                )

    def test_pressure_increases_with_temperature(self):
        temperatures = sorted(DECOMPOSITION_CURVE)
        pressures = [
            self.model.equilibrium_pressure(T) for T in temperatures
        ]
        self.assertEqual(pressures, sorted(pressures))

    def test_rejects_non_physical_temperature(self):
        for T in (0.0, -5.0):
            with self.subTest(T=T):
                with self.assertRaises(ValueError):
                    self.model.equilibrium_pressure(T)


class EquilibriumTemperatureTest(unittest.TestCase):

    def setUp(self):
        self.model = CalcinationModel()

    def test_is_the_inverse_of_equilibrium_pressure(self):
        for T in (900.0, 1050.0, 1170.0, 1300.0, 1500.0):
            with self.subTest(T=T):
                p = self.model.equilibrium_pressure(T)
                self.assertAlmostEqual(
                    self.model.equilibrium_temperature(p), T, places=6
                )

    def test_one_atmosphere_returns_the_anchor(self):
        self.assertAlmostEqual(
            self.model.equilibrium_temperature(1.0),
            self.model.T_equilibrium_1atm,
            places=6,
        )

    def test_onset_falls_as_the_gas_gets_leaner_in_co2(self):
        # A leaner gas lets calcination start colder. This is the
        # composition dependence the fixed 1073 K window could not
        # express.
        lean = self.model.equilibrium_temperature(0.10)
        rich = self.model.equilibrium_temperature(0.30)
        self.assertLess(lean, rich)

        # Both must bracket the literal the window used, or the
        # closure is not a like-for-like replacement for it.
        self.assertLess(lean, 1073.0)
        self.assertGreater(rich, 1073.0)

    def test_rejects_non_physical_pressure(self):
        for p in (0.0, -1.0):
            with self.subTest(p=p):
                with self.assertRaises(ValueError):
                    self.model.equilibrium_temperature(p)


if __name__ == "__main__":
    unittest.main()
