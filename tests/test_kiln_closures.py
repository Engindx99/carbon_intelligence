"""
Faz 5 closure tests.

The point of this file is that the closure is checked against physics
that is stated INDEPENDENTLY of the implementation, in the same spirit
as tests/test_thermochemistry.py: the anchors and identities are
written out here, and the module has to reproduce them.
"""

import unittest

import numpy as np

from physics.kiln_closures import (
    EPS_G_RANGE,
    MEAN_BEAM_FACTOR,
    gas_density,
    gas_emissivity,
    grey_gas_surface_emissivity,
    kiln_transfer_coefficients,
    mean_beam_length,
    nusselt_gas_bed,
    nusselt_gas_wall,
    prandtl_gas,
    radiating_partial_pressure,
    two_surface_emissivity,
)
from physics.physics import bed_segment_geometry, sigma


# ======================================================
# GAS EMISSIVITY ANCHORS
#
# Total emissivity of a CO2 + H2O combustion gas at 1 atm,
# p_w/p_c ~ 1. These are the values the fit in
# physics.kiln_closures is anchored on; they are restated
# here so the test does not read them from the module.
#
# If the fit is ever replaced by a real coefficient table
# (Leckner 1972, Smith/Shen/Friedman 1982), this table is
# what the replacement has to reproduce.
# ======================================================
EMISSIVITY_ANCHORS = {
    (0.1, 1000.0): 0.16,
    (0.1, 1500.0): 0.11,
    (0.1, 2000.0): 0.075,
    (1.0, 1000.0): 0.33,
    (1.0, 1500.0): 0.25,
    (1.0, 2000.0): 0.18,
    (3.0, 1000.0): 0.44,
    (3.0, 1500.0): 0.34,
    (3.0, 2000.0): 0.26,
}

ANCHOR_TOLERANCE = 0.20      # relative


class GasEmissivityTest(unittest.TestCase):

    def test_reproduces_every_anchor(self):

        for (pL, T), expected in EMISSIVITY_ANCHORS.items():

            got = float(gas_emissivity(T, pL))

            self.assertLessEqual(
                abs(got - expected) / expected,
                ANCHOR_TOLERANCE,
                f"pL={pL} atm m, T={T} K: got {got:.4f}, "
                f"anchor {expected:.3f}",
            )

    def test_rises_with_path_length(self):
        """Band absorption: a longer path absorbs more, never less."""

        eps = gas_emissivity(1500.0, np.array([0.1, 0.3, 1.0, 3.0]))

        self.assertTrue(np.all(np.diff(eps) > 0.0))

    def test_saturates_with_path_length(self):
        """Sub-linear: doubling pL must less than double emissivity."""

        e1 = float(gas_emissivity(1500.0, 0.5))
        e2 = float(gas_emissivity(1500.0, 1.0))

        self.assertLess(e2, 2.0 * e1)

    def test_falls_with_temperature(self):
        """The bands shift out of the Planck peak as the gas heats."""

        eps = gas_emissivity(
            np.array([800.0, 1200.0, 1600.0, 2000.0]),
            1.0,
        )

        self.assertTrue(np.all(np.diff(eps) < 0.0))

    def test_stays_inside_physical_bounds(self):

        lo, hi = EPS_G_RANGE

        eps = gas_emissivity(
            np.array([400.0, 1000.0, 3000.0]),
            np.array([1e-6, 1.0, 50.0]),
        )

        self.assertTrue(np.all(eps >= lo))
        self.assertTrue(np.all(eps <= hi))
        self.assertTrue(np.all(eps <= 1.0))

    def test_rejects_unphysical_input(self):

        with self.assertRaises(ValueError):
            gas_emissivity(0.0, 1.0)

        with self.assertRaises(ValueError):
            gas_emissivity(1500.0, -1.0)


class RadiationNetworkTest(unittest.TestCase):

    def test_grey_gas_against_a_black_surface_is_the_gas_emissivity(self):

        self.assertAlmostEqual(
            grey_gas_surface_emissivity(0.3, 1.0),
            0.3,
            places=12,
        )

    def test_grey_gas_pair_is_symmetric_in_its_two_emissivities(self):

        self.assertAlmostEqual(
            grey_gas_surface_emissivity(0.3, 0.8),
            grey_gas_surface_emissivity(0.8, 0.3),
            places=12,
        )

    def test_two_black_surfaces_exchange_fully(self):

        self.assertAlmostEqual(
            two_surface_emissivity(1.0, 1.0, 0.3),
            1.0,
            places=12,
        )

    def test_two_surface_network_matches_the_closed_form(self):
        """1 / (1/e1 + (A1/A2)(1/e2 - 1)), stated independently."""

        e1, e2, ar = 0.9, 0.85, 0.2875

        expected = 1.0 / (1.0 / e1 + ar * (1.0 / e2 - 1.0))

        self.assertAlmostEqual(
            two_surface_emissivity(e1, e2, ar),
            expected,
            places=12,
        )

    def test_a_large_surface_seeing_a_small_one_approaches_its_own(self):
        """As A_1/A_2 -> 0 the small surface stops limiting."""

        self.assertAlmostEqual(
            two_surface_emissivity(0.9, 0.2, 0.0),
            0.9,
            places=12,
        )

    def test_mean_beam_length_is_the_enclosure_rule(self):
        """L_m = 3.6 V/A, and 4V/A is exactly D_e, so L_m = 0.9 D_e."""

        self.assertAlmostEqual(MEAN_BEAM_FACTOR, 3.6 / 4.0, places=12)

        _, _, _, _, D_e = bed_segment_geometry(4.2, 0.08)

        self.assertAlmostEqual(
            mean_beam_length(D_e),
            3.6 * D_e / 4.0,
            places=12,
        )


