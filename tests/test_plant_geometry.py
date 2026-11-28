"""geometry/plant_geometry.{yaml,py}: the plant's one geometry source.

Step 1 of the single-source plan: the source holds today's primary
dimensions and the module derives today's documented volumes, areas
and heights from them. Until the macros' Const blocks are generated
from the source (step 4), the macros are held to it here.
"""

import math
import re
import unittest
import yaml

from geometry import plant_geometry as pg
from tests.test_plant_topology_cfd_lock import MACROS, _cases, _consts
from tests.twin_harness import REPO_ROOT

TOL = 1e-3


class TheSourceTest(unittest.TestCase):
    def test_every_entry_says_where_it_comes_from(self):
        g = pg.load()
        n = 0
        for key, entry in pg.entries(g):
            n += 1
            with self.subTest(key=key):
                self.assertIn(entry.get("source"), pg.SOURCES)
                self.assertIn("unit", entry)
                self.assertTrue((REPO_ROOT / "geometry" / entry["doc"]).is_file(), entry["doc"])
        self.assertGreater(n, 50)


class TheDerivedValuesAreTodaysTest(unittest.TestCase):
    """The documented figures (equipment docs, Derived Properties)."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()

    def near(self, got, want, tol):
        self.assertAlmostEqual(got, want, delta=tol)

    def test_cyclones(self):
        for name, vol, area, h in (
            ("C1", 124.54, 140.56, 11.44),
            ("C2", 283.2, 235.17, 13.60),
            ("C3", 283.2, 235.17, 13.60),
            ("C4", 283.2, 235.17, 13.60),
            ("C5", 311.0, 250.34, 14.03),
        ):
            c = pg.cyclone(self.g, name)
            with self.subTest(cyclone=name):
                self.near(c["volume"], vol, 0.1)
                self.near(c["wet_area"], area, 0.05)
                self.near(c["height"], h, 0.005)

    def test_c5_is_c4_scaled(self):
        c4, c5 = pg.cyclone(self.g, "C4"), pg.cyclone(self.g, "C5")
        self.assertAlmostEqual(c5["scale"], 6.5 / 6.3, places=12)
        for key in pg.CYCLONE_DIMS:
            self.assertAlmostEqual(c5[key], c4[key] * 6.5 / 6.3, places=12)

    def test_calciner(self):
        c = pg.calciner(self.g)
        self.near(c["D_throat"], 3.130, 0.001)
        self.near(c["h_cone"], 3.871, 0.001)
        self.near(c["vessel_volume"], 1009.711, 0.001)
        self.near(c["v_throat"], 24.085, 0.001)

    def test_calciner_boundaries(self):
        """The CFD's inlets: the doc's densities, mass fractions that sum
        to one, and the duct its own flow sizes."""
        b = pg.calciner_boundaries(self.g)
        kiln, ta = b["kiln_gas_inlet"], b["tertiary_air_inlet"]
        self.near(kiln["rho"], 0.2753, 1e-4)
        self.near(ta["rho"], 0.3276, 1e-4)
        for s in (kiln, ta):
            self.near(sum(s["y"].values()), 1.0, 1e-12)
        self.near(ta["D_sized"], ta["D_h"], 2e-4)

    def test_gooseneck(self):
        gn = pg.gooseneck(self.g)
        self.near(gn["D_neck"], 4.950, 0.001)
        self.near(gn["piece"], 4.950, 0.001)
        self.near(gn["level"], 2.475, 0.001)        # 0.5 D since 24 Nov 2026 (the tower by the calciner)
        self.near(gn["y_off"], 9.660, 0.001)
        self.near(gn["crown"], 39.105, 0.001)
        self.near(gn["channel"], 4.207, 0.001)       # 0.85 D since 24 Nov 2026 (C5 3.25 m higher)
        self.near(gn["z_split"], 28.923, 0.001)
        self.near(gn["z_end"], 26.772, 0.001)
        self.near(gn["arm_piece"], 4.301, 0.001)
        self.near(gn["x_bend"], 3.725, 0.001)
        self.near(gn["x_leg"], 5.475, 0.001)         # arm run 0.5 D_leg since 24 Nov 2026
        self.near(gn["volume"], 420.12, 0.01)
        self.near(gn["wall_area"], 390.91, 0.01)

    def test_the_gooseneck_pieces(self):
        """User decision, 15 Nov 2026: three straight pieces (45 deg up,
        level, 45 deg down) over the roof's middle, mitred, the neck
        coming down in front of the vessel and dividing into two arms.
        Checked by hand: the two inclined pieces rise and fall by the
        same, so the neck's lower end is as high as the roof; its forward
        run is the pieces' and the level one's."""
        gn = pg.gooseneck(self.g)
        cal = pg.calciner(self.g)
        c = math.sqrt(0.5)
        self.near(gn["y_off"], gn["root_forward"] + 2.0 * gn["piece"] * c + gn["level"], 1e-9)
        self.near(gn["z_n3"], cal["z_roof"], 1e-9)
        self.near(gn["z_split"], gn["z_n3"] - gn["channel"], 1e-9)
        self.near(gn["crown"], cal["z_roof"] + gn["piece"] * c + 0.5 * gn["D_neck"], 1e-9)
        # the arms: arm_angle out of the vertical down to the level runs' axis, then a level run
        la = gn["arm_piece"]
        self.near(gn["fall"], gn["z_split"] - gn["z_end"], 1e-9)
        g_arm = math.radians(gn["arm_angle"])
        self.near(gn["x_bend"], la * math.sin(g_arm), 1e-9)
        self.near(gn["fall"], la * math.cos(g_arm), 1e-9)
        self.near(gn["x_leg"], gn["x_bend"] + gn["arm_run"], 1e-9)
        self.assertGreater(gn["fall"], 0.0)
        # the runs' axis is C5's inlet axis (the layout puts C5 there)
        lay = pg.layout(self.g)
        self.near(lay["z_c5_inlet"], lay["z_gooseneck_cfd_end"], 1e-9)
        # the two runs clear of one another, the plane of the arms clear of the vessel
        self.assertGreater(gn["x_leg"], 0.5 * gn["D_leg"])
        self.assertGreater(gn["y_off"] - 0.5 * gn["D_leg"] - cal["R"], 1.0)
        # the first piece pierces the roof in front of the axis by what keeps its cap inside the vessel
        # (an inclined pipe cuts the roof in an ellipse longer than the vessel is wide)
        beta, r_n = math.radians(gn["slope"]), 0.5 * gn["D_neck"]
        phi = [2.0 * math.pi * k / 3600 for k in range(3600)]
        reach = max(math.hypot(r_n * math.sin(f),
                               -gn["root_forward"] + gn["setback"] * math.cos(beta) + r_n * math.cos(f) * math.sin(beta))
                    for f in phi)
        self.assertLessEqual(reach, cal["R"] - 0.049)
        self.assertGreater(reach, cal["R"] - 0.051)
        # a mitre between equal pipes adds the axis lengths: the neck is the first piece's cap setback,
        # the two inclined pieces, the level one and the vertical channel
        self.near(gn["neck_length"], gn["setback"] + 2.0 * gn["piece"] + gn["level"] + gn["channel"], 1e-9)

    def test_the_shared_volumes_do_not_depend_on_the_grid(self):
        gn = pg.gooseneck(self.g)
        cal = pg.calciner(self.g)
        r_n, r_l = 0.5 * gn["D_neck"], 0.5 * gn["D_leg"]
        beta, gamma = math.radians(gn["slope"]), math.radians(gn["arm_angle"])
        coarse = pg._gn_shared(r_n, r_l, cal["R"], cal["z_roof"], gn["setback"], gn["root_forward"], beta,
                               gn["piece"], gn["nodes"][4][0], gn["nodes"][4][1],
                               gn["channel"], gamma, gn["arm_piece"], nn=200)
        for got, want, what in zip(coarse, (gn["inside_vessel"], gn["overlap_neck_arm"], gn["overlap_arms"],
                                            gn["overlap_all"]),
                                   ("first piece inside the vessel", "neck x arm", "arm x arm", "all three")):
            with self.subTest(what):
                self.assertAlmostEqual(got, want, delta=max(0.12, 1.5e-2 * want))

    def test_kiln_and_cooler(self):
        k, c = pg.kiln(self.g), pg.cooler(self.g)
        self.near(k["volume"], 1085.73, 0.01)
        self.near(k["wall_area"], 904.78, 0.01)
        self.near(k["burning_L"], 35.0, 1e-9)
        self.near(c["length"], 29.9, 1e-9)
        self.near(c["box_volume"], 358.80, 1e-9)


class TheMacrosAgreeWithTheSourceTest(unittest.TestCase):
    """The CFD macros' values, read back through their generated
    blocks (tools/gen_geometry.py), are the source's."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cyc = (MACROS / "cyclone.bas").read_text(encoding="latin-1")
        cal = (MACROS / "calciner.bas").read_text(encoding="latin-1")
        cls.cc = _consts(cyc)
        cls.case = _cases(cyc, cls.cc)
        cls.cal = _consts(cal)

    def test_cyclone_cases(self):
        names = {
            "D_barrel": "D_BARREL", "H_barrel": "H_BARREL", "H_cone": "H_CONE",
            "L_vortex": "L_VORTEX", "D_vortex": "D_VORTEX", "D_dust": "D_DUST",
            "W_inlet": "W_INLET", "H_inlet": "H_INLET", "inlet_slope": "INLET_SLOPE_DEG",
            "outlet_turn": "OUTLET_TURN_DEG", "outlet_rise_over_Dx": "OUTLET_EXT_OVER_VORTEX_D",
            "outlet_bend_R_over_Dx": "ELBOW_R_OVER_VORTEX_D",
            "outlet_run_over_Dx": "OUTLET_DOWN_OVER_VORTEX_D", "boi_radius": "BOI_RADIUS",
        }
        for name in ("C1", "C4", "C5"):
            c = pg.cyclone(self.g, name)
            for key, macro in names.items():
                with self.subTest(cyclone=name, key=key):
                    self.assertAlmostEqual(c[key], self.case[name][macro], delta=TOL)

    def test_cyclone_domain(self):
        d = self.g["cyclone_domain"]
        for key, macro in (
            ("vortex_wall", "VORTEX_WALL"), ("inlet_duct_length", "L_INLET"),
            ("inlet_roof_clearance", "INLET_ROOF_CLEARANCE"),
            ("inlet_tangent_relief", "INLET_TANGENT_RELIEF"), ("volute_tongue", "INLET_TONGUE"),
            ("volute_overlap", "VOLUTE_OVERLAP"), ("c1_riser_area_share", "RISER_AREA_SHARE"),
            ("c1_riser_transition", "RISER_TRANS_LEN"),
            ("c1_riser_bend_R_over_D", "RISER_BEND_R_OVER_D"),
            ("c1_riser_above_feed", "RISER_ABOVE_FEED"), ("c1_riser_below_feed", "RISER_BELOW_FEED"),
            ("c1_feed_width", "FEED_W"), ("c1_feed_height", "FEED_H"),
            ("c1_feed_depth", "FEED_DEPTH"), ("meal_slope", "FEED_SLOPE_DEG"),
        ):
            with self.subTest(key=key):
                self.assertAlmostEqual(pg.v(d[key]), self.cc[macro], delta=TOL)
        self.assertAlmostEqual(pg.r1_D(self.g), self.cc["D_RISER_SRC"], delta=TOL)

    def test_calciner_consts(self):
        c, gn = self.g["calciner"], self.g["gooseneck"]
        gn_d = pg.gooseneck(self.g)
        for value, macro in (
            (pg.v(c["D"]), "D_VESSEL"), (pg.v(c["H"]), "H_VESSEL"), (pg.v(c["cone_angle"]), "CONE_DEG"),
            (pg.v(c["throat_gas_flow"]), "M_KILN_GAS"), (pg.v(c["throat_gas_T"]), "T_KILN_GAS"),
            (pg.v(c["throat_gas_x_N2"]), "X_N2"), (pg.v(c["throat_gas_x_O2"]), "X_O2"),
            (pg.v(c["throat_gas_x_H2O"]), "X_H2O"), (pg.v(c["throat_gas_x_CO2"]), "X_CO2"),
            (pg.v(c["throat_velocity"]), "U_THROAT"), (pg.v(c["throat_length_over_D"]), "THROAT_LEN_OVER_D"),
            (pg.v(c["D_feed"]), "D_FEED"), (pg.v(c["feed_above_tertiary_air"]), "FEED_ABOVE_TA"),
            (pg.v(c["D_tertiary_air"]), "D_TA"), (pg.v(c["D_fuel"]), "D_FUEL"), (pg.v(c["fuel_slope"]), "FUEL_SLOPE_DEG"),
            (pg.v(c["tertiary_air_cone_clearance"]), "TA_CONE_CLEARANCE"),
            (pg.v(c["tertiary_air_wall_relief"]), "TA_WALL_RELIEF"), (pg.v(c["tertiary_air_stub_length"]), "TA_STUB_LEN"),
            (pg.v(c["feed_depth"]), "FEED_DEPTH"), (pg.v(gn["D_leg"]), "D_GOOSENECK_SRC"),
            (gn_d["end_over_H"], "GN_OUTLET_AT_VESSEL_H"),
            (pg.v(gn["neck_slope"]), "GN_SLOPE_DEG"), (pg.v(gn["neck_piece_over_D_neck"]), "GN_PIECE_OVER_D"),
            (pg.v(gn["neck_level_over_D_neck"]), "GN_LEVEL_OVER_D"), (pg.v(gn["arm_angle"]), "GN_ARM_DEG"),
            (pg.v(gn["arm_run_over_D_leg"]), "GN_ARM_RUN_OVER_D"),
            (pg.v(self.g["cyclone_domain"]["meal_slope"]), "FEED_SLOPE_DEG"),
        ):
            with self.subTest(macro=macro):
                self.assertAlmostEqual(value, self.cal[macro], delta=TOL)


if __name__ == "__main__":
    unittest.main()


