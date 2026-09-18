import unittest

import numpy as np

from physics.physics import h_gas
from reporter import diagnostics
from tests.twin_harness import run_twin


class SpeciesStoichiometryTest(unittest.TestCase):
    """The elemental closure is only as good as the table it reads.

    These checks need no twin: they verify that every molar mass in
    SOLID_SPECIES equals the sum of the atoms the same entry claims,
    so a typo in either column cannot silently bias the closure.
    """

    # Independent literature molar masses [g/mol].
    EXPECTED_M = {
        "CaCO3": 100.09,
        "CaO": 56.08,
        "SiO2": 60.08,
        "Al2O3": 101.96,
        "Fe2O3": 159.69,
        "C2S": 172.24,
        "C3S": 228.32,
        "C3A": 270.20,
        "C4AF": 485.96,
        "H2O": 18.02,
        "Bound_H2O": 18.02,
    }

    def test_molar_masses_match_literature(self):

        for name, expected in self.EXPECTED_M.items():
            with self.subTest(species=name):
                M = diagnostics.SOLID_SPECIES[name][0]
                self.assertAlmostEqual(M, expected, delta=0.05)

    def test_element_fractions_never_exceed_unity(self):

        for name, (M, *counts) in diagnostics.SOLID_SPECIES.items():
            with self.subTest(species=name):

                total = sum(
                    n * diagnostics.ELEMENT_MASS[e]
                    for n, e in zip(counts, diagnostics.ELEMENTS)
                )

                self.assertLessEqual(total / M, 1.0)

    def test_known_mass_fractions(self):

        # CaO is 71.47 % Ca; C3S is 52.66 % Ca and 12.30 % Si.
        M, n_ca, _, _, _ = diagnostics.SOLID_SPECIES["CaO"]
        self.assertAlmostEqual(
            n_ca * diagnostics.A_Ca / M, 0.7147, places=4
        )

        M, n_ca, n_si, _, _ = diagnostics.SOLID_SPECIES["C3S"]
        self.assertAlmostEqual(
            n_ca * diagnostics.A_Ca / M, 0.5266, places=4
        )
        self.assertAlmostEqual(
            n_si * diagnostics.A_Si / M, 0.1230, places=4
        )


class SignFlipTest(unittest.TestCase):

    def test_reports_first_negative_index(self):
        self.assertEqual(
            diagnostics._sign_flip_cell(np.array([3.0, 1.0, -1.0, 2.0])),
            2,
        )

    def test_returns_none_when_never_negative(self):
        self.assertIsNone(
            diagnostics._sign_flip_cell(np.array([3.0, 1.0, 0.0]))
        )


class DiagnosticsOnConvergedTwinTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin(nodes_per_stage=1)
        cls.state = cls.twin.state

    # ------------------------------------------------------
    # D4 is only trustworthy if it reproduces the balance the
    # solver itself closed. This rebuilds the burning gas
    # energy balance from nothing but the published per-cell
    # arrays: if they were a parallel computation rather than
    # the real one, this is where it would show.
    # ------------------------------------------------------
    def test_published_cells_reconstruct_the_gas_balance(self):

        state = self.state
        burning = self.twin.burning

        Qgs = float(np.sum(state.Burning_Qgs_cells))
        Qgw = float(np.sum(state.Burning_Qgw_cells))

        Hg_in = float(
            state.m_dot_g * h_gas(state.Tg_burning_in, burning.T_ref)
        )
        Hg_out = float(state.Hgas_burning_out)

        residual = (Hg_out - Hg_in) - (
            float(state.Q_burning) - Qgs - Qgw
        )

        self.assertLess(
            abs(residual),
            1e-3,
            f"gas balance from published cells off by {residual:.3e} W",
        )

    def test_fuel_cells_sum_to_total_heat_release(self):

        self.assertAlmostEqual(
            float(np.sum(self.state.Burning_q_fuel_cells)),
            float(self.state.Q_burning),
            delta=1e-6,
        )

    def test_wall_loss_cells_sum_to_reported_wall_loss(self):

        self.assertAlmostEqual(
            float(np.sum(self.state.Burning_Qloss_cells)),
            float(self.state.Wall_loss_burning),
            delta=1e-6,
        )

    # ------------------------------------------------------
    # The burning zone splits the wall between the covered and
    # exposed arcs, so its area densities must add back up to
    # the full perimeter 4/D and no more. The other zones use
    # the superseded packed-bed closure and do not; that is
    # measured, not asserted, so this test pins only the zone
    # that has been corrected.
    # ------------------------------------------------------
    def test_burning_wall_area_identity_holds(self):

        rows = {r["zone"]: r for r in diagnostics.zone_ntu(self.twin)}

        self.assertAlmostEqual(
            rows["burning"]["wall_area_identity"],
            1.0,
            places=12,
        )

    def test_every_zone_appears_in_the_ntu_table(self):

        rows = {r["zone"] for r in diagnostics.zone_ntu(self.twin)}

        self.assertEqual(rows, set(diagnostics.SOLID_ZONE_ORDER))

    # ------------------------------------------------------
    # A real physics assertion, not a bookkeeping one: Ca, Si,
    # Al and Fe are neither created nor destroyed by the
    # reaction network, whatever the reactions do with them.
    # None of the 14 balances covers this.
    # ------------------------------------------------------
    def test_elements_are_conserved_through_the_plant(self):

        for row in diagnostics.elemental_closure(self.twin):
            with self.subTest(element=row["element"]):
                self.assertLess(
                    abs(row["rel"]),
                    1e-3,
                    f"{row['element']} off by {row['rel']:.3e} relative",
                )

    # ------------------------------------------------------
    # The continuity diagnostic must be arithmetically sound
    # independently of whether the plant currently passes it:
    # the temperature ratio it reports has to equal the mass
    # flow ratio it reports.
    # ------------------------------------------------------
    def test_continuity_temperature_ratio_equals_flow_ratio(self):

        for row in diagnostics.zone_boundary_continuity(self.twin):
            with self.subTest(handoff=row["handoff"]):

                T_ref = self.twin.burning.T_ref

                ratio = (row["T_downstream_in"] - T_ref) / (
                    row["T_upstream_face"] - T_ref
                )

                self.assertAlmostEqual(ratio, row["ratio"], places=9)

    # ------------------------------------------------------
    # D11 compares two numbers that must be derived from
    # different places, or it proves nothing. These guard that
    # separation: the demand side must come from the feed's
    # chemistry and the supply side from the fuel, so the
    # diagnostic cannot report a gap of zero by construction.
    # ------------------------------------------------------
    def test_potential_clinker_closes_against_the_feed(self):

        t = diagnostics.thermal_demand_vs_supply(self.twin)

        feed = diagnostics._solid_feed_species(self.twin)

        M_CaCO3 = diagnostics.SOLID_SPECIES["CaCO3"][0]
        M_CO2 = diagnostics.A_C + 2 * diagnostics.A_O

        CO2_full = feed["CaCO3"] * M_CO2 / M_CaCO3

        H2O_free = self.twin.state.m_dot_H2O_evaporated_preheater

        # Everything the feed loses on the way to clinker.
        lost = CO2_full + H2O_free + feed["Bound_H2O"]

        self.assertAlmostEqual(
            t["clinker_potential"] + lost,
            t["meal"],
            places=9,
        )

    def test_meal_to_clinker_ratio_is_physically_sane(self):
        """A generic raw meal yields 1.5-1.7 kg meal per kg clinker.

        This checks the FEED composition, not the model's conversion:
        it stays true however badly the kiln is running, so a failure
        means the raw meal itself is mis-specified.
        """

        t = diagnostics.thermal_demand_vs_supply(self.twin)

        self.assertGreater(t["meal_to_clinker"], 1.45)
        self.assertLess(t["meal_to_clinker"], 1.75)

    def test_specific_heat_consumption_matches_fuel_and_clinker(self):

        t = diagnostics.thermal_demand_vs_supply(self.twin)

        self.assertAlmostEqual(
            t["shc_J_per_kg"],
            t["fuel"] * diagnostics.FUEL_LHV / t["clinker_potential"],
            places=6,
        )

    def test_full_calcination_demand_exceeds_the_modelled_one(self):
        """The plant does not fully calcine, so the ceiling must be higher.

        If these ever coincide the model has reached complete
        calcination and the missing-sink line becomes zero -- which is
        the outcome Faz 4 is aiming at, and this test is then the
        thing that says so.
        """

        t = diagnostics.thermal_demand_vs_supply(self.twin)

        self.assertGreaterEqual(t["demand_full_W"], t["demand_modelled_W"])
        self.assertAlmostEqual(
            t["missing_sink_W"],
            t["demand_full_W"] - t["demand_modelled_W"],
            places=6,
        )

    def test_report_renders_every_section(self):

        text = diagnostics.report(self.twin)

        for marker in ("D1", "D2", "D3", "D4", "D8", "D9", "D11"):
            with self.subTest(section=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
