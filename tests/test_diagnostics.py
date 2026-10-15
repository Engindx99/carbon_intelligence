import unittest

import numpy as np

from physics.gas_thermo import mole_fraction
from pyroprocess.burning.gas_phase import kiln_inlet_gas
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


class FreeLimeTest(unittest.TestCase):
    """D14, against synthetic flows -- no twin, no solve.

    Free lime is the residual a setpoint solver will be driven
    against, so its denominator has to be exactly the clinker
    stream: the nine SOLID_SPECIES, never free or bound water.
    """

    @staticmethod
    def _twin(**species):
        """A stub carrying only what free_lime reads."""

        class _Solids:
            pass

        solids = _Solids()

        for name in diagnostics.SOLID_SPECIES:
            # Two cells, because clinker_quality reads the LAST one.
            setattr(
                solids,
                name,
                np.array([0.0, float(species.get(name, 0.0))]),
            )

        # Water is present in the phase record but is NOT clinker.
        for name in ("H2O", "Bound_H2O"):
            setattr(
                solids,
                name,
                np.array([0.0, float(species.get(name, 0.0))]),
            )

        class _Flow:
            pass

        flow = _Flow()
        flow.solids = solids

        class _State:
            pass

        state = _State()
        state.material_flows = {"cooler": flow}

        class _Twin:
            pass

        twin = _Twin()
        twin.state = state

        return twin

    def test_percent_is_CaO_over_the_clinker_total(self):

        twin = self._twin(CaO=1.0, C3S=6.0, C2S=2.0, C3A=0.5, C4AF=0.5)

        result = diagnostics.free_lime(twin)

        # 1.0 of 10.0 kg/s.
        self.assertAlmostEqual(result["free_lime_pct"], 10.0, places=9)
        self.assertAlmostEqual(result["CaO_kg_s"], 1.0, places=9)
        self.assertAlmostEqual(result["clinker_kg_s"], 10.0, places=9)

    def test_water_is_excluded_from_the_denominator(self):
        """A wet stream must not dilute the percentage."""

        dry = self._twin(CaO=1.0, C3S=9.0)
        wet = self._twin(CaO=1.0, C3S=9.0, H2O=5.0, Bound_H2O=5.0)

        self.assertAlmostEqual(
            diagnostics.free_lime(dry)["free_lime_pct"],
            diagnostics.free_lime(wet)["free_lime_pct"],
            places=9,
        )
        self.assertAlmostEqual(
            diagnostics.free_lime(wet)["free_lime_pct"], 10.0, places=9
        )

    def test_zero_when_all_lime_is_bound(self):

        twin = self._twin(C3S=10.0)
        self.assertAlmostEqual(
            diagnostics.free_lime(twin)["free_lime_pct"], 0.0, places=9
        )

    def test_hundred_when_nothing_reacted(self):

        twin = self._twin(CaO=10.0)
        self.assertAlmostEqual(
            diagnostics.free_lime(twin)["free_lime_pct"], 100.0, places=9
        )

    def test_band_verdict(self):

        lo, hi = diagnostics.FREE_LIME_BAND

        self.assertTrue(
            diagnostics.free_lime(
                self._twin(CaO=1.0, C3S=99.0)
            )["ok"]
        )
        # Under-burnt: above the band.
        self.assertFalse(
            diagnostics.free_lime(
                self._twin(CaO=5.0, C3S=95.0)
            )["ok"]
        )
        # Over-fired: below the band.
        self.assertFalse(
            diagnostics.free_lime(
                self._twin(CaO=0.1, C3S=99.9)
            )["ok"]
        )
        self.assertEqual((lo, hi), (0.5, 2.0))


