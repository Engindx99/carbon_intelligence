"""The 2-D drawings, checked against the geometry they document.

The drawings exist to verify the layout, so the question these tests
ask is the one that makes them worth trusting: DOES EVERY NUMBER ON
THE PAPER STILL COME OUT OF THE PARAMETER MODEL?

Each sheet records what it quoted (`Sheet.quotes`): the source string,
the value the model returned and the length actually drawn. These tests
re-resolve every one of those sources against a FRESH spec and compare.
A dimension that was typed in rather than read would have no source to
resolve; a view that drifted from the model would fail the comparison.

No CAD kernel is needed. matplotlib is a twin dependency, so these run
wherever the twin runs.
"""

import inspect
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from geometry import drafting
from geometry.drafting import Sheet, value_of
from geometry.preheater import tower_draw
from geometry.preheater.cyclone_spec import CycloneSpec
from geometry.preheater.tower_spec import TowerSpec


# The eleven dimensions the cyclone was specified by. The section sheet
# has to carry all of them, or it is not a dimensioned drawing.
NAMED_CYCLONE_DIMENSIONS = (
    "total_height",
    "D_body",
    "cylinder_height",
    "cone_height",
    "cone_wall_inclination_deg",
    "vortex_finder_diameter",
    "vortex_finder_length",
    "dipleg_diameter",
    "dipleg_length",
    "inlet_width",
    "inlet_height",
)


class ValueOfTest(unittest.TestCase):
    """The one road a number may travel from the model to the paper."""

    def setUp(self):
        self.tower = TowerSpec()

    def test_a_property_resolves(self):

        self.assertAlmostEqual(
            value_of(self.tower, "pitch"), self.tower.pitch, places=12,
        )

    def test_a_nested_property_resolves(self):

        self.assertAlmostEqual(
            value_of(self.tower, "cyclone.D_body"),
            self.tower.cyclone.D_body,
            places=12,
        )

    def test_a_call_with_an_integer_resolves(self):

        self.assertAlmostEqual(
            value_of(self.tower, "stage_base_z(3)"),
            self.tower.stage_base_z(3),
            places=12,
        )

    def test_indices_resolve_including_negative_ones(self):

        self.assertAlmostEqual(
            value_of(self.tower, "meal_line_path(2)[-1][2]"),
            self.tower.meal_line_path(2)[-1][2],
            places=12,
        )

    def test_a_source_the_model_does_not_have_is_refused(self):

        with self.assertRaises(ValueError) as ctx:
            value_of(self.tower, "plan_width")

        self.assertIn("plan_width", str(ctx.exception))

    def test_something_that_is_not_a_source_is_refused(self):

        with self.assertRaises(ValueError):
            value_of(self.tower, "pitch * 2")


class QuoteAgreementTest(unittest.TestCase):
    """A quote that does not match what was drawn must not be printable."""

    def setUp(self):
        self.tower = TowerSpec()
        self.sheet = Sheet(
            model=self.tower,
            title="test",
            unit="test",
            number="TEST-00",
            source_note="test",
        )
        self.panel = self.sheet.panel((20.0, 20.0, 100.0, 100.0), "test")
        self.panel.fit((-30.0, 30.0), (0.0, 120.0))

    def tearDown(self):
        self.sheet.close()

    def test_a_dimension_that_matches_the_drawing_is_accepted(self):

        value = self.panel.dim_v(
            -10.0, self.tower.stage_base_z(2), self.tower.stage_base_z(1),
            "pitch",
        )

        self.assertAlmostEqual(value, self.tower.pitch, places=12)

    def test_a_dimension_drawn_to_the_wrong_length_raises(self):

        with self.assertRaises(ValueError) as ctx:
            self.panel.dim_v(-10.0, 0.0, self.tower.pitch + 0.5, "pitch")

        message = str(ctx.exception)
        self.assertIn("pitch", message)
        self.assertIn("diverged", message)

    def test_a_level_drawn_at_the_wrong_height_raises(self):

        with self.assertRaises(ValueError):
            self.panel.level(
                0.0, self.tower.stage_base_z(1) + 1.0, "stage_base_z(1)",
                x_text=-10.0,
            )

    def test_a_signed_coordinate_keeps_its_sign(self):
        """riser_approach_y is -5.563 m, and it is quoted as that."""

        value = self.panel.dim_h(
            0.0, self.tower.riser_approach_y, 10.0, "riser_approach_y",
            oriented=True,
        )

        self.assertLess(value, 0.0)

        with self.assertRaises(ValueError):
            self.panel.dim_h(
                0.0, -self.tower.riser_approach_y, 14.0,
                "riser_approach_y", oriented=True,
            )


