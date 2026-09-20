"""The cyclone's dimensions, and which of them are allowed to be chosen.

A cyclone has eleven dimensions people quote, and four of them are not
independent. The cone locks together the body diameter, the dipleg
diameter, the cone height and the cone half angle:

    tan(half_angle) = (D_body - D_dipleg) / (2 H_cone)

Three of those four are free; the fourth is arithmetic. Total height is
worse -- it is the sum of the parts and never an input at all. A spec
that lets all eleven be typed in is a spec that can be given a cone
whose angle and height disagree, and CAD built from it will be wrong in
a way no amount of looking at the model reveals.

geometry.preheater.cyclone_spec closes that by making `cone_height` and
`total_height` properties of a frozen dataclass: not fields, so they
cannot be passed to the constructor, and not settable, so they cannot
be patched afterwards. This module is what proves they still agree with
the parts they are made of.

WHICH ONE IS INDEPENDENT, AND WHY IT IS THE ANGLE
-------------------------------------------------
The angle is the quantity physics constrains. The cone wall has to be
steeper than the heap the meal makes or the meal stays in the cone
instead of leaving it, and that heap's angle is already in the plant's
config as `motion.repose_angle_deg` = 40 deg. The cone height has no
such constraint on it -- it is whatever the angle and the two diameters
leave. So the angle is the input and the height is the consequence.

THE DIAMETER IS NOT CHOSEN EITHER
---------------------------------
It is what the gas duty demands at the design inlet velocity, through
D = sqrt(Q_v / (u_in * Ka * Kb)). Every other length is a ratio to it,
so the whole cyclone follows the gas through one square root. MEASURED
by sweeping the one input that moves it most:

    u_in [m/s]    D_body [m]
       15            6.09
       18            5.56
       22            5.03

WHAT THIS MODULE DOES NOT TEST
------------------------------
Anything made of triangles or B-reps. There is no CadQuery here on
purpose: the whole parameter model runs in the twin's own environment,
so a checkout that never installs a CAD kernel still gets the
arithmetic checked. tests/test_preheater_cyclone_geometry.py is where the solid
is measured, and it skips itself when the kernel is absent.
"""

import math
import unittest
from dataclasses import fields, replace

from tests.twin_harness import REPO_ROOT  # noqa: F401  (puts repo on sys.path)

from geometry.twin_config import repose_angle_deg
from geometry.preheater.cyclone_spec import (
    RATIO_RANGES,
    SCALAR_RANGES,
    CycloneSpec,
    dimension_report,
)


# The committed operating point, restated by hand. The test is
# worthless if it imports the number it is checking.
EXPECTED = {
    "D_body": 5.56,
    "cylinder_height": 7.23,
    "cone_height": 5.51,
    "vortex_finder_diameter": 2.78,
    "vortex_finder_length": 3.34,
    "vortex_finder_protrusion": 1.39,
    "dipleg_diameter": 1.11,
    "dipleg_length": 5.56,
    "inlet_width": 1.67,
    "inlet_height": 3.06,
    "total_height": 19.69,
}


class CycloneClosureTest(unittest.TestCase):
    """The over-determined dimensions still agree with their parts."""

    def setUp(self):
        self.spec = CycloneSpec()

    def test_the_cone_height_closes_the_cone_identity(self):
        """H_cone is not stored, so it cannot disagree with the angle.

        This is the identity the whole 'which one is independent'
        argument rests on. If it ever fails, the cone in the CAD is a
        different cone from the one in the dimension table.
        """

        spec = self.spec

        self.assertAlmostEqual(
            math.tan(math.radians(spec.cone_half_angle_deg)),
            (spec.D_body - spec.dipleg_diameter) / (2.0 * spec.cone_height),
            places=12,
        )

    def test_the_cone_identity_survives_every_angle_in_range(self):
        """Not a property of 22 degrees -- a property of the formula."""

        lo, hi = SCALAR_RANGES["cone_half_angle_deg"]

        for angle in (lo, 15.0, 22.0, 27.0, hi):

            with self.subTest(cone_half_angle_deg=angle):
                spec = replace(self.spec, cone_half_angle_deg=angle)

                self.assertAlmostEqual(
                    math.tan(math.radians(angle)),
                    (spec.D_body - spec.dipleg_diameter)
                    / (2.0 * spec.cone_height),
                    places=12,
                )

    def test_total_height_is_the_sum_of_its_parts(self):
        spec = self.spec

        self.assertAlmostEqual(
            spec.total_height,
            spec.vortex_finder_protrusion
            + spec.cylinder_height
            + spec.cone_height
            + spec.dipleg_length,
            places=12,
        )

    def test_a_steeper_cone_is_a_taller_cone(self):
        """Sign check: a smaller half angle means a longer cone."""

        steep = replace(self.spec, cone_half_angle_deg=14.0)
        blunt = replace(self.spec, cone_half_angle_deg=28.0)

        self.assertGreater(steep.cone_height, blunt.cone_height)


