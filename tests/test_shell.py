"""
Faz 6 shell-loss closure tests.

Same contract as tests/test_kiln_closures.py: the physics is stated
INDEPENDENTLY here -- analytic resistances, tabulated air properties,
the Churchill & Chu correlation written out by hand, and the surface
energy balance itself -- and physics/shell.py has to reproduce it.
Nothing below imports a number from the module it is testing.
"""

import unittest

import numpy as np

from physics.physics import sigma
from physics.shell import (
    DEFAULT_WALL_STACKS,
    RA_HORIZONTAL_LIMIT,
    WallLayer,
    WallStack,
    air_film_properties,
    cp_air,
    loss_conductance,
    natural_convection_coefficient,
    radiative_coefficient,
    rayleigh_number,
    shell_closure,
    shell_temperature_from_resistance,
    wall_stack,
)


def single_layer(thickness, conductivity, emissivity=0.8,
                 orientation="horizontal"):

    return WallStack(
        zone="test",
        layers=[WallLayer("test", thickness, conductivity)],
        emissivity=emissivity,
        orientation=orientation,
    )


class AirPropertyTest(unittest.TestCase):
    """
    Against tabulated dry air at 1 atm (Incropera, Table A.4).
    """

    # T [K]: cp [J/(kg K)], k [W/(m K)], nu [m^2/s], Pr
    TABLE = {
        300.0: (1007.0, 0.02630, 15.89e-6, 0.707),
        400.0: (1014.0, 0.03380, 26.41e-6, 0.690),
        500.0: (1030.0, 0.04070, 38.79e-6, 0.684),
        600.0: (1051.0, 0.04690, 52.69e-6, 0.685),
        800.0: (1099.0, 0.05730, 84.93e-6, 0.709),
    }

    def test_cp_within_one_percent(self):

        for T, (cp, _, _, _) in self.TABLE.items():
            with self.subTest(T=T):
                self.assertAlmostEqual(cp_air(T) / cp, 1.0, delta=0.01)

    def test_conductivity_and_viscosity_over_the_film_range(self):

        # The film temperature is the mean of the skin and the
        # ambient, so it cannot exceed ~490 K for any skin inside
        # the refractory-anchor limit. Over that range Sutherland
        # holds k to 2% and nu to 3% -- nu carries the ideal-gas
        # density on top of mu, and physics.py already states
        # that Sutherland's error grows with temperature. 800 K
        # is kept in the table for cp and checked separately.
        for T, (_, k_tab, nu_tab, _) in self.TABLE.items():

            if T > 600.0:
                continue

            with self.subTest(T=T):
                k, nu, _ = air_film_properties(T)
                self.assertAlmostEqual(k / k_tab, 1.0, delta=0.02)
                self.assertAlmostEqual(nu / nu_tab, 1.0, delta=0.03)

    def test_sutherland_error_at_800_K_is_bounded(self):

        _, k_tab, nu_tab, _ = self.TABLE[800.0]

        k, nu, _ = air_film_properties(800.0)

        self.assertAlmostEqual(k / k_tab, 1.0, delta=0.05)
        self.assertAlmostEqual(nu / nu_tab, 1.0, delta=0.05)

    def test_prandtl_within_five_percent(self):

        for T, (_, _, _, Pr_tab) in self.TABLE.items():
            with self.subTest(T=T):
                _, _, Pr = air_film_properties(T)
                self.assertAlmostEqual(Pr / Pr_tab, 1.0, delta=0.05)

    def test_rejects_non_positive_temperature(self):

        with self.assertRaises(ValueError):
            air_film_properties(0.0)


