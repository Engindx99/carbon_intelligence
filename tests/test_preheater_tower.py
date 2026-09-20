"""Five identical cyclones, and the ducts that make them a preheater.

FAZ 4 -- WHY "IDENTICAL" IS NOT MEASURED HERE FIRST
---------------------------------------------------
geometry.preheater.tower_build calls build_cyclone ONCE and turns and
moves the result five times. There is no second construction that
could be given a different parameter and no stage index anywhere near
a dimension, so the five cyclones are identical by construction rather
than by agreement. The tests below still measure it -- undo a stage's
placement and its bounding box and volume come back as the base
shape's -- but what they are really guarding is that nobody later
replaces the transform with a rebuild.

FAZ 5 -- WHAT ONE SOLID PROVES
------------------------------
Fusing the five cyclones and the eleven ducts gives ONE solid. That
single number is the acceptance test for the whole layout: if any
riser missed the mouth it was aiming at, or any meal line fell short of
the riser it was supposed to join, the fusion would come back as two or
more bodies. It is also why ducts are allowed to overlap the vessels
they enter instead of merely touching -- a tangential touch fuses into
a non-manifold sliver, exactly as the volute does on the cyclone.

THE CONSTRAINT THAT SHAPES THE TOWER
------------------------------------
Meal from cyclone n is injected into the duct FEEDING cyclone n+1, not
into cyclone n+1 itself -- the ducts are where the heat exchange
happens. Since the stages were given their own places in plan, getting
it there is a two-leg problem and no longer a three-leg one: a long
vertical drop down PAST the cyclone below, then one inclined chute
steeper than the meal's angle of repose. MEASURED on the committed
layout:

    from stage  drop   chute   entry z   riser vertical run
        1       8.43    5.42    75.91     64.25 ..  83.36
        2       8.43    5.42    53.72     42.05 ..  61.16
        3       8.43    5.42    31.52     19.86 ..  38.97
        4       8.43    5.42     9.33     -5.56 ..  16.77

So the entry angle, the drop, the riser's stand-off and the stage
pitch are not four independent choices. TowerSpec rejects a
combination where a meal line misses its riser, and the test below
drives it into that rejection from both sides.

AND THE PLAN OFFSET IS NOT A CLEARANCE, IT IS A CONSTRAINT
----------------------------------------------------------
The five cyclones used to stand on ONE axis, so every dipleg
discharged directly above the next cyclone's gas outlet and the two
ducts leaving those two openings both began on that axis. They cleared
each other only if the stage gap exceeded the sum of their radii,
1.275 + 0.556 = 1.831 m. It was 1.391 m, and no routing could have
saved it.

Widening the gap patched that. Offsetting the stages in plan removed
it: the chord between neighbours is now 6.514 m and the meal line
drops down the SIDE of the cyclone below instead of dodging round it.
Six plan clearances hold that offset in place, and one rule holds
every duct off every other duct -- which is the one that matters, and
the one that was missing. `PlanOffsetTest` checks each from both
sides: a layout that clears, and a layout that is refused, asserting
WHICH check refused it rather than a phrase from the message.

WHY THE BAR IS 0.050 m AND NOT 0.300 m
--------------------------------------
This package models the fluid volume for CFD, not a fabrication. The
gap between two ducts lies outside the domain and is never meshed, so
it costs nothing; interference costs the topology, because the tower
is a union and a union merges what overlaps. The bar is numerical.

The tower is still 112.36852420346332 m tall. Not one level moved.

WHAT THIS MODULE DOES NOT CHECK
-------------------------------
Pressure drop, separation efficiency, dust loops, gas residence time,
expansion joints, supports, or anything else about the process. The
twin's preheater still runs on its placeholder 4.2 m x 25 m rotary
cylinder and nothing in geometry/ touches it.
"""

import math
import unittest
from dataclasses import replace

from tests.twin_harness import REPO_ROOT  # noqa: F401  (puts repo on sys.path)

from geometry import plan, space
from geometry.twin_config import repose_angle_deg
from geometry.preheater.cyclone_spec import CycloneSpec
from geometry.preheater.tower_spec import (
    CLEARANCES,
    LAYOUT_PATTERNS,
    TOWER_ANGLE_RANGES,
    TOWER_LENGTH_RANGES,
    TOWER_RATIO_RANGES,
    TowerSpec,
    layout_report,
)

try:
    import cadquery as cq  # noqa: F401

    from geometry.preheater.tower_build import (
        build_preheater,
        build_tower_solid,
    )

    HAS_CADQUERY = True

except ImportError:
    HAS_CADQUERY = False


SKIP_REASON = (
    "cadquery is not importable; install it with "
    "requirements-cad.txt and put it on PYTHONPATH"
)

# Coarser than the default 72, purely to keep the tower fusion quick.
TEST_SECTIONS = 36


def _connections(stage_count):
    """Every pair of bodies that is SUPPOSED to be joined.

    The whitelist for `test_nothing_overlaps_that_is_not_a_connection`.
    Written out from the process, not read off the geometry, so it
    states what the tower is meant to be rather than what it is.
    """

    pairs = set()

    for stage in range(1, stage_count + 1):
        # a riser enters the cyclone it feeds ...
        pairs.add((f"riser_{stage}", f"cyclone_{stage}"))

        # ... and leaves the one below it, on a butt joint
        if stage < stage_count:
            pairs.add((f"riser_{stage}", f"cyclone_{stage + 1}"))

    for stage in range(1, stage_count):
        pairs.add((f"meal_line_{stage}", f"cyclone_{stage}"))
        pairs.add((f"meal_line_{stage}", f"riser_{stage + 1}"))

    pairs.add(("raw_meal_inlet", "riser_1"))
    pairs.add(("exit_stack", "cyclone_1"))

    return {tuple(sorted(pair)) for pair in pairs}


