"""Component fluid volumes: dimensioning, boundary parameters, solids.

The dimensioning and the CFD boundary parameters are pure Python and
always tested. The B-rep solids need CadQuery (requirements-cad.txt)
and are skipped without it.

Each solid is checked against a volume computed WITHOUT the kernel:
the body's closed form, plus the part of the tangential inlet duct
that lies outside the barrel and cone (circle segments integrated
over height), plus the outlet bore above the roof, minus the vortex
finder's wall.
"""

import dataclasses
import math
import pathlib
import tempfile
import unittest

from geometry.catalog import CATALOG, DERIVED
from geometry.components import (
    build_component,
    component_names,
    cyclone_layout,
)
from geometry.modelling import CfdBoundaryParams, cfd_boundary_params
from geometry.properties import MissingGeometry, cyclone_properties
from geometry.report import line_report

try:
    import cadquery  # noqa: F401
    HAVE_CADQUERY = True
except ImportError:
    HAVE_CADQUERY = False


def configured():
    return cfd_boundary_params()


def expected_cyclone_volume(stage, cfd, n=4000):

    g = cyclone_layout(stage, cfd)
    R = 0.5 * g.D
    a = R - g.inlet_w
    L = -g.inlet_x0

    def radius(z):
        if z >= g.cone_h:
            return R
        return 0.5 * (g.dust_D + (g.D - g.dust_D) * z / g.cone_h)

    def inside(r):
        """Area of the duct's cross-section (x in [-L, 0], y in [a, R])
        inside a circle of radius r."""

        if r <= a:
            return 0.0

        top = min(r, R)

        def G(y):
            return 0.5 * (y * math.sqrt(max(r * r - y * y, 0.0)) + r * r * math.asin(y / r))

        return G(top) - G(a)

    z0 = g.roof - g.inlet_h
    dz = g.inlet_h / n
    inlet_outside = sum(
        (L * g.inlet_w - inside(radius(z0 + (i + 0.5) * dz))) * dz for i in range(n)
    )

    rx = 0.5 * g.vortex_D
    wall = math.pi * ((rx + g.wall) ** 2 - rx * rx) * g.vortex_len
    bore_above_roof = math.pi * rx * rx * (g.outlet_top - g.roof)

    return cyclone_properties(stage).body_volume + inlet_outside + bore_above_roof - wall