class CycloneSizingTest(unittest.TestCase):
    """The body diameter is what the gas duty demands."""

    def setUp(self):
        self.spec = CycloneSpec()

    def test_the_derived_diameter_reproduces_the_design_velocity(self):
        """Round-trip: the inlet the diameter implies passes the gas.

        Q_v / (Ka D * Kb D) must come back as the velocity that was
        asked for, or the square root was solved wrongly.
        """

        spec = self.spec

        self.assertAlmostEqual(
            spec.volumetric_flow / (spec.inlet_width * spec.inlet_height),
            spec.design_inlet_velocity_m_s,
            places=12,
        )

    def test_the_inlet_area_is_the_inlet_rectangle(self):
        spec = self.spec

        self.assertAlmostEqual(
            spec.inlet_area,
            spec.inlet_width * spec.inlet_height,
            places=12,
        )

    def test_the_gas_density_is_the_ideal_gas_law(self):
        spec = self.spec

        self.assertAlmostEqual(
            spec.gas_density
            * 8.314462618
            * spec.design_gas_temperature_K
            / (spec.design_pressure_Pa * spec.design_gas_molar_mass_kg_mol),
            1.0,
            places=12,
        )

    def test_the_diameter_goes_as_the_inverse_root_of_the_velocity(self):
        """D ~ 1/sqrt(u). Checked as a ratio, so the constant drops out."""

        base = self.spec

        for u in (15.0, 20.0, 22.0):

            with self.subTest(design_inlet_velocity_m_s=u):
                swept = replace(base, design_inlet_velocity_m_s=u)

                self.assertAlmostEqual(
                    swept.D_body / base.D_body,
                    math.sqrt(base.design_inlet_velocity_m_s / u),
                    places=12,
                )

    def test_the_diameter_goes_as_the_root_of_the_volumetric_flow(self):
        base = self.spec
        doubled = replace(base, design_gas_mass_flow_kg_s=2.0 * base.design_gas_mass_flow_kg_s)

        self.assertAlmostEqual(
            doubled.D_body / base.D_body,
            math.sqrt(2.0),
            places=12,
        )

    def test_every_length_scales_with_the_body_diameter(self):
        """One square root moves the whole cyclone, nothing else.

        Doubling the duty must multiply every length by the same
        factor. Anything that does not move is a literal that escaped
        the spec.
        """

        base = CycloneSpec()
        big = replace(base, design_gas_mass_flow_kg_s=4.0 * base.design_gas_mass_flow_kg_s)

        factor = big.D_body / base.D_body

        lengths = (
            "cylinder_height",
            "cone_height",
            "vortex_finder_diameter",
            "vortex_finder_length",
            "vortex_finder_protrusion",
            "dipleg_diameter",
            "dipleg_length",
            "inlet_width",
            "inlet_height",
            "total_height",
        )

        for name in lengths:

            with self.subTest(dimension=name):
                self.assertAlmostEqual(
                    getattr(big, name) / getattr(base, name),
                    factor,
                    places=12,
                )


class CycloneCommittedPointTest(unittest.TestCase):
    """The committed spec is the cyclone the plan agreed to build."""

    def setUp(self):
        self.spec = CycloneSpec()

    def test_the_dimension_table_is_the_one_that_was_approved(self):
        """Guards the gate: the derivation cannot drift unnoticed."""

        for name, expected in EXPECTED.items():

            with self.subTest(dimension=name):
                self.assertAlmostEqual(
                    getattr(self.spec, name),
                    expected,
                    delta=0.01,
                )

    def test_the_cyclone_is_the_size_a_cyclone_is(self):
        """A 4-6 m body is what a cement preheater cyclone measures.

        This is the check that caught the twin's inflated gas duty: at
        42.36 kg/s and 1986 K the same derivation gives 8.80 m and a
        156 m tower, which is not a machine anyone builds.
        """

        self.assertGreater(self.spec.D_body, 4.0)
        self.assertLess(self.spec.D_body, 6.0)

    def test_five_stacked_cyclones_make_a_real_tower(self):
        height = 5.0 * self.spec.total_height

        self.assertGreater(height, 60.0)
        self.assertLess(height, 120.0)

    def test_the_gate_report_runs_without_building_anything(self):
        report = dimension_report()

        self.assertIn("FAZ 1 GATE", report)
        self.assertIn("DERIVED (sum of parts)", report)
        self.assertIn("NOT WIRED INTO THE TWIN", report)