class FilmCoefficientTest(unittest.TestCase):

    def test_radiative_coefficient_is_an_exact_rewrite(self):
        """
        h_rad (Ts - Tamb) == eps sigma (Ts^4 - Tamb^4) identically.

        This is the identity the whole linearisation rests on: if
        it ever stops holding, the wall rows stop conserving
        energy at the fixed point.
        """

        eps = 0.83
        T_amb = 297.0

        for T_s in (310.0, 420.0, 560.0, 700.0):
            with self.subTest(T_s=T_s):
                h = radiative_coefficient(T_s, T_amb, eps)
                self.assertAlmostEqual(
                    h * (T_s - T_amb),
                    eps * sigma * (T_s**4 - T_amb**4),
                    delta=1e-9,
                )

    def test_churchill_chu_horizontal_against_hand_evaluation(self):

        T_s, T_amb, D = 560.0, 300.0, 4.9

        k, nu, Pr = air_film_properties(0.5 * (T_s + T_amb))

        Ra = (
            9.80665
            * (T_s - T_amb)
            * D**3
            / (0.5 * (T_s + T_amb) * nu * (nu / Pr))
        )

        Nu = (
            0.60
            + 0.387 * Ra ** (1 / 6)
            / (1 + (0.559 / Pr) ** (9 / 16)) ** (8 / 27)
        ) ** 2

        self.assertAlmostEqual(
            natural_convection_coefficient(
                T_s, T_amb, D, "horizontal"
            ),
            Nu * k / D,
            delta=1e-9,
        )

    def test_vertical_form_differs_from_horizontal(self):

        args = (500.0, 300.0, 10.0)

        self.assertNotAlmostEqual(
            natural_convection_coefficient(*args, "vertical"),
            natural_convection_coefficient(*args, "horizontal"),
            places=3,
        )

    def test_kiln_shell_film_is_in_the_expected_range(self):
        """
        A 4.9 m kiln shell at 560 K in 300 K still air: natural
        convection of order 6-7 W/(m^2 K), radiation roughly
        2.5x that. If radiation ever stops dominating here, the
        closure has lost the term this whole phase was about.
        """

        h_conv = natural_convection_coefficient(
            560.0, 300.0, 4.9, "horizontal"
        )
        h_rad = radiative_coefficient(560.0, 300.0, 0.80)

        self.assertTrue(5.0 < h_conv < 8.0, h_conv)
        self.assertTrue(2.0 < h_rad / h_conv < 3.5, h_rad / h_conv)

    def test_zero_temperature_difference_gives_no_convection(self):

        self.assertAlmostEqual(
            natural_convection_coefficient(
                300.0, 300.0, 4.9, "horizontal"
            ),
            0.36 * 0.02624 / 4.9,   # Nu -> 0.60^2 as Ra -> 0
            delta=1e-4,
        )

    def test_rejects_unknown_orientation(self):

        with self.assertRaises(ValueError):
            natural_convection_coefficient(
                500.0, 300.0, 4.9, "diagonal"
            )

    def test_rejects_non_positive_characteristic_length(self):

        with self.assertRaises(ValueError):
            natural_convection_coefficient(
                500.0, 300.0, 0.0, "horizontal"
            )


