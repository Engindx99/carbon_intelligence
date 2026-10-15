"""
The plant's fuel input and its split, against what they are derived from.

configs/twin_cfg.yaml sizes the fuel as 3100 kJ/kg (the user's SHC band
middle) on the clinker the FEED can make, from the raw-meal composition,
and takes the kiln's share from the VDZ reference plant. If the feed rate
or the composition changes and the fuel does not, these fail.
"""
import unittest

import main
from chemistry.composition import RAW_MEAL_COMPOSITION

LHV = 32.0e6                 # J/kg, petcoke (pyroprocess/*/combustion.py)
SHC = 3100.0e3               # J/kg clinker, user decision 13 Oct 2026
M_CO2, M_CaCO3 = 44.01, 100.09


def clinker_potential(meal):
    """Clinker the meal can make [kg/s]: less its water and its CO2."""
    total = sum(RAW_MEAL_COMPOSITION.values())
    water = (RAW_MEAL_COMPOSITION["H2O"] + RAW_MEAL_COMPOSITION["Bound_H2O"]) / total
    co2 = RAW_MEAL_COMPOSITION["CaCO3"] / total * M_CO2 / M_CaCO3
    return meal * (1.0 - water - co2)


class FuelBasisTest(unittest.TestCase):

    def setUp(self):
        self.cfg = main.load_cfg("configs/twin_cfg.yaml")

    def test_fuel_is_3100_kJ_per_kg_on_the_feeds_clinker(self):
        clinker = clinker_potential(float(self.cfg["feed"]["Feed_rate_kg_s"]))
        shc = float(self.cfg["fuel"]["Fuel_rate_total"]) * LHV / clinker
        self.assertAlmostEqual(shc / SHC, 1.0, delta=1e-3)

    def test_kiln_share_is_the_vdz_plants(self):
        # CEMCAP D3.2 rev 2, Tables 3.7 (kiln) and 3.5 (calciner), MW.
        vdz = 39.895 / (39.895 + 65.160)
        self.assertAlmostEqual(float(self.cfg["fuel"]["kiln_fraction"]), vdz, delta=1e-3)


if __name__ == "__main__":
    unittest.main()