class TheLayoutIsTheDrawingsTest(unittest.TestCase):
    """Step 2: the drawing's layout and C1 branch, derived here."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.drw = _consts((MACROS / "plant_topology_2d.bas").read_text(encoding="latin-1"))

    def test_c1_branch_is_the_cfd_domains(self):
        br = pg.c1_branch(self.g)
        for key, macro in (("x", "C1_RISER_X"), ("z_bend", "C1_BEND_Z"), ("z_feed", "C1_FEED_Z"),
                           ("z_floor", "C1_RISER_Z0"), ("bend_R", "C1_BEND_R"), ("bend_deg", "C1_BEND_DEG")):
            with self.subTest(key=key):
                self.assertAlmostEqual(br[key], self.drw[macro], delta=TOL)

    def test_the_twin_c1_is_the_drawings(self):
        tw = pg.c1_twin(self.g)
        for key, macro in (("branch_half", "R1_BRANCH_HALF"), ("spacing", "C1_TWIN_S"), ("y_duct", "C1_DUCT_Y")):
            with self.subTest(key=key):
                self.assertAlmostEqual(tw[key], self.drw[macro], delta=TOL)

    def test_layout_constants_are_the_drawings(self):
        L = self.g["layout"]
        for key, macro in (
            ("kiln_axis_z", "KILN_AXIS_Z"), ("chamber_margin", "CHAMBER_MARGIN"),
            ("c5_over_tertiary_air", "C5_OVER_TA"), ("gooseneck_to_c5_gap", "GN_TO_C5_GAP"),
            ("stage_gap", "STAGE_GAP"),
            ("dust_over_roof", "DUST_OVER_ROOF"), ("c1_twin_gap", "C1_TWIN_GAP"),
            ("r1_up_min", "R1_UP_MIN"), ("cooler_drop", "COOLER_DROP"),
        ):
            with self.subTest(key=key):
                self.assertAlmostEqual(pg.v(L[key]), self.drw[macro], delta=TOL)

    @unittest.skipUnless(
        (REPO_ROOT / "geometry" / "output" / "2500" / "plant_topology_2d_build.log").is_file(),
        "no SolidWorks build log here",
    )
    def test_elevations_are_the_last_drawn(self):
        """The drawing takes its Consts from the generated block, so its
        layout is this module's to the log's 1 um."""
        log = (REPO_ROOT / "geometry" / "output" / "2500" / "plant_topology_2d_build.log").read_text(
            encoding="latin-1")
        n = r"(-?\d+(?:,\d+)?)"

        def nums(pattern):
            m = re.search(pattern.replace("#", n), log)
            self.assertIsNotNone(m, pattern)
            return [float(x.replace(",", ".")) for x in m.groups()]

        L = pg.layout(self.g)
        z = nums(r"dust outlets C5 / C4 / C3 / C2 / C1 at z # / # / # / # / #")
        checks = [(L["z_dust"][s], want, f"C{s} dust outlet") for s, want in zip((5, 4, 3, 2, 1), z)]
        inner, outer = nums(r"inner column x \+-# .*?outer x \+-#")
        c1a, c1b = nums(r"twin C1 at x \+-# and \+-#")
        kx0, kz0, kx1, kz1 = nums(r"kiln: \(#, #\) -> \(#, #\)")
        cx0, cx1, cz0, cz1 = nums(r"cooler x # \.\. #, z # \.\. #")
        gn = pg.gooseneck(self.g)
        zs, xb, xl, zi = nums(r"channel down to z #, arms turn level at x \+-#, outlet faces at x \+-#, C5 inlet at z #")
        checks += [
            (L["z_calciner_throat"] + gn["z_split"], zs, "the Y's node z"),
            (gn["x_bend"], xb, "arms turn level, x"),
            (L["x_gooseneck_leg"], xl, "arms' outlet faces, x"),
            (L["z_c5_inlet"], zi, "C5 inlet z"),
            (L["z_tower"], nums(r"tower top #")[0], "tower top"),
            (L["x_inner"], inner, "inner column"),
            (L["x_outer"], outer, "outer column"),
            (L["x_c1"][0], c1a, "near C1"),
            (L["x_c1"][1], c1b, "far C1"),
            (L["a_chamber"], kx0, "kiln inlet x"),
            (L["kiln_end"][0], kx1, "kiln end x"),
            (L["kiln_end"][1], kz1, "kiln end z"),
            (L["cooler_x"][1], cx1, "cooler end"),
            (L["cooler_z"][0], cz0, "cooler floor"),
            (L["cooler_z"][1], cz1, "cooler roof"),
        ]
        for got, want, what in checks:
            with self.subTest(what):
                self.assertAlmostEqual(got, want, delta=2e-6)


class DispersionBoxGeometryTest(unittest.TestCase):
    """plant_geometry.dispersion_box: the wedge and its pipe on a vessel wall,
    the closed-form volume outside the vessel against numerical integration,
    clearances, and one design per pipe bore."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.cal = pg.calciner(cls.g)
        cls.meal = pg.calciner_inlets(cls.g)["meal"]
        cls.b = cls.g["dispersion_box"]

    def test_the_wedge_and_its_pipe(self):
        m, R, D = self.meal, self.cal["R"], self.meal["D"]
        self.assertAlmostEqual(m["width"], pg.v(self.b["width_over_D_feed"]) * D, places=12)
        self.assertAlmostEqual(m["rho_out"], R + 1.25 * D, places=12)
        self.assertAlmostEqual(math.hypot(m["rho_in"], 0.5 * m["width"]), R, places=12)   # the open face's corners on the cylinder
        # the floor is level to the tangent plane, then the ramp rises at its slope to the back face's foot
        run = m["rho_out"] - R
        self.assertAlmostEqual(m["rho_flat"], R, places=12)
        self.assertAlmostEqual((m["z_back_foot"] - m["z_bottom"]) / run, math.tan(math.radians(60.0)), places=12)
        self.assertAlmostEqual(m["z_top"] - m["z_bottom"], m["back_h"] + run * math.tan(math.radians(60.0)), places=12)
        self.assertAlmostEqual(m["rho_pipe"], m["rho_out"] - 0.5 * 1.25 * D, places=12)   # on the top face, in its outer half
        self.assertGreater(m["rho_pipe"] - 0.5 * D, R)                                    # the pipe stands outside the vessel
        self.assertAlmostEqual(m["z_pipe_top"] - m["z_top"], pg.v(self.b["pipe_rise"]), places=12)
        self.assertEqual(m["end"], (m["rho_pipe"], m["z_pipe_top"]))

    def test_it_clears_the_tertiary_air_duct_and_stands_over_the_cone(self):
        m = self.meal
        self.assertGreater(m["z_bottom"], pg.calciner_inlets(self.g)["tertiary_air"]["top"])
        self.assertGreater(m["z_bottom"], self.cal["z_cone_top"])
        self.assertLess(m["z_pipe_top"], self.cal["z_roof"])

    def test_the_volume_outside_the_vessel_is_the_integral(self):
        m, R = self.meal, self.cal["R"]
        h, n = 0.5 * m["width"], 200000
        dy = 2.0 * h / n
        tan = math.tan(math.radians(60.0))
        vol = 0.0
        for k in range(n):
            y = -h + (k + 0.5) * dy
            cyl = math.sqrt(R * R - y * y)
            L = m["rho_out"] - R
            vol += (m["height"] * (R - cyl) + m["back_h"] * L + 0.5 * tan * L * L) * dy
        self.assertAlmostEqual(m["box_volume"], vol, delta=1e-6)
        self.assertAlmostEqual(m["volume"], m["box_volume"] + m["pipe_volume"], places=12)

    def test_it_is_one_design_per_inlet_bore(self):
        R, z, D = self.cal["R"], 3.0, self.meal["D"]
        self.assertEqual(pg.dispersion_box(self.g, R, D, z), pg.dispersion_box(self.g, R, D, z))

    def test_a_box_that_does_not_fit_is_refused(self):
        with self.assertRaises(ValueError):
            pg.dispersion_box(self.g, 0.8, self.meal["D"], 0.0)


CALCINER_LOG = REPO_ROOT / "geometry" / "output" / "2500" / "calciner_build.log"