def _is_a_connection(first, second, stage_count):
    return tuple(sorted((first, second))) in _connections(stage_count)


def _intersection_volume(a, b):
    """Volume shared by two solids [m3]; 0.0 when they only touch."""

    try:
        common = a.intersect(b)
    except Exception:
        return 0.0

    if not common.Solids():
        return 0.0

    return float(common.Volume())


class TowerLayoutTest(unittest.TestCase):
    """The arrangement, checked without a CAD kernel."""

    def setUp(self):
        self.tower = TowerSpec()

    def test_the_stages_are_one_pitch_apart(self):
        bases = [
            self.tower.stage_base_z(s)
            for s in range(1, self.tower.stage_count + 1)
        ]

        for upper, lower in zip(bases, bases[1:]):

            with self.subTest(gap=upper - lower):
                self.assertAlmostEqual(
                    upper - lower, self.tower.pitch, places=12
                )

    def test_stage_one_is_the_top_and_stage_five_the_bottom(self):
        """Gas leaves at stage 1, meal leaves at stage 5."""

        self.assertAlmostEqual(self.tower.stage_base_z(5), 0.0, places=12)
        self.assertGreater(
            self.tower.stage_base_z(1), self.tower.stage_base_z(5)
        )

    def test_the_pitch_clears_the_cyclone_it_has_to_hold(self):
        """A stage cannot be shorter than the cyclone standing in it."""

        self.assertAlmostEqual(
            self.tower.pitch,
            self.tower.cyclone.total_height + self.tower.stage_gap,
            places=12,
        )
        self.assertGreater(self.tower.stage_gap, 0.0)

    def test_the_tower_is_the_height_a_preheater_tower_is(self):
        self.assertGreater(self.tower.tower_height, 60.0)
        self.assertLess(self.tower.tower_height, 120.0)

    def test_the_tower_height_is_frozen(self):
        """112.3685 m, and re-proportioning inside it does not move it.

        The stage gap had to grow by 1.112 m per stage to let the gas
        elbow clear the dipleg above it. That came out of the exhaust
        stack stub, whose length nothing physical sets, rather than off
        the top of the tower. This test is what makes that a rule and
        not a coincidence: any future trade has to balance the same way.
        """

        self.assertAlmostEqual(self.tower.tower_height, 112.3685, delta=1.0e-3)

    def test_the_offset_clears_the_cyclone_the_dipleg_drops_past(self):
        """The defect that eight overlaps came from, as an inequality.

        A dipleg used to discharge directly above the next cyclone's
        gas outlet, because the two shared an axis. Now it discharges
        `chord_between_stages` away from it, and that chord has to beat
        the cyclone's reach on the flank it comes down plus the meal
        line's own radius -- or the line drops through a roof no matter
        how it is routed afterwards.

        This is the check the whole plan offset exists to satisfy, and
        it is the one that binds: at 27 deg of azimuth step it has
        0.636 m to spare and at 26 deg it does not clear at all.
        """

        needed = (
            self.tower.meal_side_envelope_radius
            + 0.5 * self.tower.meal_line_diameter
            + self.tower.mesh_clearance_m
        )

        self.assertGreater(self.tower.chord_between_stages, needed)

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                self.assertGreaterEqual(
                    self.tower.dipleg_drop_clearance(stage),
                    self.tower.mesh_clearance_m,
                )

    def test_the_riser_lift_is_not_the_stage_gap(self):
        """Two defaults that were the same number, and should not be.

        When `riser_rise_ratio` equalled `stage_gap_ratio` the riser's
        vertical lift ended exactly at the dipleg discharge above it and
        its elbow sat on the meal outlet.
        """

        self.assertNotAlmostEqual(
            self.tower.riser_rise_ratio,
            self.tower.stage_gap_ratio,
            places=6,
        )

    def test_an_out_of_range_stage_is_refused(self):
        for stage in (0, -1, 6):

            with self.subTest(stage=stage):

                with self.assertRaises(ValueError) as caught:
                    self.tower.stage_base_z(stage)

                self.assertIn("1 = top", str(caught.exception))

    def test_every_tower_ratio_is_rejected_outside_its_range(self):
        for name, (lo, hi) in TOWER_RATIO_RANGES.items():

            for bad in (lo - 0.01, hi + 0.01):

                with self.subTest(field=name, value=bad):

                    with self.assertRaises(ValueError) as caught:
                        replace(self.tower, **{name: bad})

                    self.assertIn(name, str(caught.exception))

    def test_every_tower_angle_is_rejected_outside_its_range(self):
        for name, (lo, hi) in TOWER_ANGLE_RANGES.items():

            for bad in (lo - 1.0, hi + 1.0):

                with self.subTest(field=name, value=bad):

                    with self.assertRaises(ValueError) as caught:
                        replace(self.tower, **{name: bad})

                    self.assertIn(name, str(caught.exception))

    def test_every_tunable_field_has_a_range(self):
        """The rule that would have caught the one that shipped without.

        `meal_azimuth_offset_deg` was a tunable with no range at all,
        so the sweep above walked straight past it. Suffix decides
        which table a field belongs in; `cyclone`, `calciner`,
        `stage_count` and `layout_pattern` are not numbers and match
        neither, which is a fact about them rather than a skip list.
        """

        import dataclasses

        for field in dataclasses.fields(TowerSpec):

            with self.subTest(field=field.name):

                if field.name.endswith("_ratio"):
                    self.assertIn(field.name, TOWER_RATIO_RANGES)

                elif field.name.endswith("_deg"):
                    self.assertIn(
                        field.name,
                        set(TOWER_ANGLE_RANGES) | {"dipleg_entry_angle_deg"},
                    )

                elif field.name.endswith("_m"):
                    self.assertIn(field.name, TOWER_LENGTH_RANGES)

                else:
                    self.assertIn(
                        field.name,
                        {
                            "cyclone",
                            "calciner",
                            "stage_count",
                            "layout_pattern",
                        },
                    )

    def test_an_unknown_layout_pattern_is_refused(self):

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, layout_pattern="helix")

        self.assertIn("layout_pattern", str(caught.exception))

    def test_the_layout_report_runs_without_building_anything(self):
        report = layout_report(self.tower)

        self.assertIn("IDENTICAL cyclones", report)
        self.assertIn("NOT WIRED INTO THE TWIN", report)


