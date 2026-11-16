"""The kiln inlet seal and the riser leak part of the calciner's air in at
ambient temperature (calciner.seal_air_fraction, configs/twin_cfg.yaml).

It is part of the calciner's air, the complement of the kiln's share of
the stack-O2 total, so it displaces tertiary air rather than adding gas;
it enters the riser with the kiln gas and the tertiary air and is an
ambient intake in the global balances. Checked on the twin reference
state (tests/data/twin_state_reference.json).
"""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml

REPO = Path(__file__).resolve().parents[1]


def _snapshot():
    with open(REPO / "tests" / "data" / "twin_state_reference.json", encoding="utf-8") as fh:
        return json.load(fh)["snapshot"]


def _cfg():
    with open(REPO / "configs" / "twin_cfg.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TheLeakIsPartOfTheCalcinerAirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.s = _snapshot()
        cls.calciner = _cfg()["calciner"]

    def test_the_sourced_share(self):
        """0.041 of the calciner's air: VDZ N2 balance over the riser,
        E-200 - E-100 - tertiary (CEMCAP D3.2 Tables 3.8-3.9)."""
        self.assertEqual(self.calciner["seal_air_fraction"], 0.041)

    def test_it_is_that_share_of_the_calciner_air(self):
        s = self.s
        self.assertAlmostEqual(
            s["mass_flow_m_dot_riser_seal_air"],
            self.calciner["seal_air_fraction"] * s["mass_flow_m_dot_air_calciner"],
            places=9,
        )

    def test_it_displaces_tertiary_air(self):
        """tertiary + leak = the calciner's air, exactly."""
        s = self.s
        self.assertAlmostEqual(
            s["mass_flow_m_dot_tertiary_air"] + s["mass_flow_m_dot_riser_seal_air"],
            s["mass_flow_m_dot_air_calciner"],
            places=9,
        )


class TheRiserGasCarriesItTest(unittest.TestCase):

    def _state(self, leak):
        return SimpleNamespace(
            m_dot_g_transition=20.0,
            m_dot_tertiary_air=40.0,
            m_dot_riser_seal_air=leak,
            m_dot_fuel_calciner=3.0,
            Transition_gas_species_out={"CO2": 5.0, "N2": 13.0, "O2": 1.0, "H2O": 1.0},
        )

    def test_mass_and_species(self):
        from pyroprocess.precalciner import raw_meal_inlet

        with_leak = self._state(2.0)
        without = self._state(0.0)

        self.assertAlmostEqual(
            raw_meal_inlet.inlet_gas_flow(with_leak)
            - raw_meal_inlet.inlet_gas_flow(without),
            2.0,
            places=12,
        )

        a = raw_meal_inlet.calciner_inlet_species(with_leak)
        b = raw_meal_inlet.calciner_inlet_species(without)
        self.assertAlmostEqual(sum(a.values()) - sum(b.values()), 2.0, places=9)
        self.assertGreater(a["N2"], b["N2"])


class TheCalcinerRejectsAnImpossibleShareTest(unittest.TestCase):

    def test_out_of_range(self):
        from geometry import plant_geometry
        from pyroprocess.precalciner.precalciner import Calciner

        cfg = plant_geometry.load_config(str(REPO / "configs" / "twin_cfg.yaml"))
        for bad in (-0.01, 1.0):
            with self.subTest(fraction=bad):
                cfg["calciner"] = dict(cfg["calciner"], seal_air_fraction=bad)
                with self.assertRaises(ValueError):
                    Calciner(cfg=cfg)


if __name__ == "__main__":
    unittest.main()
