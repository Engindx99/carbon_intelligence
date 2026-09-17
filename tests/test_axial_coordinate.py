import unittest

import numpy as np

from physics.axial_coordinate import (
    SOLID_FLOW_ZONE_ORDER,
    build_axial_layout,
    total_length,
)


# Lengths [m] and cell counts from configs/twin_cfg.yaml
LENGTHS = {
    "preheater": 25.0,
    "calciner": 25.0,
    "transition": 25.0,
    "burning": 60.0,
    "cooler": 25.0,
}

CELL_COUNTS = {
    "preheater": 5,
    "calciner": 20,
    "transition": 20,
    "burning": 20,
    "cooler": 20,
}


class AxialLayoutTest(unittest.TestCase):

    def setUp(self):
        self.layout = build_axial_layout(LENGTHS, CELL_COUNTS)

    def test_segment_bounds_follow_solid_path(self):

        expected = {
            "preheater": (0.0, 25.0),
            "calciner": (25.0, 50.0),
            "transition": (50.0, 75.0),
            "burning": (75.0, 135.0),
            "cooler": (135.0, 160.0),
        }

        for zone, (z0, z1) in expected.items():
            with self.subTest(zone=zone):
                self.assertAlmostEqual(self.layout[zone].z_start, z0)
                self.assertAlmostEqual(self.layout[zone].z_end, z1)

        self.assertAlmostEqual(total_length(self.layout), 160.0)

    def test_segments_are_contiguous(self):

        for upstream, downstream in zip(SOLID_FLOW_ZONE_ORDER, SOLID_FLOW_ZONE_ORDER[1:]):
            with self.subTest(interface=f"{upstream}->{downstream}"):
                self.assertEqual(
                    self.layout[upstream].z_end,
                    self.layout[downstream].z_start,
                )

    def test_local_mesh(self):

        for zone, seg in self.layout.items():
            with self.subTest(zone=zone):
                self.assertAlmostEqual(seg.dz, LENGTHS[zone] / CELL_COUNTS[zone])

                faces = seg.z_faces
                self.assertEqual(faces.shape, (seg.N + 1,))
                self.assertTrue(np.all(np.diff(faces) > 0.0))
                self.assertAlmostEqual(faces[0], seg.z_start)
                self.assertAlmostEqual(faces[-1], seg.z_end)

                np.testing.assert_allclose(seg.z_centers, 0.5 * (faces[:-1] + faces[1:]))

    def test_index_order(self):

        pre = self.layout["preheater"]
        # Stage 5 (index 4, feed inlet) sits upstream of Stage 1 (index 0)
        self.assertLess(pre.z_at_index[4], pre.z_at_index[0])
        np.testing.assert_allclose(pre.z_at_index, [22.5, 17.5, 12.5, 7.5, 2.5])

        for zone in SOLID_FLOW_ZONE_ORDER[1:]:
            with self.subTest(zone=zone):
                np.testing.assert_array_equal(
                    self.layout[zone].z_at_index,
                    self.layout[zone].z_centers,
                )

    def test_invalid_inputs_raise(self):

        cases = {
            "zero length": ({**LENGTHS, "burning": 0.0}, CELL_COUNTS),
            "negative length": ({**LENGTHS, "cooler": -1.0}, CELL_COUNTS),
            "zero cells": (LENGTHS, {**CELL_COUNTS, "calciner": 0}),
            "non-integer cells": (LENGTHS, {**CELL_COUNTS, "transition": 2.5}),
            "missing zone": (
                {k: v for k, v in LENGTHS.items() if k != "transition"},
                CELL_COUNTS,
            ),
        }

        for name, (lengths, counts) in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    build_axial_layout(lengths, counts)


if __name__ == "__main__":
    unittest.main()