class TowerDuctSizingTest(unittest.TestCase):
    """Both duct bores are derived, so neither can drift."""

    def setUp(self):
        self.tower = TowerSpec()

    def test_the_riser_carries_the_gas_at_the_design_inlet_velocity(self):
        """Same gas, same velocity, therefore the same area.

        A riser with a ratio of its own could have disagreed with the
        inlet the cyclone was sized around; this one cannot.
        """

        tower = self.tower
        area = math.pi * tower.riser_diameter ** 2 / 4.0

        self.assertAlmostEqual(area, tower.cyclone.inlet_area, places=12)

        self.assertAlmostEqual(
            tower.cyclone.volumetric_flow / area,
            tower.cyclone.design_inlet_velocity_m_s,
            places=12,
        )

    def test_the_meal_lines_are_the_cyclones_own_dipleg_bore(self):
        self.assertAlmostEqual(
            self.tower.meal_line_diameter,
            self.tower.cyclone.dipleg_diameter,
            places=12,
        )

    def test_both_bores_follow_the_cyclone_when_it_is_resized(self):
        """Nothing in the tower is a length of its own."""

        base = TowerSpec()
        big = TowerSpec(
            cyclone=replace(
                base.cyclone,
                design_gas_mass_flow_kg_s=4.0
                * base.cyclone.design_gas_mass_flow_kg_s,
            )
        )

        factor = big.cyclone.D_body / base.cyclone.D_body

        for name in ("riser_diameter", "meal_line_diameter", "pitch", "tower_height"):

            with self.subTest(quantity=name):
                self.assertAlmostEqual(
                    getattr(big, name) / getattr(base, name), factor, places=9
                )