@unittest.skipUnless(CALCINER_LOG.is_file(), "no SolidWorks calciner build log here")
class TheCalcinerSolidIsTheSourcesTest(unittest.TestCase):
    """The last calciner.bas build (geometry/output/2500/
    calciner_build.log, written by the macro) against
    plant_geometry.calciner / gooseneck: the same formulas in VBA and
    Python, the same values from the one source."""

    NUM = r"(-?\d+(?:[.,]\d*)?)"

    @classmethod
    def setUpClass(cls):
        cls.log = CALCINER_LOG.read_text(encoding="latin-1")
        cls.g = pg.load()

    def num(self, pattern):
        m = re.search(pattern.replace("#", self.NUM), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        first = self.log.splitlines()[0]
        self.assertTrue(first.startswith("calciner built"), first)
        self.assertNotIn("ABORTED", first)

    def test_the_dimensions_and_elevations(self):
        cal, gn = pg.calciner(self.g), pg.gooseneck(self.g)
        ins = pg.calciner_inlets(self.g)
        ta, meal, fuel = ins["tertiary_air"], ins["meal"], ins["fuel"]
        x_ta, z_ta, y_ta, v_ta = self.num(r"tertiary air: duct D # m, tangential, axis at x = # m, z = # m, "
                                          r"face at y = # m, # m3")[1:]
        for got, want, what in (
            (self.num(r"throat D # m")[0], cal["D_throat"], "throat D"),
            (self.num(r"cone # deg, # m tall")[1], cal["h_cone"], "cone height"),
            (self.num(r"cylinder D # m, z # \.\. # m")[2], cal["z_roof"], "roof"),
            (self.num(r"gooseneck neck: D # m, 3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[0],
             gn["D_neck"], "neck D"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[0],
             gn["slope"], "neck slope"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[1],
             gn["piece"], "neck piece"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[2],
             gn["level"], "neck level piece"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[4],
             gn["setback"], "cap setback"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[5],
             gn["inside_vessel"], "first piece inside the vessel"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[6],
             gn["crown"], "crown"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[7],
             gn["y_off"], "neck's lower end y"),
            (self.num(r"3 straight pieces at # deg: # m, level # m, # m; first piece's cap # m behind the roof point \(# m3 inside the vessel\); crown z = # m; lower end at y = -# m, z = # m")[8],
             gn["z_split"], "neck's lower end z"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[0], gn["arm_angle"], "arm angle"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[1], gn["arm_piece"], "arm piece"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[2], gn["arm_run"], "arm level run"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[3], gn["x_bend"], "arm turns level, x"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[4], gn["x_leg"], "outlet faces x"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[5], gn["z_end"], "level runs z"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[6], gn["overlap_neck_arm"], "channel x arm"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[7], gn["overlap_arms"], "arm x arm"),
            (self.num(r"leaving the channel's lower end at # deg, piece # m, level runs # m from x = \+-# m to the outlet faces at x = \+-# m, z = # m \(channel x arm # m3, arms # m3, all # m3 shared\)")[8], gn["overlap_all"], "all three"),
            (self.num(r"gooseneck channel: vertical, D # m, # m long, from z = # m to z = # m")[1], gn["channel"], "channel length"),
            (self.num(r"gooseneck channel: vertical, D # m, # m long, from z = # m to z = # m")[2], gn["z_n3"], "channel top z"),
            (self.num(r"gooseneck channel: vertical, D # m, # m long, from z = # m to z = # m")[3], gn["z_split"], "channel bottom z"),
            (x_ta, ta["x"], "tertiary air x"),
            (z_ta, ta["z"], "tertiary air z"),
            (y_ta, ta["y_end"], "tertiary air face y"),
            (v_ta, ta["volume"], "tertiary air volume"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[0], meal["width"], "box width"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[1], meal["rho_out"], "box back rho"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[2], meal["back_h"], "box back height"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[4], meal["rho_in"], "box rho in"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[5], meal["height"], "box height"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[6], meal["z_bottom"], "box bottom z"),
            (self.num(r"meal feed: 2 dispersion boxes, wedge, width # m, back face rho # m # m high, floor # deg down to the window in the tangent plane \(flat lead-in from rho # m\), # m high, z # \.\. # m")[7], meal["z_top"], "box top z"),
            (self.num(r"meal feed: .*?top face centred \(\+-#, 0, #\), # m3")[0], meal["end"][0], "meal end x"),
            (self.num(r"meal feed: .*?top face centred \(\+-#, 0, #\), # m3")[1], meal["end"][1], "meal end z"),
            (self.num(r"meal feed: .*?top face centred \(\+-#, 0, #\), # m3")[2], meal["volume"], "meal volume"),
            (self.num(r"fuel: .*?end faces centred \(0, \+-#, #\), # m3")[0], fuel["end"][0], "fuel end y"),
            (self.num(r"fuel: .*?end faces centred \(0, \+-#, #\), # m3")[1], fuel["end"][1], "fuel end z"),
            (self.num(r"fuel: .*?end faces centred \(0, \+-#, #\), # m3")[2], fuel["volume"], "fuel volume"),
            (self.num(r"vessel volume \(cone \+ cylinder\)\s+# m3")[0], cal["vessel_volume"], "vessel"),
        ):
            with self.subTest(what):
                self.assertAlmostEqual(got, want, delta=1e-5 * max(1.0, abs(want)))

    def test_the_measured_stages(self):
        """Each build step's volume as SolidWorks measured it, to the
        macro's own VOL_TOL (0.1 %), against the closed forms here; the
        small pieces' ADDED volumes to its 1 %."""
        cal, gn = pg.calciner(self.g), pg.gooseneck(self.g)
        ins = pg.calciner_inlets(self.g)
        rl = 0.5 * gn["D_leg"]
        v_neck = math.pi * (0.5 * gn["D_neck"]) ** 2 * gn["neck_length"] - gn["inside_vessel"]
        v_arm = math.pi * rl * rl * gn["arm_length"]
        steps = {"1 ": cal["v_throat"] + cal["vessel_volume"]}
        steps["2 "] = steps["1 "] + v_neck
        steps["3a"] = steps["2 "] + v_arm - gn["overlap_neck_arm"]
        steps["3b"] = steps["3a"] + v_arm - gn["overlap_neck_arm"] - gn["overlap_arms"] + gn["overlap_all"]
        self.assertAlmostEqual(steps["3b"], cal["v_throat"] + cal["vessel_volume"] + gn["volume"], places=6)
        added = {"5a": ins["meal"]["volume"], "5b": ins["meal"]["volume"], "6 ": ins["tertiary_air"]["volume"],
                 "7a": ins["fuel"]["volume"], "7b": ins["fuel"]["volume"]}
        for tag, dv in added.items():
            steps[tag] = list(steps.values())[-1] + dv
        for tag, want in steps.items():
            got, expected = self.num(rf"stage {re.escape(tag)}[^:\n]*: # m3 \(expected #\)")
            with self.subTest(stage=tag.strip()):
                self.assertAlmostEqual(expected, want, delta=1e-5 * want)
                self.assertAlmostEqual(got, want, delta=1e-3 * want)
        for tag, dv in added.items():
            got, expected = self.num(rf"stage {re.escape(tag)}[^:\n]*: added # m3 \(expected #\)")
            with self.subTest(added=tag.strip()):
                self.assertAlmostEqual(expected, dv, delta=1e-5 * max(1.0, dv))
                # what a pipe adds is the difference of two ~1600 m3 volumes, good to ~1e-6 of
                # themselves (calciner.bas' ADD_NOISE floor, 1.5e-5 of the body since 24 Nov 2026): the fuel pipe
                # read 1.5, 2.9 and 8 % off on three builds
                self.assertAlmostEqual(got, dv, delta=1e-2 * dv + 1.5e-5 * steps["1 "] * 1.6)

    def test_the_boundary_faces(self):
        """Each named face found once, with the area of what it is."""
        cal, gn = pg.calciner(self.g), pg.gooseneck(self.g)
        ins = pg.calciner_inlets(self.g)
        disc = lambda d: math.pi * 0.25 * d * d
        for name, want in (
            ("kiln_gas_inlet", disc(cal["D_throat"])),
            ("gas_outlet_1", disc(gn["D_leg"])), ("gas_outlet_2", disc(gn["D_leg"])),
            ("tertiary_air_inlet", ins["tertiary_air"]["end_area"]),
            ("meal_feed_1", ins["meal"]["end_area"]), ("meal_feed_2", ins["meal"]["end_area"]),
            ("fuel_inlet_1", ins["fuel"]["end_area"]), ("fuel_inlet_2", ins["fuel"]["end_area"]),
        ):
            with self.subTest(name):
                self.assertAlmostEqual(self.num(rf"boundary {name}: # m2")[0], want, delta=2e-3 * want)


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "c1_twin_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheTwinSolidIsTheSourcesTest(unittest.TestCase):
    """c1_twin.bas copies the verified C1_riser solid twice (read-only)
    and adds R1 and its Y; its log says the copies are the source's,
    the twin is one body inside its volume bounds, the source untouched."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "c1_twin_build.log").read_text(encoding="latin-1")

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("c1_twin built"), self.log.splitlines()[0])
        self.assertIn("source unchanged: ", self.log)

    def test_the_pair_is_the_source(self):
        tw = pg.c1_twin(pg.load())
        m = re.search(r"twin: C1 axes ([\d.]+) apart, branches ([\d.]+) apart \(walls ([\d.]+)\), R1 ([\d.]+) in front",
                      self.log)
        self.assertIsNotNone(m)
        got = [float(x) for x in m.groups()]
        want = [tw["spacing"], 2.0 * tw["branch_half"], tw["gap"], -tw["y_branch"]]
        for g_, w in zip(got, want):
            self.assertAlmostEqual(g_, w, delta=0.001)


class TheGasPathsAreTheDecisionsTest(unittest.TestCase):
    """User decisions, 14 Oct 2026: R2-R4 are the CFD outlet pipes,
    the gooseneck legs run to the C5 inlet."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()

    def test_r2_r4_rise_beside_the_cyclone_above(self):
        """User decision, 17 Nov 2026: R(k) is C(k+1)'s outlet pipe
        straight up (its CFD outlet the first part), its walls turning in
        at riser_slope_deg into C(k)'s level duct, the riser clear of
        C(k)'s barrel; the columns as far apart as the widest riser asks
        and each dust outlet dust_over_roof over the roof below."""
        L, d = pg.layout(self.g), self.g["cyclone_domain"]
        for k in (2, 3, 4):
            r = pg.stage_riser(self.g, k)
            c, up = pg.cyclone(self.g, f"C{k + 1}"), pg.cyclone(self.g, f"C{k}")
            ri = r["riser"]
            with self.subTest(riser=k):
                self.assertEqual(r["parts"][0]["D"], c["D_vortex"])
                self.assertGreaterEqual(r["parts"][0]["length"], c["outlet_rise"])   # the CFD outlet inside
                self.assertAlmostEqual(r["parts"][2]["length"], up["inlet_duct_length"], places=12)
                self.assertGreaterEqual(ri["clearance"], pg.v(d["riser_barrel_clearance"]) - 1e-9)
                self.assertAlmostEqual(ri["offset"], L["column_offset"], places=12)
                # the inclined duct (22 Nov 2026): the riser straight up,
                # a flat-faced duct climbing at riser_duct_slope_deg from it
                # into the level duct; the riser no closer than the mitre,
                # the taper (riser_taper_deg at most) and its radius allow
                c_k = pg.cyclone(self.g, f"C{k}")
                al = math.radians(pg.v(d["riser_duct_slope_deg"]))
                H_k, W_k = c_k["H_inlet"], c_k["W_inlet"]
                self.assertGreaterEqual(ri["run"], pg.riser_duct_run_min(
                    ri["D"], W_k, H_k, pg.v(d["riser_duct_slope_deg"]), pg.v(d["riser_taper_deg"])) - 1e-9)
                self.assertLessEqual(ri["taper_deg"], pg.v(d["riser_taper_deg"]) + 1e-9)
                self.assertAlmostEqual(ri["mitre_back"], 0.5 * H_k * math.tan(0.5 * al), places=12)
                self.assertAlmostEqual(ri["taper_L"], ri["run"] - 0.5 * ri["D"] - ri["mitre_back"], places=12)
                # the seam's foot: the floor plane at the riser's axis
                self.assertAlmostEqual(ri["drop"], 0.5 * H_k + ri["run"] * math.tan(al) + 0.5 * H_k / math.cos(al),
                                       places=12)
                self.assertAlmostEqual(ri["drop"] - ri["drop_top"], H_k / math.cos(al), places=12)
                # the volume: more than the inclined duct's straight part
                # behind the mitre plus the riser's back half
                a = 0.5 * ri["D"]
                v_lo = W_k * H_k / math.cos(al) * (ri["run"] - ri["mitre_back"]) \
                    + 0.5 * math.pi * a * a * H_k / math.cos(al)
                self.assertGreater(ri["volume"], v_lo)
                self.assertLess(ri["volume"], v_lo * 1.3)
                self.assertGreaterEqual(L["z_dust"][k] - L["z_roof"][k + 1],
                                        pg.v(self.g["layout"]["dust_over_roof"]) - 1e-9)
                # the roofs step by the riser: vertical + its turn
                self.assertAlmostEqual(L["z_roof"][k] - L["z_roof"][k + 1],
                                       L["riser_vertical"][k] + ri["drop"], places=9)

    def test_the_gooseneck_reaches_c5(self):
        gp, L = pg.gooseneck_plant(self.g), pg.layout(self.g)
        self.assertLess(L["z_c5_inlet"], L["z_gooseneck_top"])
        self.assertGreater(gp["leg_length"], 0.0)
        self.assertGreater(gp["volume"], 0.0)

    def test_the_twin_c1_share_one_r1(self):
        """User decision, 13 Nov 2026: a mirror pair, ducts facing each
        other, R1 on the mirror plane; the pair as tight as the branches'
        walls c1_twin_gap apart allow, nothing else touching."""
        tw, br = pg.c1_twin(self.g), pg.c1_branch(self.g)
        c, s = pg.cyclone(self.g, "C1"), pg.cyclone_duct_inlet(self.g, "C1")
        R, rb = 0.5 * c["D_barrel"], 0.5 * br["D"]
        self.assertAlmostEqual(tw["branch_gap"], pg.v(self.g["layout"]["c1_twin_gap"]), places=12)
        self.assertGreater(tw["barrel_gap"], tw["gap"])               # the barrels clear too
        self.assertGreater(0.5 * tw["spacing"] - s["y_outer"], 0.0)   # each duct on its own side
        self.assertGreater(tw["branch_half"], rb)                     # the Y's branches part
        self.assertGreater(tw["y_rise"], 0.0)
        self.assertAlmostEqual(tw["z_split"] + tw["y_rise"], br["z_floor"], places=12)
        L = pg.layout(self.g)
        self.assertAlmostEqual(L["x_c1"][1] - L["x_c1"][0], tw["spacing"], places=9)
        self.assertAlmostEqual(0.5 * sum(L["x_c1"]), L["x_r1"], places=9)   # symmetric over R1


class TheTwinReadsTheSourceTest(unittest.TestCase):
    """Step 3: the twin's geometry comes from the source only."""

    def test_the_config_writes_no_geometry(self):
        import yaml

        with open(REPO_ROOT / "configs" / "twin_cfg.yaml", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        for section, keys in pg.TWIN_KEYS.items():
            for key in keys:
                with self.subTest(key=f"{section}.{key}"):
                    self.assertNotIn(key, raw.get(section) or {})

    def test_a_second_value_is_refused(self):
        with self.assertRaises(ValueError):
            pg.apply_to_config({"kiln": {"diameter": 4.2}})

    def test_the_loader_puts_it_in(self):
        import main

        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
        self.assertEqual(cfg["kiln"]["diameter"], pg.kiln(pg.load())["D"])
        self.assertEqual(len(cfg["preheater"]["stages"]), 4)
        self.assertEqual([z["name"] for z in cfg["calciner"]["zone_segments"]], ["vessel", "gooseneck", "C5"])


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheKilnSolidIsTheSourcesTest(unittest.TestCase):
    """kiln.bas builds a plain cylinder of the published D, from the end
    of the kiln inlet chamber's stub to the hood end (stub + solid = the
    published L, user 22 Nov 2026); its log (decimal comma or point)
    carries the volume, the end faces and the slope it does not build in,
    held here to plant_geometry.kiln."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_build.log").read_text(encoding="latin-1")
        cls.k = pg.kiln(pg.load())

    def num(self, pattern):
        m = re.search(pattern.replace("#", r"(-?[\d.,]+)"), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("kiln built"), self.log.splitlines()[0])
        self.assertIn("closed manifold solid", self.log)

    def test_the_tube_is_the_sources(self):
        d, length, z0, z1, slope, vol = self.num(
            r"kiln: D # m, L # m \(the solid from z # to z #: the chamber's stub before it, the flame volume after it\), "
            r"slope # % \(installation, not built into the solid\), volume # m3")
        self.assertAlmostEqual(d, self.k["D"], places=5)
        self.assertAlmostEqual(length, self.k["L"], places=5)
        self.assertAlmostEqual(z0, self.k["z_cfd0"], places=5)
        self.assertAlmostEqual(z1, self.k["z_cfd1"], places=5)
        # the flame volume's bore takes over at z1: stub + solid + its bore = L, no overlap
        self.assertAlmostEqual(z1, pg.kiln_flame(pg.load())["z_cut"], places=9)
        self.assertAlmostEqual(z0, pg.kiln_inlet_chamber(pg.load())["L_stub"], places=9)
        self.assertAlmostEqual(slope, self.k["slope"], places=5)
        self.assertAlmostEqual(vol, self.k["volume_cfd"], delta=1e-6 * self.k["volume_cfd"])

    def test_the_zones_are_the_sources(self):
        tr, burn = self.num(r"transition # m from the back end, burning # m")
        self.assertAlmostEqual(tr, self.k["transition_L"], places=5)
        self.assertAlmostEqual(burn, self.k["burning_L"], places=5)

    def test_the_solid_is_the_tube(self):
        vol = self.num(r"kiln volume # m3")[0]
        self.assertAlmostEqual(vol, self.k["volume_cfd"], delta=1e-3 * self.k["volume_cfd"])
        zmin, zmax = self.num(r"extent: x [-\d.,]+ \.\. [-\d.,]+, y [-\d.,]+ \.\. [-\d.,]+, z # \.\. # m")
        self.assertAlmostEqual(zmin, self.k["z_cfd0"], places=2)
        self.assertAlmostEqual(zmax, self.k["z_cfd1"], places=2)

    def test_the_two_ends_are_the_boundaries(self):
        area = math.pi * (0.5 * self.k["D"]) ** 2
        for name in ("kiln_back", "burning_zone"):
            with self.subTest(name):
                self.assertAlmostEqual(self.num(rf"boundary {name}: # m2")[0], area, delta=2e-3 * area)
        self.assertAlmostEqual(self.num(r"boundary wall: \d+ faces, # m2")[0], self.k["wall_area_cfd"],
                               delta=2e-3 * self.k["wall_area_cfd"])


class TheCoolerVolumeIsItsAirTest(unittest.TestCase):
    """The cooler's CFD volume (cooler_cfd(), cooler_boundaries(); user
    decisions, 23 Nov 2026): the FLS segment shape at the twin's 2.2
    kg/kg, the hood outlets as the flame volume's cooler inlets, the vent
    the rest, the bed the FLS design bed at the twin's grate speed."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.c, cls.f = pg.cooler(cls.g), pg.cooler_cfd(cls.g)
        cls.b = pg.cooler_boundaries(cls.g)

    def test_the_segments_carry_the_air_rate_in_the_fls_shape(self):
        co, m = self.g["cooler"], self.b["air"]["m"]
        clinker = self.g["kiln"]["clinker_flow"]["value"]
        self.assertAlmostEqual(sum(m), co["air_rate"]["value"] * clinker, places=9)
        fls = [40.89, 18.56] + [16.24] * 8
        for got, w in zip(m, fls):
            self.assertAlmostEqual(got / sum(m), w / sum(fls), places=12)
        self.assertEqual(len(m), self.c["segments"])

    def test_the_mass_balances_and_the_vent_takes_the_rest(self):
        bal = self.b["balance"]
        self.assertAlmostEqual(bal["in"], bal["hood_1"] + bal["hood_2"] + bal["vent"], places=9)
        self.assertGreater(bal["vent"], 0.0)
        bc = self.b["bc"]
        inlets = sum(x["m"] for k, x in bc.items() if x["kind"] == "mass_flow_inlet")
        self.assertAlmostEqual(inlets, bal["in"], places=9)
        self.assertEqual(bc["vent_out"]["kind"], "pressure_outlet")

    def test_the_hood_outlets_are_the_flame_volumes_cooler_inlets(self):
        fb = pg.kiln_flame_boundaries(self.g)
        seal = fb["streams"]["seal_leak"]
        self.assertAlmostEqual(self.b["bc"]["hood_1"]["m"] + seal, fb["bc"]["secondary_air_in"]["m"], places=9)
        self.assertAlmostEqual(self.b["bc"]["hood_2"]["m"], fb["bc"]["tertiary_supply_in"]["m"], places=9)
        faces = {x[0]: x for x in pg.kiln_flame(self.g)["faces"]}
        for mine, theirs in (("hood_1", "secondary_air_in"), ("hood_2", "tertiary_supply_in")):
            with self.subTest(mine):
                self.assertAlmostEqual(self.f["faces"][mine], faces[theirs][3])

    def test_every_face_has_a_value(self):
        self.assertEqual(set(self.f["faces"]), set(self.b["bc"]))

    def test_the_vent_is_its_flow_at_the_literature_velocity(self):
        co = self.g["cooler"]
        rho = 101325.0 * pg.AIR_M / (pg.R_GAS * co["vent_T"]["value"])
        u = self.b["balance"]["vent"] / (rho * self.f["faces"]["vent_out"])
        self.assertAlmostEqual(u, co["vent_velocity"]["value"], places=9)
        self.assertGreaterEqual(self.f["vent_L"] / self.f["vent_D"], 3.0 - 1e-12)
        self.assertLessEqual(self.f["vent_x"] + 0.5 * self.f["vent_D"], self.c["length"])
        # near the middle, one segment towards the cold end (user, 23 Nov 2026)
        self.assertAlmostEqual(self.f["vent_x"], 0.5 * self.c["length"] + self.c["segment_L"], places=12)
        self.assertLess(self.f["vent_D"], self.c["width"])

    def test_the_bed_is_the_fls_bed_at_the_twins_grate_speed(self):
        cfg = yaml.safe_load((REPO_ROOT / "configs" / "twin_cfg.yaml").read_text())["cooler"]
        co = self.g["cooler"]
        self.assertEqual(cfg["bed_porosity"], co["bed_porosity"]["value"])
        self.assertEqual(cfg["solid_density"], co["solid_density"]["value"])
        self.assertEqual(cfg["particle_diameter_m"], co["particle_d"]["value"])
        clinker = self.g["kiln"]["clinker_flow"]["value"]
        h = clinker / (self.c["bed_rho"] * self.c["width"] * cfg["grate_speed_m_s"])
        self.assertAlmostEqual(h, self.c["bed_h"], delta=1e-3 * self.c["bed_h"])
        self.assertAlmostEqual(self.b["bed"]["clinker_velocity"], cfg["grate_speed_m_s"], delta=1e-4)

    def test_the_inlet_grate_is_the_sources(self):
        co = self.g["cooler"]
        self.assertAlmostEqual(self.c["cis_L"], co["cis_segments"]["value"] * self.c["segment_L"])
        self.assertAlmostEqual(self.c["cis_rise"], self.c["cis_L"] * math.tan(math.radians(co["cis_angle"]["value"])))
        self.assertLess(self.c["cis_rise"] + self.c["bed_h"], self.c["casing_height"])

    def test_the_ergun_coefficients(self):
        eps, d = 0.4, 0.015
        visc, inert = pg.ergun(eps, d)
        self.assertAlmostEqual(visc, 150 * 0.36 / (0.064 * 2.25e-4), delta=1e-6 * visc)
        self.assertAlmostEqual(inert, 3.5 * 0.6 / (0.064 * 0.015), delta=1e-9 * inert)


class TheCoolerMeetsTheHoodFaceToFaceTest(unittest.TestCase):
    """The cooler, the hood and the kiln one gas path (user, 23 Nov 2026):
    placed by cooler_placement(), the cooler's hood_1 / hood_2 lie on the
    flame volume's secondary_air_in / tertiary_supply_in (same plane, same
    rectangle), its roof elsewhere on the hood's floor level, no gap or
    overlap."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.cp, cls.c, cls.f = pg.cooler_placement(cls.g), pg.cooler(cls.g), pg.cooler_cfd(cls.g)
        cls.fl = {x[0]: x for x in pg.kiln_flame(cls.g)["faces"]}

    def test_the_hood_openings_are_the_flame_inlets(self):
        seg, w2 = self.c["segment_L"], 0.5 * self.c["width"]
        for k, (mine, theirs) in enumerate((("hood_1", "secondary_air_in"), ("hood_2", "tertiary_supply_in"))):
            z = self.f["hood_z"][k]
            with self.subTest(mine):
                # the centre on the flame face's point, the normals opposite, the areas equal
                ctr = self.cp["to_kiln"](((k + 0.5) * seg, 0.0, z))
                for a, b in zip(ctr, self.fl[theirs][1]):
                    self.assertAlmostEqual(a, b, places=9)
                up = self.cp["R"][2]
                self.assertAlmostEqual(sum(a * b for a, b in zip(up, self.fl[theirs][2])), -1.0, places=12)
                self.assertAlmostEqual(self.f["faces"][mine], self.fl[theirs][3], places=9)
                # its corners too: the rectangle seg x width, hot end at the hood's back wall
                for x in (k * seg, (k + 1) * seg):
                    for y in (-w2, w2):
                        p = self.cp["to_kiln"]((x, y, z))
                        h = sum((p[i] - (0.0, 0.0, pg.kiln(self.g)["L"])[i]) * self.cp["R"][0][i] for i in range(3))
                        self.assertGreaterEqual(h, -1e-9)
                        self.assertLessEqual(h, pg.kiln_hood(self.g)["depth"] + 1e-9)

    def test_the_roof_is_the_hoods_floor(self):
        hd = pg.kiln_hood(self.g)
        p = self.cp["to_kiln"]((0.0, 0.0, self.c["casing_height"]))
        u = sum((p[i] - (0.0, 0.0, pg.kiln(self.g)["L"])[i]) * self.cp["R"][2][i] for i in range(3))
        self.assertAlmostEqual(u, -hd["below"], places=9)
        # the roof is flat (no steps) and the flame volume has no stubs: its
        # floor is split across at one segment into its two inlets
        self.assertEqual(self.f["hood_z"], (self.c["casing_height"],) * 2)
        fl = pg.kiln_flame(self.g)
        self.assertFalse([b for b in fl["bodies"] if b["name"].startswith("cooler_seg")])
        K = (0.0, 0.0, pg.kiln(self.g)["L"])
        for q in fl["floor_split"]:
            h = sum((q[i] - K[i]) * self.cp["R"][0][i] for i in range(3))
            u = sum((q[i] - K[i]) * self.cp["R"][2][i] for i in range(3))
            self.assertAlmostEqual(h, self.c["segment_L"], places=9)
            self.assertAlmostEqual(u, -hd["below"], places=9)

    def test_the_assembly_holds_the_cooler_where_placed(self):
        log = REPO_ROOT / "geometry" / "output" / "2500" / "kiln_outlet_assembly_build.log"
        if not log.is_file():
            self.skipTest("no assembly log")
        text = log.read_text(encoding="latin-1")
        self.assertIn("placed cooler.SLDPRT", text)
        m = re.search(r"component cooler-1: x ([-\d.,]+) \.\. ([-\d.,]+), y ([-\d.,]+) \.\. ([-\d.,]+), z ([-\d.,]+) \.\. ([-\d.,]+)", text)
        self.assertIsNotNone(m)
        got = [float(t.replace(",", ".").rstrip(".")) for t in m.groups()]
        want = [self.cp["box"][i] for i in (0, 3, 1, 4, 2, 5)]
        for a, b in zip(got, want):
            self.assertAlmostEqual(a, b, delta=0.01)

    def test_the_kiln_bore_meets_the_flame_volume(self):
        # the kiln's CFD bore ends where the flame volume's begins (one gas
        # path from the inlet chamber's stub to the hood), and the assembly
        # holds it there
        k, f = pg.kiln(self.g), pg.kiln_flame(self.g)
        self.assertAlmostEqual(k["z_cfd1"], f["z_cut"], places=12)
        self.assertAlmostEqual(k["z_cfd0"] + k["L_cfd"] + f["L_flame"], k["L"], places=9)
        log = REPO_ROOT / "geometry" / "output" / "2500" / "kiln_outlet_assembly_build.log"
        if not log.is_file():
            self.skipTest("no assembly log")
        text = log.read_text(encoding="latin-1")
        m = re.search(r"component kiln-1: x [-\d.,]+ \.\. [-\d.,]+, y [-\d.,]+ \.\. [-\d.,]+, z ([-\d.,]+) \.\. ([-\d.,]+)", text)
        self.assertIsNotNone(m)
        z0, z1 = (float(t.replace(",", ".").rstrip(".")) for t in m.groups())
        self.assertAlmostEqual(z0, k["z_cfd0"], delta=0.01)
        self.assertAlmostEqual(z1, k["z_cfd1"], delta=0.01)
        self.assertIn("view from the kiln inlet, kiln bore hidden, flame volume and cooler see-through", text)


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "cooler_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheCoolerSolidIsTheSourcesTest(unittest.TestCase):
    """cooler.bas builds cooler_cfd(): the bed and the freeboard; its log
    carries the size, the volumes, the floor's strips, the hood outlets,
    the vent and the walls, held here to plant_geometry."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "cooler_build.log").read_text(encoding="latin-1")
        g = pg.load()
        cls.c, cls.f = pg.cooler(g), pg.cooler_cfd(g)

    def num(self, pattern):
        m = re.search(pattern.replace("#", r"(-?[\d.,]+)"), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".").rstrip(".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("cooler built"), self.log.splitlines()[0])
        self.assertIn("bed: closed manifold solid", self.log)
        self.assertIn("freeboard: closed manifold solid", self.log)

    def test_the_casing_is_the_sources(self):
        w, length, h, cis, rise, bed = self.num(
            r"cooler: # m wide, # m long, # m high; inlet grate # m, rising # m to the hot end; bed # m deep")
        for got, want in ((w, self.c["width"]), (length, self.c["length"]), (h, self.c["casing_height"]),
                          (cis, self.c["cis_L"]), (rise, self.c["cis_rise"]), (bed, self.c["bed_h"])):
            self.assertAlmostEqual(got, want, places=5)
        for what, key in (("bed", "bed_volume"), ("freeboard", "freeboard_volume")):
            with self.subTest(what):
                got = self.num(rf"{what} volume # m3")[0]
                self.assertAlmostEqual(got, self.f[key], delta=1e-3 * self.f[key])

    def test_the_vent_is_the_sources(self):
        D, x, L = self.num(r"vent: bore # m at x = # m, run # m up")
        self.assertAlmostEqual(D, self.f["vent_D"], places=5)
        self.assertAlmostEqual(x, self.f["vent_x"], places=4)
        self.assertAlmostEqual(L, self.f["vent_L"], places=5)

    def test_the_zones_are_the_sources(self):
        n, seg, nh, hood = self.num(r"cooler: # segments of # m \(grate_air_1 \.\. \d+ from the hot end\), hood opening # segments, x 0 \.\. # m")
        self.assertEqual(int(n), self.c["segments"])
        self.assertAlmostEqual(seg, self.c["segment_L"], places=5)
        self.assertEqual(int(nh), self.c["hood_segments"])
        self.assertAlmostEqual(hood, self.c["hood_L"], places=5)

    def test_every_face_is_the_sources(self):
        for name, area in self.f["faces"].items():
            if name == "bed_top":
                continue
            with self.subTest(name):
                self.assertAlmostEqual(self.num(rf"boundary {name}: # m2")[0], area, delta=2e-3 * area)
        top = self.num(r"boundary bed_top: # m2 \(bed\), # m2 \(freeboard\)")
        for got in top:
            self.assertAlmostEqual(got, self.f["faces"]["bed_top"], delta=2e-3 * self.f["faces"]["bed_top"])
        for what in ("bed", "freeboard"):
            with self.subTest(what):
                want = self.f["walls"][what]
                self.assertAlmostEqual(self.num(rf"boundary wall \({what}\): \d+ faces, # m2")[0], want,
                                       delta=2e-3 * want)


class TheIdFanIsTheProcessDutyTest(unittest.TestCase):
    """The ID fan (fan/id_fan.md) is sized by fan laws from a design
    duty: the twin's exhaust when the CFD solid was built, frozen there
    (user decision, 15 Nov 2026). The twin must stay near that duty."""

    # Band within which the twin's exhaust may drift before the fan's
    # duty has to be revisited (user decision, 15 Nov 2026; no source).
    T_BAND = 5.0          # K
    FLOW_BAND = 0.02      # relative

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.fan = pg.id_fan(cls.g)

    def test_the_twin_runs_at_the_fans_duty(self):
        import json

        with open(REPO_ROOT / "tests" / "data" / "twin_state_reference.json", encoding="utf-8") as handle:
            snap = json.load(handle)["snapshot"]
        f = self.g["id_fan"]
        strings = pg.v(self.g["plant"]["strings"])
        flow = pg.v(f["exhaust_flow_per_string"]) * strings
        self.assertAlmostEqual(flow, snap["mass_flow_m_dot_exhaust"], delta=self.FLOW_BAND * flow,
                               msg="the twin's exhaust left the ID fan's design duty: revisit the fan")
        self.assertAlmostEqual(pg.v(f["exhaust_T"]), snap["stage4_gas_outlet_temperature"], delta=self.T_BAND,
                               msg="the twin's exhaust left the ID fan's design duty: revisit the fan")

    def test_the_size_follows_from_the_duty(self):
        fan = self.fan
        self.assertAlmostEqual(fan["q"] * fan["rho"], pg.v(self.g["id_fan"]["exhaust_flow_per_string"]), places=9)
        self.assertAlmostEqual(fan["p_shaft"] * pg.v(self.g["id_fan"]["efficiency"]), fan["q"] * fan["dp"], places=3)
        # tip speed from the pressure coefficient, the impeller from the speed
        self.assertAlmostEqual(0.5 * fan["rho"] * fan["u_tip"] ** 2 * pg.v(self.g["id_fan"]["pressure_coefficient"]),
                               fan["dp"], places=6)
        self.assertAlmostEqual(fan["D_impeller"] * math.pi * pg.v(self.g["id_fan"]["speed"]) / 60.0, fan["u_tip"], places=9)

    def test_the_size_class_is_the_literatures(self):
        fan = self.fan
        self.assertTrue(2.2 <= fan["D_impeller"] <= 3.5, fan["D_impeller"])         # Pengxiang catalogue
        self.assertTrue(600e3 <= fan["q_total_h"] <= 900e3, fan["q_total_h"])       # 5000 t/d, vendor range
        self.assertTrue(1500e3 <= 2 * fan["p_shaft"] <= 3000e3, fan["p_shaft"])     # both fans, guide range

    def test_the_flow_path_keeps_the_volume_flow(self):
        """Continuity at the eye, the blade row's inlet and outlet, the
        volute's discharge and the inlet box: each carries Q."""
        fan, q = self.fan, self.fan["q"]
        self.assertAlmostEqual(fan["c0"] * math.pi * fan["D_inlet"] ** 2 / 4.0, q, places=9)
        self.assertAlmostEqual(fan["c0"] * math.pi * fan["D_inlet"] * fan["b1"], q, places=9)
        self.assertAlmostEqual(fan["cm2"] * math.pi * fan["D_impeller"] * fan["b2"] * fan["tau2"], q, places=9)
        self.assertAlmostEqual(fan["u_section"] * fan["B"] * fan["h_out"], q, places=9)
        self.assertAlmostEqual(fan["u_out"] * fan["B"] * fan["h_stub"], q, places=9)
        self.assertAlmostEqual(fan["u_box"] * fan["H_box"] * fan["depth_box"], q, places=9)

    def test_the_impeller_gives_the_pressure_by_euler(self):
        """dp = eta_h rho u2 cu2, with cu2 from Wiesner's slip, inside
        Wiesner's own D1/D2 limit; z from k sin(beta2) / (1 - D1/D2)."""
        f, fan = self.g["id_fan"], self.fan
        b2 = math.radians(fan["beta2"])
        self.assertAlmostEqual(pg.v(f["hydraulic_efficiency"]) * fan["rho"] * fan["u_tip"] * fan["cu2"], fan["dp"], places=6)
        self.assertAlmostEqual(fan["cu2"], fan["u_tip"] * (fan["slip"] - fan["cm2"] / (fan["u_tip"] * math.tan(b2))), places=9)
        self.assertLess(fan["D_inlet"] / fan["D_impeller"], fan["slip_limit"])
        self.assertEqual(fan["z"], round(pg.v(f["blade_number_coeff"]) * math.sin(b2) / (1.0 - pg.v(f["eye_ratio"]))))
        self.assertTrue(0.4 <= fan["D_inlet"] / fan["D_impeller"] <= 0.7 + 1e-12)     # IJTE 2022 band
        self.assertGreater(fan["beta1"], fan["beta1_flow"])
        self.assertTrue(0.0 < fan["tau1"] < 1.0 and 0.0 < fan["tau2"] < 1.0)
        # the blade arc meets both radii at its angles (angles from the tangent)
        r1, r2, rb, rc = fan["D_inlet"] / 2, fan["D_impeller"] / 2, fan["blade_arc_R"], fan["blade_arc_centre_r"]
        self.assertAlmostEqual(rc ** 2, rb ** 2 + r1 ** 2 - 2 * rb * r1 * math.cos(math.radians(fan["beta1"])), places=9)

    def test_the_volute_carries_q_at_its_outlet_velocity(self):
        """The spiral grows so the discharge carries Q at the chosen outlet
        velocity; the width is in the 2-3 b2 rule; the parts nest without
        overlap; the cone and the box clear the volute's front plate."""
        fan = self.fan
        self.assertAlmostEqual(fan["u_out"], pg.v(self.g["id_fan"]["volute_outlet_velocity"]), places=6)
        self.assertLess(fan["u_out"], fan["cu2"])                  # the casing decelerates the gas
        self.assertGreater(fan["y_box"], fan["B"])                 # the box sits outside the volute
        self.assertAlmostEqual(fan["L_cone"], fan["y_box"] - fan["b1"], places=12)
        self.assertTrue(2.0 <= fan["B"] / fan["b2"] <= 3.0)
        r2 = fan["D_impeller"] / 2
        self.assertTrue(r2 < fan["r_mrf"] < fan["r3"] < fan["r_end"])
        self.assertTrue(0.05 <= fan["tongue_radius"] / fan["D_impeller"] <= 0.10)
        self.assertLess(fan["b1"], fan["B"])                       # the eye's shroud sits inside the volute's width
        self.assertLess(fan["D_cone"] / 2, fan["r_mrf"])           # the cone's mouth clears the volute
        self.assertTrue(min(fan["V_rotor_bladed"], fan["V_volute"], fan["V_cone"], fan["V_box"]) > 0.0)
        self.assertGreater(fan["nose_clearance"], 0.0)                # the tongue's nose clears the MRF zone
        # the discharge runs along -x: its two walls are level, h_out cos(alpha) - 2 rho apart
        a = math.radians(fan["spiral_angle"])
        self.assertAlmostEqual(fan["h_stub"], fan["h_out"] * math.cos(a) - 2 * fan["tongue_radius"], places=9)

    def test_the_blade_arc_meets_its_angles(self):
        """The single arc, placed backward against the rotation, makes
        beta1 with the circle at r1 and beta2 at r2."""
        fan = self.fan
        r1, r2, rb, rc, s = (fan["D_inlet"] / 2, fan["D_impeller"] / 2, fan["blade_arc_R"],
                             fan["blade_arc_centre_r"], fan["blade_sense"])

        def phi(r):
            return math.acos((rc ** 2 + r ** 2 - rb ** 2) / (2 * rc * r))

        h = 1e-7
        for r, want in ((r1 + h, fan["beta1"]), (r2 - 2 * h, fan["beta2"])):
            dth = s * (phi(r + h) - phi(r))
            self.assertLess(dth, 0.0)                                   # theta falls as r grows: backward
            self.assertAlmostEqual(math.degrees(math.atan(h / (r * abs(dth)))), want, delta=0.01)


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "id_fan_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheIdFanSolidIsTheSourcesTest(unittest.TestCase):
    """id_fan.bas builds the fan's three zones (rotor, volute, inlet);
    its log carries their volumes and the boundary faces, held here to
    plant_geometry.id_fan."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "id_fan_build.log").read_text(encoding="latin-1")
        cls.f = pg.id_fan(pg.load())

    def num(self, pattern):
        m = re.search(pattern.replace("#", r"(-?[\d.,]+)"), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".").rstrip(".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("id_fan built"), self.log.splitlines()[0])

    def test_each_zone_is_closed_and_the_sources_volume(self):
        f = self.f
        want = {"rotor": f["V_rotor_bladed"], "volute": f["V_volute"], "inlet": f["V_cone"] + f["V_box"]}
        for name, v in want.items():
            with self.subTest(name):
                got = self.num(rf"body {name}: closed, \d+ edges, # m3")[0]
                self.assertAlmostEqual(got, v, delta=1e-3 * v)

    def test_the_boundary_faces_are_the_sources(self):
        f = self.f
        r1, r_mrf = f["D_inlet"] / 2, f["r_mrf"]
        want = {
            "fan_inlet": f["H_box"] * f["depth_box"],
            "fan_outlet": f["a_out"],
            "interface_eye inlet side": math.pi * r1 ** 2,
            "interface_eye rotor side": math.pi * r1 ** 2,
            "interface_rim rotor side": 2 * math.pi * r_mrf * f["b2"],
            "interface_rim volute side": 2 * math.pi * r_mrf * f["B"],
        }
        for name, a in want.items():
            with self.subTest(name):
                self.assertAlmostEqual(self.num(rf"boundary {name}: # m2")[0], a, delta=2e-3 * a)
        self.assertGreaterEqual(int(self.num(r"boundary blade: # faces")[0]), 2 * f["z"])


class TheKilnBurnerIsTheKilnFiringTest(unittest.TestCase):
    """The JETFLEX 2.0 burner (kiln/kiln_burner.md) takes the twin's kiln
    firing; its primary air (axial + swirl) leaves at the manual's channel
    pressures through the brochure's openings, scaled to pass it."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.b = pg.kiln_burner(cls.g)

    def test_the_duty_is_the_twins_kiln_firing(self):
        import json

        with open(REPO_ROOT / "tests" / "data" / "twin_state_reference.json", encoding="utf-8") as handle:
            snap = json.load(handle)["snapshot"]
        f = self.g["kiln_burner"]
        self.assertAlmostEqual(pg.v(f["fuel_flow"]), snap["mass_flow_m_dot_fuel_kiln"], places=4)
        self.assertAlmostEqual(pg.v(f["kiln_air_flow"]), snap["mass_flow_m_dot_air_kiln"], places=3)
        self.assertAlmostEqual(self.b["m_pa"], snap["mass_flow_m_dot_primary_air"], places=3)

    def test_the_primary_air_share_is_the_twins(self):
        import yaml

        with open(REPO_ROOT / "configs" / "twin_cfg.yaml", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)
        self.assertEqual(pg.v(self.g["kiln_burner"]["primary_air_fraction"]), cfg["burning"]["primary_air_fraction"])

    def test_the_channels_pass_the_flows(self):
        b = self.b
        self.assertAlmostEqual(b["m_axial"] + b["m_swirl"], b["m_pa"], places=12)
        self.assertAlmostEqual(b["rho_axial"] * b["u_axial"] * b["A_axial"], b["m_axial"], places=12)
        self.assertAlmostEqual(b["rho_swirl"] * b["u_swirl"] * b["A_swirl"], b["m_swirl"], places=12)
        self.assertAlmostEqual(b["rho_transport"] * b["u_coal"] * b["A_coal"], b["m_transport"], places=12)
        f = self.g["kiln_burner"]
        self.assertAlmostEqual(b["A_axial"], pg.v(f["n_axial"]) * b["slot_l"] * b["slot_w"], places=12)
        self.assertAlmostEqual(b["A_axial"], pg.v(f["n_axial"]) * pg.v(f["axial_slot_area_over_D2"]) * b["D_tip"] ** 2,
                               places=12)
        self.assertAlmostEqual(b["slot_l"] / b["slot_w"], pg.v(f["axial_slot_aspect"]), places=9)

    def test_the_jets_are_the_isentropic_ones(self):
        # 1/2 u^2 = cp (T0 - T), p / rho = R T at ambient pressure
        b, f = self.b, self.g["kiln_burner"]
        cp = 1.4 / 0.4 * pg.R_GAS / 0.028965
        T0 = pg.v(f["primary_air_T"])
        for ch in ("axial", "swirl"):
            with self.subTest(ch):
                self.assertAlmostEqual(0.5 * b[f"u_{ch}"] ** 2, cp * (T0 - b[f"T_{ch}"]), places=6)
                self.assertAlmostEqual(101325.0 / b[f"rho_{ch}"], pg.R_GAS / 0.028965 * b[f"T_{ch}"], places=6)
        self.assertLess(b["u_axial"], 340.0 * 0.7)

    def test_it_is_inside_the_jetflex_range(self):
        # 10-250 MW (FLSmidth); the momentum in its 7-11 N/MW
        b, f = self.b, self.g["kiln_burner"]
        self.assertTrue(10.0 <= b["thermal_MW"] <= 250.0)
        self.assertAlmostEqual(b["momentum_N"], b["m_axial"] * b["u_axial"] + b["m_swirl"] * b["u_swirl"], places=9)
        self.assertTrue(pg.v(f["momentum_min_per_MW"]) <= b["momentum_per_MW"] <= pg.v(f["momentum_max_per_MW"]))

    def test_the_coal_pipe_meets_the_literature_velocity(self):
        # not an input: the scale comes from the slots; within 15 % of 33 m/s
        ref = pg.v(self.g["kiln_burner"]["coal_velocity_ref"])
        self.assertLess(abs(self.b["u_coal"] - ref) / ref, 0.15)

    def test_the_channels_do_not_meet(self):
        b, f = self.b, self.g["kiln_burner"]
        for what, gap in b["walls"].items():
            with self.subTest(what):
                self.assertGreaterEqual(gap, pg.v(f["wall_min"]))
        self.assertLessEqual(b["axial_plenum"][1], 0.5 * b["D_tip"])

    def test_the_groups_hold_their_openings(self):
        b, f = self.b, self.g["kiln_burner"]
        n = {g: sum(1 for q in b["bodies"] if q["group"] == g) for g in ("coal", "axial", "swirl")}
        self.assertEqual(n, {"coal": 1, "axial": pg.v(f["n_axial"]) + 1, "swirl": pg.v(f["n_swirl"]) + 1})
        sw = b["groups"]["swirl"]
        self.assertAlmostEqual(sw["a_out"] * math.cos(b["swirl_angle"]), b["A_swirl"], places=12)


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_burner_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheKilnBurnerSolidIsTheSourcesTest(unittest.TestCase):
    """kiln_burner.bas builds the three channels; its log carries their
    volumes and boundary faces, held here to plant_geometry.kiln_burner."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_burner_build.log").read_text(encoding="latin-1")
        cls.b = pg.kiln_burner(pg.load())

    def num(self, pattern):
        m = re.search(pattern.replace("#", r"(-?[\d.,]+)"), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".").rstrip(".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("kiln_burner built"), self.log.splitlines()[0])

    def test_each_channel_is_the_sources(self):
        for g, q in self.b["groups"].items():
            with self.subTest(g):
                self.assertAlmostEqual(self.num(rf"body {g}: # m3")[0], q["V"], delta=2e-6)
                n, a = self.num(rf"boundary {g}_outlet: # faces, # m2")
                self.assertEqual(int(n), q["n_out"])
                self.assertAlmostEqual(a, q["a_out"], delta=2e-6)
                self.assertAlmostEqual(self.num(rf"boundary {g}_inlet: 1 faces, # m2")[0], q["a_in"], delta=2e-6)


class TheWholeBurnerIsTheBrochuresSideViewTest(unittest.TestCase):
    """plant_geometry.kiln_burner_body(): the whole burner as envelopes,
    each length a brochure ratio of the tip D; the channel solid fits
    inside its steel pipe."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.r = pg.kiln_burner_body(cls.g)
        cls.ch = pg.kiln_burner(cls.g)

    def test_the_lengths_add_up(self):
        b, D = self.g["kiln_burner"], self.r["D_tip"]
        parts = ("castable_L", "collar_L", "flange_L", "head_L", "bellows_L", "coal_L")
        want = sum(pg.v(b[f"body_{k}"]) for k in parts) * D
        self.assertAlmostEqual(self.r["L_total"], want, places=9)
        self.assertAlmostEqual(self.r["D_tip"], self.ch["D_tip"], places=12)

    def test_the_channels_fit_inside_the_pipe(self):
        r = self.r
        self.assertAlmostEqual(r["r_pipe_in"], self.ch["axial_plenum"][1], places=12)
        self.assertLess(r["r_pipe"], r["R_castable"])
        self.assertLess(r["R_castable"], 0.5 * r["D_tip"])
        self.assertLess(self.ch["L_coal"], r["L_total"])

    def test_the_inner_tubes_meet_the_plenums(self):
        """Inside the steel pipe the core tube and the swirl tube bound the
        two annuli the channel solid's plenums continue (brochure p. 4:
        two air systems), and end at the plenums' back face."""
        by = {b["name"]: b for b in self.r["bodies"]}
        sw0, sw1 = self.ch["swirl_plenum"]
        ax0, ax1 = self.ch["axial_plenum"]
        core, swirl = by["core_tube"]["p"], by["swirl_tube"]["p"]
        self.assertAlmostEqual(core[6], sw0, places=12)                    # core tube OD = swirl plenum's inner wall
        self.assertAlmostEqual(swirl[8], sw1, places=12)                   # swirl tube ID = swirl plenum's outer wall
        self.assertAlmostEqual(swirl[6], ax0, places=12)                   # swirl tube OD = axial plenum's inner wall
        self.assertAlmostEqual(self.r["r_pipe_in"], ax1, places=12)       # steel pipe = axial plenum's outer wall
        z_pl = -(self.ch["plate_t"] + self.ch["plenum_L"])
        for p in (core, swirl):
            self.assertAlmostEqual(p[2] + p[7], z_pl, places=9)

    def test_the_core_holds_the_fuel_pipe_and_the_tip_tubes(self):
        by = {b["name"]: b for b in self.r["bodies"]}
        r_core_in = by["core_tube"]["p"][8]
        fuel = by["fuel_pipe"]["p"]
        self.assertAlmostEqual(fuel[8], 0.5 * self.ch["D_coal"], places=12)     # its bore = the CFD coal pipe
        self.assertAlmostEqual(fuel[2] + fuel[7], -self.ch["L_coal"], places=9)  # runs on into it
        self.assertLess(abs(fuel[1]) + fuel[6], r_core_in)
        for name in ("fuel_lance", "flame_scanner", "igniter"):
            p = by[name]["p"]
            self.assertLess(math.hypot(p[0], p[1]) + p[6], r_core_in, name)

    def test_the_partition_parts_the_two_inlets(self):
        """The head's partition: the elbow (axial air) in front of it, air
        inlet 2 (swirl air) behind it."""
        by = {b["name"]: b for b in self.r["bodies"]}
        z0, z1 = by["head_partition"]["p"][2:4]
        self.assertLess(by["air_inlet_2_flange"]["box"][5], z0)
        self.assertGreater(by["elbow_leg"]["box"][2], z1)

    def test_each_body_its_volume_and_box(self):
        for q in self.r["bodies"]:
            with self.subTest(q["name"]):
                bx = q["box"]
                self.assertGreater(q["V"], 0.0)
                self.assertLessEqual(q["V"], (bx[3] - bx[0]) * (bx[4] - bx[1]) * (bx[5] - bx[2]) * (1 + 1e-12))


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_burner_body_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheWholeBurnerSolidIsTheSourcesTest(unittest.TestCase):
    """kiln_burner_body.bas logs each body (a group of parts joined): its
    volume where the parts do not overlap, held to the source."""

    def test_each_body(self):
        log = (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_burner_body_build.log").read_text(encoding="latin-1")
        self.assertTrue(log.startswith("kiln_burner_body built"), log.splitlines()[0])
        groups = pg.kiln_burner_body(pg.load())["groups"]
        for name, q in groups.items():
            with self.subTest(name):
                m = re.search(rf"body {name} \((\d+) parts\): (-?[\d.,]+) m3", log)
                self.assertIsNotNone(m)
                self.assertEqual(int(m.group(1)), q["n"])
                if q["V"] is not None:
                    self.assertAlmostEqual(float(m.group(2).replace(",", ".")), q["V"], delta=2e-6)


class TheKilnHoodAndChamberPassTheVelocityChecksTest(unittest.TestCase):
    """Hood and inlet chamber have no published size (user decision,
    16 Nov 2026: size by gas velocity). The inlet chamber keeps the layout
    square; the hood is a box round the kiln's outlet seal (user decision,
    23 Nov 2026) and must still pass the literature's velocities."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.hood, cls.ch = pg.kiln_hood(cls.g), pg.kiln_inlet_chamber(cls.g)

    def test_the_hood_air_is_inside_the_literatures_range(self):
        h = self.hood
        self.assertTrue(h["u_min"] <= h["u"] <= h["u_max"], h["u"])
        self.assertTrue(h["u_min"] <= h["u_hot"] <= h["u_max"], h["u_hot"])      # the hotter secondary air too
        self.assertGreaterEqual(h["area"], h["area_min"])
        # the box less the two triangles under the hopper's walls
        self.assertAlmostEqual(h["area"], h["W"] * h["H"] - h["hopper_dw"] * h["hopper_rise"])

    def test_the_hopper_runs_from_the_coolers_edge_to_the_hood_wall(self):
        h, co = self.hood, pg.cooler(self.g)
        self.assertAlmostEqual(2.0 * h["hopper_dw"] + co["width"], h["W"])
        self.assertAlmostEqual(h["hopper_rise"], h["hopper_dw"] * math.tan(h["hopper_angle"]))
        # steeper than the clinker's angle of repose: no dust settles on it
        self.assertGreater(math.degrees(h["hopper_angle"]), pg.v(self.g["kiln"]["repose_angle"]))
        self.assertLess(h["hopper_rise"], h["H"])

    def test_the_hopper_clears_the_kilns_bore(self):
        h, co, kl = self.hood, pg.cooler(self.g), pg.kiln(self.g)
        R, x0 = 0.5 * kl["D"], 0.5 * co["width"]
        for i in range(101):
            x = x0 + i * (min(R, 0.5 * h["W"]) - x0) / 100
            bore = h["below"] - math.sqrt(max(0.0, R * R - x * x))
            self.assertGreater(bore - (x - x0) * math.tan(h["hopper_angle"]), 1.0, x)
        self.assertGreater(h["hopper_gap"], 1.0)

    def test_the_hood_holds_the_outlet_seal(self):
        h = self.hood
        c = pg.v(self.g["kiln_hood"]["seal_clearance"])
        self.assertGreaterEqual(0.5 * h["W"], h["R_seal"] + c - 1e-9)
        self.assertGreaterEqual(h["above"], h["R_seal"] + c - 1e-9)
        self.assertAlmostEqual(h["above"] + h["below"], h["H"])
        self.assertEqual(self.g["kiln_hood"]["seal_clearance"]["source"], "model")

    def test_the_hood_stands_on_the_cooler_roof_over_its_two_segments(self):
        L, co = pg.layout(self.g), pg.cooler(self.g)
        self.assertAlmostEqual(L["hood_z"][0], L["cooler_z"][1])
        self.assertAlmostEqual(L["hood_z"][1] - L["hood_z"][0], self.hood["H"])
        self.assertAlmostEqual(L["hood_x"][0], L["kiln_end"][0])
        self.assertAlmostEqual(L["hood_x"][1] - L["hood_x"][0], co["hood_L"])

    def test_the_chamber_gas_is_under_the_limit_and_above_the_updraft_minimum(self):
        c = self.ch
        self.assertLessEqual(c["u_chamber"], c["u_max"])
        self.assertGreaterEqual(c["u_chamber"], 4.0)
        self.assertGreaterEqual(c["side"], c["side_min"])

    def test_the_square_is_the_layouts_and_a_model_value(self):
        a = pg.layout(self.g)["a_chamber"]
        self.assertAlmostEqual(self.ch["side"], 2.0 * a)
        self.assertEqual(self.g["layout"]["chamber_margin"]["source"], "model")

    def test_the_calciner_sits_on_the_roof(self):
        # user decision, 22 Nov 2026: no throat extension; the chamber's top is
        # the roof's highest point under the throat, the calciner's foot on it
        c, L = self.ch, pg.layout(self.g)
        self.assertAlmostEqual(c["height"], c["roof_left"][1])
        self.assertAlmostEqual(L["z_calciner_throat"] - L["z_chamber_floor"], c["height"])
        self.assertLess(c["D_throat"], c["side"])
        wedge = 2.0 * c["r_throat"] * math.tan(c["alpha"])                         # 0 at x = -r, this at x = +r
        self.assertAlmostEqual(c["height"] - c["roof_at_throat"], wedge)
        self.assertLess(wedge, 0.1)

    def test_the_section_is_the_users_sketch_with_the_kilns_lines_carried_in(self):
        # 21 Nov 2026 sketch: throat walls down, a 50 deg ramp, the foot and
        # the roof the kiln tube's bottom and top lines (kiln.slope)
        c, L = self.ch, pg.layout(self.g)
        R, r, al = c["R_mouth"], c["r_throat"], c["alpha"]
        self.assertAlmostEqual(c["ramp_top"][0], -r)                                 # the ramp starts at the throat's left wall
        self.assertAlmostEqual(math.degrees(math.atan2(c["ramp_top"][1] - c["toe"][1], c["toe"][0] - c["ramp_top"][0])),
                               c["ramp_deg"])
        self.assertGreaterEqual(c["ramp_deg"], 45.0)                                 # over meal's 40-45 deg angle of repose
        for p, q in ((c["toe"], c["lip_low"]), (c["lip_up"], c["roof_left"])):       # along the kiln axis
            self.assertAlmostEqual((q[1] - p[1]) / (q[0] - p[0]), -math.tan(al))
        # the mouth's face: R either side of the axis, square to it
        self.assertAlmostEqual(math.dist(c["lip_low"], c["lip_up"]), 2.0 * R)
        self.assertAlmostEqual(c["lip_up"][0] - c["lip_low"][0], 2.0 * R * math.sin(al))
        self.assertLess(c["ramp_top"][1], c["roof_at_throat"])                       # the throat reaches the roof everywhere
        # the topology draws the same toe and ramp top
        self.assertAlmostEqual(L["chamber_ramp_toe"][1] - L["z_chamber_floor"], c["toe"][1])
        self.assertAlmostEqual(L["z_chamber_ramp_top"] - L["z_chamber_floor"], c["ramp_top"][1])

    def test_the_cfd_inlet_is_the_kiln_tubes_stub_and_the_volume_adds_up(self):
        c = self.ch
        self.assertEqual(self.g["kiln_inlet_chamber"]["mouth_stub_over_D"]["source"], "model")
        self.assertAlmostEqual(c["L_stub"], 0.5 * 2.0 * c["R_mouth"])
        self.assertAlmostEqual(c["volume"], c["V_box"] + c["V_throat"] + c["V_stub"])
        self.assertAlmostEqual(c["V_box"], c["profile_area"] * c["side"])
        # reported next to the check, never replacing it
        self.assertEqual(self.g["kiln_inlet_chamber"]["gas_velocity_ref_holcim"]["source"], "literature")

    def test_the_kiln_tube_inlet_velocity_is_reported_not_hidden(self):
        # the CFD's kiln gas flow is high for the 4.8 m tube (12.3 m/s against ~10): written in the doc
        self.assertGreater(self.ch["u_kiln"], self.ch["u_max"])
        text = (REPO_ROOT / "geometry" / "kiln" / "kiln_inlet_chamber.md").read_text(encoding="utf-8")
        self.assertIn("10 m/s'yi aşıyor", text)


class TheMealPipesAreTheCalcinersPipeScaledByFluxTest(unittest.TestCase):
    """Meal pipes C1-C5 (user decision, 16 Nov 2026): the calciner's
    literature feed pipe, which carries one string's meal, sets the mass
    flux; every other pipe is sized to it. The flows are the twin's."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.mp = pg.meal_pipes(cls.g)

    def test_the_flows_are_the_twins(self):
        import json

        with open(REPO_ROOT / "tests" / "data" / "twin_state_reference.json", encoding="utf-8") as handle:
            snap = json.load(handle)["snapshot"]
        m = self.g["meal_pipe"]
        self.assertAlmostEqual(pg.v(m["feed_per_string"]) * 2, snap["mass_flow_m_dot_s_preheater"], places=6)
        self.assertAlmostEqual(pg.v(m["c5_meal_per_string"]) * 2, snap["mass_flow_m_dot_s_transition_in"], places=2)

    def test_the_calciners_pipe_is_the_reference(self):
        # C4's meal goes down that very pipe: same flow, same diameter
        self.assertAlmostEqual(self.mp[4]["D"], pg.v(self.g["calciner"]["D_feed"]), places=9)

    def test_every_pipe_carries_the_same_flux(self):
        for s, p in self.mp.items():
            with self.subTest(stage=s):
                self.assertAlmostEqual(p["m"] / (0.25 * math.pi * p["D"] ** 2), p["flux"], places=6)

    def test_c1_has_two_pipes_each_half_the_string(self):
        self.assertEqual(self.mp[1]["count_per_string"], 2)
        self.assertAlmostEqual(2.0 * self.mp[1]["m"], pg.v(self.g["meal_pipe"]["feed_per_string"]), places=9)

    def test_the_slope_is_the_calciners_literature_value(self):
        for p in self.mp.values():
            self.assertEqual(p["slope"], pg.v(self.g["cyclone_domain"]["meal_slope"]))

    def test_the_dust_outlet_flux_is_the_same_meal_through_the_outlet(self):
        for s, p in self.mp.items():
            with self.subTest(stage=s):
                self.assertAlmostEqual(p["flux_dust"], p["m"] / (0.25 * math.pi * p["D_dust"] ** 2), places=6)
                self.assertAlmostEqual(p["dust_over_pipe"], p["flux_dust"] / p["flux"], places=12)

    def test_c1s_outlet_is_loaded_harder_than_its_pipe(self):
        """Known and kept (user decision, 16 Nov 2026): C1's FLS outlet
        carries ~2.25x the pipe's flux; C2-C4's outlets are within 10 %
        of their pipes. A change that moves these is a sizing change."""
        self.assertGreater(self.mp[1]["dust_over_pipe"], 2.0)
        for s in (2, 3, 4):
            with self.subTest(stage=s):
                self.assertLess(abs(self.mp[s]["dust_over_pipe"] - 1.0), 0.10)


class TheBurnerSitsInTheKilnAsTheLiteratureSaysTest(unittest.TestCase):
    """plant_geometry.kiln_burner_placement(): the burner on the kiln's axis,
    parallel to it, its tip 0.25 m inside the kiln (literature; user
    decision, 23 Nov 2026), its castable on past the hood's front wall."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.p, cls.k = pg.kiln_burner_placement(cls.g), pg.kiln(cls.g)

    def test_the_tip_is_inside_the_kiln_on_its_axis(self):
        h = self.g["kiln_hood"]
        tip = self.p["tip"]
        self.assertAlmostEqual(tip[2], self.k["L"] - pg.v(h["burner_insertion"]))
        self.assertAlmostEqual(tip[0], pg.v(h["burner_offset_x"]))
        self.assertAlmostEqual(tip[1], pg.v(h["burner_offset_y"]))
        for key in ("burner_insertion", "burner_offset_x", "burner_offset_y", "burner_tilt_deg"):
            with self.subTest(key):
                self.assertEqual(h[key]["source"], "literature")

    def test_the_rotation_is_proper_and_maps_the_burners_back_out_of_the_kiln(self):
        R = self.p["R"]
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(sum(R[i][k] * R[j][k] for k in range(3)), 1.0 if i == j else 0.0)
        back = self.p["to_kiln"]((0.0, 0.0, -1.0))
        self.assertGreater(back[2], self.p["tip"][2])        # the burner's back runs out toward the hood

    def test_no_bare_steel_in_the_hood(self):
        self.assertGreater(self.p["castable_past_front"], 0.0)
        self.assertGreater(self.p["z_castable_end"], self.p["z_front"])

    def test_the_tip_clears_the_lining(self):
        body = pg.kiln_burner_body(self.g)
        r = math.hypot(self.p["tip"][0], self.p["tip"][1]) + body["R_castable"]
        self.assertLess(r, 0.5 * self.k["D"])


class TheFlameVolumeIsHoodBoreAndPlacedChannelsTest(unittest.TestCase):
    """plant_geometry.kiln_flame(): the flame zone's CFD volume (hood, the
    kiln's bore over the burning zone, the burner's channels placed) and
    its seven boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.f, cls.k, cls.hd = pg.kiln_flame(cls.g), pg.kiln(cls.g), pg.kiln_hood(cls.g)
        cls.faces = {f[0]: f for f in cls.f["faces"]}

    def test_the_seven_boundaries(self):
        self.assertEqual(set(self.faces), {"secondary_air_in", "tertiary_supply_in", "tertiary_air_out",
                                           "kiln_gas_out", "coal_in", "axial_in", "swirl_in"})
        for name, p, n, a, rgb in self.f["faces"]:
            with self.subTest(name):
                self.assertAlmostEqual(math.sqrt(sum(c * c for c in n)), 1.0)
                self.assertGreater(a, 0.0)

    def test_the_inlet_areas_are_the_channel_solids(self):
        ch = pg.kiln_burner(self.g)["groups"]
        for name in ("coal", "axial", "swirl"):
            with self.subTest(name):
                self.assertAlmostEqual(self.faces[f"{name}_in"][3], ch[name]["a_in"])

    def test_the_kiln_outlet_is_the_bore_at_the_burning_zones_start(self):
        _, p, n, a, _ = self.faces["kiln_gas_out"]
        self.assertAlmostEqual(p[2], self.k["L"] - self.k["burning_L"])
        self.assertAlmostEqual(a, math.pi * 0.25 * self.k["D"] ** 2)          # the bore whole: no bed in it
        self.assertEqual(n, (0.0, 0.0, -1.0))

    def test_the_cooler_openings_are_its_two_hood_segments(self):
        co = pg.cooler(self.g)
        for name in ("secondary_air_in", "tertiary_supply_in"):
            with self.subTest(name):
                self.assertAlmostEqual(self.faces[name][3], co["segment_L"] * co["width"])

    def test_the_volume_spans_the_bore_and_the_hood(self):
        x0, y0, z0, x1, y1, z1 = self.f["box"]
        self.assertAlmostEqual(z0, self.f["z_cut"])
        self.assertAlmostEqual(x1 - x0, self.hd["W"])
        self.assertGreater(z1, self.k["L"] + self.hd["depth"] * math.cos(self.f["alpha"]) - 1e-6)


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_flame_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheFlameSolidIsTheSourcesTest(unittest.TestCase):
    """kiln_flame.bas logs the joined body and each boundary face's area."""

    def test_the_build_log(self):
        log = (REPO_ROOT / "geometry" / "output" / "2500" / "kiln_flame_build.log").read_text(encoding="latin-1")
        self.assertTrue(log.startswith("kiln_flame built"), log.splitlines()[0])
        f = pg.kiln_flame(pg.load())
        m = re.search(r"body flame \((\d+) parts\)", log)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), f["groups"]["flame"]["n"])
        for name, p, n, a, rgb in f["faces"]:
            with self.subTest(name):
                m = re.search(rf"boundary {name}: 1 face, ([\d.,]+) m2", log)
                self.assertIsNotNone(m)
                self.assertAlmostEqual(float(m.group(1).replace(",", ".")), a, delta=1e-5 * max(1.0, a))


class TheFlameBoundariesAreTheTwinsAirAndBalanceTest(unittest.TestCase):
    """plant_geometry.kiln_air_split() / kiln_flame_boundaries(): the kiln's
    air split as the twin splits it, one value per flame face, mass in =
    out; the seal's leak enters with the secondary air (user decision,
    23 Nov 2026: no face of its own)."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.sp, cls.fb = pg.kiln_air_split(cls.g), pg.kiln_flame_boundaries(cls.g)

    def test_the_seal_share_is_the_twins(self):
        import yaml
        cfg = yaml.safe_load((REPO_ROOT / "configs" / "twin_cfg.yaml").read_text(encoding="utf-8"))
        self.assertAlmostEqual(pg.v(self.g["kiln_hood"]["seal_air_fraction"]),
                               cfg["burning"]["kiln_seal_air_fraction"])
        self.assertAlmostEqual(pg.v(self.g["kiln_burner"]["primary_air_fraction"]),
                               cfg["burning"]["primary_air_fraction"])

    def test_the_split_adds_up_to_the_kiln_air(self):
        sp = self.sp
        self.assertAlmostEqual(sp["primary"] + sp["seal"] + sp["secondary"], sp["kiln"], places=12)
        ch = pg.kiln_burner(self.g)
        self.assertAlmostEqual(ch["m_axial"] + ch["m_swirl"], sp["primary"], places=12)

    def test_every_face_has_a_value(self):
        faces = {f[0] for f in pg.kiln_flame(self.g)["faces"]}
        self.assertEqual(set(self.fb["bc"]), faces)
        for name, b in self.fb["bc"].items():
            with self.subTest(name):
                self.assertIn(b["kind"], ("mass_flow_inlet", "mass_flow_outlet", "pressure_outlet", "wall"))
                if b["kind"] == "mass_flow_inlet":
                    self.assertGreater(b["m"], 0.0)
                    self.assertGreater(b["T"], 0.0)

    def test_mass_in_is_mass_out(self):
        bc, bal = self.fb["bc"], self.fb["balance"]
        m_in = sum(b["m"] for b in bc.values() if b["kind"] == "mass_flow_inlet")
        m_in += bc["coal_in"]["particles"]["m"]
        self.assertAlmostEqual(m_in, bal["in"], places=9)
        self.assertAlmostEqual(bal["in"], bal["tertiary_out"] + bal["kiln_gas_out"], places=9)
        self.assertAlmostEqual(bc["tertiary_air_out"]["m"], bc["tertiary_supply_in"]["m"], places=12)

    def test_the_mixed_secondary_inlet_holds_the_enthalpy(self):
        b, sp = self.fb["bc"]["secondary_air_in"], self.sp
        self.assertAlmostEqual(b["m"], sp["secondary"] + sp["seal"], places=12)
        T_sec = pg.v(self.g["kiln_hood"]["secondary_air_T"])
        T0 = pg.v(self.g["kiln_burner"]["primary_air_T"])
        self.assertTrue(T0 < b["T"] < T_sec)
        h_mix = sp["secondary"] * pg._air_h(T_sec) + sp["seal"] * pg._air_h(T0)
        self.assertAlmostEqual(b["m"] * pg._air_h(b["T"]), h_mix, delta=1e-6 * abs(h_mix))

    def test_the_air_enthalpy_is_the_shells_cp(self):
        from physics.shell import cp_air
        for T in (300.0, 800.0, 1300.0, 2000.0):
            with self.subTest(T=T):
                dh = (pg._air_h(T + 0.5) - pg._air_h(T - 0.5))
                self.assertAlmostEqual(dh, cp_air(T), delta=1e-3)

    def test_the_hood_still_passes_the_velocity_band(self):
        h = pg.kiln_hood(self.g)
        self.assertAlmostEqual(h["m"], self.sp["secondary"] + self.fb["bc"]["tertiary_supply_in"]["m"])
        self.assertTrue(h["u_min"] <= h["u"] <= h["u_max"], h["u"])


class TheTertiaryOutletIsClearOfTheHoodTest(unittest.TestCase):
    """The tertiary air outlet face sits tertiary_outlet_L_over_D duct
    diameters up the duct, clear of the hood's recirculation (user,
    23 Nov 2026: 3 D)."""

    def test_the_outlet_is_3_D_off_the_roof(self):
        g = pg.load()
        f, hd = pg.kiln_flame(g), pg.kiln_hood(g)
        n = pg.v(g["kiln_hood"]["tertiary_outlet_L_over_D"])
        self.assertAlmostEqual(f["L_ta"], n * 2.0 * f["r_ta"])
        self.assertGreaterEqual(n, 3.0)
        _, p, nrm, a, _ = next(x for x in f["faces"] if x[0] == "tertiary_air_out")
        # the face's height over the kiln axis, along the plant's up
        up = sum((p[i] - (0.0, 0.0, pg.kiln(g)["L"])[i]) * f["U"][i] for i in range(3))
        self.assertAlmostEqual(up, hd["above"] + f["L_ta"])
        self.assertAlmostEqual(f["box"][4], p[1] + f["r_ta"] * abs(f["U"][2]), places=6)


class TheFlameVolumeHoldsTheFlameTest(unittest.TestCase):
    """The flame volume runs at least flame_domain_margin estimated flame
    lengths from the burner tip (CLAUDE.md rule 8: the flame's end is not
    cut off); the estimate is the literature's flame scaled by the kiln D."""

    def test_the_margin(self):
        g = pg.load()
        f, h = pg.kiln_flame(g), g["kiln_hood"]
        est = pg.v(h["flame_L_ref"]) * pg.kiln(g)["D"] / pg.v(h["flame_L_ref_D"])
        self.assertAlmostEqual(f["L_flame_est"], est)
        self.assertGreaterEqual(f["L_tip_to_cut"], pg.v(h["flame_domain_margin"]) * est)
        self.assertEqual(h["flame_L_ref"]["source"], "literature")


