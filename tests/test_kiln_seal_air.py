"""The kiln outlet seal leaks part of the kiln's air in at ambient
temperature (burning.kiln_seal_air_fraction, configs/twin_cfg.yaml).

It is part of the kiln's air, sized by the flame's wet O2, so it
displaces the cooler's secondary air rather than adding gas; it is an
ambient intake in the global mass balance. Checked on the twin
reference state (tests/data/twin_state_reference.json).
"""

import json
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def _snapshot():
    with open(REPO / "tests" / "data" / "twin_state_reference.json", encoding="utf-8") as fh:
        return json.load(fh)["snapshot"]


def _cfg():
    with open(REPO / "configs" / "twin_cfg.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TheSealAirIsPartOfTheKilnAirTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.s = _snapshot()
        cls.burning = _cfg()["burning"]

    def test_the_sourced_share(self):
        """0.200 of the kiln air: VDZ E-100 N2 balance (CEMCAP D3.2)."""
        self.assertEqual(self.burning["kiln_seal_air_fraction"], 0.20)

    def test_it_is_that_share_of_the_kiln_air(self):
        s = self.s
        self.assertAlmostEqual(
            s["mass_flow_m_dot_seal_air"],
            self.burning["kiln_seal_air_fraction"] * s["mass_flow_m_dot_air_kiln"],
            places=9,
        )

    def test_it_displaces_secondary_air(self):
        """primary + seal + secondary = the kiln's air, exactly."""
        s = self.s
        self.assertAlmostEqual(
            s["mass_flow_m_dot_primary_air"]
            + s["mass_flow_m_dot_seal_air"]
            + s["mass_flow_m_dot_secondary_air"],
            s["mass_flow_m_dot_air_kiln"],
            places=9,
        )


class TheBurningConfigRejectsAnImpossibleShareTest(unittest.TestCase):

    def test_seal_plus_primary_must_leave_secondary_air(self):
        from geometry import plant_geometry
        from pyroprocess.burning.burning import Burning

        cfg = plant_geometry.load_config(str(REPO / "configs" / "twin_cfg.yaml"))
        cfg["burning"] = dict(cfg["burning"], kiln_seal_air_fraction=0.95)

        with self.assertRaises(ValueError):
            Burning(cfg=cfg)


if __name__ == "__main__":
    unittest.main()