class LinearisedRadiationTest(unittest.TestCase):
    """h_rad (T1 - T2) must equal eps sigma (T1^4 - T2^4) exactly."""

    def test_linearisation_is_algebraically_exact(self):

        out = kiln_transfer_coefficients(
            Tg=np.array([1600.0]),
            Ts=np.array([1450.0]),
            Tw=np.array([1300.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        Tg, Ts = 1600.0, 1450.0

        eps_eff = grey_gas_surface_emissivity(
            float(out["eps_gas"]),
            0.90,
        )

        q_linear = float(out["h_rad_gs"]) * (Tg - Ts)
        q_quartic = eps_eff * sigma * (Tg**4 - Ts**4)

        self.assertAlmostEqual(
            q_linear / q_quartic,
            1.0,
            places=12,
        )

    def test_no_transfer_at_equal_temperatures(self):

        out = kiln_transfer_coefficients(
            Tg=np.array([1500.0]),
            Ts=np.array([1500.0]),
            Tw=np.array([1500.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        # Every coefficient stays finite and positive; the driving
        # potential, not the coefficient, is what vanishes.
        for key in ("h_rad_gs", "h_rad_gw", "h_rad_sw"):
            value = float(np.atleast_1d(out[key])[0])
            self.assertGreater(value, 0.0)
            self.assertTrue(np.isfinite(value))

    def test_radiation_coefficients_are_never_negative(self):
        """An M-matrix needs K >= 0 whichever way the heat flows."""

        out = kiln_transfer_coefficients(
            Tg=np.array([900.0, 1800.0]),
            Ts=np.array([1400.0, 1200.0]),
            Tw=np.array([1100.0, 1700.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        for key in ("K_gs", "K_gw", "K_ws"):
            self.assertTrue(np.all(np.asarray(out[key]) >= 0.0), key)


class ConvectionTest(unittest.TestCase):

    def test_prandtl_is_in_the_combustion_gas_range(self):

        Pr = prandtl_gas(np.array([600.0, 1200.0, 2000.0]))

        self.assertTrue(np.all(Pr > 0.6))
        self.assertTrue(np.all(Pr < 1.0))

    def test_gas_density_is_the_ideal_gas_law(self):

        self.assertAlmostEqual(
            float(gas_density(1500.0)),
            101325.0 * 0.02896 / (8.314462618 * 1500.0),
            places=12,
        )

    def test_gas_wall_nusselt_matches_dittus_boelter(self):
        """Stated independently of the module."""

        from physics.physics import k_gas, mu_gas

        T, u_g, D_e = 1551.0, 15.0, 3.945

        rho = float(gas_density(T))
        Re = rho * u_g * D_e / float(mu_gas(T))
        Pr = float(prandtl_gas(T))

        self.assertAlmostEqual(
            float(nusselt_gas_wall(T, u_g, D_e, 1.5))
            / (0.023 * Re**0.8 * Pr**0.4),
            1.0,
            places=12,
        )

    def test_gas_wall_beats_a_collapsing_extrapolation(self):
        """
        The reason Tscheng-Watkinson is not used for this path: at
        this kiln's rotational Reynolds number its negative exponent
        drives h_gw below a plain duct wall, which is unphysical.
        """

        T, u_g, D_e, rpm = 1551.0, 15.0, 3.945, 1.5

        rho = float(gas_density(T))
        from physics.physics import mu_gas

        mu = float(mu_gas(T))
        omega = 2.0 * np.pi * rpm / 60.0

        Re_D = rho * u_g * D_e / mu
        Re_w = rho * omega * D_e**2 / mu

        tw = 1.54 * Re_D**0.575 * Re_w**-0.292

        self.assertGreater(float(nusselt_gas_wall(T, u_g, D_e, rpm)), tw)

    def test_gas_bed_nusselt_rises_when_the_kiln_empties(self):
        """eta^-0.341: a thinner bed is swept harder per unit area."""

        hot = float(nusselt_gas_bed(1500.0, 15.0, 3.9, 1.5, 0.04))
        cold = float(nusselt_gas_bed(1500.0, 15.0, 3.9, 1.5, 0.12))

        self.assertGreater(hot, cold)

    def test_gas_bed_nusselt_rises_with_rotation(self):

        fast = float(nusselt_gas_bed(1500.0, 15.0, 3.9, 3.0, 0.08))
        slow = float(nusselt_gas_bed(1500.0, 15.0, 3.9, 1.0, 0.08))

        self.assertGreater(fast, slow)

    def test_gas_bed_nusselt_rejects_an_empty_kiln(self):

        with self.assertRaises(ValueError):
            nusselt_gas_bed(1500.0, 15.0, 3.9, 1.5, 0.0)


class PartialPressureTest(unittest.TestCase):

    def test_pure_co2_is_one_atmosphere(self):
        """A stream that is all CO2 has p_rad = 1 atm."""

        p = float(
            radiating_partial_pressure(
                m_dot_CO2=0.04401,
                m_dot_H2O=0.0,
                m_dot_gas_total=0.04401,
            )
        )

        # Mole fraction against the air-like mean molar mass, so the
        # heavier CO2 shows up as M_CO2 / M_GAS.
        self.assertAlmostEqual(p, 1.0, places=12)

    def test_inert_gas_does_not_radiate(self):

        self.assertAlmostEqual(
            float(
                radiating_partial_pressure(0.0, 0.0, 40.0)
            ),
            0.0,
            places=12,
        )

    def test_is_bounded_by_one_atmosphere(self):

        self.assertLessEqual(
            float(radiating_partial_pressure(100.0, 100.0, 1.0)),
            1.0,
        )

    def test_rejects_a_dead_gas_stream(self):

        with self.assertRaises(ValueError):
            radiating_partial_pressure(1.0, 0.0, 0.0)


class AreaClosureTest(unittest.TestCase):

    def test_wall_area_is_split_never_created(self):
        """a_ws + a_gw == 4/D, the identity Faz 3 exists to restore."""

        D = 4.2

        out = kiln_transfer_coefficients(
            Tg=np.array([1500.0]),
            Ts=np.array([1400.0]),
            Tw=np.array([1300.0]),
            D=D,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        self.assertAlmostEqual(
            (out["a_ws"] + out["a_gw"]) * D / 4.0,
            1.0,
            places=10,
        )

    def test_split_conductances_sum_to_the_totals(self):
        """D4 must read the same numbers the matrix was built from."""

        out = kiln_transfer_coefficients(
            Tg=np.array([1600.0, 1400.0]),
            Ts=np.array([1450.0, 1250.0]),
            Tw=np.array([1300.0, 1150.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        np.testing.assert_allclose(
            out["K_gs_conv"] + out["K_gs_rad"], out["K_gs"], rtol=1e-12
        )
        np.testing.assert_allclose(
            out["K_gw_conv"] + out["K_gw_rad"], out["K_gw"], rtol=1e-12
        )
        np.testing.assert_allclose(
            out["K_ws_cont"] + out["K_ws_rad"], out["K_ws"], rtol=1e-12
        )


class MechanismShareTest(unittest.TestCase):
    """
    The measurement that motivated Faz 5: at kiln temperatures the
    gas -> bed path is radiation-dominated. The old closure had it at
    1.0% radiation. Anything that puts it back below half is a
    regression, whatever else changed.
    """

    def test_radiation_dominates_at_kiln_temperature(self):

        out = kiln_transfer_coefficients(
            Tg=np.array([1551.0]),
            Ts=np.array([1489.0]),
            Tw=np.array([1300.0]),
            D=4.2,
            fill_fraction=0.0817,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        share = float(
            out["K_gs_rad"] / (out["K_gs_rad"] + out["K_gs_conv"])
        )

        self.assertGreater(share, 0.6)
        self.assertLess(share, 0.95)

    def test_convection_takes_over_at_cooler_temperature(self):
        """
        h_rad ~ T^3 and h_conv barely moves, so the ordering has to
        reverse somewhere down the kiln. A constant cannot do this,
        which is the whole structural argument for the change.
        """

        cold = kiln_transfer_coefficients(
            Tg=np.array([600.0]),
            Ts=np.array([550.0]),
            Tw=np.array([520.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        hot = kiln_transfer_coefficients(
            Tg=np.array([1900.0]),
            Ts=np.array([1700.0]),
            Tw=np.array([1600.0]),
            D=4.2,
            fill_fraction=0.08,
            rpm=1.5,
            m_dot_gas=13.0,
            p_rad=0.25,
            eps_bed=0.90,
            eps_wall=0.85,
            bed_conductivity=0.4,
            bed_density=1100.0,
            bed_cp=850.0,
            particle_diameter=1.0e-3,
            contact_chi=0.147,
        )

        def share(out):
            return float(
                out["K_gs_rad"] / (out["K_gs_rad"] + out["K_gs_conv"])
            )

        self.assertLess(share(cold), share(hot))


if __name__ == "__main__":
    unittest.main()
