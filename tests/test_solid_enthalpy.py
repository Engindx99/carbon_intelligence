"""
The one solid enthalpy every zone uses (physics.physics.h_solid).

Sensible heat: the "Clinker 2000" column of the clinker enthalpy
table, cementkilns.co.uk cemkilndoc021 (D. Moore, data mainly
CODATA), kJ/kg relative to 0 degC. The table excludes the melt;
its Note 2 puts ~60 kJ/kg between 1320 and 1360 degC and a
further 0.08 kJ/kg/degC above.
"""

import unittest

import numpy as np

from physics.physics import MELT_CP_EXTRA
from physics.physics import MELT_LATENT
from physics.physics import MELT_T_END
from physics.physics import MELT_T_ONSET
from physics.physics import T_solid_from_h
from physics.physics import cp_solid
from physics.physics import h_solid

T0 = 273.15

# degC -> kJ/kg, "Clinker 2000", verbatim from the table.
CLINKER_2000 = {
    100: 77.69,
    300: 256.91,
    500: 454.42,
    700: 664.93,
    900: 884.02,
    1100: 1109.96,
    1300: 1342.23,
    1550: 1649.84,
}


def _melt(T):
    return (
        MELT_LATENT
        * (min(max(T, MELT_T_ONSET), MELT_T_END) - MELT_T_ONSET)
        / (MELT_T_END - MELT_T_ONSET)
        + MELT_CP_EXTRA * max(T - MELT_T_END, 0.0)
    )


class SensibleHeatTest(unittest.TestCase):

    def test_reproduces_the_table(self):
        for t_c, h_kj in CLINKER_2000.items():
            T = T0 + t_c
            sensible = h_solid(T, T0) - _melt(T)
            self.assertAlmostEqual(sensible / 1e3, h_kj, delta=3.6)

    def test_cp_is_the_derivative(self):
        T = np.linspace(250.0, 3000.0, 2001)
        T = T[
            (np.abs(T - MELT_T_ONSET) > 1e-3) & (np.abs(T - MELT_T_END) > 1e-3)
        ]
        fd = (h_solid(T + 1e-3, T0) - h_solid(T - 1e-3, T0)) / 2e-3
        np.testing.assert_allclose(cp_solid(T), fd, rtol=1e-6)


class MeltTest(unittest.TestCase):

    def test_latent_heat_over_the_onset_ramp(self):
        jump = h_solid(MELT_T_END, T0) - h_solid(MELT_T_ONSET, T0)
        sensible = jump - MELT_LATENT
        # 40 K of sensible heat at ~1200 J/(kg K) on top of 60 kJ/kg.
        self.assertAlmostEqual(MELT_LATENT, 60.0e3)
        self.assertGreater(sensible, 40.0 * 1150.0)
        self.assertLess(sensible, 40.0 * 1250.0)

    def test_cp_is_continuous_across_the_band(self):
        """h is C1: Cp has no step at the band's ends (21 Nov 2026).
        A step there made the solid rows' Newton linearisation flip
        between two slopes at a bed node on the kink, a limit cycle
        that stopped the dynamic solve."""
        for T_edge in (MELT_T_ONSET, MELT_T_END):
            below = cp_solid(T_edge - 1e-6)
            above = cp_solid(T_edge + 1e-6)
            self.assertAlmostEqual(below, above, delta=0.01)

    def test_freezing_returns_the_heat(self):
        # The same function on the way down: a melt that freezes in
        # the cooler gives back exactly what it took in the kiln.
        h_up = h_solid(1700.0, 298.15) - h_solid(1500.0, 298.15)
        h_down = h_solid(1500.0, 1700.0)
        self.assertAlmostEqual(h_up, -h_down, places=6)


class InverseTest(unittest.TestCase):

    def test_round_trip(self):
        for T in np.linspace(250.0, 3900.0, 731):
            h = h_solid(float(T), 298.15)
            self.assertAlmostEqual(T_solid_from_h(h, 298.15), T, delta=1e-7)

    def test_monotone(self):
        T = np.linspace(200.0, 4000.0, 40001)
        self.assertTrue(np.all(np.diff(h_solid(T, 298.15)) > 0.0))

    def test_out_of_window_raises(self):
        with self.assertRaises(ValueError):
            T_solid_from_h(h_solid(4100.0, 298.15), 298.15)


if __name__ == "__main__":
    unittest.main()
