"""The cooler's air crosses the bed once: effectiveness 1 - exp(-NTU).

Each cell's gas row is a well-mixed balance, which on its own gives
the cell an effectiveness NTU / (1 + NTU). The air does not mix in
the bed: it passes through it once, past clinker whose temperature
is uniform across the cell, so the exchange is a stream past an
isothermal surface, 1 - exp(-NTU) (Incropera & DeWitt, sec. 11.3,
C_r = 0). gas_phase.through_bed_hv_gs rates the row's coefficient so
that the well-mixed row lands exactly on that.

MEASURED on the FLS cooler scenario (Svensen et al. 2024,
arXiv:2409.09076 sec. IV, 53.06 kg/s clinker at 1723 K, air
40.89 / 18.56 / 8 x 16.24 kg/s; paper 1362 K / 1172 K):

    secondary air   1212 -> 1315 K
    tertiary  air    907 ->  872 K   (FLS gas also moves between
                                      segments; not modelled)
    clinker out      330 ->  319 K
"""

import unittest

import numpy as np

from physics.physics import cp_gas
from pyroprocess.cooler import gas_phase


class _StubCooler:
    def __init__(self, N, hv_gs=180.0):
        self.N = N
        self.hv_gs = hv_gs


def _cell_outlet(hv, a_gs, V, m_air, Tg, Ts, T_in):
    """Outlet of the well-mixed row m cp (Tg - T_in) = K V (Ts - Tg)."""
    C = m_air * cp_gas(Tg)
    KV = hv * a_gs * V
    return (C * T_in + KV * Ts) / (C + KV)


class ThroughBedEffectivenessTest(unittest.TestCase):

    def test_row_reproduces_one_minus_exp(self):
        cooler = _StubCooler(N=4)
        a_gs, V = 240.0, 2.9
        m_air = np.array([0.5, 5.0, 20.0, 60.0])
        Tg = np.full(4, 1200.0)
        Ts, T_in = 1500.0, 300.0

        hv = gas_phase.through_bed_hv_gs(cooler, m_air, Tg, V, a_gs)

        for i in range(4):
            C = m_air[i] * cp_gas(Tg[i])
            NTU = min(cooler.hv_gs * a_gs * V / C, gas_phase.NTU_CAP)
            expected = Ts - (Ts - T_in) * np.exp(-NTU)
            got = _cell_outlet(hv[i], a_gs, V, m_air[i], Tg[i], Ts, T_in)
            self.assertAlmostEqual(got, expected, delta=1e-6)

    def test_always_above_well_mixed(self):
        cooler = _StubCooler(N=3)
        hv = gas_phase.through_bed_hv_gs(
            cooler, np.array([1.0, 10.0, 100.0]), np.full(3, 900.0), 2.0, 240.0
        )
        self.assertTrue(np.all(hv >= cooler.hv_gs))

    def test_no_air_keeps_film_coefficient(self):
        cooler = _StubCooler(N=2)
        hv = gas_phase.through_bed_hv_gs(
            cooler, np.array([0.0, 5.0]), np.full(2, 900.0), 2.0, 240.0
        )
        self.assertEqual(hv[0], cooler.hv_gs)
        self.assertTrue(np.all(np.isfinite(hv)))


if __name__ == "__main__":
    unittest.main()
