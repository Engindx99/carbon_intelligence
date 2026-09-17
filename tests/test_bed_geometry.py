import unittest

import numpy as np

from physics.physics import bed_segment_geometry, fill_fraction_from_holdup


D = 4.2   # m, kiln inner diameter used by the rotary zones
A_CROSS = np.pi * D**2 / 4.0


class BedSegmentGeometryTest(unittest.TestCase):

    def test_theta_reproduces_fill_fraction(self):

        for eta in (1e-4, 0.0077, 0.05, 0.10, 0.25, 0.5, 0.9):
            with self.subTest(fill_fraction=eta):
                theta = bed_segment_geometry(D, eta)[0]
                self.assertAlmostEqual((theta - np.sin(theta)) / (2.0 * np.pi), eta, places=12)

    def test_half_full_is_a_diameter(self):

        theta, a_gs, a_ws, a_gw, D_e = bed_segment_geometry(D, 0.5)

        self.assertAlmostEqual(theta, np.pi, places=12)
        # chord = D, both arcs = pi D / 2
        self.assertAlmostEqual(a_gs, D / A_CROSS, places=12)
        self.assertAlmostEqual(a_ws, a_gw, places=12)
        # half circle: A_gas = pi D²/8, P_gas = pi D/2 + D
        self.assertAlmostEqual(D_e, 4.0 * (np.pi * D**2 / 8.0) / (np.pi * D / 2.0 + D), places=12)

    def test_wall_area_is_conserved(self):

        for eta in (0.0, 0.01, 0.05, 0.2, 0.6, 0.95):
            with self.subTest(fill_fraction=eta):
                _, _, a_ws, a_gw, _ = bed_segment_geometry(D, eta)
                self.assertAlmostEqual(a_ws + a_gw, 4.0 / D, places=12)

    def test_empty_kiln(self):

        theta, a_gs, a_ws, a_gw, D_e = bed_segment_geometry(D, 0.0)

        self.assertAlmostEqual(theta, 0.0, places=12)
        self.assertAlmostEqual(a_gs, 0.0, places=12)
        self.assertAlmostEqual(a_ws, 0.0, places=12)
        self.assertAlmostEqual(a_gw, 4.0 / D, places=12)
        self.assertAlmostEqual(D_e, D, places=12)

    def test_monotonic_in_fill_fraction(self):

        etas = np.linspace(0.001, 0.4, 50)
        geo = np.array([bed_segment_geometry(D, e) for e in etas])

        self.assertTrue(np.all(np.diff(geo[:, 0]) > 0.0))   # theta
        self.assertTrue(np.all(np.diff(geo[:, 2]) > 0.0))   # a_ws
        self.assertTrue(np.all(np.diff(geo[:, 3]) < 0.0))   # a_gw

    def test_invalid_inputs_raise(self):

        for D_bad, eta in ((0.0, 0.05), (-1.0, 0.05), (D, -0.01), (D, 1.0), (D, 1.5)):
            with self.subTest(D=D_bad, fill_fraction=eta):
                with self.assertRaises(ValueError):
                    bed_segment_geometry(D_bad, eta)


class FillFractionFromHoldupTest(unittest.TestCase):

    def test_mass_continuity(self):

        eta = fill_fraction_from_holdup(m_dot_s=21.91, rho_bulk=1100.0, u_s=0.18654, A_cross=A_CROSS)

        self.assertAlmostEqual(eta * 1100.0 * 0.18654 * A_CROSS, 21.91, places=10)
        self.assertAlmostEqual(eta, 0.0077, places=4)

    def test_invalid_inputs_raise(self):

        cases = {
            "negative flow": dict(m_dot_s=-1.0, rho_bulk=1100.0, u_s=0.1, A_cross=A_CROSS),
            "zero density": dict(m_dot_s=20.0, rho_bulk=0.0, u_s=0.1, A_cross=A_CROSS),
            "zero velocity": dict(m_dot_s=20.0, rho_bulk=1100.0, u_s=0.0, A_cross=A_CROSS),
            "zero area": dict(m_dot_s=20.0, rho_bulk=1100.0, u_s=0.1, A_cross=0.0),
            "overfilled": dict(m_dot_s=1.0e6, rho_bulk=1100.0, u_s=0.01, A_cross=A_CROSS),
        }

        for name, kwargs in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    fill_fraction_from_holdup(**kwargs)


if __name__ == "__main__":
    unittest.main()