class MealPathTest(unittest.TestCase):
    """Where the meal goes, and whether it can get there."""

    def setUp(self):
        self.tower = TowerSpec()

    def test_meal_from_a_stage_joins_the_riser_feeding_the_next_stage(self):
        """Not the next cyclone -- the DUCT feeding it.

        The ducts are the heat exchanger. Dropping meal straight into
        the cyclone below would make the tower a stack of separators
        that exchange no heat.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                end = self.tower.meal_line_path(stage)[-1]
                z_low, z_high = self.tower.riser_vertical_span(stage + 1)
                axis_x, axis_y = self.tower.riser_axis(stage + 1)

                self.assertAlmostEqual(end[0], axis_x, places=12)
                self.assertAlmostEqual(end[1], axis_y, places=12)
                self.assertGreaterEqual(end[2], z_low)
                self.assertLessEqual(end[2], z_high)

    def test_the_bottom_stage_has_no_riser_to_join(self):
        """Its meal leaves the tower for the calciner."""

        with self.assertRaises(ValueError) as caught:
            self.tower.meal_line_path(self.tower.stage_count)

        self.assertIn("calciner", str(caught.exception))

    def test_a_meal_line_is_a_drop_and_a_chute(self):
        """Two legs, which is what a dipleg actually is.

        A vertical pipe with a flap valve, then an inclined chute. The
        line was three legs while the stages shared an axis, because
        the middle one had to dodge sideways around a cyclone that was
        directly underneath. The plan offset took that cyclone out of
        the way.

        The point count is asserted, so a future edit cannot quietly
        put a leg back without saying why.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                path = self.tower.meal_line_path(stage)

                self.assertEqual(len(path), 3)

                start, dropped, end = path

                # 1. straight down out of the dipleg, and a long way
                self.assertAlmostEqual(dropped[0], start[0], places=12)
                self.assertAlmostEqual(dropped[1], start[1], places=12)
                self.assertGreater(start[2] - dropped[2], self.tower.stage_gap)

                # 2. the inclined chute, which both falls and turns
                self.assertLess(end[2], dropped[2])
                self.assertGreater(
                    math.hypot(end[0] - dropped[0], end[1] - dropped[1]), 0.0
                )

    def test_the_inclined_leg_runs_steeper_than_the_meal_heaps(self):
        """Only the chute has to beat repose; the drop is vertical."""

        repose = repose_angle_deg()

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                _start, dropped, end = self.tower.meal_line_path(stage)

                run = math.hypot(end[0] - dropped[0], end[1] - dropped[1])
                drop = dropped[2] - end[2]

                self.assertGreater(math.degrees(math.atan2(drop, run)), repose)

    def test_the_vertical_leg_runs_well_past_the_stage_gap(self):
        """The premise of this test inverted when the offset arrived.

        It used to assert the drop stayed INSIDE the stage gap, because
        anything longer would have gone into the roof of the cyclone
        below. Offset in plan, the cyclone is no longer underneath, and
        the drop has to run past it -- far enough that the chute starts
        below the gas elbow it would otherwise cross.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                start, dropped, _end = self.tower.meal_line_path(stage)

                self.assertGreater(
                    start[2] - dropped[2], self.tower.stage_gap
                )

                # What the vertical leg is FOR: getting past the mouth
                # leg of the riser below before turning in. That leg
                # starts at the top of the very column the meal is
                # aiming for, and the dipleg axis stands 2.08 m off it
                # against a 1.831 m requirement -- so the turn cannot
                # happen until the line is below it.
                mouth_z = self.tower.riser_vertical_span(stage + 1)[1]

                self.assertLess(dropped[2], mouth_z)

    def test_the_raw_meal_chute_is_refused_below_the_repose_angle(self):
        """The one meal slope that is still SET rather than derived.

        The raw meal inlet comes in from outside the tower, so nothing
        in the layout fixes its slope and it keeps a field.
        """

        repose = repose_angle_deg()

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, dipleg_entry_angle_deg=repose - 5.0)

        self.assertIn("repose", str(caught.exception))
        self.assertIn("dipleg_entry_angle_deg", str(caught.exception))

    def test_a_meal_line_enters_its_riser_tangentially(self):
        """The principle, as a number.

        A meal line that drops vertically and then kinks in meets the
        riser at a wide angle, and a duct arriving across the flow is
        a duct the gas has to turn. These arrive nearly along the
        riser's own axis, so the meal is picked up rather than
        deflected.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                self.assertLess(self.tower.meal_riser_angle_deg(stage), 15.0)

    def test_the_meal_slope_is_derived_and_still_clears_repose(self):
        """Both ends are fixed, so the slope is a consequence.

        Nothing sets it; it is whatever the discharge above and the
        landing point below give. What the spec still insists on is
        that the result runs rather than plugs.
        """

        repose = repose_angle_deg()

        for stage in range(1, self.tower.stage_count):

            with self.subTest(from_stage=stage):
                self.assertGreater(
                    self.tower.meal_entry_angle_deg(stage), repose
                )

        # Land it high enough on the run and the slope goes shallow.
        # 0.95 of the run is almost level with the discharge.
        with self.assertRaises(ValueError) as caught:
            replace(self.tower, meal_entry_height_ratio=0.95)

        self.assertIn("repose", str(caught.exception))

    def test_the_riser_column_clears_the_cyclone_it_climbs_past(self):
        """Swept at the corners of the box, not by provoking the raise.

        The riser's vertical run stands `riser_reach` from its own
        cyclone's axis and has to beat the cyclone's reach ON THAT
        FLANK plus its own radius. The flank matters: the scroll is
        1.669 m wider at its mouth than where it closes, so the wrap
        angle is swept too -- it is a new dependency that arrived with
        `plan_envelope_radius` and would otherwise go unchecked.

        Not every corner of the box is buildable, and pretending
        otherwise would be the easy way to make this test pass. A
        corner that the layout cannot hold must REFUSE, and the
        refusal has to name a knob somebody can turn; a corner that is
        accepted must clear. Both halves are asserted.
        """

        knobs = (
            "riser_approach_ratio",
            "stage_azimuth_step_deg",
            "column_radius_ratio",
            "meal_side_azimuth_deg",
            "meal_drop_ratio",
        )

        built = 0
        refused = 0
        worst_margin = None

        for approach in (0.90, 1.0, 1.30):

            for inlet_width in (0.20, 0.40):

                for inlet_height in (0.45, 0.70):

                    for wrap in (180.0, 270.0, 360.0):

                        cyclone = replace(
                            CycloneSpec(),
                            inlet_width_ratio=inlet_width,
                            inlet_height_ratio=inlet_height,
                            vortex_finder_length_ratio=0.75,
                            volute_wrap_angle_deg=wrap,
                        )

                        with self.subTest(
                            approach=approach,
                            inlet_width=inlet_width,
                            inlet_height=inlet_height,
                            wrap=wrap,
                        ):
                            try:
                                tower = TowerSpec(
                                    cyclone=cyclone,
                                    riser_approach_ratio=approach,
                                )

                            except ValueError as caught:
                                refused += 1

                                self.assertTrue(
                                    any(knob in str(caught) for knob in knobs),
                                    f"refusal names no knob: {caught}",
                                )
                                continue

                            built += 1
                            margin = (
                                tower.riser_column_clearance()
                                / cyclone.D_body
                            )

                            self.assertGreater(
                                tower.riser_column_clearance(),
                                tower.mesh_clearance_m,
                            )

                            if worst_margin is None or margin < worst_margin:
                                worst_margin = margin

        self.assertGreater(built, 0)
        self.assertGreater(worst_margin, 0.10)