class TheClinkerBedIsTheContinuitysTest(unittest.TestCase):
    """plant_geometry.kiln_bed(): the bed's fill is the clinker flow times
    its Sullivan transit over the bulk density (user decision, 23 Nov
    2026), its surface at the dynamic angle of repose; the flame volume
    loses that segment over the burning zone."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.b, cls.k = pg.kiln_bed(cls.g), pg.kiln(cls.g)

    def test_the_transit_is_the_twins(self):
        # configs/twin_cfg.yaml: 3.0 rpm, 3 % give 27.14 min over the 60 m tube
        self.assertAlmostEqual(self.b["tau"] / 60.0, 27.14, places=2)

    def test_the_fill_is_flow_times_time(self):
        k, b = self.g["kiln"], self.b
        held = pg.v(k["clinker_flow"]) * b["tau_bz"] / pg.v(k["clinker_bulk_density"])
        self.assertAlmostEqual(b["A_bed"] * self.k["burning_L"], held, places=9)
        self.assertAlmostEqual((b["phi"] - math.sin(b["phi"])) / (2.0 * math.pi), b["fill"], places=9)

    def test_the_surface_is_at_the_repose_angle(self):
        n = self.b["n"]
        self.assertAlmostEqual(math.degrees(math.acos(n[1])), pg.v(self.g["kiln"]["repose_angle"]))
        R = 0.5 * self.k["D"]
        self.assertAlmostEqual(self.b["c"] ** 2 + self.b["d_c"] ** 2, R * R)

    def test_the_bed_is_a_wall_strip_not_material(self):
        # user decision, 23 Nov 2026: no bed in the volume; the strip of the
        # bore's wall under its chord is a CFD region
        f = pg.kiln_flame(self.g)
        self.assertNotIn("bed", {x[0] for x in f["faces"]})
        self.assertFalse(any("clinker_bed" in b["name"] for b in f["bodies"]))
        st, R = f["bed_strip"], 0.5 * self.k["D"]
        self.assertAlmostEqual(st["d_c"] ** 2 + st["c"] ** 2, R * R)
        self.assertAlmostEqual(st["arc"], 2.0 * R * math.asin(self.b["c"] / R))
        self.assertAlmostEqual(st["area"], st["arc"] * self.k["burning_L"])
        # the strip's arc is the bed's: its segment area is the fill
        phi = st["arc"] / R
        self.assertAlmostEqual(0.5 * R * R * (phi - math.sin(phi)), self.b["A_bed"], places=9)


class TheFuelFinenessIsSourcedTest(unittest.TestCase):
    """The coal inlet carries a literature Rosin-Rammler distribution (the
    twin burns petcoke: Alcaide-Moreno et al., ECOS 2023, Table 5)."""

    def test_the_distribution(self):
        g = pg.load()
        size = pg.kiln_flame_boundaries(g)["bc"]["coal_in"]["particles"]["size"]
        self.assertEqual(size["dist"], "rosin_rammler")
        self.assertTrue(size["d_min"] < size["d_mean"] < size["d_max"])
        self.assertGreater(size["n"], 0.0)
        for k in ("fuel_rr_mean", "fuel_rr_n", "fuel_d_min", "fuel_d_max"):
            with self.subTest(k):
                self.assertEqual(g["kiln_burner"][k]["source"], "literature")


class TheCoolersMechanicalPartsAreTheSourcesTest(unittest.TestCase):
    """cooler_body(): the cooler's mechanical envelopes (user, 23 Nov 2026;
    not a CFD input): one fan and compartment per segment, Cross-Bar lanes
    and cylinders, the undergrate on the plant's ground."""

    def setUp(self):
        self.g = pg.load()
        self.b, self.co = pg.cooler_body(self.g), pg.cooler(self.g)

    def test_one_fan_and_compartment_per_segment(self):
        n = self.co["segments"]
        names = [q["name"] for q in self.b["bodies"]]
        self.assertEqual(len(self.b["fans"]), n)
        self.assertEqual(sum(nm.startswith("fan_volute_") for nm in names), n)
        self.assertEqual(sum(nm.startswith("partition_") for nm in names), n)      # the last: the chute's back wall

    def test_the_fans_carry_the_segments_air_at_the_sourced_pressures(self):
        f, bd = self.b["fans"], self.g["cooler_body"]
        self.assertAlmostEqual(sum(q["m"] for q in f), pg.cooler_air(self.g)["total"], places=9)
        self.assertAlmostEqual(f[0]["dp"], pg.v(bd["fan_dp_first"]))
        self.assertAlmostEqual(f[-1]["dp"], pg.v(bd["fan_dp_last"]))
        for q in f:
            self.assertLess(q["D1"], q["D2"])
            self.assertAlmostEqual(q["P"], q["q"] * q["dp"] / pg.v(bd["fan_efficiency"]), places=6)

    def test_lanes_are_cross_bar_frames_and_no_cylinder_in_the_first_chamber(self):
        self.assertEqual(self.b["lanes"], round(self.co["width"] / 0.6))
        cyl = [q for q in self.b["bodies"] if q["name"].startswith("cylinder_")]
        self.assertEqual(len(cyl), self.b["lanes"] * int(pg.v(self.g["cooler_body"]["cylinders_per_lane"])))
        seg = self.co["segment_L"]
        for q in cyl:
            self.assertGreater(q["box"][0], seg)          # past the first chamber

    def test_the_undergrate_stands_on_the_ground_under_the_grate(self):
        self.assertGreater(self.b["h_undergrate"], 1.0)
        slab = next(q for q in self.b["bodies"] if q["name"] == "ground_slab")
        self.assertAlmostEqual(slab["box"][5], self.b["z_ground"], places=12)
        for q in self.b["bodies"]:
            if not q["name"].startswith("ground_slab"):
                self.assertGreaterEqual(q["box"][2], self.b["z_ground"] - 1e-9, q["name"])

    def test_the_slab_is_open_under_the_chute(self):
        L, Lt = self.co["length"], pg.cooler_cfd(self.g)["length_total"]
        for q in self.b["bodies"]:
            if q["name"].startswith("ground_slab"):
                x0, y0, _, x1, y1, _ = q["box"]
                under = x0 < Lt - 1e-9 and x1 > L + 1e-9 and y0 < -1e-9 and y1 > 1e-9
                self.assertFalse(under, q["name"])

    def test_no_part_enters_the_cfd_volume(self):
        w2, H = 0.5 * self.co["width"], self.co["casing_height"]
        L = pg.cooler_cfd(self.g)["length_total"]
        for q in self.b["bodies"]:
            x0, y0, z0, x1, y1, z1 = q["box"]
            inside = x0 < L - 1e-9 and x1 > 1e-9 and y0 < w2 - 1e-9 and y1 > -w2 + 1e-9 and z0 < H - 1e-9 and z1 > 1e-9
            self.assertFalse(inside, q["name"])

    def test_the_solid_is_the_sources(self):
        log = REPO_ROOT / "geometry" / "output" / "2500" / "cooler_body_build.log"
        if not log.is_file():
            self.skipTest("no cooler_body log")
        text = log.read_text(encoding="latin-1")
        self.assertIn("cooler_body built, verified and exported", text)
        self.assertIn(f"{len(self.b['bodies'])} bodies, each its volume and extent", text)


