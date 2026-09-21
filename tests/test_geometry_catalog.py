"""The geometry catalogue says where every dimension came from.

Each value is published, derived from ONE named FLS ratio, or a
source's own modelling assumption -- and a dimension no source gives
is None, not a guess. These tests pin that contract, and pin the
derived numbers to the ones geometry/SOURCES.md shows the user, so
the table a person reads and the values the geometry is built from
cannot drift apart.
"""

import unittest

from geometry.catalog import (
    CATALOG,
    DERIVED,
    FLS_RATIOS,
    MODEL_ASSUMPTION,
    PUBLISHED,
    SOURCES,
    C1_TRANSFER_ASSUMPTION,
    RISER_MAPPING_REF,
    W_IN_ASSUMPTION,
    Measure,
    derive,
    published,
    reference_line,
)
from geometry.config import reference_line_key


# geometry/SOURCES.md, per line: stage -> (D, barrel_h, cone_h,
# vortex_len, vortex_D, dust_D, inlet_w, inlet_h), metres.
SOURCES_MD_CYCLONES = {
    "1500": {
        1: (4.132, 6.50, 4.45, 2.07, 2.30, 0.38, 0.83, 4.75),
        2: (5.319, 3.20, 5.68, 2.66, 3.79, 0.70, 1.07, 7.59),
        3: (5.272, 2.69, 6.08, 2.64, 3.87, 0.70, 1.05, 7.91),
        4: (5.537, 3.04, 6.41, 2.78, 4.07, 0.71, 1.11, 8.30),
        5: (5.584, 3.04, 6.38, 2.79, 4.07, 0.71, 1.12, 8.24),
    },
    "2500": {
        1: (4.32, 6.79, 4.65, 2.16, 2.40, 0.40, 0.86, 4.97),
        2: (6.10, 3.67, 6.51, 3.05, 4.35, 0.80, 1.23, 8.71),
        3: (6.30, 3.22, 7.26, 3.15, 4.62, 0.84, 1.26, 9.46),
        4: (6.30, 3.46, 7.30, 3.17, 4.63, 0.81, 1.27, 9.44),
        5: (6.50, 3.53, 7.43, 3.25, 4.74, 0.83, 1.30, 9.59),
    },
    "5000": {
        1: (4.805, 7.56, 5.17, 2.40, 2.67, 0.45, 0.96, 5.53),
        2: (6.554, 3.94, 7.00, 3.28, 4.67, 0.86, 1.32, 9.36),
        3: (6.496, 3.32, 7.49, 3.25, 4.77, 0.86, 1.30, 9.75),
        4: (6.757, 3.71, 7.83, 3.40, 4.97, 0.87, 1.36, 10.12),
        5: (6.815, 3.71, 7.79, 3.41, 4.97, 0.87, 1.37, 10.05),
    },
}

SOURCES_MD_RISER_D = {
    "1500": (3.82, 3.82, 4.02, 4.02),
    "2500": (3.07, 3.35, 3.45, 3.60),
    "5000": (4.71, 4.71, 4.91, 4.91),
}

CYCLONE_FIELDS = (
    "D", "barrel_h", "cone_h", "vortex_len",
    "vortex_D", "dust_D", "inlet_w", "inlet_h",
)

# SOURCES.md prints two decimals (three for some diameters).
TOL = 0.01


class ProvenanceTest(unittest.TestCase):

    def test_every_value_is_positive_with_a_known_basis_and_a_ref(self):

        for line in CATALOG.values():
            for path, m in line.measures():

                if m is None:
                    continue

                with self.subTest(line=line.key, field=path):
                    self.assertIsInstance(m, Measure)
                    self.assertIn(m.basis, (PUBLISHED, DERIVED, MODEL_ASSUMPTION))
                    self.assertGreater(m.value, 0.0)
                    self.assertTrue(m.ref)

    def test_every_ref_names_a_listed_source(self):

        for line in CATALOG.values():
            for path, m in line.measures():

                if m is None:
                    continue

                with self.subTest(line=line.key, field=path):
                    self.assertIn(m.ref.split(":")[0].split(" ")[0], SOURCES)

    def test_a_derived_value_names_the_fls_ratio_it_used(self):

        for line in CATALOG.values():
            for path, m in line.measures():

                if m is not None and m.basis == DERIVED:
                    with self.subTest(line=line.key, field=path):
                        self.assertIn(" x FLS:", m.ref)

    def test_published_values_never_carry_an_fls_ratio(self):

        for line in CATALOG.values():
            for path, m in line.measures():

                if m is not None and m.basis == PUBLISHED:
                    with self.subTest(line=line.key, field=path):
                        self.assertNotIn(" x FLS:", m.ref)

    def test_a_basis_outside_the_three_is_refused(self):

        with self.assertRaises(ValueError):
            Measure(1.0, "estimated", "PF2500")

    def test_derive_accepts_only_ratios_sources_md_defines(self):

        base = published(6.0, "PF2500")

        for name in ("riser_L/D_riser", "riser_cone_L/D_riser",
                     "riser_end_D/D_riser", "gooseneck_L/D", "capacity"):
            with self.subTest(ratio=name):
                with self.assertRaises(KeyError):
                    derive(base, name, 1)

        defined = {name for name, _ in FLS_RATIOS}
        self.assertEqual(
            defined,
            {
                "eff_over_shell", "barrel_h/D", "cone_h/D", "vortex_len/D",
                "vortex_D/D", "dust_D/D", "inlet_w/D", "inlet_h/D",
                "riser_D/D_src", "calciner_eff_over_shell", "calciner_H/D",
                "kiln_eff_over_shell",
            },
        )