class PlanOffsetTest(unittest.TestCase):
    """Where the stages stand, and the seven checks that put them there.

    Every one of these runs without a CAD kernel, which is the point:
    the layout has to be provable in the environment the twin itself
    runs in, before any solid is built.
    """

    def setUp(self):
        self.tower = TowerSpec()

    # ---------- the shape of the layout ----------
    def test_every_stage_stands_on_the_column_circle(self):

        for placement in self.tower.placements():

            with self.subTest(stage=placement.stage):
                self.assertAlmostEqual(
                    math.hypot(placement.x, placement.y),
                    self.tower.column_radius,
                    places=9,
                )

    def test_stage_one_stands_on_the_x_axis(self):
        """So that `column_radius` is a line a drawing can dimension."""

        first = self.tower.placement(1)

        self.assertAlmostEqual(first.x, self.tower.column_radius, places=12)
        self.assertAlmostEqual(first.y, 0.0, places=12)

    def test_a_fan_is_one_stage_screwed_up_a_helix(self):
        """Equal steps in place AND in facing, so every stage sees the
        same local picture -- which is why the seven clearances come
        out stage-independent."""

        tower = TowerSpec(layout_pattern="fan")
        placements = tower.placements()

        for below, above in zip(placements, placements[1:]):

            with self.subTest(stage=above.stage):

                turned = (
                    above.azimuth_deg - below.azimuth_deg
                ) % 360.0

                self.assertAlmostEqual(
                    turned, tower.stage_azimuth_step_deg, places=9,
                )

    def test_a_fan_puts_every_stage_in_a_different_place(self):

        tower = TowerSpec(layout_pattern="fan")
        places = [(p.x, p.y) for p in tower.placements()]

        for i, here in enumerate(places):
            for j, there in enumerate(places[i + 1:], start=i + 1):

                with self.subTest(stages=(i + 1, j + 1)):
                    self.assertGreater(math.dist(here, there), 1.0)

    def test_a_zigzag_repeats_every_other_stage(self):
        """Stated rather than implied: it is the whole difference
        between the two patterns, and it is what the second-neighbour
        offset gives up."""

        tower = TowerSpec(layout_pattern="zigzag")
        places = [(p.x, p.y) for p in tower.placements()]

        self.assertAlmostEqual(math.dist(places[0], places[2]), 0.0, places=9)
        self.assertAlmostEqual(math.dist(places[1], places[3]), 0.0, places=9)
        self.assertGreater(math.dist(places[0], places[1]), 1.0)

    def test_both_patterns_offset_every_NEIGHBOUR_by_the_same_chord(self):

        for pattern in LAYOUT_PATTERNS:

            tower = TowerSpec(layout_pattern=pattern)
            placements = tower.placements()

            for below, above in zip(placements, placements[1:]):

                with self.subTest(pattern=pattern, stage=above.stage):
                    self.assertAlmostEqual(
                        math.dist((below.x, below.y), (above.x, above.y)),
                        tower.chord_between_stages,
                        places=9,
                    )

    def test_the_tower_height_is_the_same_for_both_patterns(self):
        """A purely horizontal rearrangement, and this says so."""

        for pattern in LAYOUT_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertEqual(
                    TowerSpec(layout_pattern=pattern).tower_height,
                    112.36852420346332,
                )

    # ---------- the seven, accepted ----------
    def test_the_committed_layout_clears_every_check(self):
        """Walked, not written out.

        This test used to list seven assertions by hand, which is the
        same mistake `_validate_plan` used to make and for the same
        reason: a list that is written out cannot be counted against
        anything, so a check that is added in one place and forgotten
        in another goes unnoticed. It walks `CLEARANCES` now, so a
        seventh check is tested the moment it exists.
        """

        for check, have, need in self.tower.clearances():

            with self.subTest(check=check.number, label=check.label):
                self.assertGreaterEqual(have, need)

    def test_no_flow_passage_touches_one_it_does_not_join(self):
        """The rule that replaced two hand-written clearances.

        This is the whole fluid-volume criterion: the tower is built
        as a union, so any overlap away from a junction merges two
        passages and puts a short circuit in the CFD domain.
        """

        self.assertEqual(
            [
                f"{a}[{i}] x {b}[{j}]: {gap:+.3f} m"
                for a, i, b, j, gap in self.tower.duct_interferences()
            ],
            [],
        )

    def test_the_zigzag_is_no_wider_than_it_has_to_be(self):
        """The rule the default was chosen by, as a test.

        Every extra degree of azimuth step lengthens the gas ducts, and
        duct is pressure drop and shell loss, so the step is the
        SMALLEST opening at which no passage touches one it does not
        join. Two degrees tighter has to be refused -- 44 deg still
        clears by 0.131 m, 43 deg does not clear at all -- and that
        asymmetry is why this steps by two and not by one.
        """

        tower = self.tower

        self.assertEqual(tower.duct_interferences(), [])

        with self.assertRaises(ValueError) as caught:
            replace(
                tower,
                stage_azimuth_step_deg=tower.stage_azimuth_step_deg - 2.0,
            )

        self.assertIn("stage_azimuth_step_deg", str(caught.exception))

    # ---------- refused, and BY WHICH CHECK ----------
    #
    # Every one of these asserts the check NUMBER, not a phrase from
    # the message. Two checks can name the same knob -- turning the
    # flank moves the riser column as well as the meal line -- so a
    # test keyed on a knob name cannot tell which inequality actually
    # fired, and would pass for the wrong reason.

    def test_a_chord_too_short_to_drop_the_meal_past_is_refused(self):
        """Close the zigzag and the chord closes with it.

        The chord, not the circle: shrinking `column_radius_ratio`
        walks the cyclones onto the calciner and check 4 fires first,
        which is a different (and also correct) refusal. Narrowing the
        step leaves the circle where it is and isolates check 1.
        """

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, stage_azimuth_step_deg=22.0)

        self.assertIn("check 1", str(caught.exception))

    def test_a_step_that_crosses_the_meal_line_over_its_riser_is_refused(self):
        """Between 22 and 45 deg the plan checks all pass and the
        fluid volume is still wrong -- which is the whole reason the
        duct rule exists. At 24 deg the meal line goes through the
        mouth leg of the riser it is aiming at."""

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, stage_azimuth_step_deg=24.0)

        message = str(caught.exception)

        self.assertIn("TowerSpec ducts", message)
        self.assertIn("meal_line_1", message)

    def test_a_column_that_stands_on_the_calciner_is_refused(self):
        """The chord is held up by a wider azimuth step, so the only
        thing left to fail is the calciner the tower stands around."""

        with self.assertRaises(ValueError) as caught:
            replace(
                self.tower,
                column_radius_ratio=0.80,
                stage_azimuth_step_deg=70.0,
            )

        message = str(caught.exception)

        self.assertIn("calciner", message)
        self.assertIn("column_radius_ratio", message)

    def test_a_step_that_swings_the_risers_onto_the_calciner_is_refused(self):

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, stage_azimuth_step_deg=110.0)

        self.assertIn("calciner", str(caught.exception))

    def test_a_meal_side_on_the_wrong_flank_is_refused(self):
        """Turn the cyclone so the meal comes down past the scroll's
        mouth and the same chord no longer clears."""

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, meal_side_azimuth_deg=350.0)

        # Check 5, not check 1: turning the flank turns the WHOLE
        # cyclone, so the riser column swings with it and reaches the
        # calciner before the meal line runs out of chord.
        self.assertIn("check 5", str(caught.exception))

    def test_a_dipleg_drop_too_short_to_pass_the_elbow_is_refused(self):

        with self.assertRaises(ValueError) as caught:
            replace(self.tower, meal_drop_ratio=0.12)

        message = str(caught.exception)

        # Refused by the duct rule now, not by a hand-written
        # clearance: shortening the drop turns the line in while it is
        # still level with the mouth leg of the riser it is aiming at,
        # which is the crossing the rule exists to catch.
        self.assertIn("TowerSpec ducts", message)
        self.assertIn("meal_line_1", message)

    def test_every_refusal_names_the_stage_it_measured(self):

        for kwargs in (
            {"column_radius_ratio": 0.80},
            {"column_radius_ratio": 0.80, "stage_azimuth_step_deg": 70.0},
            {"stage_azimuth_step_deg": 110.0},
            {"meal_side_azimuth_deg": 0.0},
            {"meal_drop_ratio": 0.12},
        ):

            with self.subTest(**kwargs):

                with self.assertRaises(ValueError) as caught:
                    replace(self.tower, **kwargs)

                message = str(caught.exception)

                self.assertTrue(
                    any(f"stage {n}" in message or f"riser {n}" in message
                        or f"cyclone {n}" in message
                        for n in range(1, 6)),
                    f"no stage named: {message}",
                )

    # ---------- the 2-D sibling of the collision test ----------
    def test_the_plan_layout_has_no_unintended_overlap(self):
        """Every pair of bodies, in plan, without a CAD kernel.

        The 3-D check on the built solids answers a different
        question -- whether what was BUILT matches the layout. This
        one answers whether the layout could be built at all, and it
        runs where cadquery does not.

        Two bodies at different elevations may of course overlap in
        plan; what may not is a pair that also shares a z band. So the
        pairs checked here are the ones that do: a stage's envelope
        against the ducts that run past it at its own height.
        """

        tower = self.tower
        r_meal = 0.5 * tower.meal_line_diameter
        r_riser = 0.5 * tower.riser_diameter

        for stage in range(1, tower.stage_count + 1):

            envelope = tower.stage_envelope(stage)

            # the riser that climbs past this cyclone to feed it
            with self.subTest(stage=stage, against=f"riser_{stage}"):
                self.assertGreater(
                    plan.polygon_point_distance(
                        envelope, tower.riser_axis(stage)
                    )
                    - r_riser,
                    0.0,
                )

            # the meal line that drops past it from the stage above
            if stage > 1:

                a, b = tower.meal_chute_plan(stage - 1)

                with self.subTest(stage=stage, against=f"meal_{stage - 1}"):
                    self.assertGreater(
                        plan.polygon_segment_distance(envelope, a, b)
                        - r_meal,
                        0.0,
                    )

            # the calciner reserved on the tower axis
            with self.subTest(stage=stage, against="calciner"):
                self.assertGreater(
                    plan.polygon_point_distance(envelope, (0.0, 0.0))
                    - tower.calciner.reserved_radius,
                    0.0,
                )