class TheTowerStandsOnOneGasPathTest(unittest.TestCase):
    """tower_placement() (user, 23 Nov 2026; option A: the CFD solids as
    they are): each riser on the axis of the cyclone below, R1 on C2's
    outlet face, the overlaps and the one gap listed."""

    def setUp(self):
        self.g = pg.load()
        self.t = pg.tower_placement(self.g)

    def test_twelve_parts_two_strings(self):
        names = [p["name"] for p in self.t["parts"]]
        self.assertEqual(len(names), 14)
        self.assertIn("kiln_outlet", names)
        self.assertIn("meal_pipes", names)
        for k in (1, 2):
            for n in ("C5", "C4", "C3", "C2", "C1_twin"):
                self.assertIn(f"{n}_{k}", names)

    def test_every_riser_stands_on_the_cyclone_below(self):
        for j in self.t["joints"]:
            if j["kind"] == "overlap":
                for a, b in zip(j["riser_at"], j["axis_below"]):
                    self.assertAlmostEqual(a, b, places=6, msg=j["what"])
                self.assertGreater(j["L"], 0.0, j["what"])            # the two domains share a piece of riser

    def test_r1_sits_on_c2s_outlet_face(self):
        log = REPO_ROOT / "geometry" / "output" / "2500" / "c1_twin_build.log"
        if not log.is_file():
            self.skipTest("no c1_twin log")
        z_floor = float(re.search(r"R1 stub: D [\d.]+, z (-?[\d.]+)", log.read_text(encoding="latin-1")).group(1))
        lay, c2 = pg.layout(self.g), pg.cyclone(self.g, "C2")
        top = lay["z_dust"][2] + c2["height"] + c2["outlet_rise"]
        self.assertAlmostEqual(lay["z_dust"][1] + z_floor, top, places=3)

    def test_the_gooseneck_arm_meets_c5s_inlet_level(self):
        for j in self.t["joints"]:
            if j["what"].startswith("gooseneck"):
                # the arm's axis r_leg under C5's roof, the duct's H_inlet / 2: 4 mm apart (D_leg 3.50 vs H 3.508)
                self.assertAlmostEqual(j["z"][0], j["z"][1], delta=0.01)
                self.assertAlmostEqual(j["L"], 0.0, places=9)              # C5_plant's duct on the arm's face

    def test_string_2_is_string_1s_mirror(self):
        parts = {p["name"]: p for p in self.t["parts"]}
        for n in ("C5", "C4", "C3", "C2", "C1_twin"):
            a, b = parts[f"{n}_1"], parts[f"{n}_2"]
            # a solid and its mirror (C5: string 1 the mirrored solid, 24 Nov 2026)
            self.assertEqual({a["file"], b["file"]}, {a["file"].replace("_m.SLDPRT", ".SLDPRT"),
                                                      a["file"].replace("_m.SLDPRT", ".SLDPRT").replace(".SLDPRT", "_m.SLDPRT")})
            self.assertEqual(b["o"], (-a["o"][0], a["o"][1], a["o"][2]))
            # a mirrored part's point (-x, y, z) lands on the mirror of the original's
            for p in ((1.0, 2.0, 3.0), (-4.0, 0.5, 7.0)):
                pa = tuple(a["o"][k] + sum(p[i] * a["R"][i][k] for i in range(3)) for k in range(3))
                q = (-p[0], p[1], p[2])
                pb = tuple(b["o"][k] + sum(q[i] * b["R"][i][k] for i in range(3)) for k in range(3))
                for u, v in zip(pb, (-pa[0], pa[1], pa[2])):
                    self.assertAlmostEqual(u, v, places=9)

    def test_the_mirrored_solids_are_built(self):
        log = REPO_ROOT / "geometry" / "output" / "2500" / "plant_assembly_build.log"
        for n in ("C4", "C5_plant", "C1_twin"):
            if not (REPO_ROOT / "geometry" / "output" / "2500" / f"{n}_m.SLDPRT").is_file():
                self.skipTest("mirrored solids not built")
        self.assertTrue(log.is_file())

    def test_the_rotations_are_proper(self):
        for p in self.t["parts"]:
            R = p["R"]
            det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1]) - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
                   + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
            self.assertAlmostEqual(det, 1.0, places=9, msg=p["name"])

    def test_the_assembly_holds_every_part(self):
        log = REPO_ROOT / "geometry" / "output" / "2500" / "plant_assembly_build.log"
        if not log.is_file():
            self.skipTest("no plant_assembly log")
        text = log.read_text(encoding="latin-1")
        self.assertIn("plant_assembly built, verified and saved", text)
        self.assertEqual(text.count("placed "), len(self.t["parts"]))

    def test_the_kiln_comes_out_of_the_chambers_mouth(self):
        j = next(j for j in self.t["joints"] if j["what"].startswith("kiln_inlet_chamber"))
        self.assertAlmostEqual(j["L"], 0.0, places=6)
        # the kiln's hood end where layout() has it (its x is the plant's -y here)
        lay, kl = pg.layout(self.g), pg.kiln(self.g)
        k = next(p for p in self.t["parts"] if p["name"] == "kiln_outlet")
        end = tuple(k["o"][i] + kl["L"] * k["R"][2][i] for i in range(3))
        self.assertAlmostEqual(-end[1], lay["kiln_end"][0], places=6)
        self.assertAlmostEqual(end[0], 0.0, places=9)
        self.assertAlmostEqual(end[2], lay["kiln_end"][1], places=6)


