"""D15, the gas-only pressure losses: each section put at its own CFD's
operating point must give back the CFD's dP (the twin's air-like gas
density differs from the CFD's by a percent or two), and the rows must
follow the plant's strings and units. No twin solve: a stand-in twin
carries only what the report reads."""

import unittest
from types import SimpleNamespace

import numpy as np

import main
from geometry import plant_geometry as pg
from reporter.diagnostics import gas_pressure_losses


def stand_in(T_vessel, m_cal, stage_T, m_ph, N=20):
    cfg = main.load_cfg("configs/twin_cfg.yaml")
    seg = np.array([s["volume"] for s in cfg["calciner"]["zone_segments"]])
    state = SimpleNamespace(
        Tg_calciner=np.full(N, float(T_vessel)),
        m_dot_g_calciner=m_cal,
        m_dot_g_preheater=m_ph,
    )
    stages = [SimpleNamespace(gas_inlet_temperature=T) for T in stage_T]
    return SimpleNamespace(
        cfg=cfg, state=state,
        calciner=SimpleNamespace(segment_volumes=seg),
        preheater=SimpleNamespace(stages=stages),
    )


class GasPressureLossesTest(unittest.TestCase):

    def rows(self, twin):
        return {r["section"]: r for r in gas_pressure_losses(twin)["rows"]}

    def test_calciner_gives_back_its_cfd(self):
        # The CFD: 116.37 kg/s out at 1209.4 K, total-pressure loss 180.9 Pa.
        r = self.rows(stand_in(1209.43, 116.36944, [1000.0] * 4, 100.0))
        self.assertAlmostEqual(r["calciner"]["dP"], 180.9, delta=0.02 * 180.9)

    def test_c4_gives_back_its_cfd(self):
        # The CFD: 56 kg/s at 1033 K, 522.8 Pa; one C4 per string.
        strings = int(pg.load()["plant"]["strings"]["value"])
        r = self.rows(stand_in(1100.0, 100.0, [1033.0] * 4, 56.0 * strings))
        self.assertAlmostEqual(r["C4"]["dP"], 522.8, delta=0.04 * 522.8)

    def test_c1_gives_back_its_plant_point(self):
        # cyclone_C1.md at plant flow: 28 kg/s per C1 at 603 K, 1232 Pa.
        g = pg.load()
        units = int(g["plant"]["strings"]["value"]) * int(pg.cyclone(g, "C1")["per_string"])
        r = self.rows(stand_in(1100.0, 100.0, [603.0] * 4, 28.0 * units))
        self.assertAlmostEqual(r["C1"]["dP"], 1232.0, delta=0.02 * 1232.0)

    def test_sections_in_gas_order_and_power_is_dp_times_flow(self):
        twin = stand_in(1150.0, 110.0, [1090.0, 1000.0, 900.0, 750.0], 110.0)
        out = gas_pressure_losses(twin)
        self.assertEqual([r["section"] for r in out["rows"]],
                         ["calciner", "C5", "C4", "C3", "C2", "C1"])
        for r in out["rows"]:
            rho = 2.0 * r["q"] / r["v"] ** 2
            self.assertGreater(r["dP"], 0.0)
            self.assertAlmostEqual(r["power_W"], r["dP"] * r["units"] * r["m_dot"] / rho, places=6)
        self.assertAlmostEqual(out["total_dP"], sum(r["dP"] for r in out["rows"]), places=9)


if __name__ == "__main__":
    unittest.main()
