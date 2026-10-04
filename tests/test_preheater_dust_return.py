"""
C1 dust return (pyroprocess/preheater/heat_transfer.py).

The top cyclone C1 (Stage 5, index N-1) separates eta of the solid it
receives; the dust it lets through is caught by the filter and comes
back with the feed. At steady state that dust recirculates through
Stage 5 only: the solid sent down to Stage 4 and on to the calciner is
the same as without separation, and the plant loses only the heat the
dust carries out between the C1 solid outlet and the feed temperature.
"""

import copy
import unittest

from pyroprocess.preheater.preheater import Preheater
from tests.test_preheater_nodes import assert_balances_pass
from tests.twin_harness import REPO_ROOT, run_twin
import main


class DustReturnTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin()

    def test_config_separates(self):
        self.assertLess(self.twin.preheater.c1_separation_efficiency, 1.0)

    def test_balances_pass(self):
        assert_balances_pass(self, self.validations)

    def test_dust_flow_closes_the_c1_loop(self):
        ph = self.twin.preheater
        state = self.twin.state

        eta = ph.c1_separation_efficiency
        vapor = state.material_flows["preheater"].gases.H2O

        # Underflow to Stage 4: the fresh feed less Stage 5's moisture.
        underflow = state.m_dot_s_preheater - vapor[-1]

        self.assertAlmostEqual(
            ph.m_dot_dust_return,
            (1.0 - eta) / eta * underflow,
            places=12,
        )

        # The dust is (1 - eta) of everything Stage 5 sends out.
        self.assertAlmostEqual(
            ph.m_dot_dust_return / (underflow + ph.m_dot_dust_return),
            1.0 - eta,
            places=12,
        )

    def test_solid_to_calciner_is_unchanged_by_separation(self):
        ph = self.twin.preheater
        state = self.twin.state

        vapor = state.material_flows["preheater"].gases.H2O

        self.assertAlmostEqual(
            ph.m_dot_s_out,
            state.m_dot_s_preheater - float(sum(vapor)),
            places=12,
        )

    def test_dust_heat_loss(self):
        ph = self.twin.preheater
        state = self.twin.state

        expected = (
            ph.m_dot_dust_return
            * ph.Cp_s
            * (state.Ts_preheater[-1] - state.Feed_temperature)
        )

        self.assertGreater(state.Q_dust_loss_preheater, 0.0)
        self.assertAlmostEqual(
            state.Q_dust_loss_preheater / expected, 1.0, places=9
        )


class SeparationEfficiencyBoundsTest(unittest.TestCase):

    def test_rejects_out_of_range(self):
        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        for eta in (0.0, -0.1, 1.01):
            bad = copy.deepcopy(cfg)
            bad["preheater"]["c1_separation_efficiency"] = eta

            with self.subTest(eta=eta):
                with self.assertRaises(ValueError):
                    Preheater(
                        L=bad["preheater"]["length"],
                        nodes_per_stage=bad["preheater"]["nodes_per_stage"],
                        cfg=bad,
                    )


if __name__ == "__main__":
    unittest.main()