class WhatNoSourceGivesStaysEmptyTest(unittest.TestCase):

    def test_no_3000_line(self):

        self.assertEqual(set(CATALOG), {"1500", "2500", "5000", "FLS"})

        with self.assertRaises(KeyError):
            reference_line("3000")

    def test_riser_length_end_cone_and_end_diameter_are_none_on_vendor_lines(self):

        for key in ("1500", "2500", "5000"):
            for d in CATALOG[key].ducts:
                with self.subTest(line=key, duct=d.name):
                    self.assertIsNone(d.length)
                    self.assertIsNone(d.end_cone_len)
                    self.assertIsNone(d.end_D)

    def test_gooseneck_length_is_none_everywhere(self):

        for line in CATALOG.values():
            with self.subTest(line=line.key):
                self.assertIsNone(line.gooseneck.length)

    def test_gooseneck_diameter_exists_only_where_hfc_publishes_it(self):

        self.assertEqual(CATALOG["2500"].gooseneck.D.basis, PUBLISHED)
        self.assertEqual(CATALOG["2500"].gooseneck.D.value, 3.50)

        for key in ("1500", "5000", "FLS"):
            with self.subTest(line=key):
                self.assertIsNone(CATALOG[key].gooseneck.D)

    def test_no_tertiary_duct_and_no_meal_pipe_in_the_model(self):

        paths = {p for line in CATALOG.values() for p, _ in line.measures()}

        for word in ("tertiary", "meal"):
            with self.subTest(word=word):
                self.assertFalse(any(word in p for p in paths))


class AssumptionsAreVisibleTest(unittest.TestCase):

    def test_fls_inlet_width_and_height_are_model_assumptions(self):

        for c in CATALOG["FLS"].cyclones:
            with self.subTest(stage=c.stage):
                self.assertEqual(c.inlet_w.basis, MODEL_ASSUMPTION)
                self.assertEqual(c.inlet_h.basis, MODEL_ASSUMPTION)
                self.assertIn(W_IN_ASSUMPTION, c.inlet_w.assumptions)
                self.assertEqual(c.inlet_area.basis, PUBLISHED)

    def test_vendor_inlets_carry_the_w_in_assumption(self):

        for key in ("1500", "2500", "5000"):
            for c in CATALOG[key].cyclones:
                with self.subTest(line=key, stage=c.stage):
                    self.assertIn(W_IN_ASSUMPTION, c.inlet_w.assumptions)
                    self.assertIn(W_IN_ASSUMPTION, c.inlet_h.assumptions)

    def test_every_derived_c1_value_carries_the_transfer_assumption(self):

        for key in ("1500", "2500", "5000"):
            c1 = CATALOG[key].cyclones[0]
            self.assertGreater(c1.count, 1)

            for name in CYCLONE_FIELDS:
                m = getattr(c1, name)

                if m.basis == DERIVED:
                    with self.subTest(line=key, field=name):
                        self.assertIn(C1_TRANSFER_ASSUMPTION, m.assumptions)

    def test_lower_stages_carry_no_c1_transfer_assumption(self):

        for key in ("1500", "2500", "5000"):
            for c in CATALOG[key].cyclones[1:]:
                for name in CYCLONE_FIELDS:
                    with self.subTest(line=key, stage=c.stage, field=name):
                        self.assertNotIn(
                            C1_TRANSFER_ASSUMPTION, getattr(c, name).assumptions
                        )

    def test_the_riser_mapping_is_cited_not_assumed(self):
        """FLS Table 7 states which cyclones each riser connects, so
        neither the FLS risers nor the ratio-filled ones carry a mapping
        assumption; the FLS risers cite Table 7 instead."""

        for key in ("1500", "5000"):
            for d in CATALOG[key].ducts:
                with self.subTest(line=key, duct=d.name):
                    self.assertEqual(d.D.basis, DERIVED)
                    self.assertEqual(d.D.assumptions, ())

        for d in CATALOG["FLS"].ducts:
            for name in ("shell_D", "D", "length", "end_cone_len", "end_D"):
                m = getattr(d, name)

                with self.subTest(duct=d.name, field=name):
                    self.assertEqual(m.basis, PUBLISHED)
                    self.assertEqual(m.assumptions, ())
                    self.assertIn(RISER_MAPPING_REF, m.ref)
                    self.assertIn("Table 7", m.ref)