class DrawingSetTest(unittest.TestCase):
    """The four sheets, built once."""

    @classmethod
    def setUpClass(cls):
        cls.tower = TowerSpec()
        cls.sheets = tower_draw.build_sheets(cls.tower)

    @classmethod
    def tearDownClass(cls):
        for sheet in cls.sheets:
            sheet.close()

    # ---------- the assertion the whole set rests on ----------
    def test_every_quote_re_resolves_against_a_fresh_model(self):
        """Nothing on any sheet is a number somebody typed in."""

        fresh_tower = TowerSpec()
        fresh_cyclone = CycloneSpec()

        for sheet in self.sheets:

            model = (
                fresh_cyclone
                if isinstance(sheet.model, CycloneSpec)
                else fresh_tower
            )

            for quote in sheet.quotes:

                with self.subTest(sheet=sheet.number, source=quote.source):

                    self.assertAlmostEqual(
                        value_of(model, quote.source),
                        quote.value,
                        places=9,
                    )

    def test_every_quote_matches_the_geometry_it_was_drawn_over(self):

        for sheet in self.sheets:
            for quote in sheet.quotes:

                with self.subTest(sheet=sheet.number, source=quote.source):

                    self.assertAlmostEqual(
                        quote.drawn, quote.value,
                        delta=drafting.AGREEMENT_TOLERANCE_M,
                    )

    def test_the_set_quotes_something_on_every_sheet(self):

        for sheet in self.sheets:
            with self.subTest(sheet=sheet.number):
                self.assertGreater(len(sheet.quotes), 0)

    def test_sheet_numbers_are_unique(self):

        numbers = [sheet.number for sheet in self.sheets]

        self.assertEqual(len(numbers), len(set(numbers)))

    def test_every_panel_is_at_a_standard_scale(self):

        for sheet in self.sheets:
            for panel in sheet.panels:

                with self.subTest(sheet=sheet.number, panel=panel.title):

                    self.assertIn(panel.scale, drafting.STANDARD_SCALES)

    # ---------- what the sheets have to carry ----------
    def test_the_section_carries_all_eleven_named_dimensions(self):

        section = self.sheets[0]
        quoted = {quote.source for quote in section.quotes}

        for name in NAMED_CYCLONE_DIMENSIONS:
            with self.subTest(dimension=name):
                self.assertIn(name, quoted)

    def test_the_elevation_marks_every_stage(self):

        elevation = self.sheets[1]
        quoted = {quote.source for quote in elevation.quotes}

        for stage in range(1, self.tower.stage_count + 1):
            with self.subTest(stage=stage):
                self.assertIn(f"stage_base_z({stage})", quoted)
                self.assertIn(f"mouth_point({stage})[2]", quoted)

    def test_the_plan_places_every_stage(self):
        """The mirror of the elevation's level marks.

        A plan sheet that was never re-laid-out would still render --
        its surviving quotes are z-quotes and quotes that draw to
        their own value -- so this is the assertion that notices.
        """

        quoted = {quote.source for quote in self.sheets[2].quotes}

        for stage in (2, 4):
            with self.subTest(stage=stage):
                self.assertIn(f"placement({stage}).x", quoted)
                self.assertIn(f"placement({stage}).y", quoted)

        self.assertIn("column_radius", quoted)
        self.assertIn("stage_azimuth_step_deg", quoted)

    def test_the_plan_shows_the_calciner_the_tower_stands_around(self):

        quoted = {quote.source for quote in self.sheets[2].quotes}

        self.assertIn("calciner.D_body", quoted)

    def test_no_sheet_quotes_a_local_length_as_a_world_one(self):
        """`mouth_x` and `riser_approach_y` are in the cyclone's frame.

        They are world coordinates for no stage now, so they may only
        be dimensioned on a panel that says it is a local view. The
        drawing would not have raised on its own: `dim_h` compares the
        quote against what was DRAWN, and a stale panel draws to the
        stale value quite happily.
        """

        for sheet in self.sheets:
            for quote in sheet.quotes:

                if quote.source not in ("mouth_x", "riser_approach_y"):
                    continue

                with self.subTest(sheet=sheet.number, source=quote.source):
                    self.assertIn("lokal", quote.panel)

    def test_the_elevation_carries_the_tower_height(self):

        quoted = {quote.source for quote in self.sheets[1].quotes}

        self.assertIn("tower_height", quoted)
        self.assertIn("pitch", quoted)
        self.assertIn("stage_gap", quoted)

    def test_the_angles_are_quoted_where_they_are_true(self):
        """A quantity may only be dimensioned where it is true.

        The chute's slope is true only in the developed view, because
        the chute turns in plan. `meal_side_azimuth_deg` is true only in the
        stage's own frame, because it is measured from the cyclone's
        own mouth. So each angle belongs to exactly one panel, and
        every panel carrying one has to say in its title which frame
        it is.
        """

        detail = self.sheets[3]

        angles = {q.source: q.panel for q in detail.quotes if q.kind == "angle"}

        self.assertEqual(
            set(angles),
            {"meal_entry_angle_deg(1)", "meal_side_azimuth_deg"},
        )

        self.assertIn("GERÇEK BOY", angles["meal_entry_angle_deg(1)"])
        self.assertIn("lokal", angles["meal_side_azimuth_deg"])

    def test_the_drawings_need_no_cad_kernel(self):
        """They run in the twin's environment, so they may not import one."""

        for module in (drafting, tower_draw):
            with self.subTest(module=module.__name__):
                self.assertNotIn(
                    "import cadquery", inspect.getsource(module),
                )

    def test_the_set_writes_its_files(self):

        with tempfile.TemporaryDirectory() as directory:

            sheets, paths = tower_draw.write_drawings(
                self.tower, output_dir=directory,
            )

            try:
                for path in paths:
                    with self.subTest(path=path.name):
                        self.assertTrue(Path(path).exists())
                        self.assertGreater(Path(path).stat().st_size, 0)

                self.assertEqual(len(paths), len(sheets) + 1)

            finally:
                for sheet in sheets:
                    sheet.close()


