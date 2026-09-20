"""The calciner's reserved envelope.

No vessel is modelled, so there is nothing here about cones, burners or
tertiary air. What is tested is the only claim the spec makes: that the
radius the preheater tower stands back from is DERIVED from the gas the
tower itself carries, and that it cannot be edited past its validation.

No CAD kernel; these run in the twin's own environment.
"""

import math
import unittest
from dataclasses import replace

from tests.twin_harness import REPO_ROOT  # noqa: F401  (puts repo on sys.path)

from geometry.calciner.ilc_spec import ILCSpec, SCALAR_RANGES, ilc_report
from geometry.preheater.cyclone_spec import CycloneSpec
from geometry.preheater.tower_spec import TowerSpec


class ILCSizingTest(unittest.TestCase):

    def setUp(self):
        self.spec = ILCSpec(design_volumetric_flow_m3_s=91.9043)

    def test_the_bore_reproduces_the_design_velocity(self):
        """The only claim the diameter makes: Qv = A u."""

        area = math.pi * self.spec.D_body ** 2 / 4.0

        self.assertAlmostEqual(
            self.spec.design_volumetric_flow_m3_s / area,
            self.spec.gas_velocity_m_s,
            places=12,
        )

    def test_the_bore_goes_as_the_inverse_root_of_the_velocity(self):

        slow = replace(self.spec, gas_velocity_m_s=5.0)
        fast = replace(self.spec, gas_velocity_m_s=8.0)

        self.assertAlmostEqual(
            fast.D_body / slow.D_body, math.sqrt(5.0 / 8.0), places=12,
        )

    def test_the_bore_goes_as_the_root_of_the_duty(self):

        doubled = replace(
            self.spec,
            design_volumetric_flow_m3_s=(
                2.0 * self.spec.design_volumetric_flow_m3_s
            ),
        )

        self.assertAlmostEqual(
            doubled.D_body / self.spec.D_body, math.sqrt(2.0), places=12,
        )

    def test_the_reserved_radius_is_half_the_bore(self):
        """Bare vessel. The erection clearance is the tower's to add."""

        self.assertAlmostEqual(
            self.spec.reserved_radius, 0.5 * self.spec.D_body, places=12,
        )

    def test_the_body_is_a_cylinder(self):

        self.assertAlmostEqual(
            self.spec.body_volume,
            math.pi * self.spec.reserved_radius ** 2 * self.spec.body_height_m,
            places=9,
        )

    def test_the_body_alone_does_not_have_to_carry_the_residence_time(self):
        """1.67 s in the body; the ducts carry the rest to 2-5 s.

        Stated as a test so that a later change to `body_height_m`
        cannot quietly claim the band is met by the vessel alone.
        """

        self.assertLess(self.spec.body_residence_time, 2.0)

        with_ducts = self.spec.body_residence_time + 22.0 / 18.0

        self.assertGreater(with_ducts, 2.0)
        self.assertLess(with_ducts, 5.0)


class ILCRejectionTest(unittest.TestCase):
    """Out of range is refused, never clamped."""

    def setUp(self):
        self.spec = ILCSpec(design_volumetric_flow_m3_s=91.9043)

    def test_every_scalar_is_rejected_outside_its_stated_range(self):

        for name, (lo, hi) in SCALAR_RANGES.items():

            for value in (lo - abs(lo) * 0.5 - 0.1, hi + abs(hi) * 0.5 + 0.1):

                with self.subTest(field=name, value=value):

                    with self.assertRaises(ValueError) as ctx:
                        replace(self.spec, **{name: value})

                    self.assertIn(name, str(ctx.exception))

    def test_a_velocity_outside_the_ilc_band_is_refused(self):
        """Below 5 m/s the meal drops out; above 8 the time collapses."""

        for velocity in (3.0, 12.0):
            with self.subTest(velocity=velocity):
                with self.assertRaises(ValueError):
                    replace(self.spec, gas_velocity_m_s=velocity)

    def test_derived_values_cannot_be_assigned(self):

        with self.assertRaises(Exception):
            self.spec.D_body = 4.0


class OneGasTest(unittest.TestCase):
    """The tower and the calciner may not disagree about the gas."""

    def test_the_tower_hands_the_calciner_its_own_duty(self):

        tower = TowerSpec()

        self.assertAlmostEqual(
            tower.calciner.design_volumetric_flow_m3_s,
            tower.cyclone.volumetric_flow,
            places=12,
        )

    def test_the_duty_follows_when_the_cyclone_is_resized(self):

        hotter = CycloneSpec(design_gas_mass_flow_kg_s=40.0)
        tower = TowerSpec(cyclone=hotter)

        self.assertAlmostEqual(
            tower.calciner.design_volumetric_flow_m3_s,
            hotter.volumetric_flow,
            places=12,
        )
        self.assertGreater(
            tower.calciner.D_body, TowerSpec().calciner.D_body,
        )

    def test_the_reserved_bore_lands_near_the_twins_placeholder(self):
        """4.42 m against the twin's placeholder 4.2 m.

        An independent consistency check, not a constraint: the twin's
        4.2 m is a placeholder (physics/shell.py:842-848) and nothing
        here is wired to it. If the two ever drift far apart, one of
        them has stopped describing this plant.
        """

        self.assertAlmostEqual(TowerSpec().calciner.D_body, 4.2, delta=0.5)

    def test_a_caller_can_still_hand_in_its_own_calciner(self):

        mine = ILCSpec(
            design_volumetric_flow_m3_s=120.0, gas_velocity_m_s=7.0,
        )
        tower = TowerSpec(calciner=mine)

        self.assertIs(tower.calciner, mine)


class ILCReportTest(unittest.TestCase):

    def test_the_report_runs_without_building_anything(self):

        text = ilc_report()

        self.assertIn("reserved radius", text)
        self.assertIn("2-5 s", text)
        self.assertIn("NOT WIRED INTO THE TWIN", text)


if __name__ == "__main__":
    unittest.main()