class LimeSaturationTest(unittest.TestCase):
    """Free lime here is KINETIC, not stoichiometric.

    If the raw meal carried surplus CaO, free lime would have a
    floor no amount of firing could reach and it would be
    useless as a specification. It does not: the meal is lime
    SHORT of full C3S formation, so complete reaction leaves
    zero. This pins that, because a composition edit could
    silently destroy the whole premise.
    """

    def test_meal_is_lime_short_of_full_C3S(self):

        from chemistry.composition import RAW_MEAL_COMPOSITION as MEAL

        M_CaCO3, _, _, _, _ = diagnostics.SOLID_SPECIES["CaCO3"]
        M_CaO, _, _, _, _ = diagnostics.SOLID_SPECIES["CaO"]
        M_SiO2, _, _, _, _ = diagnostics.SOLID_SPECIES["SiO2"]
        M_Al2O3, _, _, _, _ = diagnostics.SOLID_SPECIES["Al2O3"]
        M_Fe2O3, _, _, _, _ = diagnostics.SOLID_SPECIES["Fe2O3"]

        # CaO the meal can release: its own plus all the carbonate.
        cao = MEAL["CaO"] + MEAL["CaCO3"] * M_CaO / M_CaCO3

        sio2 = MEAL["SiO2"]
        al2o3 = MEAL["Al2O3"]
        fe2o3 = MEAL["Fe2O3"]

        # Lime saturation factor, Bogue form.
        lsf = cao / (
            2.8 * sio2 + 1.18 * al2o3 + 0.65 * fe2o3
        )

        self.assertAlmostEqual(lsf, 0.950, places=2)

        # Below 1.0 means complete reaction consumes ALL the lime,
        # so free lime is zero at completion and any reading above
        # zero is time-at-temperature talking.
        self.assertLess(lsf, 1.0)


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

        # Rebuilt with the kiln's own inlet mixture, the one the
        # burner enthalpy was inverted with.
        Hg_in = float(
            state.m_dot_g
            * kiln_inlet_gas(state).h(float(state.Tg_burning_in), burning.T_ref)
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

    def test_calciner_budget_closes_like_the_solver(self):

        budget = diagnostics.calciner_energy_budget(self.twin)

        self.assertIsNotNone(budget)
        # The terms are the solver's own, inlet gases split apart:
        # they close to what its balance closed to, up to the
        # summation order on ~250 MW.
        energy_in = sum(v for _, v in budget["terms_in"])
        self.assertAlmostEqual(
            budget["residual_W"],
            float(self.state.Calciner_energy_balance),
            delta=1e-9 * energy_in,
        )
        # The outlet rates against its own gas.
        self.assertAlmostEqual(
            budget["p_CO2_out"],
            mole_fraction(self.state.Calciner_gas_species_out, "CO2"),
            places=9,
        )
        # Within a few K of the plateau: the model has no
        # recarbonation, so once calcination stops the tail (the
        # gooseneck, C5) can cool below T_eq by its wall loss --
        # 1.95 K at the reference state (15 Oct 2026).
        self.assertGreaterEqual(budget["Tg_out"], budget["T_eq_out"] - 5.0)

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
            # A constant closure gives exactly 1. The transition's
            # span depends on how hot the kiln runs: 1.17 once the
            # clay water left in the preheater and the burning
            # zone's bed peak fell from 1931 to 1755 K (15 Oct 2026).
            self.assertGreater(
                float(K.max() / K.min()),
                1.1,
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

        # Free moisture only: the preheater's water to the gas
        # also carries the clay water it dehydroxylates, which
        # feed["Bound_H2O"] below already counts.
        H2O_free = (
            self.twin.state.m_dot_H2O_evaporated_preheater
            - self.twin.state.m_dot_BoundH2O_reacted_preheater
        )

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

        # Reached, 13 Oct 2026: with the suspension area the meal
        # calcines completely before the burning zone, and the two
        # agree to 6e-12 relative. Allow that round-off, not more.
        self.assertGreaterEqual(
            t["demand_full_W"],
            t["demand_modelled_W"] * (1.0 - 1e-9),
        )
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

        # The riser is co-current: gas also runs 0 -> N-1, so its
        # last cell is the discharge too.
        self.assertAlmostEqual(
            gas[-1] / state.m_dot_g_calciner,
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
        """Mass only ever moves bed -> gas here, never back: the
        bed loses it and the gas gains it, both along 0 -> N-1
        (co-current riser)."""

        state = self.twin.state

        solid = np.asarray(state.m_dot_s_calciner_cells, dtype=float)
        gas = np.asarray(state.m_dot_g_calciner_cells, dtype=float)

        self.assertTrue(np.all(np.diff(solid) <= 1e-12))
        self.assertTrue(np.all(np.diff(gas) >= -1e-12))

    # ------------------------------------------------------
    # D12 is only worth reading if it is the SAME accounting the
    # plant closed, not a parallel one that happens to look
    # plausible. These pin that.
    # ------------------------------------------------------
    def test_ledger_closes(self):

        led = diagnostics.plant_thermal_ledger(self.twin)

        # Relative to the fuel, at the outer solve's own tolerance:
        # it was an absolute 1 W, ~4e-9 of the old 258 MW of fuel;
        # the plant now converges to ~1.5e-8 of 169 MW (2.6 W).
        self.assertLess(
            abs(led["closure_W"]),
            1e-7 * led["fuel_W"],
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

    # ------------------------------------------------------
    # D13 and the wall row of D12 are two views of the same
    # energy. They are built from different attributes -- D12
    # sums Wall_loss_<zone>, D13 reads the shell geometry each
    # zone published and divides by it -- so a zone that starts
    # publishing one without the other shows up here rather than
    # as two plausible tables that quietly disagree.
    # ------------------------------------------------------
    def test_shell_split_totals_the_ledger_wall_row(self):

        shells = diagnostics.shell_loss_split(self.twin)
        led = diagnostics.plant_thermal_ledger(self.twin)

        wall_row = next(
            r for r in led["rows"] if r["label"] == "wall losses"
        )

        self.assertAlmostEqual(
            shells["total_W"], wall_row["W"], delta=1e-6
        )

        self.assertAlmostEqual(
            shells["total_J_per_kg"],
            wall_row["J_per_kg"],
            delta=1e-9,
        )

    def test_every_zone_reports_a_shell(self):
        """
        All five zones must carry the Faz 6 closure. A zone that
        loses its `shell` attribute would silently drop out of
        D13 while still contributing to D12's total.
        """

        shells = diagnostics.shell_loss_split(self.twin)

        self.assertEqual(
            [r["zone"] for r in shells["rows"]],
            list(diagnostics.SOLID_ZONE_ORDER),
        )

    def test_shell_fluxes_are_physical(self):
        """
        The bare rotary shells and the lagged vessels have to
        land in the ranges their construction implies. This is
        the check that distinguishes "the lining model is wrong"
        from "the plant geometry does not match its throughput",
        which is what the wall row of D12 cannot tell apart.
        """

        bare = {"burning", "transition"}

        for r in diagnostics.shell_loss_split(self.twin)["rows"]:
            with self.subTest(zone=r["zone"]):

                lo, hi = (
                    (3.0e3, 8.0e3)
                    if r["zone"] in bare
                    else (0.0, 2.0e3)
                )

                self.assertTrue(
                    lo <= r["flux_W_per_m2"] <= hi,
                    f"{r['zone']}: {r['flux_W_per_m2']:.0f} W/m2",
                )

    def test_shell_temperature_is_published_not_reconstructed(self):
        """
        D2's shell check must read the zone's own solved skin.
        Rebuilding it from a resistance ratio is what made it
        report 868 K for walls the solver was running near 550 K.
        """

        for zone in diagnostics.SOLID_ZONE_ORDER:
            with self.subTest(zone=zone):
                self.assertIsInstance(
                    getattr(
                        self.state,
                        f"{zone.capitalize()}_T_shell_max",
                    ),
                    float,
                )

    def test_report_renders_every_section(self):

        text = diagnostics.report(self.twin)

        for marker in (
            "D1", "D2", "D3", "D4", "D8", "D9", "D11", "D12", "D13",
        ):
            with self.subTest(section=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
