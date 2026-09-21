"""The tower gate: every line is refused, by name, for what it lacks.

The builder must not complete geometry. These tests pin exactly which
fields each catalogue line is missing for a tower, and the blockers
that are not fields (a double string, the open riser shape), so that
a value appearing in the catalogue later shows up here as a change
rather than being filled in silently.
"""

import dataclasses
import unittest

from geometry.catalog import CATALOG
from geometry.modelling import cfd_boundary_params
from geometry.tower import (
    RISER_SHAPE_OPEN,
    LayoutParams,
    TowerIncomplete,
    build_tower,
    missing_for_tower,
    required_fields,
    tower_blockers,
)


RISER_LENGTHS = ["R1.length", "R2.length", "R3.length", "R4.length"]


class MissingFieldsTest(unittest.TestCase):

    def test_2500_lacks_the_riser_lengths_and_the_gooseneck_length(self):

        self.assertEqual(
            missing_for_tower(CATALOG["2500"]), RISER_LENGTHS + ["gooseneck.length"]
        )

    def test_1500_also_lacks_the_gooseneck_diameter(self):

        self.assertEqual(
            missing_for_tower(CATALOG["1500"]),
            RISER_LENGTHS + ["gooseneck.D", "gooseneck.length"],
        )

    def test_5000_lacks_what_1500_lacks(self):

        self.assertEqual(
            missing_for_tower(CATALOG["5000"]),
            RISER_LENGTHS + ["gooseneck.D", "gooseneck.length"],
        )

    def test_fls_lacks_only_the_gooseneck(self):

        self.assertEqual(
            missing_for_tower(CATALOG["FLS"]), ["gooseneck.D", "gooseneck.length"]
        )

    def test_the_tower_needs_no_tertiary_duct_and_no_meal_pipe(self):

        for key, line in CATALOG.items():
            prefixes = {prefix for prefix, _, _ in required_fields(line)}

            with self.subTest(line=key):
                self.assertEqual(
                    prefixes,
                    {"C1", "C2", "C3", "C4", "C5", "R1", "R2", "R3", "R4",
                     "gooseneck", "calciner"},
                )


class BlockersTest(unittest.TestCase):

    def test_the_riser_shape_blocks_every_line(self):

        for key, line in CATALOG.items():
            with self.subTest(line=key):
                self.assertIn(RISER_SHAPE_OPEN, tower_blockers(line))

    def test_only_5000_is_blocked_as_a_double_string(self):

        for key, line in CATALOG.items():
            doubled = any("strings" in b for b in tower_blockers(line))

            with self.subTest(line=key):
                self.assertEqual(doubled, key == "5000")


class BuildTowerTest(unittest.TestCase):

    def test_every_line_is_refused_with_everything_it_lacks(self):

        cfd = cfd_boundary_params()

        for key, line in CATALOG.items():
            with self.subTest(line=key):
                with self.assertRaises(TowerIncomplete) as caught:
                    build_tower(line, cfd, layout=None)

                self.assertEqual(list(caught.exception.missing), missing_for_tower(line))
                self.assertEqual(list(caught.exception.blockers), tower_blockers(line))

                for field in missing_for_tower(line):
                    self.assertIn(field, str(caught.exception))

    def test_refusing_leaves_the_catalogue_as_it_was(self):

        before = {k: l.measures() for k, l in CATALOG.items()}

        for line in CATALOG.values():
            with self.assertRaises(TowerIncomplete):
                build_tower(line, cfd_boundary_params(), layout=None)

        self.assertEqual({k: l.measures() for k, l in CATALOG.items()}, before)


class LayoutParamsTest(unittest.TestCase):

    def test_layout_has_no_values_in_code(self):

        with self.assertRaises(TypeError):
            LayoutParams()

        for f in dataclasses.fields(LayoutParams):
            with self.subTest(field=f.name):
                self.assertIs(f.default, dataclasses.MISSING)

    def test_layout_is_not_part_of_the_catalogue(self):

        names = {f.name for f in dataclasses.fields(LayoutParams)}

        for key, line in CATALOG.items():
            fields = {path.split(".")[-1] for path, _ in line.measures()}

            with self.subTest(line=key):
                self.assertFalse(names & fields)


if __name__ == "__main__":
    unittest.main()