class DuctCrossingTest(unittest.TestCase):
    """No duct passes through another except where they join.

    THE TEST THAT WOULD HAVE CAUGHT IT. Four collisions of 1.657 m
    lived in this tower through every check it had:

      * the nine plan clearances did not see them, because a plan
        distance cannot tell a joint from a crossing when the two
        ducts are supposed to meet;
      * `test_nothing_overlaps_that_is_not_a_connection` did not see
        them, because its whitelist is keyed on a PAIR OF NAMES and
        skips the pair unmeasured. `(meal_line_1, riser_2)` is on that
        whitelist -- rightly, they join -- and the same entry excused
        the meal line running through riser 2's mouth leg nine metres
        higher up;
      * the fusion did not see them, because a duct that runs through
        the duct it joins still fuses into one solid.

    This one measures every pair of LEGS in space and decides what is
    a joint from the geometry, the way `geometry/space.is_junction` does: an
    END of one path landing on the LEG being excused. No names, no
    whitelist, nothing to keep in step with the process.

    No CAD kernel, so it runs in the twin's own environment.
    """

    def setUp(self):
        self.tower = TowerSpec()

    def test_no_two_ducts_come_closer_than_their_bores(self):

        ducts = [
            (name, path, 0.5 * bore)
            for name, _kind, path, bore in self.tower.connections()
        ]

        offenders = []

        for index, (name, path, radius) in enumerate(ducts):

            for other, other_path, other_radius in ducts[index + 1:]:

                for i, a, b in space.legs(path):
                    for j, c, d in space.legs(other_path):

                        gap = space.segment_segment_distance(a, b, c, d) - (
                            radius + other_radius
                        )

                        if gap >= 0.0:
                            continue

                        # PER LEG, and that is the whole test. Where
                        # the two really do join, ONE pair of legs is
                        # allowed to interfere -- the pair carrying the
                        # joint. Asking "do these two PATHS join" and
                        # excusing the pair on the answer is the bug
                        # this test exists to catch: the meal line does
                        # end on its riser, and that fact would excuse
                        # it for going through the same riser nine
                        # metres higher up.
                        if space.is_junction(path, i, other_path, j):
                            continue

                        offenders.append(
                            f"{name}[{i}] x {other}[{j}]: {gap:+.3f} m"
                        )

        self.assertEqual(
            offenders,
            [],
            "ducts interfere away from any joint:\n  "
            + "\n  ".join(offenders),
        )

    def test_a_meal_line_crosses_its_riser_exactly_once(self):
        """The defect, stated the way the user stated it.

        A dipleg meets the duct it feeds once. Twice means it went
        through it on the way.
        """

        tower = self.tower
        reach = 0.5 * (tower.meal_line_diameter + tower.riser_diameter)

        for stage in range(1, tower.stage_count):

            meal = tower.meal_line_path(stage)
            riser = tower.riser_path(stage + 1)

            touching = [
                (i, j)
                for i, a, b in space.legs(meal)
                for j, c, d in space.legs(riser)
                if space.segment_segment_distance(a, b, c, d) < reach
            ]

            with self.subTest(stage=stage, touching=touching):
                self.assertEqual(len(touching), 1)


