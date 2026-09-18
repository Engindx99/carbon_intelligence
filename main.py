# ======================================================
# BLAS THREADING
#
# Every zone solver factorises a dense 3N x 3N system
# (N = cells per zone, so 30x30 at N=10) roughly 620 times
# per steady-state iteration. At that size the LU costs
# ~19 us single-threaded, but a multi-threaded BLAS spawns
# one worker per core and spin-waits on the barriers, which
# measured 79 ms per solve on a 20-core host -- ~4000x
# slower, and ~85 minutes of pure spin across a full solve.
#
# Pinning the BLAS to a single thread does not change the
# physics: it only changes dgesv's internal blocking, so the
# solution moves at double-precision rounding level. Measured
# over 400 captured zone systems: max |dT| = 1.8e-12 K, which
# is 6 orders below the Picard tolerance (1e-6 K) and 9 below
# the steady-state tolerance (1e-3 K).
#
# setdefault is used so an explicit environment override
# from the caller still wins.
#
# MUST run before numpy is imported (directly or via any
# pyroprocess/physics module) -- the thread pool is sized
# at library load time and ignores later changes.
# ======================================================

import os

for _blas_thread_var in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_blas_thread_var, "1")


from pyroprocess.globalstate import GlobalState
from pyroprocess.burning import Burning
from pyroprocess.transition import Transition
from pyroprocess.precalciner import Calciner
from pyroprocess.preheater import Preheater
from pyroprocess.cooler import Cooler

from physics.physics import gas_mass_balance
from physics.steady_state_mass import SteadyStateMassFlow
from physics.axial_coordinate import SOLID_FLOW_ZONE_ORDER, build_axial_layout


from validators.energy import validate_energy
from validators.mass import validate_mass
from reporter.validation import report_validation
from reporter import diagnostics
from visualization.zone_profiles import (
    plot_zone_temperature_profiles,
    plot_global_temperature_profile,
)
from visualization.mass_flow_profiles import plot_mass_flow_profiles

import numpy as np
import yaml



