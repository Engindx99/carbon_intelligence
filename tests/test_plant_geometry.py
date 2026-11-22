"""geometry/plant_geometry.{yaml,py}: the plant's one geometry source.

Step 1 of the single-source plan: the source holds today's primary
dimensions and the module derives today's documented volumes, areas
and heights from them. Until the macros' Const blocks are generated
from the source (step 4), the macros are held to it here.
"""

import math
import re
import unittest

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
        self.near(gn["level"], 4.950, 0.001)
        self.near(gn["y_off"], 12.135, 0.001)
        self.near(gn["crown"], 39.105, 0.001)
        self.near(gn["channel"], 7.425, 0.001)
        self.near(gn["z_split"], 25.706, 0.001)
        self.near(gn["z_end"], 23.522, 0.001)
        self.near(gn["arm_piece"], 4.366, 0.001)
        self.near(gn["x_bend"], 3.781, 0.001)
        self.near(gn["x_leg"], 10.781, 0.001)
        self.near(gn["volume"], 631.93, 0.01)
        self.near(gn["wall_area"], 596.32, 0.01)

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
        self.near(k["volume"], 1339.07, 0.01)
        self.near(k["wall_area"], 1115.89, 0.01)
        self.near(k["burning_L"], 43.17, 1e-9)
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


