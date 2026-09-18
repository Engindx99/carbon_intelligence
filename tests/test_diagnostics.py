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

        # The kiln gas GAINS mass: residual calcination in the bed
        # sends CO2 across the phase boundary, carrying its own
        # enthalpy at the local bed temperature. Without this term
        # the reconstruction is short by 6.94 MW -- it was correct
        # only while nothing calcined in the kiln.
        #
        # Read from state, not recomputed here, so this really is
        # the number the solver's own balance booked.
        H_phase_change = float(
            getattr(state, "Burning_H_phase_change", 0.0)
        )

        residual = (Hg_out - Hg_in) - (
            float(state.Q_burning) - Qgs - Qgw + H_phase_change
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

    # ------------------------------------------------------
    # FAZ 5. The acceptance criterion for replacing hv_gs /
    # hv_gw / hv_ws and k_eff was mechanism correctness, not a
    # temperature target, so these are the tests that decide
    # whether the change did what it claimed.
    # ------------------------------------------------------
    def test_both_rotating_zones_split_the_wall_area_exactly(self):
        """
        a_ws + a_gw == 4/D. Before Faz 5 the transition zone read
        1.5850 here: it charged the full perimeter to gas->wall and
        then charged the covered arc to wall->bed on top of it.
        """

        rows = {r["zone"]: r for r in diagnostics.zone_ntu(self.twin)}

        for zone in diagnostics.MECHANISM_SPLIT_ZONES:
            self.assertAlmostEqual(
                rows[zone]["wall_area_identity"],
                1.0,
                places=10,
                msg=f"{zone} double-counts wall area",
            )

    def test_radiation_carries_the_kiln_not_convection(self):
        """
        The measurement that motivated Faz 5: at kiln temperature the
        gas->bed path is radiation-dominated. The old closure put it
        at 1.0% radiation because k_eff = 0.005 suppressed eps*sigma
        200-fold. Anything that puts it back under half is a
        regression, whatever else moved.
        """

        for zone in diagnostics.MECHANISM_SPLIT_ZONES:

            split = diagnostics.zone_mechanism_split(
                self.twin.state, zone
            )

            row = {r["pair"]: r for r in split["rows"]}["gas->solid"]

            self.assertGreater(
                row["radiation_pct"],
                50.0,
                f"{zone} gas->solid is convection-dominated",
            )

    def test_conductances_are_not_constant_along_the_kiln(self):
        """
        The structural argument for the change: h_rad goes as T^3 and
        a single constant cannot represent it. If K came back uniform
        the closure would have silently collapsed to a constant again.
        """

        for zone in diagnostics.MECHANISM_SPLIT_ZONES:

            K = np.asarray(
                getattr(
                    self.twin.state,
                    f"{zone.capitalize()}_K_gs_cells",
                ),
                dtype=float,
            )

            self.assertGreater(K.size, 1)
            self.assertGreater(
                float(K.max() / K.min()),
                1.2,
                f"{zone} K_gs barely varies; closure may be constant",
            )

    def test_the_rotating_zones_no_longer_carry_the_old_constants(self):
        """
        Deleted, not merely unused: a fallback that still exists is a
        fallback something will eventually take.
        """

        from physics.physics import ZONE_HT_CONFIG, ZONE_RAD_CONFIG

        for zone in diagnostics.MECHANISM_SPLIT_ZONES:

            self.assertNotIn(zone, ZONE_HT_CONFIG)
            self.assertNotIn(zone, ZONE_RAD_CONFIG)

            z = diagnostics._zone_object(self.twin, zone)

            for attr in ("hv_gs", "hv_gw", "hv_ws"):
                self.assertFalse(
                    hasattr(z, attr),
                    f"{zone} still carries {attr}",
                )

    def test_gas_emissivity_is_physical_in_both_zones(self):
        """
        A participating gas, not a transparent one and not a black
        body. Outside roughly 0.05-0.6 the radiation network would be
        describing something that is not combustion gas.
        """

        for zone in diagnostics.MECHANISM_SPLIT_ZONES:

            eps = np.asarray(
                getattr(
                    self.twin.state,
                    f"{zone.capitalize()}_eps_gas_cells",
                ),
                dtype=float,
            )

            self.assertTrue(np.all(eps > 0.05), f"{zone} gas too thin")
            self.assertTrue(np.all(eps < 0.6), f"{zone} gas too thick")

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

    # ------------------------------------------------------
    # Faz 1b + 1c deliverable. Every zone that loses mass now
    # builds its outlet enthalpy on the flow that outlet face
    # actually carries, so each handoff must invert back to the
    # temperature the upstream zone discharged.
    #
    # This is the one property no energy balance can protect:
    # a mismatched flow conserves J/s exactly while rescaling
    # K, so all 14 balances close at machine precision either
    # way. Only an explicit check keeps it fixed.
    # ------------------------------------------------------
    def test_every_solid_handoff_is_temperature_continuous(self):

        for row in diagnostics.zone_boundary_continuity(self.twin):
            with self.subTest(handoff=row["handoff"]):

                self.assertAlmostEqual(
                    row["ratio"],
                    1.0,
                    places=9,
                    msg=(
                        f"{row['handoff']} converts enthalpy with "
                        f"{row['m_dot_up']:.4f} kg/s upstream "
                        f"(from {row['m_dot_up_source']}) and "
                        f"{row['m_dot_down']:.4f} kg/s downstream"
                    ),
                )

                self.assertAlmostEqual(
                    row["delta_T"],
                    0.0,
                    places=6,
                )

    # ------------------------------------------------------
    # The per-cell profiles and the scalar mass chain in
    # physics.steady_state_mass are two independent accountings
    # of the same stream. They are derived differently -- one by
    # marching the chemistry cell by cell, one by subtracting
    # zone totals -- so agreement at the endpoints is a real
    # cross-check, not a tautology.
    # ------------------------------------------------------
    def test_calciner_cell_flows_match_the_scalar_chain(self):

        state = self.twin.state
        mf = self.twin.mass_flow

        solid = np.asarray(state.m_dot_s_calciner_cells, dtype=float)
        gas = np.asarray(state.m_dot_g_calciner_cells, dtype=float)

        # RELATIVE, not absolute. These flows are tens of kg/s and
        # the two accountings agree to the outer solver's own
        # tolerance, not to the last bit: an absolute places=9 on
        # 44.7 kg/s is asking for 2e-11 relative, which is tighter
        # than the iteration that produced them.

        # Solid runs 0 -> N-1, so its last cell is the discharge.
        self.assertAlmostEqual(
            solid[-1] / mf.m_dot_s_calciner_out,
            1.0,
            places=9,
        )

        # Gas runs N-1 -> 0, so its first cell is the discharge.
        self.assertAlmostEqual(
            gas[0] / state.m_dot_g_calciner,
            1.0,
            places=9,
        )

        # The derived gas inlet must equal what the upstream
        # streams actually deliver, assembled independently.
        self.assertAlmostEqual(
            state.m_dot_g_calciner_in
            / (
                state.m_dot_g_transition
                + mf.m_dot_tertiary_air
                + mf.m_dot_fuel_calciner
            ),
            1.0,
            places=9,
        )

    def test_calciner_stream_flows_are_monotonic(self):
        """Mass only ever moves bed -> gas here, never back."""

        state = self.twin.state

        solid = np.asarray(state.m_dot_s_calciner_cells, dtype=float)
        gas = np.asarray(state.m_dot_g_calciner_cells, dtype=float)

        self.assertTrue(np.all(np.diff(solid) <= 1e-12))
        self.assertTrue(np.all(np.diff(gas) <= 1e-12))

    # ------------------------------------------------------
    # D12 is only worth reading if it is the SAME accounting the
    # plant closed, not a parallel one that happens to look
    # plausible. These pin that.
    # ------------------------------------------------------
    def test_ledger_closes(self):

        led = diagnostics.plant_thermal_ledger(self.twin)

        self.assertLess(
            abs(led["closure_W"]),
            1.0,
            f"ledger does not close: {led['closure_W']:.3e} W",
        )

    def test_ledger_reaction_total_is_the_disjoint_set(self):
        """Several published reaction scalars contain each other.

        Calciner_Q_sink already holds Dehydroxylation_Q_sink, and
        Burning_Q_sink already holds Calcination_Q_burning, so the
        naive sum of every reaction attribute double-counts. This
        checks the ledger uses the disjoint set AND that the naive
        sum really would differ -- if the overlap ever disappears
        this test should be revisited, not deleted.
        """

        state = self.twin.state

        def g(n):
            return float(getattr(state, n, 0.0))

        disjoint = (
            g("Preheater_Q_sink")
            + g("Calciner_Q_sink")
            + g("Calcination_Q_transition")
            + g("Burning_Q_sink")
        )

        naive = (
            g("Drying_Q_sink")
            + g("Dehydroxylation_Q_sink")
            + g("Calcination_Q_sink")
            + g("Calcination_Q_transition")
            + g("Calcination_Q_burning")
            + g("Belite_Q_sink")
            + g("Alite_Q_sink")
            + g("C3A_Q_sink")
            + g("C4AF_Q_sink")
            + g("Calciner_Q_sink")
            + g("Burning_Q_sink")
        )

        led = diagnostics.plant_thermal_ledger(self.twin)

        reactions = next(
            r for r in led["rows"] if r["label"] == "reactions (net)"
        )

        self.assertAlmostEqual(reactions["W"], disjoint, places=6)

        # The overlap is real, so the naive sum must be bigger.
        self.assertGreater(naive, disjoint)

    def test_ledger_per_kg_uses_potential_not_modelled_clinker(self):
        """Dividing by the model's clinker stream would flatter it.

        That stream still carries uncalcined CaCO3, so using it
        would count raw meal as product and understate the
        specific consumption.
        """

        led = diagnostics.plant_thermal_ledger(self.twin)
        demand = diagnostics.thermal_demand_vs_supply(self.twin)

        self.assertAlmostEqual(
            led["clinker_potential"],
            demand["clinker_potential"],
            places=9,
        )

        self.assertGreater(
            led["clinker_potential"],
            0.5 * self.twin.mass_flow.m_dot_s_preheater,
        )

    def test_report_renders_every_section(self):

        text = diagnostics.report(self.twin)

        for marker in ("D1", "D2", "D3", "D4", "D8", "D9", "D11", "D12"):
            with self.subTest(section=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
