"""
The burning zone's per-cell under-relaxation of its reaction heat.

Burning.apply blends what the chemistry just produced with the previous
apply's arrays, cell by cell, at one weight w. These pin that the WHOLE
reaction heat -- calcination and the four clinkering reactions -- is
blended at that weight, together with the CO2 it releases and the slope
(scaled by w), because a clinkering exotherm left at its new value while
the calcination endotherm lagged gave a period-2 cycle (burning.py).
"""
import unittest
from unittest import mock

import numpy as np

import main
from pyroprocess.burning import burning as burning_module
from pyroprocess.globalstate import GlobalState


class _Stop(Exception):
    pass


class WholeReactionHeatTest(unittest.TestCase):

    def setUp(self):
        cfg = main.load_cfg("configs/twin_cfg.yaml")
        self.twin = main.Twin(state=GlobalState(N=cfg["plant"]["N"]), cfg=cfg)
        self.burning = self.twin.burning
        self.state = self.twin.state
        self.N = self.burning.N

    def _apply(self, new):
        """One apply with the chemistry replaced by `new` and the
        thermal solve replaced by a capture of what it is handed."""

        def chemistry(state, dz, u_s):
            for k, v in new.items():
                setattr(state, k, np.array(v, dtype=float))
            return state

        captured = {}

        def thermal_step(*args, **kwargs):
            st = self.state
            captured.update(
                Q=np.array(st.Burning_Q_sink_cells),
                Q_calc=np.array(st.Calcination_Q_burning_cells),
                dm=np.array(st.m_dot_CO2_generated_burning_cells),
                slope=np.array(st.Calcination_Q_burning_slope_cells),
            )
            raise _Stop

        b = self.burning
        with mock.patch.object(burning_module.solid_phase, "resolve_solid_motion", return_value=1.0), \
             mock.patch.object(burning_module.burner, "resolve_gas_flow", return_value=1.0), \
             mock.patch.object(burning_module.gas_phase, "resolve_gas_inlet"), \
             mock.patch.object(burning_module.solid_phase, "resolve_solid_inlet"), \
             mock.patch.object(burning_module.heat_transfer, "kiln_dynamic", return_value=False), \
             mock.patch.object(b.chemistry, "apply_burning", side_effect=chemistry), \
             mock.patch.object(b, "thermal_step", side_effect=thermal_step):
            with self.assertRaises(_Stop):
                b.apply(self.state, None)

        return captured

    def test_clinkering_heat_is_blended_at_the_calcination_weight(self):
        N, w = self.N, self.burning.calcination_relaxation
        rng = np.random.default_rng(1)

        prev = dict(
            Burning_Q_sink_cells=rng.uniform(-5e6, 5e6, N),
            Calcination_Q_burning_cells=rng.uniform(0, 5e6, N),
            m_dot_CO2_generated_burning_cells=rng.uniform(0, 1, N),
        )
        for k, v in prev.items():
            setattr(self.state, k, v.copy())

        new = dict(
            Burning_Q_sink_cells=rng.uniform(-5e6, 5e6, N),
            Calcination_Q_burning_cells=rng.uniform(0, 5e6, N),
            m_dot_CO2_generated_burning_cells=rng.uniform(0, 1, N),
            Calcination_Q_burning_slope_cells=rng.uniform(0, 1e5, N),
        )

        got = self._apply(new)

        blend = lambda k: w * new[k] + (1 - w) * prev[k]
        np.testing.assert_allclose(got["Q"], blend("Burning_Q_sink_cells"), rtol=1e-12)
        np.testing.assert_allclose(got["Q_calc"], blend("Calcination_Q_burning_cells"), rtol=1e-12)
        np.testing.assert_allclose(got["dm"], blend("m_dot_CO2_generated_burning_cells"), rtol=1e-12)
        np.testing.assert_allclose(got["slope"], w * new["Calcination_Q_burning_slope_cells"], rtol=1e-12)

        # The clinkering part (total less calcination) carries the
        # same weight as calcination.
        clink = lambda d: d["Burning_Q_sink_cells"] - d["Calcination_Q_burning_cells"]
        np.testing.assert_allclose(
            got["Q"] - got["Q_calc"], w * clink(new) + (1 - w) * clink(prev),
            rtol=1e-9, atol=1e-3,
        )

    def test_fixed_point_is_the_identity(self):
        N = self.N
        same = dict(
            Burning_Q_sink_cells=np.linspace(-1e6, 2e6, N),
            Calcination_Q_burning_cells=np.linspace(0, 3e6, N),
            m_dot_CO2_generated_burning_cells=np.linspace(0, 0.5, N),
        )
        for k, v in same.items():
            setattr(self.state, k, v.copy())
        got = self._apply({**same, "Calcination_Q_burning_slope_cells": np.ones(N)})
        np.testing.assert_allclose(got["Q"], same["Burning_Q_sink_cells"], rtol=1e-12)
        np.testing.assert_allclose(got["dm"], same["m_dot_CO2_generated_burning_cells"], rtol=1e-12)


if __name__ == "__main__":
    unittest.main()