class DispersionPlateGeometryTest(unittest.TestCase):
    """plant_geometry.calciner_dispersion_plate: the arc meets its ends,
    the plate clears the meal pipe, the hole, the tertiary air duct and
    the wall at its edge, and its in-vessel volume is bounded by its own."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.dp = pg.calciner_dispersion_plate(cls.g)
        cls.cal = pg.calciner(cls.g)
        cls.meal = pg.calciner_inlets(cls.g)["meal"]

    def test_the_arc_runs_from_the_pipe_slope_to_the_exit(self):
        dp, R = self.dp, self.cal["R"]
        cx, cz = dp["centre"]
        for p, rad in ((dp["A"], dp["R_arc"]), (dp["E"], dp["R_arc"]),
                       (dp["A_low"], dp["R_arc"] + dp["thickness"]), (dp["E_low"], dp["R_arc"] + dp["thickness"])):
            self.assertAlmostEqual(math.hypot(p[0] - cx, p[1] - cz), rad, places=12)
        self.assertAlmostEqual(dp["A"][0], R, places=12)
        self.assertAlmostEqual(R - dp["E"][0], dp["protrusion"], places=12)
        # tangent at A along the pipe (down-inward at the slope), at E at the exit angle
        ta = (dp["A"][1] - cz, -(dp["A"][0] - cx))   # radius rotated: the inward travel direction
        self.assertAlmostEqual(math.degrees(math.atan2(ta[1], -ta[0])), -self.meal["slope"], places=9)
        te = (dp["E"][1] - cz, -(dp["E"][0] - cx))
        self.assertAlmostEqual(math.degrees(math.atan2(te[1], -te[0])), dp["exit_angle"], places=9)

    def test_it_clears_the_pipe_the_duct_and_the_wall(self):
        dp, R = self.dp, self.cal["R"]
        self.assertGreater(dp["pipe_clearance"], 0.0)
        self.assertLess(dp["A"][1], self.meal["hole_bottom"])
        self.assertGreater(dp["z_low"], pg.calciner_inlets(self.g)["tertiary_air"]["top"])
        for p in (dp["E"], dp["E_low"]):
            self.assertLess(math.hypot(p[0], 0.5 * dp["width"]), R)
        # the tail's end lies outside the vessel, so the plate's back end is in the wall
        self.assertGreater(min(dp["T"][0], dp["T_low"][0]), R)

    def test_the_volumes(self):
        dp = self.dp
        self.assertAlmostEqual(dp["volume"], dp["profile_area"] * dp["width"], places=12)
        self.assertGreater(dp["inside_vessel"], 0.5 * dp["volume"])
        self.assertLess(dp["inside_vessel"], dp["volume"])


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
        y_ta, z_ta, x_ta, v_ta = self.num(r"tertiary air: duct D # m, tangential, axis at y = # m, z = # m, "
                                          r"face at x = # m, # m3")[1:]
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
            (y_ta, ta["y"], "tertiary air y"),
            (z_ta, ta["z"], "tertiary air z"),
            (x_ta, ta["x_end"], "tertiary air face x"),
            (v_ta, ta["volume"], "tertiary air volume"),
            (self.num(r"meal feed: 2 pipes D # m at # deg, axes meet the wall at z = # m")[2],
             meal["z_wall"], "meal at the wall"),
            (self.num(r"meal feed: .*?end faces centred \(\+-#, 0, #\), # m3")[0], meal["end"][0], "meal end x"),
            (self.num(r"meal feed: .*?end faces centred \(\+-#, 0, #\), # m3")[1], meal["end"][1], "meal end z"),
            (self.num(r"meal feed: .*?end faces centred \(\+-#, 0, #\), # m3")[2], meal["volume"], "meal volume"),
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
                # themselves (calciner.bas' ADD_NOISE floor, 5e-6 of the body): the fuel pipe
                # read 1.5, 2.9 and 8 % off on three builds
                self.assertAlmostEqual(got, dv, delta=1e-2 * dv + 5e-6 * steps["1 "] * 1.6)

    def test_the_dispersion_plates(self):
        """Stages 8a / 8b: each plate body to the closed form (0.1 %), the
        fluid it removes to plant_geometry's integral (the ADD_NOISE floor),
        the body after it to the running total."""
        if "dispersion plate" not in self.log:
            self.skipTest("the build log predates the dispersion plates")
        dp = pg.calciner_dispersion_plate(self.g)
        for tag in ("8a", "8b"):
            with self.subTest(stage=tag):
                got, want = self.num(rf"stage {tag}[^:\n]*: plate body # m3 \(expected #\)")
                self.assertAlmostEqual(want, dp["volume"], delta=1e-5)
                self.assertAlmostEqual(got, dp["volume"], delta=1e-3 * dp["volume"])
                got, want = self.num(rf"stage {tag}[^:\n]*: removed # m3 of fluid \(expected #\)")
                self.assertAlmostEqual(want, dp["inside_vessel"], delta=1e-5)
                self.assertAlmostEqual(got, dp["inside_vessel"], delta=1e-2 * dp["inside_vessel"] + 5e-6 * 1690.0 * 1.6)

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
                # the elbow (22 Nov 2026): a mitre on the riser's cut at
                # riser_cut_deg, then a tapering bend over the rest of 90 deg,
                # its centreline radius run / cos(cut), riser_bend_R_over_H x H
                # at least; the cut's centre H/2 + R (1 - sin) under the roof
                c_k = pg.cyclone(self.g, f"C{k}")
                a = 0.5 * ri["D"]
                bt = math.radians(pg.v(d["riser_cut_deg"]))
                self.assertGreaterEqual(ri["bend_R"], pg.v(d["riser_bend_R_over_H"]) * c_k["H_inlet"] - 1e-9)
                self.assertAlmostEqual(ri["bend_R"] * math.cos(bt), ri["run"], places=12)
                self.assertGreater(ri["bend_R_inner"], 0.0)
                self.assertAlmostEqual(ri["drop_mid"], 0.5 * c_k["H_inlet"] + ri["bend_R"] * (1.0 - math.sin(bt)),
                                       places=12)
                self.assertAlmostEqual(ri["drop"], ri["drop_mid"] + a * math.tan(bt), places=12)
                self.assertAlmostEqual(ri["drop_high"], ri["drop_mid"] - a * math.tan(bt), places=12)
                self.assertAlmostEqual(ri["start_H"], ri["D"] / math.cos(bt), places=12)
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
    """kiln.bas builds a plain cylinder of the published D and L; its
    log (decimal comma or point) carries the volume, the end faces and
    the slope it does not build in, held here to plant_geometry.kiln."""

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
        d, length, slope, vol = self.num(r"kiln: D # m, L # m, slope # % \(installation, not built into the solid\), volume # m3")
        self.assertAlmostEqual(d, self.k["D"], places=5)
        self.assertAlmostEqual(length, self.k["L"], places=5)
        self.assertAlmostEqual(slope, self.k["slope"], places=5)
        self.assertAlmostEqual(vol, self.k["volume"], delta=1e-6 * self.k["volume"])

    def test_the_zones_are_the_sources(self):
        tr, burn = self.num(r"transition # m from the back end, burning # m")
        self.assertAlmostEqual(tr, self.k["transition_L"], places=5)
        self.assertAlmostEqual(burn, self.k["burning_L"], places=5)

    def test_the_solid_is_the_tube(self):
        vol = self.num(r"kiln volume # m3")[0]
        self.assertAlmostEqual(vol, self.k["volume"], delta=1e-3 * self.k["volume"])
        zmin, zmax = self.num(r"extent: x [-\d.,]+ \.\. [-\d.,]+, y [-\d.,]+ \.\. [-\d.,]+, z # \.\. # m")
        self.assertAlmostEqual(zmin, 0.0, places=2)
        self.assertAlmostEqual(zmax, self.k["L"], places=2)

    def test_the_two_ends_are_the_boundaries(self):
        area = math.pi * (0.5 * self.k["D"]) ** 2
        for name in ("kiln_back", "kiln_hood"):
            with self.subTest(name):
                self.assertAlmostEqual(self.num(rf"boundary {name}: # m2")[0], area, delta=2e-3 * area)
        self.assertAlmostEqual(self.num(r"boundary wall: \d+ faces, # m2")[0], self.k["wall_area"],
                               delta=2e-3 * self.k["wall_area"])


@unittest.skipUnless(
    (REPO_ROOT / "geometry" / "output" / "2500" / "cooler_build.log").is_file(),
    "no SolidWorks build log here",
)
class TheCoolerSolidIsTheSourcesTest(unittest.TestCase):
    """cooler.bas builds the box of cooler.md; its log carries the size,
    the floor's strips, the hood opening and the wall, held here to
    plant_geometry.cooler."""

    @classmethod
    def setUpClass(cls):
        cls.log = (REPO_ROOT / "geometry" / "output" / "2500" / "cooler_build.log").read_text(encoding="latin-1")
        cls.c = pg.cooler(pg.load())

    def num(self, pattern):
        m = re.search(pattern.replace("#", r"(-?[\d.,]+)"), self.log)
        self.assertIsNotNone(m, pattern)
        return [float(x.replace(",", ".").rstrip(".")) for x in m.groups()]

    def test_the_build_succeeded(self):
        self.assertTrue(self.log.startswith("cooler built"), self.log.splitlines()[0])
        self.assertIn("closed manifold solid", self.log)

    def test_the_box_is_the_sources(self):
        w, length, h, vol = self.num(r"cooler: # m wide, # m long, # m high, volume # m3")
        self.assertAlmostEqual(w, self.c["width"], places=5)
        self.assertAlmostEqual(length, self.c["length"], places=5)
        self.assertAlmostEqual(h, self.c["casing_height"], places=5)
        self.assertAlmostEqual(vol, self.c["box_volume"], delta=1e-6 * self.c["box_volume"])
        got = self.num(r"cooler volume # m3")[0]
        self.assertAlmostEqual(got, self.c["box_volume"], delta=1e-3 * self.c["box_volume"])

    def test_the_zones_are_the_sources(self):
        n, seg, nh, hood = self.num(r"cooler: # segments of # m \(grate_air_1 \.\. \d+ from the hot end\), hood opening # segments, x 0 \.\. # m")
        self.assertEqual(int(n), self.c["segments"])
        self.assertAlmostEqual(seg, self.c["segment_L"], places=5)
        self.assertEqual(int(nh), self.c["hood_segments"])
        self.assertAlmostEqual(hood, self.c["hood_L"], places=5)

    def test_every_strip_and_the_hood_are_one_face(self):
        for i in range(1, self.c["segments"] + 1):
            with self.subTest(i):
                self.assertAlmostEqual(self.num(rf"boundary grate_air_{i}: # m2")[0], self.c["segment_area"],
                                       delta=2e-3 * self.c["segment_area"])
        self.assertAlmostEqual(self.num(r"boundary hood_opening: # m2")[0], self.c["hood_area"],
                               delta=2e-3 * self.c["hood_area"])
        self.assertAlmostEqual(self.num(r"boundary wall: \d+ faces, # m2")[0], self.c["wall_area"],
                               delta=2e-3 * self.c["wall_area"])


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
    """The JETFLEX burner (kiln/kiln_burner.md) takes the twin's kiln
    firing; the jet follows from FLSmidth's N/MW."""

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

    def test_the_jet_follows_from_the_momentum(self):
        b = self.b
        self.assertAlmostEqual(b["u_jet"] * b["m_pa"], b["momentum_N"], places=6)
        self.assertAlmostEqual(b["rho_pa"] * b["u_jet"] * b["jet_area"], b["m_pa"], places=9)
        self.assertAlmostEqual(b["momentum_N"] / b["thermal_MW"], pg.v(self.g["kiln_burner"]["momentum_per_MW"]), places=9)

    def test_it_is_inside_the_jetflex_range(self):
        # 10-250 MW, 7-11 N/MW (FLSmidth)
        self.assertTrue(10.0 <= self.b["thermal_MW"] <= 250.0)
        self.assertTrue(7.0 <= self.b["momentum_N"] / self.b["thermal_MW"] <= 11.0)