class DepthTest(unittest.TestCase):
    """Which side of a cyclone a duct passes on.

    A riser column stands `riser_reach` clear of its own cyclone, but an
    elevation only shows the part of that across the line of sight, and
    for at least one stage in any view that part is nearly nothing. Drawn
    flat the duct band lay over the body with the body's outline showing
    through it, and the sheet read as a duct routed THROUGH the vessel.

    These tests hold the two halves of the fix apart: that the drawing
    knows front from behind, and that the tower it is drawing has the
    clearance the drawing claims.
    """

    def setUp(self):
        self.tower = TowerSpec()

        self.horizontal = lambda placement: placement.x
        self.azimuths = lambda placement: (
            -placement.azimuth_deg, 180.0 - placement.azimuth_deg,
        )

        self.occluders = tower_draw.stage_occluders(
            self.tower, self.horizontal, self.azimuths, tower_draw.depth_xz,
        )

    def test_the_depth_of_a_view_grows_away_from_its_viewer(self):
        """A-A looks along +y, B-B along -x; nearer must be smaller."""

        self.assertLess(
            tower_draw.depth_xz((0.0, -5.0, 0.0)),
            tower_draw.depth_xz((0.0, +5.0, 0.0)),
        )
        self.assertLess(
            tower_draw.depth_yz((+5.0, 0.0, 0.0)),
            tower_draw.depth_yz((-5.0, 0.0, 0.0)),
        )

    def test_a_point_beside_a_cyclone_is_over_no_cyclone_at_all(self):

        placement = self.tower.placement(1)
        clear = (placement.x + 30.0, placement.y, placement.z + 8.0)

        self.assertEqual(
            tower_draw.visibility_of(
                clear, tower_draw.xz, tower_draw.depth_xz, self.occluders,
            ),
            "clear",
        )

    def test_the_same_point_moved_through_the_body_changes_sides(self):
        """The only difference between the two probes is the sign of y.

        Both project onto stage 1's body, so if the test could not tell
        them apart the drawing could not either -- which is exactly the
        state the sheet was in.
        """

        placement = self.tower.placement(1)
        z = placement.z + 0.5 * self.tower.cyclone.total_height

        for dy, expected in ((-8.0, "front"), (+8.0, "hidden")):
            with self.subTest(dy=dy):
                self.assertEqual(
                    tower_draw.visibility_of(
                        (placement.x, placement.y + dy, z),
                        tower_draw.xz, tower_draw.depth_xz, self.occluders,
                    ),
                    expected,
                )

    def test_every_duct_is_drawn_in_pieces_that_cover_it_exactly(self):
        """Splitting a duct may not lose any of it or move its ends."""

        for name, _kind, path, _bore in self.tower.connections():

            runs = tower_draw._visibility_runs(
                path, tower_draw.xz, tower_draw.depth_xz, self.occluders,
            )

            with self.subTest(duct=name):

                # Almost, not exactly: the pieces are rebuilt by
                # walking the densified path, so the last point is a
                # sum of steps rather than the original float. The
                # difference is 1e-15 m and the question being asked
                # is whether the pieces COVER the duct.
                def same(a, b):
                    for i in range(3):
                        self.assertAlmostEqual(a[i], b[i], places=9)

                same(runs[0][1][0], path[0])
                same(runs[-1][1][-1], path[-1])

                for before, after in zip(runs, runs[1:]):
                    same(before[1][-1], after[1][0])
                    self.assertNotEqual(before[0], after[0])

                drawn = sum(
                    math.dist(a, b)
                    for _where, run in runs
                    for a, b in zip(run, run[1:])
                )
                whole = sum(
                    math.dist(a, b) for a, b in zip(path, path[1:])
                )

                self.assertAlmostEqual(drawn, whole, places=9)

    def test_a_duct_is_seen_from_both_sides_across_the_tower(self):
        """Both branches are live, so neither is untested code.

        Which ducts pass in front and which behind is a property of
        where the stages face, not of the drawing; fixing the view
        along +y for this test is what makes the answer stable.
        """

        seen = set()

        for _name, _kind, path, _bore in self.tower.connections():
            seen.update(
                where
                for where, _run in tower_draw._visibility_runs(
                    path, tower_draw.xz, tower_draw.depth_xz, self.occluders,
                )
            )

        self.assertEqual(seen, {"clear", "front", "hidden"})

    def test_a_duct_that_enters_a_cyclone_is_not_counted_against_it(self):
        """`_joins` reads the joints off the geometry, not off a list.

        Every real joint in this tower is an END of a duct, so a riser
        joins the cyclone it leaves and the one it enters, and nothing
        else.
        """

        joined = {
            name: {
                stage
                for stage in range(1, self.tower.stage_count + 1)
                if tower_draw._joins(self.tower, path, stage)
            }
            for name, _kind, path, _bore in self.tower.connections()
        }

        for stage in range(1, self.tower.stage_count):
            with self.subTest(riser=stage):
                self.assertEqual(
                    joined[f"riser_{stage}"], {stage, stage + 1},
                )

        self.assertEqual(joined["riser_5"], {5})
        self.assertEqual(joined["exit_stack"], {1})
        self.assertEqual(joined["raw_meal_inlet"], set())

        for stage in range(1, self.tower.stage_count):
            with self.subTest(meal=stage):
                self.assertEqual(joined[f"meal_line_{stage}"], {stage})

    def test_the_zigzag_has_a_view_in_which_no_duct_crosses_a_cyclone(self):
        """THE DEFECT THAT WAS REPORTED, AS A NUMBER.

        A duct drawn over a cyclone it does not enter is what "the pipe
        goes through the cyclone" looks like on paper. This measures it
        directly, and on the committed layout it must be positive.
        """

        bearing, gap = tower_draw.best_elevation_bearing(self.tower)

        self.assertGreater(gap, 0.0)
        self.assertAlmostEqual(
            gap, tower_draw.elevation_clearance(self.tower, bearing),
            places=9,
        )

    def test_the_fan_has_no_such_view_from_any_direction(self):
        """Why the zigzag is the default, held as a measurement.

        If some view of the fan DID show its ducts clear, the reason
        given for the default would be wrong and this would fail.
        """

        fan = replace(TowerSpec(), layout_pattern="fan")

        _bearing, gap = tower_draw.best_elevation_bearing(fan)

        self.assertLess(gap, 0.0)

    def test_the_layouts_differ_only_in_plan(self):
        """Neither pattern may move a level, in either direction."""

        fan = replace(TowerSpec(), layout_pattern="fan")

        self.assertEqual(fan.tower_height, self.tower.tower_height)

        for stage in range(1, self.tower.stage_count + 1):
            with self.subTest(stage=stage):
                self.assertEqual(
                    fan.stage_base_z(stage), self.tower.stage_base_z(stage),
                )
                # and in both, the column stands its full reach off.
                placement = self.tower.placement(stage)
                axis = self.tower.riser_axis(stage)
                self.assertAlmostEqual(
                    math.hypot(axis[0] - placement.x, axis[1] - placement.y),
                    self.tower.riser_reach,
                    places=9,
                )

    def test_the_offset_is_dimensioned_where_it_is_true(self):
        """`riser_reach` may only be quoted in the stage's own frame.

        Two panels are entitled to it -- the local plan on PH-CAD-04 and
        the section on PH-CAD-02 whose cutting plane contains both axes
        -- and each says so in its title. No orthographic elevation may
        carry it, because in an elevation it is not that distance.
        """

        sheets = tower_draw.build_sheets(self.tower)

        try:
            panels = {
                quote.panel
                for sheet in sheets
                for quote in sheet.quotes
                if quote.source in (
                    "riser_reach", "riser_column_clearance()",
                )
            }

            self.assertTrue(panels)

            for panel in panels:
                with self.subTest(panel=panel):
                    self.assertTrue(
                        "lokal" in panel or "KESİT D-D" in panel,
                        f"{panel!r} quotes a distance that is only true in "
                        "the stage's own frame without saying it is one",
                    )

            self.assertIn(
                "KESİT D-D",
                " ".join(panels),
                "the elevation sheet must carry the section that shows "
                "the riser standing clear of its cyclone",
            )

        finally:
            for sheet in sheets:
                sheet.close()

    def test_the_section_plane_holds_both_axes(self):
        """What makes D-D able to show what no elevation can.

        The cut runs along the cyclone's own riser bearing, so the
        column lands at exactly `riser_reach` on the paper -- not at a
        projection of it.
        """

        bearing = self.tower.riser_bearing_rad
        unit = (math.cos(bearing), math.sin(bearing))
        offset = self.tower.riser_offset_local

        self.assertAlmostEqual(
            offset[0] * unit[0] + offset[1] * unit[1],
            self.tower.riser_reach,
            places=9,
        )