class MatchesSourcesMdTest(unittest.TestCase):

    def test_cyclones(self):

        for key, stages in SOURCES_MD_CYCLONES.items():
            for c in CATALOG[key].cyclones:
                for name, expected in zip(CYCLONE_FIELDS, stages[c.stage]):
                    with self.subTest(line=key, stage=c.stage, field=name):
                        self.assertAlmostEqual(
                            getattr(c, name).value, expected, delta=TOL
                        )

    def test_riser_diameters(self):

        for key, expected in SOURCES_MD_RISER_D.items():
            for d, value in zip(CATALOG[key].ducts, expected):
                with self.subTest(line=key, duct=d.name):
                    self.assertAlmostEqual(d.D.value, value, delta=TOL)

    def test_calciners(self):

        expected = {
            "1500": (5.898, DERIVED, 31.60, DERIVED),
            "2500": (5.50, PUBLISHED, 29.46, DERIVED),
            "5000": (6.740, DERIVED, 30.0, PUBLISHED),
            "FLS": (6.16, PUBLISHED, 33.0, PUBLISHED),
        }

        for key, (D, D_basis, H, H_basis) in expected.items():
            calciner = CATALOG[key].calciner
            with self.subTest(line=key):
                self.assertAlmostEqual(calciner.D.value, D, delta=TOL)
                self.assertEqual(calciner.D.basis, D_basis)
                self.assertAlmostEqual(calciner.length.value, H, delta=TOL)
                self.assertEqual(calciner.length.basis, H_basis)

    def test_kilns(self):

        expected = {
            "1500": (3.5, 54.0, 3.179),
            "2500": (4.0, 60.0, 3.633),
            "5000": (4.8, 74.0, 4.360),
        }

        for key, (shell, length, D) in expected.items():
            kiln = CATALOG[key].kiln
            with self.subTest(line=key):
                self.assertEqual(kiln.shell_D.value, shell)
                self.assertEqual(kiln.length.value, length)
                self.assertEqual(kiln.D.basis, DERIVED)
                self.assertAlmostEqual(kiln.D.value, D, delta=TOL)

    def test_published_2500_preheater_is_hfc(self):

        line = CATALOG["2500"]

        for c in line.cyclones:
            with self.subTest(stage=c.stage):
                self.assertEqual(c.D.basis, PUBLISHED)
                self.assertEqual(c.D.ref, "HFC2500")

        self.assertEqual(line.kiln.shell_D.ref, "PF2500")
        self.assertEqual(line.cooler.grate_area.ref, "PF2500")


class LinesTest(unittest.TestCase):

    def test_published_shells_grow_with_capacity(self):

        lines = [CATALOG[k] for k in ("1500", "2500", "5000")]

        kiln = [l.kiln.shell_D.value for l in lines]
        self.assertEqual(kiln, sorted(kiln))

        for stage in range(5):
            shells = [l.cyclones[stage].shell_D.value for l in lines]
            with self.subTest(stage=stage + 1):
                self.assertEqual(shells, sorted(shells))

    def test_cyclone_counts_and_strings(self):

        self.assertEqual([c.count for c in CATALOG["2500"].cyclones], [2, 1, 1, 1, 1])
        self.assertEqual([c.count for c in CATALOG["5000"].cyclones], [4, 2, 2, 2, 2])
        self.assertEqual(CATALOG["5000"].strings, 2)
        self.assertEqual(CATALOG["FLS"].capacity_t_d, None)

    def test_ducts_run_from_the_stage_below_to_the_stage_above(self):

        for line in CATALOG.values():
            with self.subTest(line=line.key):
                self.assertEqual(
                    [(d.from_stage, d.to_stage) for d in line.ducts],
                    [(2, 1), (3, 2), (4, 3), (5, 4)],
                )

    def test_config_selects_the_2500_line(self):

        self.assertEqual(reference_line_key(), "2500")
        self.assertIs(reference_line(reference_line_key()), CATALOG["2500"])


if __name__ == "__main__":
    unittest.main()