class ConductionGeometryTest(unittest.TestCase):

    def test_single_layer_matches_the_analytic_cylinder(self):

        r_in, t, k, L = 2.1, 0.20, 1.8, 3.0

        geom = single_layer(t, k).geometry(
            r_inner=r_in, L_cell=L, L_char=4.6
        )

        self.assertAlmostEqual(
            geom.R_cond,
            np.log((r_in + t) / r_in) / (2 * np.pi * k * L),
            delta=1e-12,
        )

        self.assertAlmostEqual(geom.r_outer, r_in + t, delta=1e-12)

    def test_layers_add_in_series(self):

        r_in, L = 2.1, 3.0

        stack = WallStack(
            zone="test",
            layers=[
                WallLayer("a", 0.10, 1.0),
                WallLayer("b", 0.20, 2.0),
                WallLayer("c", 0.025, 45.0),
            ],
            emissivity=0.8,
            orientation="horizontal",
        )

        geom = stack.geometry(r_inner=r_in, L_cell=L, L_char=5.0)

        expected = 0.0
        r = r_in

        for t, k in ((0.10, 1.0), (0.20, 2.0), (0.025, 45.0)):
            expected += np.log((r + t) / r) / (2 * np.pi * k * L)
            r += t

        self.assertAlmostEqual(geom.R_cond, expected, delta=1e-14)

    def test_thin_layer_tends_to_the_plane_wall(self):
        """
        ln(1 + t/r)/(2 pi k L) -> t/(k * 2 pi r L) as t/r -> 0.

        The cylindrical form has to REDUCE to the plane one, or
        the old model and this one would disagree in a regime
        where they must not.
        """

        r_in, t, k, L = 2.1, 1.0e-4, 1.8, 3.0

        geom = single_layer(t, k).geometry(
            r_inner=r_in, L_cell=L, L_char=4.3
        )

        plane = t / (k * 2 * np.pi * r_in * L)

        self.assertAlmostEqual(geom.R_cond / plane, 1.0, delta=1e-4)

    def test_thick_layer_sits_between_the_two_plane_forms(self):
        """
        The cylindrical resistance is t/(k A L) at the LOG-MEAN
        area, so it is bracketed by the plane form taken at the
        inner area and at the outer one. Every zone used to pass
        its INNER area, which therefore OVERSTATED the lining
        resistance and understated the loss.
        """

        r_in, t, k, L = 2.1, 0.35, 1.8, 3.0

        geom = single_layer(t, k).geometry(
            r_inner=r_in, L_cell=L, L_char=4.9
        )

        plane_inner = t / (k * 2 * np.pi * r_in * L)
        plane_outer = t / (k * 2 * np.pi * (r_in + t) * L)

        self.assertLess(plane_outer, geom.R_cond)
        self.assertLess(geom.R_cond, plane_inner)

        # For a real kiln lining the old inner-area form was 8%
        # stiff. Small next to the missing outer radiation, but
        # it biased the same way in every zone.
        self.assertAlmostEqual(
            plane_inner / geom.R_cond, 1.08, delta=0.01
        )

    def test_rejects_degenerate_geometry(self):

        stack = single_layer(0.2, 1.8)

        with self.assertRaises(ValueError):
            stack.geometry(r_inner=0.0, L_cell=3.0, L_char=4.6)

        with self.assertRaises(ValueError):
            stack.geometry(r_inner=2.1, L_cell=0.0, L_char=4.6)

    def test_rejects_unphysical_layers(self):

        with self.assertRaises(ValueError):
            WallLayer("bad", 0.0, 1.8)

        with self.assertRaises(ValueError):
            WallLayer("bad", 0.2, 0.0)

        with self.assertRaises(ValueError):
            WallStack("test", [], 0.8, "horizontal")

        with self.assertRaises(ValueError):
            WallStack(
                "test",
                [WallLayer("a", 0.2, 1.8)],
                1.4,
                "horizontal",
            )


