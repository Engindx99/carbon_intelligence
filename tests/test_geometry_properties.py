"""Closed-form properties of the catalogue's fluid volumes.

The formulas are checked against things they do not share code
with: numerical integration of the swept radius, the FLS reference
model's own wetted-area equation written out from its printed
table, and textbook limits (a frustum with equal ends is a cylinder,
one with a point end is a cone). Where the catalogue has no value,
the property must refuse by name rather than assume one.
"""

import ast
import math
import pathlib
import unittest

from geometry.catalog import CATALOG, FLS_CYCLONES, CycloneStage
from geometry.config import repose_angle_deg
from geometry.properties import (
    MissingGeometry,
    annulus,
    circle,
    cyclone_properties,
    cylinder_volume,
    duct_section,
    frustum_side_area,
    frustum_volume,
    rectangle,
    vessel_properties,
)


def integrate_volume(radius_at, L, n=20000):
    """Midpoint rule on pi r(z)^2 over [0, L]."""

    dz = L / n

    return sum(math.pi * radius_at((i + 0.5) * dz) ** 2 for i in range(n)) * dz


class PrimitivesTest(unittest.TestCase):

    def test_frustum_with_equal_ends_is_a_cylinder(self):

        self.assertAlmostEqual(frustum_volume(3.0, 3.0, 7.0), cylinder_volume(3.0, 7.0))

    def test_frustum_to_a_point_is_a_cone(self):

        r, L = 1.5, 4.0
        self.assertAlmostEqual(frustum_volume(2 * r, 0.0, L), math.pi * r * r * L / 3.0)
        self.assertAlmostEqual(
            frustum_side_area(2 * r, 0.0, L), math.pi * r * math.hypot(r, L)
        )

    def test_frustum_volume_matches_integration(self):

        D1, D2, L = 6.82, 0.90, 7.28
        linear = lambda z: 0.5 * (D1 + (D2 - D1) * z / L)
        self.assertAlmostEqual(
            frustum_volume(D1, D2, L), integrate_volume(linear, L), places=4
        )

    def test_hydraulic_diameters(self):

        self.assertAlmostEqual(circle(4.2).hydraulic_D, 4.2)
        self.assertAlmostEqual(rectangle(1.2, 8.0).hydraulic_D, 2 * 1.2 * 8.0 / 9.2)
        self.assertAlmostEqual(annulus(6.0, 4.0).hydraulic_D, 2.0)