class ConnectionTopologyTest(unittest.TestCase):
    """Every port is joined, and joined to the right thing."""

    def setUp(self):
        self.tower = TowerSpec()
        self.names = {name for name, _k, _p, _d in self.tower.connections()}

    def test_every_stage_is_fed_by_a_riser(self):
        for stage in range(1, self.tower.stage_count + 1):

            with self.subTest(stage=stage):
                self.assertIn(f"riser_{stage}", self.names)

    def test_the_tower_has_a_gas_exit_and_a_meal_inlet(self):
        self.assertIn("exit_stack", self.names)
        self.assertIn("raw_meal_inlet", self.names)

    def test_a_riser_starts_at_the_outlet_of_the_stage_below(self):
        tower = self.tower

        for stage in range(1, tower.stage_count):

            with self.subTest(riser=stage):
                self.assertEqual(
                    tower.riser_path(stage)[0], tower.outlet_point(stage + 1)
                )

    def test_every_riser_ends_at_the_mouth_it_feeds(self):
        for stage in range(1, self.tower.stage_count + 1):

            with self.subTest(riser=stage):
                self.assertEqual(
                    self.tower.riser_path(stage)[-1],
                    self.tower.mouth_point(stage),
                )

    def test_the_bottom_riser_comes_from_below_the_tower(self):
        """Stage 5 is fed by the calciner, not by another cyclone."""

        foot = self.tower.riser_path(self.tower.stage_count)[0]

        self.assertLess(foot[2], 0.0)

    def test_the_exit_stack_leaves_the_top_cyclone(self):
        self.assertEqual(self.tower.exit_stack_path()[0], self.tower.outlet_point(1))

    def test_the_raw_meal_enters_the_duct_feeding_the_top_cyclone(self):
        end = self.tower.meal_inlet_path()[1]
        z_low, z_high = self.tower.riser_vertical_span(1)

        self.assertGreaterEqual(end[2], z_low)
        self.assertLessEqual(end[2], z_high)


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class FiveIdenticalCyclonesTest(unittest.TestCase):
    """Faz 4: one shape, five placements."""

    @classmethod
    def setUpClass(cls):
        cls.tower = TowerSpec()
        cls.cyclones, cls.ducts, cls.base = build_preheater(
            cls.tower, sections=TEST_SECTIONS
        )

    def test_there_are_five_of_them(self):
        self.assertEqual(len(self.cyclones), self.tower.stage_count)

    def test_they_all_have_the_volume_of_the_one_that_was_built(self):
        """Translation cannot change a volume; a rebuild could."""

        for stage, cyclone in enumerate(self.cyclones, start=1):

            with self.subTest(stage=stage):
                self.assertAlmostEqual(
                    cyclone.Volume(), self.base.Volume(), places=9
                )

    def test_they_are_the_same_shape_to_machine_precision(self):
        volumes = [c.Volume() for c in self.cyclones]

        self.assertLess(max(volumes) - min(volumes), 1.0e-9)

    def test_each_stage_is_the_base_shape_moved(self):
        """Undo the placement and every stage is the one that was built.

        This replaces a bounding-box comparison, which stopped meaning
        anything the moment the stages were given their own azimuths:
        an axis-aligned box is not invariant under rotation, so five
        identical cyclones turned five different ways have five
        different boxes. Undoing the transform is strictly stronger --
        it catches a rebuild AND a wrong transform, which the box
        never could.
        """

        for placement, placed in zip(self.tower.placements(), self.cyclones):

            with self.subTest(stage=placement.stage):

                restored = placed.translate(
                    cq.Vector(-placement.x, -placement.y, -placement.z)
                ).rotate(
                    cq.Vector(0, 0, 0),
                    cq.Vector(0, 0, 1),
                    -placement.azimuth_deg,
                )

                here = restored.BoundingBox()
                there = self.base.BoundingBox()

                for axis in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"):
                    self.assertAlmostEqual(
                        getattr(here, axis), getattr(there, axis), places=9,
                    )

                self.assertAlmostEqual(
                    restored.Volume(), self.base.Volume(), places=9,
                )

    def test_they_sit_one_pitch_apart(self):
        zmins = sorted(c.BoundingBox().zmin for c in self.cyclones)

        for lower, upper in zip(zmins, zmins[1:]):

            with self.subTest(gap=upper - lower):
                self.assertAlmostEqual(
                    upper - lower, self.tower.pitch, delta=1.0e-6
                )

    def test_no_two_cyclones_touch_each_other(self):
        """They connect through ducts, never body to body."""

        for i, a in enumerate(self.cyclones):

            for j, b in enumerate(self.cyclones[i + 1:], start=i + 1):

                with self.subTest(stages=(i + 1, j + 1)):
                    self.assertAlmostEqual(
                        _intersection_volume(a, b), 0.0, delta=1.0e-9
                    )


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class TowerSolidTest(unittest.TestCase):
    """Faz 5: the ducts really join what they claim to join."""

    @classmethod
    def setUpClass(cls):
        cls.tower = TowerSpec()
        cls.cyclones, cls.ducts, cls.base = build_preheater(
            cls.tower, sections=TEST_SECTIONS
        )
        cls.solid = build_tower_solid(cls.tower, sections=TEST_SECTIONS)

    def test_every_duct_is_a_single_valid_solid(self):
        for name, duct in self.ducts.items():

            with self.subTest(duct=name):
                self.assertEqual(len(duct.Solids()), 1)
                self.assertTrue(duct.isValid())
                self.assertGreater(duct.Volume(), 0.0)

    def test_the_whole_tower_fuses_into_one_body(self):
        """The acceptance test for the entire layout.

        Two bodies would mean a duct missed what it was aiming at.
        """

        self.assertEqual(len(self.solid.Solids()), 1)
        self.assertTrue(self.solid.isValid())

    def test_the_tower_stands_where_the_layout_says(self):
        bb = self.solid.BoundingBox()

        self.assertAlmostEqual(
            bb.zmax, self.tower.tower_height, delta=1.0e-6
        )
        self.assertAlmostEqual(
            bb.zmin,
            -self.tower.gas_inlet_height_ratio * self.tower.D,
            delta=1.0e-6,
        )

    def test_each_riser_reaches_the_cyclone_it_feeds(self):
        for stage in range(1, self.tower.stage_count + 1):

            with self.subTest(riser=stage):
                self.assertGreater(
                    _intersection_volume(
                        self.ducts[f"riser_{stage}"], self.cyclones[stage - 1]
                    ),
                    0.0,
                )

    def test_each_riser_leaves_the_cyclone_below_it(self):
        """Joined, and the test does not care which kind of joint it is.

        It used to be a butt joint: the riser lifted `riser_rise_ratio`
        = 0.25 D straight off the outlet face before turning, and its
        bore (2.55 m) being narrower than the outlet's (2.78 m) meant
        they shared a plane and no volume.

        Shortening that lift to 0.03 D -- which is what stopped the gas
        elbow from sitting on the dipleg discharge above -- turned it
        into an overlap instead: the elbow's own radius now reaches back
        down inside the outlet duct. Both are correct connections, so
        what is asserted is the thing that actually matters, that fusing
        the two gives ONE body. A riser that had drifted off its outlet
        would come back as two.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(riser=stage):
                duct = self.ducts[f"riser_{stage}"]
                below = self.cyclones[stage]

                self.assertEqual(len(duct.fuse(below).Solids()), 1)

    def test_each_meal_line_leaves_its_own_cyclone(self):
        """A BUTT joint now, so the criterion is the fuse, not a volume.

        The meal line has the dipleg's own bore and, since the stages
        were offset, leaves it straight down -- so the two meet face to
        face and share no volume at all. They used to overlap only
        because the line turned sideways within 0.30 m and the elbow's
        sphere reached back up inside the dipleg. A dipleg continued as
        a pipe is the better joint; what has to be asserted about it is
        that fusing the two gives ONE body.
        """

        for stage in range(1, self.tower.stage_count):

            with self.subTest(meal_line=stage):
                duct = self.ducts[f"meal_line_{stage}"]
                cyclone = self.cyclones[stage - 1]

                self.assertEqual(len(duct.fuse(cyclone).Solids()), 1)

    def test_each_meal_line_reaches_the_riser_it_joins(self):
        for stage in range(1, self.tower.stage_count):

            with self.subTest(meal_line=stage):
                self.assertGreater(
                    _intersection_volume(
                        self.ducts[f"meal_line_{stage}"],
                        self.ducts[f"riser_{stage + 1}"],
                    ),
                    0.0,
                )

    def test_the_raw_meal_inlet_reaches_the_top_riser(self):
        self.assertGreater(
            _intersection_volume(
                self.ducts["raw_meal_inlet"], self.ducts["riser_1"]
            ),
            0.0,
        )

    def test_the_exit_stack_leaves_the_top_cyclone(self):
        """Also a butt joint, on stage 1's outlet face."""

        stack = self.ducts["exit_stack"]

        self.assertAlmostEqual(
            _intersection_volume(stack, self.cyclones[0]), 0.0, delta=1.0e-9
        )
        self.assertEqual(len(stack.fuse(self.cyclones[0]).Solids()), 1)

    def test_the_tower_holds_more_gas_than_its_five_cyclones(self):
        """The ducts are part of the gas path, not decoration."""

        cyclone_total = sum(c.Volume() for c in self.cyclones)

        self.assertGreater(self.solid.Volume(), cyclone_total)

    def test_the_tower_is_the_size_a_preheater_tower_is(self):
        self.assertGreater(self.tower.tower_height, 60.0)
        self.assertLess(self.tower.tower_height, 120.0)

    def test_nothing_overlaps_that_is_not_a_connection(self):
        """Every pair of bodies: either a connection, or no contact.

        THE TEST THAT WAS MISSING. Everything above asserts that the
        intended joints EXIST. Nothing asserted that the unintended
        ones do NOT, and a duct is perfectly free to pass straight
        through a vessel it has no business touching -- the fusion
        still comes back as one solid, and every other assertion here
        still passes.

        It found two families of real defect on the first run, eight
        overlaps totalling 14.8 m3:

          meal_line_N x cyclone_{N+1}   2.073 m3 each
              The dipleg discharges 1.39 m above the roof of the
              cyclone below it, and a single straight run to the riser
              column then goes through that cyclone's gas outlet.

          meal_line_N x riser_N         1.615 m3 each
              `riser_rise_ratio` and `stage_gap_ratio` were both 0.25,
              so a riser's vertical lift ended EXACTLY at the dipleg
              discharge of the cyclone above and its elbow sat on the
              meal outlet. Two defaults that happened to be the same
              number.

        Both are fixed by giving the meal line a lateral leg off the
        dipleg, which is what a real dipleg has anyway, and by letting
        the two ratios differ.
        """

        parts = dict(self.ducts)

        for index, cyclone in enumerate(self.cyclones, start=1):
            parts[f"cyclone_{index}"] = cyclone

        names = sorted(parts)
        offenders = []

        for i, first in enumerate(names):

            for second in names[i + 1:]:

                if _is_a_connection(first, second, self.tower.stage_count):
                    continue

                shared = _intersection_volume(parts[first], parts[second])

                if shared > 1.0e-6:
                    offenders.append((first, second, shared))

        self.assertEqual(
            offenders,
            [],
            "bodies overlap that are not joined:\n"
            + "\n".join(
                f"  {a} x {b}: {v:.3f} m3"
                for a, b, v in sorted(offenders, key=lambda r: -r[2])
            ),
        )


if __name__ == "__main__":
    unittest.main()