class ShellClosureTest(unittest.TestCase):
    """
    The solved surface energy balance, checked against itself.
    """

    def setUp(self):

        self.stack = wall_stack(None, "burning")

        self.geom = self.stack.geometry(
            r_inner=2.1,
            L_cell=3.0,
            L_char=4.2 + 2 * self.stack.thickness,
        )

        self.T_amb = 300.0

    def flux_balance_residual(self, T_hf, T_s):
        """
        Conduction into the skin minus what the skin sheds. Zero
        at the solution, by definition of the solution.
        """

        conducted = (T_hf - T_s) / self.geom.R_cond

        h_ext = (
            natural_convection_coefficient(
                T_s,
                self.T_amb,
                self.geom.L_char,
                self.stack.orientation,
            )
            + radiative_coefficient(
                T_s, self.T_amb, self.stack.emissivity
            )
        )

        shed = h_ext * self.geom.A_outer_cell * (T_s - self.T_amb)

        return conducted - shed

    def test_solution_closes_the_surface_energy_balance(self):

        for T_hf in (500.0, 900.0, 1400.0, 1700.0):
            with self.subTest(T_hf=T_hf):
                _, T_s, _ = shell_closure(
                    T_hf, self.geom, self.T_amb
                )

                scale = (T_hf - self.T_amb) / self.geom.R_cond

                self.assertLess(
                    abs(self.flux_balance_residual(T_hf, T_s)),
                    1e-6 * scale,
                )

    def test_r_total_carries_exactly_the_solved_flux(self):

        T_hf = 1650.0

        R_total, T_s, _ = shell_closure(T_hf, self.geom, self.T_amb)

        self.assertAlmostEqual(
            (T_hf - self.T_amb) / R_total,
            (T_hf - T_s) / self.geom.R_cond,
            delta=1e-6,
        )

    def test_shell_sits_between_ambient_and_hot_face(self):

        for T_hf in (310.0, 800.0, 1700.0):
            with self.subTest(T_hf=T_hf):
                _, T_s, _ = shell_closure(
                    T_hf, self.geom, self.T_amb
                )
                self.assertTrue(self.T_amb <= T_s <= T_hf, T_s)

    def test_hot_face_at_ambient_loses_nothing(self):

        R_total, T_s, _ = shell_closure(
            self.T_amb, self.geom, self.T_amb
        )

        self.assertAlmostEqual(T_s, self.T_amb, delta=1e-9)
        self.assertAlmostEqual(
            (self.T_amb - self.T_amb) / R_total, 0.0, delta=1e-12
        )

    def test_more_insulation_means_cooler_skin_and_less_loss(self):

        T_hf = 1600.0

        bare = single_layer(0.20, 1.8).geometry(
            r_inner=2.1, L_cell=3.0, L_char=4.6
        )

        lagged = WallStack(
            zone="test",
            layers=[
                WallLayer("refractory", 0.20, 1.8),
                WallLayer("wool", 0.10, 0.12),
            ],
            emissivity=0.8,
            orientation="horizontal",
        ).geometry(r_inner=2.1, L_cell=3.0, L_char=4.8)

        R_bare, T_bare, _ = shell_closure(T_hf, bare, self.T_amb)
        R_lag, T_lag, _ = shell_closure(T_hf, lagged, self.T_amb)

        self.assertLess(T_lag, T_bare)
        self.assertGreater(R_lag, R_bare)

    def test_loss_rises_monotonically_with_the_hot_face(self):

        T = np.array([400.0, 700.0, 1000.0, 1300.0, 1600.0])

        R_total, T_s, _ = shell_closure(T, self.geom, self.T_amb)

        q = (T - self.T_amb) / R_total

        self.assertTrue(np.all(np.diff(q) > 0.0))
        self.assertTrue(np.all(np.diff(T_s) > 0.0))

    def test_result_is_independent_of_the_starting_guess(self):

        T_hf = 1500.0

        reference = shell_closure(T_hf, self.geom, self.T_amb)[1]

        for guess in (301.0, 400.0, 900.0, 1499.0):
            with self.subTest(guess=guess):
                _, T_s, _ = shell_closure(
                    T_hf,
                    self.geom,
                    self.T_amb,
                    T_shell_guess=guess,
                )
                self.assertAlmostEqual(T_s, reference, delta=1e-6)

    def test_scalar_and_array_paths_agree(self):

        T = np.array([450.0, 800.0, 1200.0, 1650.0])

        R_arr, T_arr, _ = shell_closure(T, self.geom, self.T_amb)

        for i, t in enumerate(T):
            with self.subTest(T_hf=t):
                R_s, T_s, _ = shell_closure(
                    float(t), self.geom, self.T_amb
                )
                self.assertAlmostEqual(R_s / R_arr[i], 1.0, delta=1e-10)
                self.assertAlmostEqual(T_s / T_arr[i], 1.0, delta=1e-10)

    def test_inverse_recovers_the_shell_temperature(self):

        T = np.array([600.0, 1100.0, 1650.0])

        R_total, T_s, _ = shell_closure(T, self.geom, self.T_amb)

        recovered = shell_temperature_from_resistance(
            T, R_total, self.geom, self.T_amb
        )

        self.assertTrue(
            np.allclose(recovered, T_s, rtol=0.0, atol=1e-6)
        )

    def test_loss_conductance_matches_a_numerical_derivative(self):

        for T_hf in (700.0, 1200.0, 1650.0):
            with self.subTest(T_hf=T_hf):

                def q_of(t):
                    R, _, _ = shell_closure(
                        float(t), self.geom, self.T_amb
                    )
                    return (t - self.T_amb) / R

                h = 0.5
                numeric = (q_of(T_hf + h) - q_of(T_hf - h)) / (2 * h)

                _, T_s, _ = shell_closure(
                    T_hf, self.geom, self.T_amb
                )

                analytic = loss_conductance(
                    T_s, self.geom, self.T_amb
                )

                # The convective leg is differentiated as
                # (4/3) h_conv rather than exactly, so a few
                # percent is the honest tolerance here.
                self.assertAlmostEqual(
                    analytic / numeric, 1.0, delta=0.05
                )

    def test_rejects_non_positive_hot_face(self):

        with self.assertRaises(ValueError):
            shell_closure(0.0, self.geom, self.T_amb)