class CycloneTest(unittest.TestCase):

    def test_fls_wetted_area_is_the_papers_equation_4(self):
        """Ac = 2 pi r_c (h_t - h_c) + pi (r_c^2 - r_x^2)
                + pi (r_c + r_d) sqrt((r_c - r_d)^2 + h_c^2)"""

        for stage in CATALOG["FLS"].cyclones:
            c = FLS_CYCLONES[stage.stage]
            expected = (
                2 * math.pi * c["r_c"] * (c["h_t"] - c["h_c"])
                + math.pi * (c["r_c"] ** 2 - c["r_x"] ** 2)
                + math.pi * (c["r_c"] + c["r_d"])
                * math.hypot(c["r_c"] - c["r_d"], c["h_c"])
            )

            with self.subTest(stage=stage.stage):
                self.assertAlmostEqual(
                    cyclone_properties(stage).wetted_area, expected, places=9
                )

    def test_body_volume_matches_integration(self):

        for key, line in CATALOG.items():
            for stage in line.cyclones:
                D, dust = stage.D.value, stage.dust_D.value
                hb, hc = stage.barrel_h.value, stage.cone_h.value

                def r(z):
                    return 0.5 * D if z < hb else 0.5 * (D + (dust - D) * (z - hb) / hc)

                with self.subTest(line=key, stage=stage.stage):
                    self.assertAlmostEqual(
                        cyclone_properties(stage).body_volume,
                        integrate_volume(r, hb + hc, n=40000),
                        delta=1e-3 * cyclone_properties(stage).body_volume,
                    )

    def test_every_catalogue_cyclone_has_finite_positive_properties(self):

        for key, line in CATALOG.items():
            for stage in line.cyclones:
                p = cyclone_properties(stage)

                with self.subTest(line=key, stage=stage.stage):
                    for value in (
                        p.barrel_volume, p.cone_volume, p.wetted_area, p.height,
                        p.barrel.hydraulic_D, p.inlet.hydraulic_D,
                        p.roof_annulus.area, p.dust_outlet.area,
                    ):
                        self.assertTrue(math.isfinite(value) and value > 0.0)

                    self.assertEqual(p.count, stage.count)

    def test_cone_wall_is_steeper_than_the_meals_repose_angle(self):
        """The meal must slide out of the cone. Wall angle from the
        horizontal is 90 deg minus the half angle."""

        repose = repose_angle_deg()

        for key, line in CATALOG.items():
            for stage in line.cyclones:
                wall = 90.0 - cyclone_properties(stage).cone_half_angle_deg

                with self.subTest(line=key, stage=stage.stage, wall_deg=round(wall, 1)):
                    self.assertGreater(wall, repose)

    def test_vortex_finder_ends_inside_the_body(self):

        for key, line in CATALOG.items():
            for stage in line.cyclones:
                with self.subTest(line=key, stage=stage.stage):
                    self.assertLess(stage.vortex_len.value, cyclone_properties(stage).height)
                    self.assertLess(stage.vortex_D.value, stage.D.value)
                    self.assertLess(stage.dust_D.value, stage.D.value)

    def test_a_missing_field_is_named_not_assumed(self):

        full = CATALOG["2500"].cyclones[1]
        partial = CycloneStage(
            stage=2, count=1, D=full.D, barrel_h=full.barrel_h,
            vortex_len=full.vortex_len, vortex_D=full.vortex_D,
            dust_D=full.dust_D, inlet_w=full.inlet_w,
        )

        with self.assertRaises(MissingGeometry) as caught:
            cyclone_properties(partial)

        self.assertEqual(caught.exception.fields, ("C2.cone_h", "C2.inlet_h"))


class VesselAndDuctTest(unittest.TestCase):

    def test_calciner_and_kiln_are_cylinders(self):

        for key, line in CATALOG.items():
            for name, vessel in (("calciner", line.calciner), ("kiln", line.kiln)):
                D, L = vessel.D.value, vessel.length.value
                p = vessel_properties(vessel, name)

                with self.subTest(line=key, vessel=name):
                    self.assertAlmostEqual(p.volume, math.pi * D * D * L / 4.0)
                    self.assertAlmostEqual(p.wetted_area, math.pi * D * L)
                    self.assertAlmostEqual(p.section.hydraulic_D, D)

    def test_every_riser_has_a_section(self):

        for key, line in CATALOG.items():
            for duct in line.ducts:
                with self.subTest(line=key, duct=duct.name):
                    self.assertAlmostEqual(
                        duct_section(duct, duct.name).hydraulic_D, duct.D.value
                    )

    def test_gooseneck_section_only_where_its_diameter_is_published(self):

        self.assertAlmostEqual(
            duct_section(CATALOG["2500"].gooseneck, "gooseneck").area,
            math.pi * 3.5 ** 2 / 4.0,
        )

        for key in ("1500", "5000", "FLS"):
            with self.subTest(line=key):
                with self.assertRaises(MissingGeometry) as caught:
                    duct_section(CATALOG[key].gooseneck, "gooseneck")

                self.assertEqual(caught.exception.fields, ("gooseneck.D",))

    def test_gooseneck_volume_refuses_for_want_of_a_length(self):

        with self.assertRaises(MissingGeometry) as caught:
            vessel_properties(CATALOG["2500"].gooseneck, "gooseneck")

        self.assertEqual(caught.exception.fields, ("gooseneck.length",))


class IsolationTest(unittest.TestCase):

    def test_geometry_imports_no_twin_module(self):

        twin = {"physics", "pyroprocess", "chemistry", "solver", "main"}
        root = pathlib.Path(__file__).resolve().parent.parent / "geometry"

        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    continue

                for name in names:
                    with self.subTest(file=path.name, module=name):
                        self.assertNotIn(name.split(".")[0], twin)


if __name__ == "__main__":
    unittest.main()
