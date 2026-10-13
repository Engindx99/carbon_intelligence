"""
Cyclone separation and dust circulation (pyroprocess/preheater/heat_transfer.py).

Each stage's cyclone sends eta of the solid leaving it down and lets the
rest up with its gas. The top cyclone C1 (Stage 4, index N-1) lets its
dust out with the exhaust; the filter catches it and it comes back with
the feed. C2-C4 (Stages 3-1) let theirs into the stage
above, where it joins that stage's solid: an internal loop. At steady
state the solid sent to the calciner is the same as without separation,
and the plant loses only the heat C1's dust carries out between the C1
solid outlet and the feed temperature.
"""

import copy
import unittest

import numpy as np

from pyroprocess.preheater.heat_transfer import circulating_solid_flows
from pyroprocess.preheater.preheater import Preheater
from tests.test_preheater_nodes import assert_balances_pass
from tests.twin_harness import REPO_ROOT, run_twin
import main
from physics.physics import h_solid


def stage_mass_residuals(m_dot_s_in, m_dot_escape, vapor, eta, feed):
    """S_i - (underflow from above + dust from below [+ feed + C1 dust])."""
    N = len(m_dot_s_in)
    outflow = np.asarray(m_dot_s_in) - np.asarray(vapor)
    underflow = np.asarray(eta) * outflow

    residuals = []
    for i in range(N):
        expected = feed + m_dot_escape[-1] if i == N - 1 else underflow[i + 1]
        if i > 0:
            expected += m_dot_escape[i - 1]
        residuals.append(m_dot_s_in[i] - expected)

    return np.array(residuals), underflow


class CirculatingFlowsTest(unittest.TestCase):

    feed = 30.0
    vapor = np.array([0.0, 0.0, 0.0, 0.0, 1.4])
    without = feed - np.concatenate((np.cumsum(vapor[::-1])[::-1][1:], [0.0]))

    def test_no_separation_is_exactly_the_old_model(self):
        flows, escape = circulating_solid_flows(
            self.without, self.vapor, np.ones(5)
        )

        self.assertTrue(np.array_equal(flows, self.without))
        self.assertTrue(np.array_equal(escape, np.zeros(5)))

    def test_c1_alone_matches_the_closed_form(self):
        eta = np.array([1.0, 1.0, 1.0, 1.0, 0.96])
        flows, escape = circulating_solid_flows(self.without, self.vapor, eta)

        underflow = self.feed - self.vapor[-1]

        self.assertAlmostEqual(
            escape[-1], (1.0 - 0.96) / 0.96 * underflow, places=12
        )
        self.assertTrue(np.array_equal(flows[:-1], self.without[:-1]))

    def test_every_stage_closes_and_the_calciner_gets_the_feed(self):
        eta = np.array([0.85, 0.93, 0.93, 0.93, 0.96])
        flows, escape = circulating_solid_flows(self.without, self.vapor, eta)

        residuals, underflow = stage_mass_residuals(
            flows, escape, self.vapor, eta, self.feed
        )

        np.testing.assert_allclose(residuals, 0.0, atol=1e-12)
        self.assertAlmostEqual(
            underflow[0], self.feed - self.vapor.sum(), places=12
        )
        self.assertTrue(np.all(flows > self.without))


class DustReturnTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin()

    def test_config_separates(self):
        ph = self.twin.preheater
        self.assertLess(ph.c1_separation_efficiency, 1.0)
        self.assertLess(ph.c2_c4_separation_efficiency, 1.0)
        # C1-C4 only: C5 is the calciner's outlet cyclone.
        self.assertEqual(ph.N, 4)
        np.testing.assert_allclose(
            ph.separation_efficiency,
            [ph.c2_c4_separation_efficiency] * 3
            + [ph.c1_separation_efficiency],
        )

    def test_balances_pass(self):
        assert_balances_pass(self, self.validations)

    def test_stage_mass_balances_close(self):
        ph = self.twin.preheater
        state = self.twin.state
        vapor = np.asarray(state.material_flows["preheater"].gases.H2O)

        residuals, _ = stage_mass_residuals(
            ph.m_dot_s_stage_in,
            ph.m_dot_dust_escape,
            vapor,
            ph.separation_efficiency,
            state.m_dot_s_preheater,
        )

        np.testing.assert_allclose(residuals, 0.0, atol=1e-9)

    def test_dust_is_the_unseparated_share(self):
        ph = self.twin.preheater
        vapor = np.asarray(self.twin.state.material_flows["preheater"].gases.H2O)

        np.testing.assert_allclose(
            ph.m_dot_dust_escape,
            (1.0 - ph.separation_efficiency) * (ph.m_dot_s_stage_in - vapor),
            rtol=1e-12,
        )
        self.assertEqual(ph.m_dot_dust_return, ph.m_dot_dust_escape[-1])
        self.assertTrue(np.all(ph.m_dot_dust_escape > 0.0))

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

        expected = ph.m_dot_dust_return * (
            h_solid(float(state.Ts_preheater[-1]), ph.T_ref)
            - h_solid(float(state.Feed_temperature), ph.T_ref)
        )

        self.assertGreater(state.Q_dust_loss_preheater, 0.0)
        self.assertAlmostEqual(
            state.Q_dust_loss_preheater / expected, 1.0, places=9
        )


class SeparationEfficiencyBoundsTest(unittest.TestCase):

    def test_rejects_out_of_range(self):
        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        for key in (
            "c1_separation_efficiency",
            "c2_c4_separation_efficiency",
        ):
            for eta in (0.0, -0.1, 1.01):
                bad = copy.deepcopy(cfg)
                bad["preheater"][key] = eta

                with self.subTest(key=key, eta=eta):
                    with self.assertRaises(ValueError):
                        Preheater(
                            L=bad["preheater"]["length"],
                            nodes_per_stage=bad["preheater"]["nodes_per_stage"],
                            cfg=bad,
                        )


if __name__ == "__main__":
    unittest.main()