def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Twin:

    def __init__(self, state, cfg):

        self.state = state
        self.mass_flow = SteadyStateMassFlow()

        # ======================================================
        # ZONE MODELS
        # ======================================================
        self.burning = Burning(
            N=cfg["plant"]["N"],
            L=cfg["plant"]["length"],
        )

        self.transition = Transition(
            N=cfg["plant"]["N"],
            L=cfg["transition"]["length"],
        )

        self.calciner = Calciner(
            N=cfg["plant"]["N"],
            L=cfg["calciner"]["length"],
        )

        self.preheater = Preheater(
            L=cfg["preheater"]["length"],
            nodes_per_stage=cfg["preheater"]["nodes_per_stage"],
        )

        self.cooler = Cooler(
            N=cfg["plant"]["N"],
            L=cfg["cooler"]["length"],
        )

        # ======================================================
        # GLOBAL AXIAL COORDINATE (diagnostic, not read by solvers)
        #
        # Built from the L and N each zone actually uses, so it
        # cannot drift from the solver meshes.
        # ======================================================
        self.axial_layout = build_axial_layout(
            lengths={z: getattr(self, z).L for z in SOLID_FLOW_ZONE_ORDER},
            cell_counts={z: getattr(self, z).N for z in SOLID_FLOW_ZONE_ORDER},
        )

        # ======================================================
        # NUMERICAL
        # ======================================================
        self.eps = 1e-9

        # ======================================================
        # STEADY-STATE TRANSPORT VARIABLES
        # ======================================================
        self.state.u_s = self.calciner.u_s


        # ======================================================
        # FUEL CONFIG (PETCOKE ONLY)
        # ======================================================
        fuel = cfg.get("fuel", {})

        self._last_inputs = {
            "Fuel_rate_total": fuel.get("Fuel_rate_total", 0.0),
            "O2": fuel.get("O2", 3.5),
        }

        # ======================================================
        # FEED CONFIG
        # ======================================================
        feed = cfg.get("feed", {})

        self._last_inputs["Feed_rate_kg_s"] = feed.get(
            "Feed_rate_kg_s",
            0.0
        )

        # ======================================================
        # INITIAL STEADY-STATE MASS FLOW INPUTS
        # ======================================================
        self.mass_flow.set_external_inputs(
            m_dot_raw_meal=self._last_inputs["Feed_rate_kg_s"],
            m_dot_fuel=self._last_inputs["Fuel_rate_total"],
            m_dot_air=0.0,
        )
        
    def _validate_solid_handoffs(self):
        state = self.state

        print("\n========== SOLID HANDOFF DEBUG ==========")

        print("\n--- Preheater -> Calciner ---")
        print(f"Hsolid_preheater_out = {state.Hsolid_preheater_out:.12e} W")
        print(f"Hsolid_calciner_in   = {state.Hsolid_calciner_in:.12e} W")
        print(
            f"Difference           = "
            f"{state.Hsolid_preheater_out - state.Hsolid_calciner_in:.12e} W"
        )

        print("\n--- Calciner -> Transition ---")
        print(f"Hsolid_calciner_out  = {state.Hsolid_calciner_out:.12e} W")
        print(f"Hsolid_transition_in  = {state.Hsolid_transition_in:.12e} W")
        print(
            f"Difference           = "
            f"{state.Hsolid_calciner_out - state.Hsolid_transition_in:.12e} W"
        )

        print("\n--- Burning -> Cooler ---")
        print(f"Hsolid_burning_out    = {state.Hsolid_burning_out:.12e} W")
        print(f"Hsolid_cooler_in      = {state.Hsolid_cooler_in:.12e} W")
        print(
            f"Difference            = "
            f"{state.Hsolid_burning_out - state.Hsolid_cooler_in:.12e} W"
        )

        assert np.isclose(
            state.Hsolid_calciner_in,
            state.Hsolid_preheater_out,
            rtol=1e-10,
            atol=1e-3,
        )

        assert np.isclose(
            state.Hsolid_transition_in,
            state.Hsolid_calciner_out,
            rtol=1e-10,
            atol=1e-3,
        )

        assert np.isclose(
            state.Hsolid_cooler_in,
            state.Hsolid_burning_out,
            rtol=1e-10,
            atol=1e-3,
        )
        
        
    # ==========================================================
    # CENTRAL ENERGY VALIDATION
    # ==========================================================
    def _validate_energy_balances(self):

        equipment_models = [
            ("Burning", self.burning),
            ("Transition", self.transition),
            ("Calciner", self.calciner),
            ("Cooler", self.cooler),
        ]

        for equipment_name, equipment in equipment_models:

            result = validate_energy(
                energy_in=equipment.energy_in,
                energy_out=equipment.energy_out,
            )

            report_validation(
                result,
                equipment=equipment_name,
                balance_type="energy",
            )

        # ======================================================
        # PREHEATER GLOBAL ENERGY BALANCE
        # ======================================================

        # The zone balance cannot close tighter than the
        # inter-stage handoff criterion the solver stops on,
        # so it is held to that instead of the 1e-3 W default.
        # Derived in preheater/heat_transfer.py from the solid
        # handoff tolerance, the stream capacity and N.
        result = validate_energy(
            energy_in=self.preheater.energy_in,
            energy_out=self.preheater.energy_out,
            energy_source=sum(
                stage.Q_reaction
                for stage in self.preheater.stages
            ),
            absolute_tolerance=self.preheater.energy_closure_tolerance,
        )

        report_validation(
            result,
            equipment="Preheater",
            balance_type="energy",
        )

        # ======================================================
        # PREHEATER STAGES
        # ======================================================

        for stage in self.preheater.stages:

            result = validate_energy(
                energy_in=stage.energy_in,
                energy_out=stage.energy_out,
            )

            report_validation(
                result,
                equipment=f"Preheater Stage {stage.stage_id}",
                balance_type="energy",
            )


    def _validate_global_energy_balance(self):

        state = self.state

        # ======================================================
        # GLOBAL EXTERNAL INPUT
        # ======================================================

        H_rawmeal_in = state.Hsolid_preheater_in
        H_air_in = getattr(state, "Hgas_cooler_in", 0.0)

        # Primary air is an independent ambient intake at the
        # burner (not drawn through the cooler), so it is not
        # part of H_air_in. Derived from already-computed fields
        # rather than recomputing m_dot_primary_air * h_gas(...)
        # a second time: state.Hgas_burning_in = H_primary +
        # H_secondary (pyroprocess/burning/gas_phase.py), so
        # subtracting the secondary share recovers H_primary
        # exactly.
        H_primary_in = (
            state.Hgas_burning_in
            - getattr(state, "Hgas_cooler_secondary", 0.0)
        )

        # Both firings release fuel energy into the process, so
        # both belong on the input side. Counting only Q_burning
        # was correct while the kiln burner was the plant's only
        # heat source; with fuel.kiln_fraction < 1 the calciner
        # supplies the rest.
        Q_burning = state.Q_burning
        Q_calciner = getattr(state, "Q_calciner", 0.0)

        global_energy_in = (
            H_rawmeal_in
            + H_air_in
            + H_primary_in
            + Q_burning
            + Q_calciner
        )

        # ======================================================
        # GLOBAL EXTERNAL OUTPUT
        # ======================================================

        H_exhaust_out = state.Hgas_preheater_out
        H_clinker_out = state.Hsolid_cooler_out

        # Vent air leaves the cooler directly to atmosphere and
        # never enters the process gas train, so its (hot) exit
        # enthalpy does not show up anywhere inside H_exhaust_out
        # and must be accounted separately.
        H_vent_out = getattr(state, "Hgas_cooler_vent", 0.0)

        Q_wall_total = (
            state.Wall_loss_burning
            + state.Wall_loss_transition
            + state.Wall_loss_calciner
            + state.Wall_loss_preheater
            + state.Wall_loss_cooler
        )

        Q_reaction_total = (
            state.Calcination_Q_transition
            + state.Calciner_Q_sink
            + state.Preheater_Q_sink
            + state.Burning_Q_sink
        )

        print("\n========== GLOBAL REACTION DEBUG ==========")
        print(f"Calcination_Q_transition = {state.Calcination_Q_transition:.12e} W")
        print(f"Calciner_Q_sink          = {state.Calciner_Q_sink:.12e} W")
        print(f"Preheater_Q_sink         = {state.Preheater_Q_sink:.12e} W")
        print(f"Burning_Q_sink           = {state.Burning_Q_sink:.12e} W")
        print(f"Q_reaction_total         = {Q_reaction_total:.12e} W")
        print("==========================================")

        global_energy_out = (
            H_exhaust_out
            + H_clinker_out
            + H_vent_out
            + Q_wall_total
            + Q_reaction_total
        )

        # ======================================================
        # GLOBAL ENERGY VALIDATION
        #
        # Unlike the mass balance (an exact algebraic species
        # closure, ~1e-12 relative), this sums Hgas/Hsolid/wall
        # loss/reaction-sink terms from 5 zones that each
        # converged their OWN Picard loop independently, so it
        # cannot reach the shared 1e-9 relative_tolerance default
        # (see Preheater's own energy check, main.py above, which
        # is held to its own derived energy_closure_tolerance for
        # the same reason). Observed residual here is 0.2-0.5 W;
        # the outer solve's own convergence criterion
        # (thermal_tolerance = 1e-3 K) would permit up to ~62 W on
        # the exhaust stream alone, so 1.0 W is a tight bound that
        # still leaves ~2x margin over the observed numerical
        # noise floor while remaining far below the scale (kW-MW)
        # of any real missing or double-counted term.
        # ======================================================

        result = validate_energy(
            energy_in=global_energy_in,
            energy_out=global_energy_out,
            energy_source=0.0,
            absolute_tolerance=1.0,
        )

        report_validation(
            result,
            equipment="Pyroprocess",
            balance_type="global_energy",
        )

        # ======================================================
        # FINAL GLOBAL OUTPUT
        # ======================================================

        print()
        print("========== PYROPROCESS ENERGY CLOSURE ==========")

        print()
        print("EXTERNAL INPUT")
        print(
            f"    Raw meal enthalpy = "
            f"{H_rawmeal_in:.6e} W"
        )
        print(
            f"    Air enthalpy      = "
            f"{H_air_in:.6e} W"
        )
        print(
            f"    Primary air       = "
            f"{H_primary_in:.6e} W"
        )
        print(
            f"    Burning heat      = "
            f"{Q_burning:.6e} W"
        )
        print(
            f"    Energy in         = "
            f"{global_energy_in:.6e} W"
        )

        print()
        print("EXTERNAL OUTPUT")
        print(
            f"    Exhaust gas       = "
            f"{H_exhaust_out:.6e} W"
        )
        print(
            f"    Clinker           = "
            f"{H_clinker_out:.6e} W"
        )
        print(
            f"    Vent air          = "
            f"{H_vent_out:.6e} W"
        )
        print(
            f"    Wall losses       = "
            f"{Q_wall_total:.6e} W"
        )
        print(
            f"    Reaction sinks    = "
            f"{Q_reaction_total:.6e} W"
        )
        print(
            f"    Energy out        = "
            f"{global_energy_out:.6e} W"
        )

        print()
        print("GLOBAL BALANCE")
        print(
            f"    Residual          = "
            f"{result['residual']:.6e} W"
        )
        print(
            f"    Relative residual = "
            f"{result['relative_residual']:.6e}"
        )
        print(
            f"    Status            = "
            f"{'PASS' if result['converged'] else 'FAIL'}"
        )

        print("=" * 58)

    def _validate_global_mass_balance(self):

        mass_flow = self.mass_flow

        result = validate_mass(
            mass_in=mass_flow.mass_flow_in,
            mass_out=mass_flow.mass_flow_out,
            mass_source=0.0,
        )

        report_validation(
            result,
            equipment="Pyroprocess",
            balance_type="global_mass",
        )

        print()
        print("========== PYROPROCESS MASS CLOSURE ==========")
        print()
        print("EXTERNAL INPUT")
        print(
            f"    Raw meal          = "
            f"{mass_flow.m_dot_raw_meal:.6e} kg/s"
        )
        print(
            f"    Fuel              = "
            f"{mass_flow.m_dot_fuel:.6e} kg/s"
        )
        print(
            f"    Primary air       = "
            f"{mass_flow.m_dot_primary_air:.6e} kg/s"
        )
        print(
            f"    Cooler air        = "
            f"{mass_flow.m_dot_air_cooler:.6e} kg/s "
            f"(secondary + tertiary + vent)"
        )
        print(
            f"    Mass in           = "
            f"{mass_flow.mass_flow_in:.6e} kg/s"
        )

        print()
        print("EXTERNAL OUTPUT")
        print(
            f"    Clinker           = "
            f"{mass_flow.m_dot_clinker:.6e} kg/s"
        )
        print(
            f"    Exhaust gas       = "
            f"{mass_flow.m_dot_exhaust:.6e} kg/s"
        )
        print(
            f"    Vent air          = "
            f"{mass_flow.m_dot_vent_air:.6e} kg/s"
        )
        print(
            f"    Mass out          = "
            f"{mass_flow.mass_flow_out:.6e} kg/s"
        )

        print()
        print("GLOBAL BALANCE")
        print(
            f"    Residual          = "
            f"{result['residual']:.6e} kg/s"
        )
        print(
            f"    Relative residual = "
            f"{result['relative_residual']:.6e}"
        )
        print(
            f"    Status            = "
            f"{'PASS' if result['converged'] else 'FAIL'}"
        )

        print("=" * 58)

    def _validate_cooler_air_split(self):

        state = self.state

        result = validate_mass(
            mass_in=state.m_dot_air_cooler,
            mass_out=(
                state.m_dot_secondary_air
                + state.m_dot_tertiary_air
                + state.m_dot_vent_air
            ),
            mass_source=0.0,
        )

        report_validation(
            result,
            equipment="Cooler",
            balance_type="air_split",
        )

        print()
        print("========== COOLER AIR SPLIT CLOSURE ==========")
        print()
        print(
            f"    Cooler air (total) = "
            f"{state.m_dot_air_cooler:.6e} kg/s"
        )
        print(
            f"    Secondary air      = "
            f"{state.m_dot_secondary_air:.6e} kg/s"
        )
        print(
            f"    Tertiary air       = "
            f"{state.m_dot_tertiary_air:.6e} kg/s"
        )
        print(
            f"    Vent air           = "
            f"{state.m_dot_vent_air:.6e} kg/s"
        )
        print(
            f"    Residual           = "
            f"{result['residual']:.6e} kg/s"
        )
        print(
            f"    Status             = "
            f"{'PASS' if result['converged'] else 'FAIL'}"
        )

        print("=" * 58)

    def _validate_co2_species_balance(self):

        mass_flow = self.mass_flow

        co2_generated_total = (
            mass_flow.m_dot_CO2_generated
            + mass_flow.m_dot_CO2_generated_transition
            + mass_flow.m_dot_CO2_generated_burning
        )

        # m_dot_exhaust also carries two H2O mass-flow terms
        # that leave the solid stream and join the gas stream
        # the same way CO2 does: free moisture evaporated in
        # the preheater (m_dot_H2O_generated) and dehydroxylation
        # water released in the calciner
        # (m_dot_H2O_generated_calciner). Both must be subtracted
        # to isolate CO2, or this check reports their combined
        # mass as an apparent CO2 shortfall.
        # The precalciner's own fuel is injected into its gas
        # stream too (physics.steady_state_mass), so its mass is
        # in m_dot_exhaust exactly as tertiary air is and has to
        # come off here as well. The kiln's fuel needs no term of
        # its own: it is already inside m_dot_g_burning.
        co2_in_gas_stream = (
            mass_flow.m_dot_exhaust
            - mass_flow.m_dot_g_burning
            - mass_flow.m_dot_tertiary_air
            - mass_flow.m_dot_fuel_calciner
            - mass_flow.m_dot_H2O_generated
            - mass_flow.m_dot_H2O_generated_calciner
        )

        result = validate_mass(
            mass_in=co2_generated_total,
            mass_out=co2_in_gas_stream,
            mass_source=0.0,
        )

        report_validation(
            result,
            equipment="Pyroprocess",
            balance_type="global_co2_species",
        )

        print()
        print("========== PYROPROCESS CO2 SPECIES CLOSURE ==========")
        print()
        print(
            f"    CO2 generated (calciner)   = "
            f"{mass_flow.m_dot_CO2_generated:.6e} kg/s"
        )
        print(
            f"    CO2 generated (transition) = "
            f"{mass_flow.m_dot_CO2_generated_transition:.6e} kg/s"
        )
        print(
            f"    CO2 generated (total)      = "
            f"{co2_generated_total:.6e} kg/s"
        )
        print(
            f"    CO2 present in gas stream  = "
            f"{co2_in_gas_stream:.6e} kg/s"
        )
        print(
            f"    Residual                   = "
            f"{result['residual']:.6e} kg/s"
        )
        print(
            f"    Status                     = "
            f"{'PASS' if result['converged'] else 'FAIL'}"
        )
        print(
            "    NOTE: this checks the bulk CO2 bookkeeping "
            "chain for internal consistency only. Both sides "
            "are derived from the same m_dot_CO2_generated_* "
            "scalars, so it cannot detect a stoichiometry error "
            "(e.g. a wrong CO2_ratio) shared by both terms."
        )

        print("=" * 58)

    # ==========================================================
    # STEADY-STATE STATE SNAPSHOT
    # ==========================================================
    def _snapshot_state(self):

        return {
            "Tg_burning": self.state.Tg_burning.copy(),
            "Ts_burning": self.state.Ts_burning.copy(),
            "Tw_burning": self.state.Tw_burning.copy(),

            "Tg_transition": self.state.Tg_transition.copy(),
            "Ts_transition": self.state.Ts_transition.copy(),
            "Tw_transition": self.state.Tw_transition.copy(),

            "Tg_calciner": self.state.Tg_calciner.copy(),
            "Ts_calciner": self.state.Ts_calciner.copy(),
            "Tw_calciner": self.state.Tw_calciner.copy(),

            "Tg_preheater": self.state.Tg_preheater.copy(),
            "Ts_preheater": self.state.Ts_preheater.copy(),
            "Tw_preheater": self.state.Tw_preheater.copy(),

            "Tg_cooler": self.state.Tg_cooler.copy(),
            "Ts_cooler": self.state.Ts_cooler.copy(),
            "Tw_cooler": self.state.Tw_cooler.copy(),

            "m_dot_g": float(self.state.m_dot_g),
            "m_dot_s": float(self.state.m_dot_s),
        }
        
    # ==========================================================
    # STEADY-STATE CONVERGENCE RESIDUAL
    # ==========================================================
    def _state_residual(self, old_state):
        thermal_residual = 0.0

        zone_keys = {
            "Burning": [
                "Tg_burning",
                "Ts_burning",
                "Tw_burning",
            ],
            "Transition": [
                "Tg_transition",
                "Ts_transition",
                "Tw_transition",
            ],
            "Calciner": [
                "Tg_calciner",
                "Ts_calciner",
                "Tw_calciner",
            ],
            "Preheater": [
                "Tg_preheater",
                "Ts_preheater",
                "Tw_preheater",
            ],
            "Cooler": [
                "Tg_cooler",
                "Ts_cooler",
                "Tw_cooler",
            ],
        }

        zone_residuals = {}

        for zone, keys in zone_keys.items():

            zone_residual = 0.0

            for key in keys:
                old_value = old_state[key]
                new_value = getattr(self.state, key)

                residual = np.max(
                    np.abs(new_value - old_value)
                )

                zone_residual = max(
                    zone_residual,
                    residual,
                )

            zone_residuals[zone] = zone_residual

            thermal_residual = max(
                thermal_residual,
                zone_residual,
            )

        mass_residual = abs(
            self.mass_flow.steady_state_mass_residual
        )

        # ==========================================================
        # SOLID ENERGY HANDOFF RESIDUAL
        # ==========================================================

        solid_handoff_residual = max(
            abs(
                self.state.Hsolid_calciner_in
                - self.state.Hsolid_preheater_out
            ),
            abs(
                self.state.Hsolid_transition_in
                - self.state.Hsolid_calciner_out
            ),
        )

        return {
            "thermal": thermal_residual,
            "mass": mass_residual,
            "solid_handoff": solid_handoff_residual,
            "zones": zone_residuals,
        }
        
        

    def _update_steady_state_mass_flow(self, inputs):
        """
        Update continuous steady-state mass flows.

        All flow rates are SI:
            kg/s
        """

        # ======================================================
        # EXTERNAL INPUTS
        # ======================================================

        m_dot_raw_meal = float(
            inputs["Feed_rate_kg_s"]
        )

        m_dot_fuel = float(
            inputs["Fuel_rate_total"]
        )

        # ======================================================
        # COMBUSTION GAS
        # ======================================================

        # ======================================================
        # FUEL SPLIT
        #
        # The total air is still sized from the TOTAL fuel
        # against the dry stack O2 target -- that target is a
        # plant-level measurement and both firings share the
        # same exhaust. The air is then partitioned in the same
        # ratio as the fuel, which gives each firing the same
        # excess-air level and keeps the stack figure exact.
        # ======================================================

        kiln_fraction = self.burning.kiln_fuel_fraction

        m_dot_fuel_kiln = kiln_fraction * m_dot_fuel
        m_dot_fuel_calciner = m_dot_fuel - m_dot_fuel_kiln

        m_dot_air = (
            gas_mass_balance(
                fuel_rate_total=m_dot_fuel,
                O2=inputs["O2"],
                eps=self.eps,
            )
            - m_dot_fuel
        )

        m_dot_air_kiln = kiln_fraction * m_dot_air
        m_dot_air_calciner = m_dot_air - m_dot_air_kiln

        # The kiln burner now carries only its own share.
        m_dot_g_burning = (
            m_dot_air_kiln
            + m_dot_fuel_kiln
        )

        self.mass_flow.m_dot_fuel_kiln = m_dot_fuel_kiln
        self.mass_flow.m_dot_fuel_calciner = m_dot_fuel_calciner
        self.mass_flow.m_dot_air_kiln = m_dot_air_kiln
        self.mass_flow.m_dot_air_calciner = m_dot_air_calciner

        self.state.m_dot_fuel_kiln = m_dot_fuel_kiln
        self.state.m_dot_fuel_calciner = m_dot_fuel_calciner

        self.mass_flow.set_external_inputs(
            m_dot_raw_meal=m_dot_raw_meal,
            m_dot_fuel=m_dot_fuel,
            m_dot_air=m_dot_air,
        )

        self.mass_flow.m_dot_g_burning = (
            m_dot_g_burning
        )

        self.state.m_dot_air = (
            self.mass_flow.m_dot_air
        )

        # ======================================================
        # SOLID STREAM
        # ======================================================

        self.mass_flow.m_dot_s_preheater = (
            m_dot_raw_meal
        )

        # ======================================================
        # PREHEATER DRYING
        #
        # Free moisture evaporated in the cyclone stages
        # (chemistry.reactions.ChemistryModel.apply_preheater)
        # leaves the solid stream before the calciner and
        # leaves the plant with the exhaust gas.
        # ======================================================

        m_dot_H2O_evaporated = float(
            getattr(
                self.state,
                "m_dot_H2O_evaporated_preheater",
                0.0,
            )
        )

        self.mass_flow.m_dot_H2O_generated = (
            m_dot_H2O_evaporated
        )

        self.mass_flow.m_dot_s_calciner_in = (
            self.mass_flow.m_dot_s_preheater
            - m_dot_H2O_evaporated
        )

        # ======================================================
        # GAS: BURNING -> TRANSITION
        #
        # Residual (in-flight) calcination in the transition
        # zone adds its own CO2 to the gas stream before it
        # reaches the calciner.
        # ======================================================

        # Residual calcination inside the KILN comes first on the
        # gas path: the burning zone is upstream of the transition
        # for the gas, so its CO2 is already in the stream that
        # reaches the transition.
        m_dot_CO2_generated_burning = float(
            getattr(
                self.state,
                "m_dot_CO2_generated_burning",
                0.0,
            )
        )

        self.mass_flow.m_dot_CO2_generated_burning = (
            m_dot_CO2_generated_burning
        )

        self.mass_flow.m_dot_g_burning_out = (
            self.mass_flow.m_dot_g_burning
            + m_dot_CO2_generated_burning
        )

        m_dot_CO2_generated_transition = float(
            getattr(
                self.state,
                "m_dot_CO2_generated_transition",
                0.0,
            )
        )

        self.mass_flow.calculate_transition_flow(
            m_dot_CO2_generated=m_dot_CO2_generated_transition
        )

        # ======================================================
        # CALCINER CHEMISTRY
        # ======================================================

        m_dot_CO2_generated = float(
            getattr(
                self.state,
                "m_dot_CO2_generated_calciner",
                0.0,
            )
        )

        # Dehydroxylation transfers Bound_H2O mass from the
        # solid stream to the gas stream in the calciner, the
        # same way calcination transfers CO2.
        m_dot_H2O_generated_dehydroxylation = float(
            getattr(
                self.state,
                "m_dot_H2O_generated_dehydroxylation",
                0.0,
            )
        )

        (
            m_dot_s_calciner_out,
            _,
        ) = self.mass_flow.calculate_calciner_flow(
            m_dot_CO2_generated=m_dot_CO2_generated,
            m_dot_tertiary_air=self.state.m_dot_tertiary_air,
            m_dot_H2O_generated=m_dot_H2O_generated_dehydroxylation,
            m_dot_fuel_calciner=self.mass_flow.m_dot_fuel_calciner,
        )

        # ======================================================
        # SOLID DOWNSTREAM
        #
        # Residual (in-flight) calcination in the transition
        # zone removes its own reacted CaCO3 mass from the
        # solid stream on top of the calciner's reduction.
        # ======================================================

        self.mass_flow.m_dot_s_transition = (
            m_dot_s_calciner_out
            - self.mass_flow.m_dot_CO2_generated_transition
        )

        self.mass_flow.m_dot_s_burning = (
            self.mass_flow.m_dot_s_transition
        )

        # The kiln finishes the calcination, so the bed leaves it
        # lighter than it arrived. m_dot_s_burning is the INLET,
        # m_dot_s_cooler the OUTLET; they are no longer the same
        # number, and the clinker is the outlet one.
        self.mass_flow.calculate_burning_flow(
            m_dot_CO2_generated=m_dot_CO2_generated_burning
        )

        # ======================================================
        # GAS DOWNSTREAM
        # ======================================================

        self.mass_flow.m_dot_g_preheater = (
            self.mass_flow.m_dot_g_calciner
        )

        # m_dot_g_preheater is the gas ENTERING the preheater;
        # the exhaust also carries the evaporated moisture.
        self.mass_flow.m_dot_exhaust = (
            self.mass_flow.m_dot_g_preheater
            + self.mass_flow.m_dot_H2O_generated
        )

        # ======================================================
        # CLINKER
        # ======================================================

        self.mass_flow.m_dot_clinker = (
            self.mass_flow.m_dot_s_cooler
        )

        # ======================================================
        # COOLER AIR SPLIT (secondary / tertiary / vent)
        #
        # Cooler air is independent of the kiln's own combustion
        # gas flow (state.m_dot_g), sized from clinker throughput.
        # It splits three ways: secondary air (derived from kiln
        # stoichiometry, i.e. the non-primary share of the kiln's
        # own combustion air), tertiary air (an independent
        # cooler-side fraction routed to the precalciner), and
        # vent air (whatever remains, exhausted to atmosphere).
        #
        # Computed here (before the global mass balance) so both
        # self.mass_flow and self.state carry the same, internally
        # consistent secondary+tertiary+vent split -- the global
        # balance below needs self.mass_flow.m_dot_air_cooler and
        # self.mass_flow.m_dot_vent_air to close correctly.
        # ======================================================

        self.mass_flow.m_dot_air_cooler = (
            self.cooler.cooling_air_rate
            * self.mass_flow.m_dot_clinker
        )

        # Primary and secondary air serve the KILN burner, so
        # they are shares of the kiln's air, not of the plant's.
        self.mass_flow.m_dot_primary_air = (
            self.burning.primary_air_fraction
            * self.mass_flow.m_dot_air_kiln
        )

        self.mass_flow.m_dot_secondary_air = (
            self.mass_flow.m_dot_air_kiln
            - self.mass_flow.m_dot_primary_air
        )

        # Tertiary air IS the precalciner's combustion air, so it
        # is set by the calciner's fuel share rather than by an
        # independent fraction of the cooler flow. Reading
        # cooler_air.tertiary_air_fraction as well would
        # over-determine the split and break the stack O2 target.
        self.mass_flow.m_dot_tertiary_air = (
            self.mass_flow.m_dot_air_calciner
        )

        self.mass_flow.m_dot_vent_air = (
            self.mass_flow.m_dot_air_cooler
            - self.mass_flow.m_dot_secondary_air
            - self.mass_flow.m_dot_tertiary_air
        )

        if self.mass_flow.m_dot_vent_air < 0.0:
            raise ValueError(
                "Cooler air split infeasible: secondary + tertiary "
                "air demand exceeds total cooler air flow. Increase "
                "cooler_air.cooling_air_rate_kg_per_kg_clinker or "
                "reduce tertiary_air_fraction / primary_air_fraction."
            )

        self.state.m_dot_air_cooler = self.mass_flow.m_dot_air_cooler
        self.state.m_dot_primary_air = self.mass_flow.m_dot_primary_air
        self.state.m_dot_secondary_air = self.mass_flow.m_dot_secondary_air
        self.state.m_dot_tertiary_air = self.mass_flow.m_dot_tertiary_air
        self.state.m_dot_vent_air = self.mass_flow.m_dot_vent_air

        # ======================================================
        # GLOBAL MASS BALANCE
        # ======================================================

        self.mass_flow.calculate_global_balance()

        # ======================================================
        # STATE OUTPUTS
        # ======================================================

        # The bed ENTERING the kiln. It leaves lighter, because
        # the meal finishes calcining there.
        self.state.m_dot_s_burning_in = (
            self.mass_flow.m_dot_s_burning
        )

        # state.m_dot_s is the CLINKER, i.e. the kiln outlet and
        # the cooler's flow throughout. The cooler runs no
        # reactions, so one scalar is correct for it.
        self.state.m_dot_s = (
            self.mass_flow.m_dot_s_cooler
        )

        self.state.m_dot_s_preheater = (
            self.mass_flow.m_dot_s_preheater
        )

        self.state.m_dot_s_calciner = (
            self.mass_flow.m_dot_s_calciner_in
        )

        self.state.m_dot_s_transition = (
            self.mass_flow.m_dot_s_transition_in
        )

        self.state.m_dot_g = (
            self.mass_flow.m_dot_g_burning
        )

        self.state.m_dot_g_transition = (
            self.mass_flow.m_dot_g_transition
        )

        self.state.m_dot_g_calciner = (
            self.mass_flow.m_dot_g_calciner
        )

        self.state.m_dot_g_preheater = (
            self.mass_flow.m_dot_g_preheater
        )

        self.state.Global_mass_balance = (
            self.mass_flow.steady_state_mass_residual
        )

        mass_scale = max(
            abs(self.mass_flow.mass_flow_in),
            abs(self.mass_flow.mass_flow_out),
            1.0,
        )

        self.state.Global_mass_balance_relative = (
            abs(self.state.Global_mass_balance)
            / mass_scale
        )

        return self.state
    
    
    def step(self):

        inputs = dict(self._last_inputs)


        # ======================================================
        # INITIAL STEADY-STATE MASS FLOW
        #
        # Provides inlet flows for thermal calculations.
        # Calciner reaction products are not available yet.
        # ======================================================

        self._update_steady_state_mass_flow(inputs)

        inputs["rho_g"] = getattr(
            self.state,
            "rho_g",
            1.2
        )

        # ======================================================
        # 1. BURNING
        # ======================================================

        self.state = self.burning.apply(
            self.state,
            inputs
        )

        # ======================================================
        # 2. TRANSITION
        # ======================================================

        self.state = self.transition.apply(
            self.state
        )

        # ======================================================
        # 3. CALCINER
        # ======================================================

        self.state = self.calciner.apply(
            self.state,
        )

        # ======================================================
        # UPDATE MASS FLOW AFTER CALCINATION
        # ======================================================

        self._update_steady_state_mass_flow(inputs)

        # ======================================================
        # 4. PREHEATER
        # ======================================================

        self.state = self.preheater.apply(
            self.state,
        )

        # ======================================================
        # 5. COOLER
        # ======================================================

        self.state = self.cooler.apply(
            self.state
        )
        
        

        return self.state
    
        



    def run(self):

        # ======================================================
        # STEADY-STATE SOLVER
        #
        # 150 (was 100): the cooler air split (secondary/tertiary/
        # vent) adds one more coupled dependency -- tertiary air
        # depends on clinker mass, which itself only settles after
        # the calciner/transition solid chain converges -- so the
        # solid_handoff residual now needs a handful more Picard
        # iterations to clear its tolerance. The residual decays
        # smoothly and geometrically (~0.75x/iteration); 100 was
        # cutting it off just before it crossed the threshold.
        #
        # 400 (was 150): residual calcination inside the kiln
        # (Faz 4b) is a stiff coupling. The reaction is very sharp
        # in temperature -- at kiln conditions k*tau is large
        # enough that it runs to completion wherever the bed is
        # hot enough -- so what oscillates between sweeps is WHERE
        # the front sits, and the bed temperature and the sink
        # chase each other. Burning.calcination_relaxation damps
        # it per cell, but the approach is no longer geometric and
        # takes ~125 sweeps at either discretisation. 150 left
        # almost no margin; this is headroom, not a change of
        # answer -- the run stops at the same tolerance either
        # way.
        #
        # The proper fix is not more damping (heavier damping is
        # WORSE here: 0.25 and below do not converge at all,
        # because they slow the approach without touching the
        # front's oscillation). It is CO2 back-pressure in the
        # calcination kinetics, which smooths the front instead of
        # suppressing it, and is already on the roadmap as a
        # missing closure.
        # ======================================================
        max_iterations = 400

        thermal_tolerance = 1e-3
        mass_tolerance = 1e-6


        print(
            "STEADY-STATE SOLVE STARTED",
            flush=True,
        )

        # ======================================================
        # CONVERGENCE LOOP
        # ======================================================
        for iteration in range(max_iterations):

            old_state = self._snapshot_state()

            try:
                self.step()

            except Exception as e:

                print(
                    f"[STEADY STATE CRASH @ "
                    f"iteration {iteration + 1}] "
                    f"-> {repr(e)}",
                    flush=True,
                )

                raise

            residual = self._state_residual(
                old_state
            )

            zones = residual["zones"]

            print(
                f"[ITER {iteration + 1:05d}] "
                f"thermal={residual['thermal']:.6e} K | "
                f"Burning={zones['Burning']:.6e} | "
                f"Transition={zones['Transition']:.6e} | "
                f"Calciner={zones['Calciner']:.6e} | "
                f"Preheater={zones['Preheater']:.6e} | "
                f"Cooler={zones['Cooler']:.6e} | "
                f"mass={residual['mass']:.6e} kg/s | "
                f"solid_handoff={residual['solid_handoff']:.6e} W",
                flush=True,
            )

            # ==================================================
            # CONVERGENCE CHECK
            # ==================================================
            if (
                residual["thermal"] < thermal_tolerance
                and
                residual["mass"] < mass_tolerance
                and
                residual["solid_handoff"] < 1e-3
            ):

                print(
                    "STEADY STATE CONVERGED "
                    f"@ iteration {iteration + 1}",
                    flush=True,
                )
                
                        # ======================================================
                # ENERGY HANDOFF DIAGNOSTIC
                # Read-only: no physics/state modification
                # ======================================================

                print("\n========== ENERGY HANDOFF DIAGNOSTIC ==========")

                print("\n--- Cooler -> Burning (Gas) ---")
                print(
                    f"Hgas_cooler_out       = "
                    f"{self.state.Hgas_cooler_out:.12e} W"
                )
                print(
                    f"Hgas_burning_in       = "
                    f"{getattr(self.state, 'Hgas_burning_in', 0.0):.12e} W"
                )
                print(
                    f"Gas handoff diff       = "
                    f"{self.state.Hgas_cooler_out - getattr(self.state, 'Hgas_burning_in', 0.0):.12e} W"
                )

                print("\n--- Burning -> Transition (Gas) ---")
                print(
                    f"Hgas_burning_out      = "
                    f"{self.state.Hgas_burning_out:.12e} W"
                )
                print(
                    f"Hgas_transition_in    = "
                    f"{self.state.Hgas_transition_in:.12e} W"
                )
                print(
                    f"Gas handoff diff       = "
                    f"{self.state.Hgas_burning_out - self.state.Hgas_transition_in:.12e} W"
                )

                print("\n--- Transition -> Calciner (Gas) ---")
                print(
                    f"Hgas_transition_out   = "
                    f"{self.state.Hgas_transition_out:.12e} W"
                )
                print(
                    f"Hgas_calciner_in      = "
                    f"{self.state.Hgas_calciner_in:.12e} W"
                )
                print(
                    f"Gas handoff diff       = "
                    f"{self.state.Hgas_transition_out - self.state.Hgas_calciner_in:.12e} W"
                )

                print("\n--- Calciner -> Preheater (Gas) ---")
                print(
                    f"Hgas_calciner_out     = "
                    f"{self.state.Hgas_calciner_out:.12e} W"
                )
                print(
                    f"Hgas_preheater_in     = "
                    f"{self.state.Hgas_preheater_in:.12e} W"
                )
                print(
                    f"Gas handoff diff       = "
                    f"{self.state.Hgas_calciner_out - self.state.Hgas_preheater_in:.12e} W"
                )

                print("\n--- Preheater -> Calciner (Solid) ---")
                print(
                    f"Hsolid_preheater_out  = "
                    f"{self.state.Hsolid_preheater_out:.12e} W"
                )
                print(
                    f"Hsolid_calciner_in    = "
                    f"{self.state.Hsolid_calciner_in:.12e} W"
                )
                print(
                    f"Solid handoff diff     = "
                    f"{self.state.Hsolid_preheater_out - self.state.Hsolid_calciner_in:.12e} W"
                )

                print("\n--- Calciner -> Transition (Solid) ---")
                print(
                    f"Hsolid_calciner_out   = "
                    f"{self.state.Hsolid_calciner_out:.12e} W"
                )
                print(
                    f"Hsolid_transition_in  = "
                    f"{self.state.Hsolid_transition_in:.12e} W"
                )
                print(
                    f"Solid handoff diff     = "
                    f"{self.state.Hsolid_calciner_out - self.state.Hsolid_transition_in:.12e} W"
                )

                print("\n--- Transition -> Burning (Solid) ---")
                print(
                    f"Hsolid_transition_out = "
                    f"{self.state.Hsolid_transition_out:.12e} W"
                )
                print(
                    f"Hsolid_burning_in     = "
                    f"{self.state.Hsolid_burning_in:.12e} W"
                )
                print(
                    f"Solid handoff diff     = "
                    f"{self.state.Hsolid_transition_out - self.state.Hsolid_burning_in:.12e} W"
                )

                print("\n--- Burning -> Cooler (Solid) ---")
                print(
                    f"Hsolid_burning_out    = "
                    f"{self.state.Hsolid_burning_out:.12e} W"
                )
                print(
                    f"Hsolid_cooler_in      = "
                    f"{self.state.Hsolid_cooler_in:.12e} W"
                )
                print(
                    f"Solid handoff diff     = "
                    f"{self.state.Hsolid_burning_out - self.state.Hsolid_cooler_in:.12e} W"
                )

                print("\n--- LOCAL ENERGY RESIDUALS ---")
                print(
                    f"Burning residual      = "
                    f"{self.state.Burning_energy_balance:.12e} W"
                )
                print(
                    f"Transition residual   = "
                    f"{self.state.Transition_energy_balance:.12e} W"
                )
                print(
                    f"Calciner residual     = "
                    f"{self.state.Calciner_energy_balance:.12e} W"
                )
                print(
                    f"Preheater residual    = "
                    f"{self.state.Preheater_energy_balance:.12e} W"
                )
                print(
                    f"Cooler residual       = "
                    f"{self.state.Cooler_energy_balance:.12e} W"
                )

                # Exact accounting of the Cooler residual,
                # R = -gas_gap - solid_gap + wall_mismatch.
                # See pyroprocess/cooler/heat_transfer.py.
                print(
                    f"  gas_gap (Picard)    = "
                    f"{self.cooler.residual_gas_gap:.12e} W"
                )
                print(
                    f"  solid_gap (Picard)  = "
                    f"{self.cooler.residual_solid_gap:.12e} W"
                )
                print(
                    f"  wall_mismatch       = "
                    f"{self.cooler.residual_wall_mismatch:.12e} W"
                )
                print(
                    f"  decomposition check = "
                    f"{self.cooler.residual_decomposition_check:.12e} W"
                )

                print("\n--- REACTION TERMS ---")
                print(
                    f"Calcination sink      = "
                    f"{self.state.Calcination_Q_sink:.12e} W"
                )
                print(
                    f"Transition reaction   = "
                    f"{self.state.Calcination_Q_transition:.12e} W"
                )
                print(
                    f"Preheater reaction    = "
                    f"{self.state.Preheater_Q_sink:.12e} W"
                )

                print("===============================================\n")

                # ==================================================
                # FINAL STEADY-STATE PHYSICAL CHECK
                #
                # Read-only report of the actual converged state.
                # No additional step() is executed.
                # ==================================================

                idx = self.state.Tg_burning.shape[0] // 2
                idx_preheater = self.state.Tg_preheater.shape[0] // 2

                print(
                    "\n========== FINAL STEADY-STATE PHYSICAL CHECK ==========",
                    flush=True,
                )

                # --------------------------------------------------
                # MASS FLOWS
                # --------------------------------------------------

                print(
                    "\n--- MASS FLOWS ---",
                    flush=True,
                )

                print(
                    f"m_dot_g      = "
                    f"{getattr(self.state, 'm_dot_g', None)} kg/s",
                    flush=True,
                )

                print(
                    f"m_dot_s      = "
                    f"{getattr(self.state, 'm_dot_s', None)} kg/s",
                    flush=True,
                )

                print(
                    f"Clinker flow = "
                    f"{getattr(self.state, 'clinker_flow', None)} kg/s",
                    flush=True,
                )

                # --------------------------------------------------
                # TEMPERATURES
                # --------------------------------------------------

                print(
                    "\n--- TEMPERATURES ---",
                    flush=True,
                )

                print("Burning:", flush=True)
                print(
                    f"    Tg_mid = "
                    f"{self.state.Tg_burning[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_burning[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_burning[idx]:.6f} K",
                    flush=True,
                )

                print("Transition:", flush=True)
                print(
                    f"    Tg_mid = "
                    f"{self.state.Tg_transition[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_transition[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_transition[idx]:.6f} K",
                    flush=True,
                )

                print("Calciner:", flush=True)
                print(
                    f"    Tg_mid = "
                    f"{self.state.Tg_calciner[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_calciner[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_calciner[idx]:.6f} K",
                    flush=True,
                )

                print("Preheater:", flush=True)
                print(
                    f"    Tg_mid = "
                    f"{self.state.Tg_preheater[idx_preheater]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_preheater[idx_preheater]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_preheater[idx_preheater]:.6f} K",
                    flush=True,
                )

                print("Cooler:", flush=True)
                print(
                    f"    Tg_mid = "
                    f"{self.state.Tg_cooler[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_cooler[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_cooler[idx]:.6f} K",
                    flush=True,
                )

                # --------------------------------------------------
                # FUEL
                # --------------------------------------------------

                print(
                    "\n--- FUEL ---",
                    flush=True,
                )

                print(
                    "Fuel = Petcoke",
                    flush=True,
                )

                print(
                    f"Fuel_rate_total = "
                    f"{self._last_inputs.get('Fuel_rate_total', None)} kg/s",
                    flush=True,
                )

                # --------------------------------------------------
                # ENERGY
                # --------------------------------------------------

                print(
                    "\n--- ENERGY ---",
                    flush=True,
                )

                print(
                    f"Q_petcoke = "
                    f"{getattr(self.state, 'Q_petcoke', None)} W",
                    flush=True,
                )


                print(
                    f"Q_burning = "
                    f"{getattr(self.state, 'Q_burning', None)} W",
                    flush=True,
                )

                # --------------------------------------------------
                # WALL LOSSES
                # --------------------------------------------------

                print(
                    "\n--- WALL LOSSES ---",
                    flush=True,
                )

                print(
                    f"Wall_loss_burning    = "
                    f"{getattr(self.state, 'Wall_loss_burning', None)} W",
                    flush=True,
                )

                print(
                    f"Wall_loss_transition = "
                    f"{getattr(self.state, 'Wall_loss_transition', None)} W",
                    flush=True,
                )

                print(
                    f"Wall_loss_calciner   = "
                    f"{getattr(self.state, 'Wall_loss_calciner', None)} W",
                    flush=True,
                )

                print(
                    f"Wall_loss_preheater  = "
                    f"{getattr(self.state, 'Wall_loss_preheater', None)} W",
                    flush=True,
                )

                print(
                    f"Wall_loss_cooler     = "
                    f"{getattr(self.state, 'Wall_loss_cooler', None)} W",
                    flush=True,
                )

                # --------------------------------------------------
                # REACTION HEAT
                # --------------------------------------------------

                print(
                    "\n--- REACTION HEAT ---",
                    flush=True,
                )

                print(
                    f"Calcination_Q_sink = "
                    f"{getattr(self.state, 'Calcination_Q_sink', None)} W",
                    flush=True,
                )

                print(
                    f"Preheater_Q_sink   = "
                    f"{getattr(self.state, 'Preheater_Q_sink', None)} W",
                    flush=True,
                )

                # --------------------------------------------------
                # OUTLET ENTHALPY
                # --------------------------------------------------

                print(
                    "\n--- OUTLET ENTHALPY ---",
                    flush=True,
                )

                print(
                    f"Hgas_cooler_out   = "
                    f"{getattr(self.state, 'Hgas_cooler_out', None)} W",
                    flush=True,
                )

                print(
                    f"Hsolid_cooler_out = "
                    f"{getattr(self.state, 'Hsolid_cooler_out', None)} W",
                    flush=True,
                )

                print(
                    "\n=======================================================",
                    flush=True,
                )

                # ==================================================
                # FINAL ENERGY VALIDATION
                #
                # Validate the actual converged state.
                # No additional step() is executed.
                # ==================================================

                self._validate_solid_handoffs()
                self._validate_energy_balances()
                self._validate_global_energy_balance()
                self._validate_global_mass_balance()
                self._validate_cooler_air_split()
                self._validate_co2_species_balance()

                # ==================================================
                # PHYSICS DIAGNOSTICS
                #
                # Read-only. The balances above verify that the
                # bookkeeping is self-consistent; they cannot fail on
                # a wrong reaction enthalpy, a handoff that rescales
                # temperature, or a physically impossible profile,
                # because every one of those closes exactly. This
                # report is the part that can.
                #
                # It measures only -- nothing here feeds back into
                # the solution, and it runs after convergence.
                # ==================================================

                print(diagnostics.report(self))

                return self.state

        # ======================================================
        # NOT CONVERGED
        # ======================================================
        raise RuntimeError(
            "Steady-state solution did not converge "
            f"after {max_iterations} iterations."
        )


if __name__ == "__main__":

    # ======================================================
    # CONFIG LOAD
    # ======================================================
    twin_cfg = load_cfg("configs/twin_cfg.yaml")


    # ======================================================
    # STATE INIT
    # ======================================================
    state = GlobalState(N=twin_cfg["plant"]["N"])

    # ======================================================
    # TWIN INIT
    # ======================================================
    twin = Twin(
        state=state,
        cfg=twin_cfg
    )

    # ======================================================
    # RUN
    # ======================================================
    twin.run()

    # ======================================================
    # VISUALIZATION
    # ======================================================
    plot_zone_temperature_profiles(twin)
    plot_global_temperature_profile(twin)
    plot_mass_flow_profiles(twin)
