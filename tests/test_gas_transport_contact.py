import unittest

import numpy as np

from physics.physics import (
    SUTHERLAND_AIR,
    k_gas,
    mu_gas,
    wall_bed_contact_coefficient,
)


class SutherlandAirTest(unittest.TestCase):

    def test_reference_point(self):

        self.assertAlmostEqual(mu_gas(SUTHERLAND_AIR["T_0"]), SUTHERLAND_AIR["mu_0"], places=15)
        self.assertAlmostEqual(k_gas(SUTHERLAND_AIR["T_0"]), SUTHERLAND_AIR["k_0"], places=15)

    def test_against_air_property_tables(self):

        # Incropera, Fundamentals of Heat and Mass Transfer, Table A.4 (air, 1 atm).
        # Only the range where Sutherland's law holds to 2 % is asserted; at
        # 1500 K it is ~5 % (mu) and ~14 % (k) low, as documented in physics.py.
        table = {
            300.0: (184.6e-7, 26.3e-3),
            600.0: (305.8e-7, 46.9e-3),
            1000.0: (424.4e-7, 66.7e-3),
        }

        for T, (mu_ref, k_ref) in table.items():
            with self.subTest(T=T):
                self.assertLess(abs(mu_gas(T) / mu_ref - 1.0), 0.03)
                self.assertLess(abs(k_gas(T) / k_ref - 1.0), 0.03)

    def test_array_input_and_monotonic(self):

        T = np.linspace(300.0, 2000.0, 50)

        mu = mu_gas(T)
        k = k_gas(T)

        self.assertEqual(mu.shape, T.shape)
        self.assertTrue(np.all(np.diff(mu) > 0.0))
        self.assertTrue(np.all(np.diff(k) > 0.0))
        self.assertIsInstance(mu_gas(1000.0), float)

    def test_non_positive_temperature_raises(self):

        for f in (mu_gas, k_gas):
            with self.subTest(f=f.__name__):
                with self.assertRaises(ValueError):
                    f(0.0)
                with self.assertRaises(ValueError):
                    f(np.array([300.0, -1.0]))


BED = dict(theta=1.2689, rpm=1.5, k_b=0.3, rho_b=1100.0, cp_b=850.0, d_p=1.0e-3, k_g=0.08, chi=0.1)


class WallBedContactTest(unittest.TestCase):

    def test_hand_calculation(self):

        omega = 2.0 * np.pi * 1.5 / 60.0
        t_c = 1.2689 / omega
        h_pen = 2.0 * np.sqrt(0.3 * 1100.0 * 850.0 / (np.pi * t_c))
        R_gap = 0.1 * 1.0e-3 / 0.08

        self.assertAlmostEqual(
            wall_bed_contact_coefficient(**BED),
            1.0 / (R_gap + 1.0 / h_pen),
            places=10,
        )

    def test_series_resistance_bounds(self):

        h = wall_bed_contact_coefficient(**BED)

        h_gap_only = BED["k_g"] / (BED["chi"] * BED["d_p"])
        h_pen_only = wall_bed_contact_coefficient(**{**BED, "d_p": 1.0e-12})

        self.assertLess(h, h_gap_only)
        self.assertLess(h, h_pen_only)

    def test_faster_rotation_shortens_contact(self):

        h_slow = wall_bed_contact_coefficient(**{**BED, "rpm": 1.0})
        h_fast = wall_bed_contact_coefficient(**{**BED, "rpm": 3.0})

        self.assertGreater(h_fast, h_slow)

    def test_invalid_inputs_raise(self):

        cases = {
            "theta": {"theta": 0.0},
            "rpm": {"rpm": 0.0},
            "k_b": {"k_b": 0.0},
            "d_p": {"d_p": -1.0},
            "chi low": {"chi": 0.05},
            "chi high": {"chi": 0.25},
        }

        for name, override in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    wall_bed_contact_coefficient(**{**BED, **override})


if __name__ == "__main__":
    unittest.main()