class TheMealPipesFallInTheTowerTest(unittest.TestCase):
    """meal_routes() (user, 24 Nov 2026: "farin borularını bağlayalım";
    "kuleyi yaklaştır": the tower beside the calciner so C4's and C5's
    pipes fall at the meal slope)."""

    def setUp(self):
        self.g = pg.load()
        self.r = pg.meal_routes(self.g)
        self.tl = pg.tower_layout(self.g)

    def test_every_run_falls_steep_enough(self):
        lo = pg.v(self.g["meal_route"]["min_slope"])
        for q in self.r:
            for a, b in zip(q["pts"], q["pts"][1:]):
                self.assertLess(b[2], a[2], q["name"])                  # downhill all the way
            self.assertGreaterEqual(min(q["slopes"]), lo - 1e-9, q["name"])
        # C4 and C5: were ~27 and ~30 deg with the tower past the gooseneck's arms
        s = {q["name"]: q["slopes"][-1] for q in self.r if q["string"] == 1}
        self.assertGreater(s["C4"], 60.0)
        self.assertGreater(s["C5"], 55.0)

    def test_six_pipes_a_string_mirrored(self):
        one = [q for q in self.r if q["string"] == 1]
        two = [q for q in self.r if q["string"] == 2]
        self.assertEqual(sorted(q["name"] for q in one), ["C1_in", "C1_out", "C2", "C3", "C4", "C5"])
        for a, b in zip(one, two):
            for p, m in zip(a["pts"], b["pts"]):
                self.assertEqual(m, (-p[0], p[1], p[2]))

    def test_each_pipe_starts_at_its_dust_outlet(self):
        lay = pg.layout(self.g)
        for q in self.r:
            if q["string"] == 1:
                self.assertAlmostEqual(q["pts"][0][2], lay["z_dust"][q["stage"]], places=9, msg=q["name"])
                if q["stage"] > 1:
                    self.assertEqual(q["pts"][0][:2], self.tl["cols"][q["stage"]])

    def test_riser_pipes_drop_onto_a_dispersion_box_over_the_roof_below(self):
        lay = pg.layout(self.g)
        mr = self.g["meal_route"]
        into = {"C1_in": 3, "C1_out": 3, "C2": 4, "C3": 5}
        for q in self.r:
            if q["string"] == 1 and q["name"] in into:
                b = into[q["name"]]
                box = q["entry"]["box"]
                # the box's mid height is entry_up over the roof below, the last run vertical onto its top
                self.assertAlmostEqual(box["z_centre"], lay["z_roof"][b] + pg.v(mr["entry_up"]), places=9, msg=q["name"])
                self.assertAlmostEqual(q["pts"][-1][2], box["z_top"] - 0.1, places=9, msg=q["name"])
                self.assertEqual(q["pts"][-1][:2], q["pts"][-2][:2], q["name"])
                A = self.tl["cols"][b]
                self.assertAlmostEqual(math.dist(q["pts"][-1][:2], A), box["rho_pipe"], places=9, msg=q["name"])
                self.assertAlmostEqual(box["width"], pg.v(self.g["dispersion_box"]["width_over_D_feed"]) * q["D"], places=9, msg=q["name"])
            if q["name"] in ("C2", "C3"):
                self.assertGreater(q["riser_clearance"], 0.2, q["name"])

    def test_identical_entries_share_one_box_design(self):
        """C2's and C3's pipes are one design: the same cube and pipe whichever
        riser (the box's stand-off from the riser's axis follows that riser's
        radius, so only the width and the rise are compared)."""
        one = {q["name"]: q for q in self.r if q["string"] == 1}
        for k in ("width", "pipe_rise", "D"):
            self.assertAlmostEqual(one["C2"]["entry"]["box"][k], one["C3"]["entry"]["box"][k], places=9, msg=k)
        self.assertEqual(len(pg.meal_dispersion_boxes(self.g)), 10)            # C1 x2, C2, C3, C5 a string, two strings

    def test_c4_and_c5_end_in_their_targets(self):
        lay, sec = pg.layout(self.g), pg.chamber_section(self.g)
        meal = pg.calciner_inlets(self.g)["meal"]
        one = {q["name"]: q for q in self.r if q["string"] == 1}
        e = (meal["end"][0], 0.0, lay["z_calciner_throat"] + meal["end"][1])
        # C4 comes down vertically 0.1 m into the calciner's box pipe (its top face is `e`)
        self.assertAlmostEqual(math.dist(one["C4"]["pts"][-1], e), 0.1, places=9)
        self.assertEqual(one["C4"]["pts"][-1][:2], e[:2])
        # C5 onto a dispersion box on the calciner's throat wall (user, 28 Nov 2026), at mid height
        cal = pg.calciner(self.g)
        q = one["C5"]
        box = q["entry"]["box"]
        z0 = lay["z_calciner_throat"]
        self.assertAlmostEqual(box["z_centre"], z0 + 0.5 * cal["z_throat_top"], places=9)
        self.assertAlmostEqual(math.hypot(*q["pts"][-1][:2]), box["rho_pipe"], places=9)
        self.assertAlmostEqual(q["pts"][-1][2], box["z_top"] - 0.1, places=9)
        self.assertGreater(box["z_bottom"], z0)
        self.assertLess(box["z_top"], z0 + cal["z_throat_top"])                    # the box stays in the straight throat

    def test_the_straight_runs_clear_the_calciner_and_c5(self):
        """the C4 and C5 runs, sampled, against the calciner's cylinder and
        cone and C5's barrel and cone (radii by height; the walls' lining
        not modelled, so the bores 0.3 m apart at least)"""
        lay, cal, c5 = pg.layout(self.g), pg.calciner(self.g), pg.cyclone(self.g, "C5")
        z0 = lay["z_calciner_throat"]
        R, r_t = cal["R"], 0.5 * pg.chamber_section(self.g)["D_throat"]
        z_ct = z0 + cal["z_cone_top"]

        def r_cal(z):
            if z < z0:
                return None
            return R if z >= z_ct else r_t + (R - r_t) * (z - z0) / (z_ct - z0)

        A5 = self.tl["cols"][5]
        z5 = lay["z_dust"][5]
        one = {q["name"]: q for q in self.r if q["string"] == 1}
        for nm in ("C4", "C5"):
            q = one[nm]
            a, b = q["pts"][1], q["pts"][2]
            r = 0.5 * q["D"]
            n = math.dist(a, b)
            for i in range(1, 100):
                t = i / 100.0
                p = tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
                # the joint: C4 the last 2 m (the calciner's meal pipe), C5 the
                # last 4 m (it comes down along the cone into the throat under it)
                if (1.0 - t) * n < (2.0 if nm == "C4" else 4.0):
                    break
                rc = r_cal(p[2])
                if rc is not None:
                    self.assertGreater(math.hypot(p[0], p[1]) - r - rc, 0.3, f"{nm} at {p}")
                if nm == "C4" and z5 <= p[2] <= z5 + c5["height"]:
                    self.assertGreater(math.dist(p[:2], A5) - r - 0.5 * c5["D_barrel"], 0.3, f"{nm} at {p}")
