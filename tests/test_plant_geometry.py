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
            ("C1", 124.54, 139.7, 11.44),
            ("C2", 283.2, 226.1, 13.60),
            ("C3", 283.2, 226.1, 13.60),
            ("C4", 283.2, 226.1, 13.60),
            ("C5", 311.0, 240.7, 14.03),
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
        self.assertAlmostEqual(pg.v(self.g["risers"]["R1"]["D"]), self.cc["D_RISER_SRC"], delta=TOL)

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
            ("column_offset", "ZIG_DX"), ("c1_twin_gap", "C1_TWIN_GAP"),
            ("r1_up_min", "R1_UP_MIN"), ("r1_leg_on", "R1_LEG_ON"), ("cooler_drop", "COOLER_DROP"),
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

    def test_r2_r4_are_the_outlet_pipes(self):
        for k in (2, 3, 4):
            r = pg.stage_riser(self.g, k)
            c = pg.cyclone(self.g, f"C{k + 1}")
            with self.subTest(riser=k):
                self.assertTrue(all(p["D"] == c["D_vortex"] for p in r["parts"]))
                self.assertAlmostEqual(r["parts"][0]["length"], c["outlet_rise"], places=12)
                self.assertGreater(r["parts"][2]["length"], c["outlet_run"])   # past the CFD face

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
        c, s = pg.cyclone(self.g, "C1"), pg.cyclone_slot_inlet(self.g, "C1")
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
