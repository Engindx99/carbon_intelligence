"""The grate cooler's fluid volume (geometry/cooler/cooler.md).

The cooler is a box, width x length x casing height, with the
clinker bed as its bottom slice. Every number is the PF5000 grate
area or the FLS reference cooler (Svensen et al. 2024,
arXiv:2409.09076); this file re-derives each from those sources
and checks the model carries the same, rather than reading them
back from the model.
"""

import unittest

import numpy as np

import main
from tests.twin_harness import REPO_ROOT


# Published
PF5000_GRATE_AREA = 119.6  # m2
FLS_WIDTH = 4.0  # m
FLS_HEIGHT = 3.0  # m
FLS_SPEED = 0.017  # m/s
FLS_CLINKER = 191.0e3 / 3600.0  # kg/s, "191 ton/h"
FLS_POROSITY = 0.4

# FLS clinker (mass fractions) and Table II densities [kg/m3];
# C4AF is given as 3.7-3.9 g/cm3.
FLS_CLINKER_PHASES = {
    "C3S": (0.7996, 3130.0),
    "C3A": (0.0976, 3040.0),
    "C4AF": (0.1028, 3800.0),
}

PLANT_CLINKER = 5000.0e3 / 86400.0  # kg/s, 5000 t/d


def _cooler():
    cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
    return main.Cooler(
        N=cfg["plant"]["N"],
        L=cfg["cooler"]["length"],
        cfg=cfg,
    )


class TheGrateIsThePublishedOneTest(unittest.TestCase):

    def setUp(self):
        self.cooler = _cooler()

    def test_area_is_the_plants_and_width_and_height_are_fls(self):
        c = self.cooler
        self.assertAlmostEqual(c.L * c.width, PF5000_GRATE_AREA, places=9)
        self.assertEqual(c.width, FLS_WIDTH)
        self.assertEqual(c.casing_height, FLS_HEIGHT)

    def test_bulk_density_from_table_ii(self):
        rho_solid = 1.0 / sum(
            fraction / rho for fraction, rho in FLS_CLINKER_PHASES.values()
        )

        self.assertAlmostEqual(self.cooler.rho_solid, rho_solid, delta=0.5)
        self.assertAlmostEqual(
            self.cooler.rho_s,
            (1.0 - FLS_POROSITY) * self.cooler.rho_solid,
            places=9,
        )

    def test_design_bed_is_the_fls_continuity_and_the_speed_carries_5000(self):
        c = self.cooler

        # The FLS cooler's own bed: m_dot = rho_bulk w h v.
        h0 = FLS_CLINKER / (c.rho_s * FLS_WIDTH * FLS_SPEED)
        self.assertAlmostEqual(h0, 0.409, delta=5e-4)

        # The configured grate speed lays 5000 t/d down at that depth.
        self.assertAlmostEqual(c.bed_depth(PLANT_CLINKER), h0, delta=5e-4)

        # Residence on the grate: 26.9 min (FLS: 36 min).
        self.assertAlmostEqual(c.L / c.grate_speed / 60.0, 26.9, delta=0.05)

    def test_the_bed_follows_the_clinker_flow(self):
        c = self.cooler
        self.assertAlmostEqual(
            c.bed_depth(2.0 * PLANT_CLINKER),
            2.0 * c.bed_depth(PLANT_CLINKER),
            places=12,
        )


class TheExchangesActOverTheBedTest(unittest.TestCase):

    def setUp(self):
        self.cooler = _cooler()

    def test_bed_volume_and_areas_per_cell(self):
        c = self.cooler
        h = np.array([0.30, 0.409, 0.60])

        V_bed, a_gw = c.bed_geometry(h)

        np.testing.assert_allclose(V_bed, c.width * h * c.dz)

        # gas -> the walls and roof above the bed
        np.testing.assert_allclose(
            a_gw * V_bed,
            (2.0 * (c.casing_height - h) + c.width) * c.dz,
        )

        # bed -> the two side walls it lies against
        np.testing.assert_allclose(c.a_ws * V_bed, 2.0 * h * c.dz)

        # nodule surface: the packed-bed specific surface
        self.assertAlmostEqual(
            c.a_gs, 6.0 * (1.0 - c.epsilon_bed) / c.particle_diameter
        )

    def test_the_wall_areas_add_up_to_the_casing(self):
        # Above and beside the bed, the gas and the bed together
        # touch exactly the side walls and the roof of a cell.
        c = self.cooler
        h = np.array([0.409])
        V_bed, a_gw = c.bed_geometry(h)

        self.assertAlmostEqual(
            float((a_gw + c.a_ws)[0] * V_bed[0]), c.A_wall_cell, places=9
        )

    def test_a_bed_must_fit_in_the_casing(self):
        for h in (0.0, -0.1, FLS_HEIGHT, 4.0):
            with self.subTest(h=h):
                with self.assertRaises(ValueError):
                    self.cooler.bed_geometry(np.array([h]))

    def test_the_casing_is_a_flat_wall(self):
        c = self.cooler
        self.assertIsNone(c.shell.r_inner)
        self.assertAlmostEqual(c.shell.A_outer_cell, c.A_wall_cell)
        self.assertAlmostEqual(
            c.A_wall_cell, (2.0 * FLS_HEIGHT + FLS_WIDTH) * c.dz
        )


if __name__ == "__main__":
    unittest.main()