class PlantWallStackTest(unittest.TestCase):
    """
    The shipped stacks, against what the surfaces they describe
    actually run at in a cement plant.
    """

    GEOMETRY = {
        "burning": (2.1, 60.0, 20),
        "transition": (2.1, 25.0, 20),
        "calciner": (2.1, 25.0, 20),
        "preheater": (2.1, 25.0, 20),
        "cooler": (2.1, 25.0, 20),
    }

    # Hot-face temperature each surface sees, and the band its
    # outer skin is expected to land in [K]. The rotary zones are
    # BARE steel (350-670 K, the refractory-anchor limit); the
    # other three are lagged casings that have to stay near
    # touchable (310-420 K).
    CASES = {
        "burning": (1650.0, 480.0, 670.0),
        "transition": (1620.0, 480.0, 670.0),
        "calciner": (1600.0, 310.0, 420.0),
        "preheater": (1500.0, 310.0, 420.0),
        "cooler": (1100.0, 310.0, 420.0),
    }

    def build(self, zone):

        r_in, L, N = self.GEOMETRY[zone]
        stack = wall_stack(None, zone)

        L_char = (
            2 * r_in + 2 * stack.thickness
            if stack.orientation == "horizontal"
            else L
        )

        return stack, stack.geometry(
            r_inner=r_in, L_cell=L / N, L_char=L_char
        )

    def test_every_zone_has_a_stack(self):

        self.assertEqual(
            set(DEFAULT_WALL_STACKS),
            {
                "burning",
                "transition",
                "calciner",
                "preheater",
                "cooler",
            },
        )

    def test_skin_lands_in_its_band(self):

        for zone, (T_hf, lo, hi) in self.CASES.items():
            with self.subTest(zone=zone):
                _, geom = self.build(zone)
                _, T_s, _ = shell_closure(T_hf, geom, 300.0)
                self.assertTrue(lo <= T_s <= hi, f"{zone}: {T_s:.1f} K")

    def test_bare_kiln_flux_is_in_the_measured_range(self):
        """
        Measured rotary-kiln shells lose 3-8 kW/m^2 of outer
        surface. This is the check that the lining stack, not a
        calibration factor, is what puts the model there.
        """

        for zone in ("burning", "transition"):
            with self.subTest(zone=zone):
                _, geom = self.build(zone)
                R_total, _, info = shell_closure(
                    self.CASES[zone][0], geom, 300.0
                )
                flux = (
                    (self.CASES[zone][0] - 300.0)
                    / R_total
                    / geom.A_outer_cell
                )
                self.assertTrue(3e3 < flux < 8e3, f"{zone}: {flux:.0f}")
                self.assertFalse(info["Ra_limit_exceeded"])

    def test_lagged_vessels_lose_an_order_of_magnitude_less(self):

        _, kiln = self.build("burning")
        _, tower = self.build("calciner")

        q_kiln = (
            (1650.0 - 300.0)
            / shell_closure(1650.0, kiln, 300.0)[0]
            / kiln.A_outer_cell
        )

        q_tower = (
            (1600.0 - 300.0)
            / shell_closure(1600.0, tower, 300.0)[0]
            / tower.A_outer_cell
        )

        self.assertGreater(q_kiln / q_tower, 3.0)

    def test_horizontal_zones_stay_inside_the_correlation(self):

        for zone in ("burning", "transition", "cooler"):
            with self.subTest(zone=zone):
                stack, geom = self.build(zone)
                Ra = rayleigh_number(
                    self.CASES[zone][0] * 0 + 600.0,
                    300.0,
                    geom.L_char,
                )
                self.assertLess(Ra, RA_HORIZONTAL_LIMIT)

    def test_config_can_override_a_stack(self):

        cfg = {
            "wall_stack": {
                "cooler": {
                    "orientation": "vertical",
                    "shell_emissivity": 0.5,
                    "layers": [["plate", 0.01, 45.0]],
                }
            }
        }

        stack = wall_stack(cfg, "cooler")

        self.assertEqual(stack.orientation, "vertical")
        self.assertEqual(stack.emissivity, 0.5)
        self.assertEqual(len(stack.layers), 1)

        # Untouched zones keep the defaults.
        self.assertEqual(
            len(wall_stack(cfg, "burning").layers),
            len(DEFAULT_WALL_STACKS["burning"]["layers"]),
        )

    def test_unknown_zone_is_rejected(self):

        with self.assertRaises(KeyError):
            wall_stack(None, "rawmill")


if __name__ == "__main__":
    unittest.main()