class CfdBoundaryParamsTest(unittest.TestCase):

    def test_configured_values_are_read(self):

        p = configured()
        self.assertIsInstance(p, CfdBoundaryParams)

    def test_no_defaults_in_code(self):

        with self.assertRaises(TypeError):
            CfdBoundaryParams()

        for f in dataclasses.fields(CfdBoundaryParams):
            with self.subTest(field=f.name):
                self.assertIs(f.default, dataclasses.MISSING)

    def test_a_missing_key_is_named(self):

        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "cfg.yaml"
            path.write_text(
                "geometry:\n  cfd_boundary:\n    inlet_extension_over_D: 0.6\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as caught:
                cfd_boundary_params(path)

        self.assertIn("outlet_extension_over_vortex_D", str(caught.exception))
        self.assertIn("vortex_finder_wall_m", str(caught.exception))

    def test_a_missing_block_is_refused(self):

        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "cfg.yaml"
            path.write_text("geometry:\n  reference_line: '2500'\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                cfd_boundary_params(path)

    def test_non_positive_values_are_refused(self):

        with self.assertRaises(ValueError):
            CfdBoundaryParams(0.6, 1.0, 0.0)


class CycloneLayoutTest(unittest.TestCase):

    def test_every_catalogue_cyclone_can_be_laid_out(self):

        cfd = configured()

        for key, line in CATALOG.items():
            for stage in line.cyclones:
                with self.subTest(line=key, stage=stage.stage):
                    g = cyclone_layout(stage, cfd)
                    self.assertAlmostEqual(g.roof, cyclone_properties(stage).height)
                    # the wall cut lies wholly in the barrel
                    self.assertLessEqual(g.vortex_len, g.roof - g.cone_h)

    def test_an_inlet_face_inside_the_barrel_is_refused_not_moved(self):

        stage = CATALOG["2500"].cyclones[1]

        with self.assertRaises(ValueError) as caught:
            cyclone_layout(stage, CfdBoundaryParams(0.3, 1.0, 0.012))

        self.assertIn("inside the barrel", str(caught.exception))

    def test_a_wall_that_does_not_fit_is_refused(self):

        stage = CATALOG["2500"].cyclones[1]

        with self.assertRaises(ValueError):
            cyclone_layout(stage, CfdBoundaryParams(0.6, 1.0, 1.0))

    def test_a_missing_dimension_is_named(self):

        stage = dataclasses.replace(CATALOG["2500"].cyclones[1], cone_h=None)

        with self.assertRaises(MissingGeometry) as caught:
            cyclone_layout(stage, configured())

        self.assertEqual(caught.exception.fields, ("C2.cone_h",))


class ComponentNamesTest(unittest.TestCase):

    def test_components_are_the_cyclones_and_the_calciner_only(self):

        for key, line in CATALOG.items():
            with self.subTest(line=key):
                self.assertEqual(
                    component_names(line), ["C1", "C2", "C3", "C4", "C5", "calciner"]
                )


class ReportTest(unittest.TestCase):

    def test_report_marks_every_derived_value(self):

        for key, line in CATALOG.items():
            text = line_report(line)

            with self.subTest(line=key):
                for path, m in line.measures():
                    if m is not None and m.basis == DERIVED:
                        row = next(r for r in text.splitlines() if r.split()[:1] == [path])
                        self.assertEqual(row.split()[2], "R")

                self.assertIn("no volume", text)

    def test_report_volumes_are_labelled_as_equipment_volumes(self):

        text = line_report(CATALOG["2500"])
        self.assertIn("Equipment volumes", text)
        self.assertIn("no CFD extensions", text)
        self.assertIn("residence time", text)

    def test_cfd_parameters_are_not_in_the_catalogue_or_its_report(self):

        names = {f.name for f in dataclasses.fields(CfdBoundaryParams)}

        for key, line in CATALOG.items():
            text = line_report(line)
            paths = {p.split(".")[-1] for p, _ in line.measures()}

            with self.subTest(line=key):
                self.assertFalse(names & paths)

                for name in names:
                    self.assertNotIn(name, text)


@unittest.skipUnless(HAVE_CADQUERY, "CadQuery not installed (requirements-cad.txt)")
class SolidTest(unittest.TestCase):

    def test_each_component_is_one_valid_solid_of_the_expected_volume(self):

        cfd = configured()

        for key, line in CATALOG.items():
            for name in component_names(line):
                solid = build_component(line, name, cfd)

                if name == "calciner":
                    D, H = line.calciner.D.value, line.calciner.length.value
                    expected = math.pi * D * D * H / 4.0
                else:
                    stage = line.cyclones[int(name[1:]) - 1]
                    expected = expected_cyclone_volume(stage, cfd)

                with self.subTest(line=key, component=name):
                    self.assertTrue(solid.isValid())
                    self.assertEqual(len(solid.Solids()), 1)
                    self.assertTrue(all(s.Closed() for s in solid.Shells()))
                    self.assertAlmostEqual(
                        solid.Volume(), expected, delta=1e-3 * expected
                    )

    def test_a_missing_calciner_dimension_is_named(self):

        line = dataclasses.replace(
            CATALOG["2500"],
            calciner=dataclasses.replace(CATALOG["2500"].calciner, length=None),
        )

        with self.assertRaises(MissingGeometry) as caught:
            build_component(line, "calciner", configured())

        self.assertEqual(caught.exception.fields, ("calciner.length",))

    def test_there_is_no_riser_component(self):

        with self.assertRaises(KeyError):
            build_component(CATALOG["FLS"], "R1", configured())


if __name__ == "__main__":
    unittest.main()