class TheKilnHoodAndChamberPassTheVelocityChecksTest(unittest.TestCase):
    """Hood and inlet chamber have no published size (user decision,
    16 Nov 2026: size by gas velocity): the layout square round the kiln
    stays because it passes the literature's velocities."""

    @classmethod
    def setUpClass(cls):
        cls.g = pg.load()
        cls.hood, cls.ch = pg.kiln_hood(cls.g), pg.kiln_inlet_chamber(cls.g)

    def test_the_hood_air_is_inside_the_literatures_range(self):
        h = self.hood
        self.assertTrue(h["u_min"] <= h["u"] <= h["u_max"], h["u"])
        self.assertTrue(h["u_min"] <= h["u_hot"] <= h["u_max"], h["u_hot"])      # the hotter secondary air too
        self.assertGreaterEqual(h["side"], h["side_min"])

    def test_the_chamber_gas_is_under_the_limit_and_above_the_updraft_minimum(self):
        c = self.ch
        self.assertLessEqual(c["u_chamber"], c["u_max"])
        self.assertGreaterEqual(c["u_chamber"], 4.0)
        self.assertGreaterEqual(c["side"], c["side_min"])

    def test_the_square_is_the_layouts_and_a_model_value(self):
        a = pg.layout(self.g)["a_chamber"]
        self.assertAlmostEqual(self.hood["side"], 2.0 * a)
        self.assertAlmostEqual(self.ch["side"], 2.0 * a)
        self.assertEqual(self.g["layout"]["chamber_margin"]["source"], "model")

    def test_the_chamber_is_the_layouts_square_with_a_flat_roof(self):
        c, L = self.ch, pg.layout(self.g)
        self.assertAlmostEqual(c["height"], 2.0 * L["a_chamber"])
        self.assertAlmostEqual(L["z_calciner_throat"] - L["z_chamber_floor"], c["height"])   # the throat in the roof
        self.assertLess(c["D_throat"], c["side"])

    def test_the_floor_is_one_ramp_across_the_plan_no_pit(self):
        c, L = self.ch, pg.layout(self.g)
        kl = pg.kiln(self.g)
        clear = self.g["kiln_inlet_chamber"]["mouth_clearance"]["value"]
        self.assertEqual(self.g["kiln_inlet_chamber"]["mouth_clearance"]["source"], "model")
        self.assertAlmostEqual(c["ramp_run"], 2.0 * L["a_chamber"])                 # the whole plan: nothing flat behind it
        self.assertAlmostEqual(c["h_lip"], L["a_chamber"] - 0.5 * kl["D"] - clear)  # clear of the mouth's bottom
        self.assertGreater(c["h_lip"], 0.0)
        self.assertAlmostEqual(c["ramp_rise"], c["height"] - c["h_lip"])            # up to the far top corner
        self.assertAlmostEqual(math.tan(math.radians(c["ramp_slope"])), c["ramp_rise"] / c["ramp_run"])
        self.assertGreaterEqual(c["ramp_slope"], 39.0)                              # raw meal's angle of repose is 40-45 deg
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