class CycloneRejectionTest(unittest.TestCase):
    """Out of range is refused, never clamped (CLAUDE.md)."""

    def setUp(self):
        self.spec = CycloneSpec()

    def test_every_ratio_is_rejected_outside_its_stated_range(self):
        for name, (lo, hi) in RATIO_RANGES.items():

            for bad in (lo - 0.01, hi + 0.01):

                with self.subTest(field=name, value=bad):

                    with self.assertRaises(ValueError) as caught:
                        replace(self.spec, **{name: bad})

                    self.assertIn(name, str(caught.exception))
                    self.assertIn(str(bad), str(caught.exception))

    def test_every_scalar_is_rejected_outside_its_stated_range(self):
        for name, (lo, hi) in SCALAR_RANGES.items():

            for bad in (lo * 0.5, hi * 1.5):

                with self.subTest(field=name, value=bad):

                    with self.assertRaises(ValueError) as caught:
                        replace(self.spec, **{name: bad})

                    self.assertIn(name, str(caught.exception))

    def test_a_dip_tube_above_the_inlet_mouth_is_refused(self):
        """It would short-circuit the gas straight to the outlet."""

        with self.assertRaises(ValueError) as caught:
            replace(
                self.spec,
                inlet_height_ratio=0.60,
                vortex_finder_length_ratio=0.50,
            )

        self.assertIn("below the", str(caught.exception))
        self.assertIn("vortex_finder_length_ratio", str(caught.exception))

    def test_the_dip_tube_cannot_reach_the_cone_from_inside_the_ranges(self):
        """A guard that the ranges already make unreachable.

        Immersion tops out at 0.80 D and the cylinder starts at 1.00 D,
        so the bands do not overlap and `S >= h` cannot be reached by
        any accepted spec. Asserted at the worst corner rather than by
        provoking the raise, because the raise is defence against
        someone WIDENING the bands, not against ordinary input.
        """

        worst = replace(
            self.spec,
            vortex_finder_length_ratio=RATIO_RANGES["vortex_finder_length_ratio"][1],
            cylinder_height_ratio=RATIO_RANGES["cylinder_height_ratio"][0],
        )

        self.assertLess(worst.vortex_finder_length, worst.cylinder_height)

    def test_the_volute_cannot_self_intersect_from_inside_the_ranges(self):
        """Same shape of argument: inlet width tops out at 0.40 D < D/2."""

        worst = replace(
            self.spec,
            inlet_width_ratio=RATIO_RANGES["inlet_width_ratio"][1],
        )

        self.assertLess(worst.inlet_width, 0.5 * worst.D_body)

    def test_the_short_circuit_constraint_is_the_one_that_really_binds(self):
        """Immersion and inlet height DO overlap, so this one can fire.

        S runs 0.45-0.80 and a runs 0.45-0.70, so the accepted box
        contains combinations where the dip tube sits above the inlet
        mouth. That is a real interior constraint, unlike the two
        above, and it is why _validate carries all three.
        """

        s_lo, s_hi = RATIO_RANGES["vortex_finder_length_ratio"]
        a_lo, a_hi = RATIO_RANGES["inlet_height_ratio"]

        self.assertLess(s_lo, a_hi)   # the bands overlap
        self.assertGreater(s_hi, a_lo)

        with self.assertRaises(ValueError):
            replace(
                self.spec,
                inlet_height_ratio=a_hi,
                vortex_finder_length_ratio=s_lo,
            )

    def test_derived_dimensions_cannot_be_assigned(self):
        """Frozen, and properties without setters. Both doors shut."""

        for name in ("D_body", "cone_height", "total_height", "inlet_area"):

            with self.subTest(dimension=name):

                with self.assertRaises(Exception):
                    setattr(self.spec, name, 1.0)

    def test_derived_dimensions_are_not_constructor_arguments(self):
        """They are properties, so they are not fields at all."""

        field_names = {f.name for f in fields(CycloneSpec)}

        for name in ("D_body", "cone_height", "total_height"):

            with self.subTest(dimension=name):
                self.assertNotIn(name, field_names)

                with self.assertRaises(TypeError):
                    CycloneSpec(**{name: 1.0})


class ConeShedsTheMealTest(unittest.TestCase):
    """The cone wall beats the meal's angle of repose."""

    def test_the_repose_angle_comes_from_the_twin_config(self):
        """Not restated here. One plant, one meal, one number."""

        self.assertAlmostEqual(repose_angle_deg(), 40.0, places=12)

    def test_every_accepted_cone_angle_clears_the_repose_angle(self):
        """The range is already safe; the guard is for widening it.

        At the blunt end of the accepted band the wall still stands at
        90 - 30 = 60 deg from horizontal against a 40 deg heap, so the
        meal slides. This states that the band and the physical
        constraint agree, which is what makes the guard in _validate
        unreachable rather than absent.
        """

        repose = repose_angle_deg()
        lo, hi = SCALAR_RANGES["cone_half_angle_deg"]

        for angle in (lo, 22.0, hi):

            with self.subTest(cone_half_angle_deg=angle):
                spec = replace(CycloneSpec(), cone_half_angle_deg=angle)

                self.assertGreater(spec.cone_wall_inclination_deg, repose)


