"""
physics.gas_thermo: ideal-gas mixtures of N2, O2, Ar, CO2, H2O from
the NIST Shomate fits (Chase 1998).

The species points are the NIST Chemistry WebBook JANAF tables
(H - H298.15, kJ/mol), read 13 Oct 2026. Air is checked against the
ideal-gas air table of Cengel & Boles, Thermodynamics, Table A-17
(h in kJ/kg on its own datum, so differences are compared).
"""

import unittest

import numpy as np

from physics.physics import FUEL_COMPOSITION
from physics.gas_thermo import AIR
from physics.gas_thermo import AIR_MIXTURE
from physics.gas_thermo import GasMixture
from physics.gas_thermo import MOLAR_MASS
from physics.gas_thermo import add
from physics.gas_thermo import air
from physics.gas_thermo import burned
from physics.gas_thermo import air_for_wet_O2
from physics.gas_thermo import mole_fraction


NIST_H = {   # T [K]: H - H298.15 [kJ/mol]
    "N2": {500: 5.91, 1000: 21.46, 1500: 38.41, 2000: 56.14, 3000: 92.71},
    "O2": {600: 9.24, 1000: 22.70, 1700: 47.96, 2500: 78.33},
    "CO2": {400: 4.00, 800: 22.81, 1200: 44.47, 1500: 61.71, 2500: 121.90},
    "H2O": {600: 10.50, 1000: 26.00, 1700: 57.76, 2500: 99.11},
}

A17_AIR = {300: 300.19, 1000: 1046.04, 1400: 1515.42, 1600: 1757.57, 2000: 2252.10}


class SpeciesTest(unittest.TestCase):

    def test_reproduces_the_nist_tables(self):
        for s, points in NIST_H.items():
            gas = GasMixture({s: 1.0})
            for T, h_kj_mol in points.items():
                got = gas.h(float(T)) * MOLAR_MASS[s] / 1e3
                self.assertAlmostEqual(got, h_kj_mol, delta=0.1, msg=f"{s} {T} K")


class AirTest(unittest.TestCase):

    def test_air_matches_the_air_table(self):
        for T, h in A17_AIR.items():
            got = AIR_MIXTURE.h(float(T), 300.0) / 1e3
            want = h - A17_AIR[300]
            self.assertLess(abs(got - want), 0.005 * max(want, 1.0), msg=f"{T} K")

    def test_air_cp_at_room_temperature(self):
        self.assertAlmostEqual(AIR_MIXTURE.cp(300.0), 1005.0, delta=3.0)

    def test_air_fractions_sum_to_one(self):
        self.assertAlmostEqual(sum(AIR.values()), 1.0, places=12)


class MixtureTest(unittest.TestCase):

    GAS = GasMixture({"N2": 0.70, "O2": 0.02, "CO2": 0.24, "H2O": 0.04})

    def test_mixture_is_mass_weighted(self):
        for T in (400.0, 1100.0, 1900.0, 2600.0):
            parts = sum(
                w * GasMixture({s: 1.0}).h(T)
                for s, w in self.GAS.w.items() if w > 0.0
            )
            self.assertAlmostEqual(self.GAS.h(T), parts, delta=1e-6 * abs(parts))

    def test_cp_is_the_derivative(self):
        for T in np.linspace(300.0, 3500.0, 321):
            # Skip the segment edges, where Cp has NIST's own jumps.
            if min(abs(T - e) for e in (500, 700, 1200, 1700, 2000)) < 1.0:
                continue
            fd = (self.GAS.h(T + 1e-3) - self.GAS.h(T - 1e-3)) / 2e-3
            self.assertAlmostEqual(self.GAS.cp(T), fd, delta=1e-4 * fd)

    def test_round_trip(self):
        for T in (300.0, 777.0, 1360.0, 2450.0, 3900.0):
            h = self.GAS.h(T)
            self.assertAlmostEqual(
                self.GAS.T_from_h(h, 298.15, 250.0, 4000.0), T, delta=1e-8 * T
            )

    def test_outside_the_window_raises(self):
        with self.assertRaises(ValueError):
            self.GAS.T_from_h(self.GAS.h(4500.0), 298.15, 250.0, 4000.0)

    def test_monotone(self):
        T = np.linspace(250.0, 4000.0, 3751)
        self.assertTrue(np.all(np.diff(self.GAS.h(T)) > 0.0))


class CompositionTest(unittest.TestCase):

    def test_burning_conserves_mass(self):
        m_air, m_fuel = 25.0, 2.1
        flows = burned(m_air, m_fuel, FUEL_COMPOSITION)
        self.assertAlmostEqual(sum(flows.values()), m_air + m_fuel, places=9)

    def test_burning_uses_oxygen(self):
        flows = burned(25.0, 2.1, FUEL_COMPOSITION)
        self.assertLess(flows["O2"], air(25.0)["O2"])
        self.assertGreater(flows["CO2"], air(25.0)["CO2"])

    def test_too_little_air_raises(self):
        with self.assertRaises(ValueError):
            burned(5.0, 2.1, FUEL_COMPOSITION)

    def test_add(self):
        total = add(air(1.0), {"CO2": 0.5})
        self.assertAlmostEqual(sum(total.values()), 1.5, places=12)



class AirForWetO2Test(unittest.TestCase):
    """The kiln air sized by its flame's wet O2 (fuel.kiln_O2_wet)."""

    def test_round_trip_through_the_products(self):
        for x in (0.005, 0.015, 0.031, 0.08):
            with self.subTest(O2=x):
                m = air_for_wet_O2(2.0949, x, FUEL_COMPOSITION)
                got = mole_fraction(burned(m, 2.0949, FUEL_COMPOSITION), "O2")
                self.assertAlmostEqual(got, x, places=12)

    def test_zero_O2_is_stoichiometric(self):
        m = air_for_wet_O2(1.0, 0.0, FUEL_COMPOSITION)
        self.assertAlmostEqual(
            burned(m, 1.0, FUEL_COMPOSITION)["O2"], 0.0, places=9
        )
        with self.assertRaises(ValueError):
            burned(0.999 * m, 1.0, FUEL_COMPOSITION)

    def test_scales_with_the_fuel(self):
        a = air_for_wet_O2(1.0, 0.015, FUEL_COMPOSITION)
        b = air_for_wet_O2(3.0, 0.015, FUEL_COMPOSITION)
        self.assertAlmostEqual(b / a, 3.0, places=10)


if __name__ == "__main__":
    unittest.main()