class ProjectionTest(unittest.TestCase):
    """The helpers that turn a 3-D centre-line into a view."""

    def setUp(self):
        self.tower = TowerSpec()

    def test_a_projection_keeps_the_points_it_was_given(self):

        path = self.tower.meal_line_path(1)

        self.assertEqual(
            tower_draw.xz(path), [(p[0], p[2]) for p in path],
        )
        self.assertEqual(
            tower_draw.yz(path), [(p[1], p[2]) for p in path],
        )
        self.assertEqual(
            tower_draw.xy(path), [(p[0], p[1]) for p in path],
        )

    def test_the_developed_view_is_the_only_one_that_shows_the_angle(self):
        """This is why the sheet has a third panel.

        The inclined chute falls at `meal_entry_angle_deg` to the
        horizontal in space -- DERIVED, since both its ends are fixed.
        The developed view reproduces that; no orthographic view does,
        because the chute also turns in plan.
        """

        path = self.tower.meal_line_path(1)
        points = tower_draw.developed(path)

        run = points[2][0] - points[1][0]
        drop = points[1][1] - points[2][1]

        self.assertAlmostEqual(
            math.degrees(math.atan2(drop, run)),
            self.tower.meal_entry_angle_deg(1),
            places=9,
        )

        # And each orthographic view really is steeper, because a run
        # that turns in plan projects SHORTER onto either axis while
        # the drop stays what it is. That is true of any chute that
        # turns, which is why it is asserted that way rather than
        # against a number this layout happens to give.
        for projection in (tower_draw.xz, tower_draw.yz):

            flat = projection(path)
            projected = abs(flat[2][0] - flat[1][0])

            with self.subTest(view=projection.__name__):

                self.assertLess(projected, run)
                self.assertGreater(
                    math.degrees(math.atan2(drop, projected)),
                    self.tower.meal_entry_angle_deg(1),
                )

    def test_the_developed_view_keeps_every_elevation(self):

        path = self.tower.meal_line_path(2)
        points = tower_draw.developed(path)

        for point, drawn in zip(path, points):
            self.assertAlmostEqual(point[2], drawn[1], places=12)

    def test_the_developed_run_is_the_plan_distance(self):

        path = self.tower.meal_line_path(3)
        points = tower_draw.developed(path)

        expected = sum(
            math.hypot(b[0] - a[0], b[1] - a[1])
            for a, b in zip(path, path[1:])
        )

        self.assertAlmostEqual(points[-1][0], expected, places=12)