class CycloneVolumeTest(unittest.TestCase):
    """Closed-form volumes, which the CAD solid is later held to."""

    def setUp(self):
        self.spec = CycloneSpec()

    def test_the_cylinder_volume_is_the_cylinder(self):
        spec = self.spec

        self.assertAlmostEqual(
            spec.cylinder_volume,
            math.pi * spec.D_body ** 2 / 4.0 * spec.cylinder_height,
            places=9,
        )

    def test_the_cone_volume_is_a_frustum_not_a_full_cone(self):
        """It is cut off at the dipleg, so it keeps the small end."""

        spec = self.spec

        full_cone = math.pi * (0.5 * spec.D_body) ** 2 * spec.cone_height / 3.0

        self.assertGreater(spec.cone_volume, full_cone)

    def test_the_volute_is_longer_than_a_circle_of_the_same_radius(self):
        """A spiral that wraps 270 degrees beats three quarters of a turn."""

        spec = self.spec

        three_quarter_turn = 0.75 * 2.0 * math.pi * spec.volute_inner_radius

        self.assertGreater(spec.volute_path_length, three_quarter_turn)
        self.assertLess(
            spec.volute_path_length,
            0.75 * 2.0 * math.pi * spec.volute_outer_radius,
        )

    def test_the_separator_volume_dwarfs_the_placeholder_cell(self):
        """The twin models a stage as 69.27 m3 of rotary cylinder.

        Stated so the size of what Faz 6 item 2 would later change is
        on the record. NOTHING HERE CHANGES THE TWIN.
        """

        self.assertGreater(self.spec.separator_volume, 3.0 * 69.27)


class PlanEnvelopeTest(unittest.TestCase):
    """How far the cyclone reaches, as a function of where you look.

    This is the law the tower layout keeps its distance by, so it is
    tested here rather than wherever it happens to be used. It lived in
    the drawing module until the layout needed it too; one shape may
    not have two definitions.
    """

    def setUp(self):
        self.spec = CycloneSpec()

    def test_the_scroll_is_widest_at_its_mouth(self):

        self.assertAlmostEqual(
            self.spec.plan_envelope_radius(0.0),
            self.spec.volute_outer_radius,
            places=12,
        )

    def test_the_scroll_closes_onto_the_barrel_at_the_end_of_the_wrap(self):
        """No step at the end of the wrap -- both branches give R."""

        self.assertAlmostEqual(
            self.spec.plan_envelope_radius(self.spec.volute_wrap_angle_deg),
            0.5 * self.spec.D_body,
            places=12,
        )

    def test_the_scroll_does_not_exist_beyond_its_wrap(self):

        beyond = 0.5 * (self.spec.volute_wrap_angle_deg + 360.0)

        self.assertAlmostEqual(
            self.spec.plan_envelope_radius(beyond),
            0.5 * self.spec.D_body,
            places=12,
        )

    def test_the_envelope_shrinks_all_the_way_round_the_wrap(self):

        wrap = self.spec.volute_wrap_angle_deg
        radii = [
            self.spec.plan_envelope_radius(wrap * i / 60.0)
            for i in range(61)
        ]

        for a, b in zip(radii, radii[1:]):
            self.assertGreater(a, b - 1.0e-12)

    def test_the_azimuth_wraps_round(self):

        self.assertAlmostEqual(
            self.spec.plan_envelope_radius(30.0),
            self.spec.plan_envelope_radius(390.0),
            places=12,
        )
        self.assertAlmostEqual(
            self.spec.plan_envelope_radius(30.0),
            self.spec.plan_envelope_radius(-330.0),
            places=12,
        )

    def test_the_envelope_polygon_closes(self):
        """First point and last are the same point.

        To machine precision, not bit-for-bit: the last sample is at
        360 deg, where sin comes back as -2.4e-16 rather than zero.
        """

        polygon = self.spec.plan_envelope(sections=72)

        for axis, (a, b) in enumerate(zip(polygon[0], polygon[-1])):
            with self.subTest(axis="xy"[axis]):
                self.assertAlmostEqual(a, b, places=12)

    def test_the_envelope_polygon_spans_the_scroll_and_the_barrel(self):

        radii = [
            math.hypot(x, y) for x, y in self.spec.plan_envelope(sections=360)
        ]

        self.assertAlmostEqual(
            max(radii), self.spec.volute_outer_radius, places=9,
        )
        self.assertAlmostEqual(
            min(radii), 0.5 * self.spec.D_body, places=9,
        )

    def test_a_coarse_envelope_polygon_is_refused(self):

        with self.assertRaises(ValueError):
            self.spec.plan_envelope(sections=8)


if __name__ == "__main__":
    unittest.main()