class CycloneShapeTest(unittest.TestCase):
    """The outline the dimensions are hung on has to be the cyclone."""

    def setUp(self):
        self.cyc = CycloneSpec()

    def test_the_outline_spans_the_body_diameter(self):

        outline = tower_draw.cyclone_outline(self.cyc)
        radii = [r for r, _ in outline]

        self.assertAlmostEqual(
            max(radii) - min(radii), self.cyc.D_body, places=12,
        )

    def test_the_outline_spans_the_total_height(self):

        outline = tower_draw.cyclone_outline(self.cyc)
        heights = [z for _, z in outline]

        self.assertAlmostEqual(
            max(heights) - min(heights), self.cyc.total_height, places=12,
        )

    def test_the_outline_starts_at_the_dipleg_discharge(self):

        outline = tower_draw.cyclone_outline(self.cyc)

        self.assertAlmostEqual(min(z for _, z in outline), 0.0, places=12)

    def test_the_scroll_band_is_drawn_to_the_specs_own_envelope(self):
        """The drawing owns no curve of its own.

        `plan_envelope_radius` moved to CycloneSpec when the tower
        layout needed the same law; it is tested there. What belongs
        here is only that the scroll band READS it.
        """

        for azimuth in (0.0, 90.0, 180.0, 300.0):

            with self.subTest(azimuth=azimuth):

                band = tower_draw.volute_band(self.cyc, azimuth)
                outer = max(r for r, _ in band)

                self.assertAlmostEqual(
                    outer,
                    self.cyc.plan_envelope_radius(azimuth),
                    places=12,
                )

    def test_the_roof_is_the_top_less_the_protrusion(self):

        self.assertAlmostEqual(
            tower_draw.roof_z(self.cyc),
            self.cyc.total_height - self.cyc.vortex_finder_protrusion,
            places=12,
        )


if __name__ == "__main__":
    unittest.main()
