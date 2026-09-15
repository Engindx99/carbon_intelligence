from pyroprocess.globalstate import GlobalState
from pyroprocess.burning import Burning
from pyroprocess.transition import Transition
from pyroprocess.precalciner import Calciner
from pyroprocess.preheater import Preheater
from pyroprocess.cooler import Cooler

from physics.physics import gas_mass_balance
from physics.steady_state_mass import SteadyStateMassFlow


from validators.energy import validate_energy
from validators.mass import validate_mass
from reporter.validation import report_validation

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
            N=cfg["plant"]["N"],
            L=cfg["preheater"]["length"],
        )

        self.cooler = Cooler(
            N=cfg["plant"]["N"],
            L=cfg["cooler"]["length"],
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
        Q_burning = state.Q_burning

        global_energy_in = (
            H_rawmeal_in
            + H_air_in
            + Q_burning
        )

        # ======================================================
        # GLOBAL EXTERNAL OUTPUT
        # ======================================================

        H_exhaust_out = state.Hgas_preheater_out
        H_clinker_out = state.Hsolid_cooler_out

        Q_wall_total = (
            state.Wall_loss_burning
            + state.Wall_loss_transition
            + state.Wall_loss_calciner
            + state.Wall_loss_preheater
            + state.Wall_loss_cooler
        )

        Q_reaction_total = (
            state.Calcination_Q_transition
            + state.Calcination_Q_sink
            + state.Preheater_Q_sink
            + state.Burning_Q_sink
        )
        
        print("\n========== GLOBAL REACTION DEBUG ==========")
        print(f"Calcination_Q_transition = {state.Calcination_Q_transition:.12e} W")
        print(f"Calcination_Q_sink       = {state.Calcination_Q_sink:.12e} W")
        print(f"Preheater_Q_sink         = {state.Preheater_Q_sink:.12e} W")
        print(f"Burning_Q_sink           = {state.Burning_Q_sink:.12e} W")
        print(f"Q_reaction_total         = {Q_reaction_total:.12e} W")
        print("==========================================")

        global_energy_out = (
            H_exhaust_out
            + H_clinker_out
            + Q_wall_total
            + Q_reaction_total
        )

        # ======================================================
        # GLOBAL ENERGY VALIDATION
        # ======================================================

        result = validate_energy(
            energy_in=global_energy_in,
            energy_out=global_energy_out,
            energy_source=0.0,
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
            f"    Air               = "
            f"{mass_flow.m_dot_air:.6e} kg/s"
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

    def _validate_co2_species_balance(self):

        mass_flow = self.mass_flow

        co2_generated_total = (
            mass_flow.m_dot_CO2_generated
            + mass_flow.m_dot_CO2_generated_transition
        )

        co2_in_gas_stream = (
            mass_flow.m_dot_exhaust
            - mass_flow.m_dot_g_burning
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

        m_dot_g_burning = gas_mass_balance(
            fuel_rate_total=m_dot_fuel,
            O2=inputs["O2"],
            eps=self.eps,
        )

        m_dot_air = (
            m_dot_g_burning
            - m_dot_fuel
        )

        self.mass_flow.set_external_inputs(
            m_dot_raw_meal=m_dot_raw_meal,
            m_dot_fuel=m_dot_fuel,
            m_dot_air=m_dot_air,
        )

        self.mass_flow.m_dot_g_burning = (
            m_dot_g_burning
        )

        # ======================================================
        # SOLID STREAM
        # ======================================================

        self.mass_flow.m_dot_s_preheater = (
            m_dot_raw_meal
        )

        self.mass_flow.m_dot_s_calciner_in = (
            self.mass_flow.m_dot_s_preheater
        )

        # ======================================================
        # GAS: BURNING -> TRANSITION
        #
        # Residual (in-flight) calcination in the transition
        # zone adds its own CO2 to the gas stream before it
        # reaches the calciner.
        # ======================================================

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

        (
            m_dot_s_calciner_out,
            m_dot_g_calciner,
        ) = self.mass_flow.calculate_calciner_flow(
            m_dot_CO2_generated=m_dot_CO2_generated
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

        self.mass_flow.m_dot_s_cooler = (
            self.mass_flow.m_dot_s_burning
        )

        # ======================================================
        # GAS DOWNSTREAM
        # ======================================================

        self.mass_flow.m_dot_g_preheater = (
            self.mass_flow.m_dot_g_calciner
        )

        self.mass_flow.m_dot_exhaust = (
            self.mass_flow.m_dot_g_preheater
        )

        # ======================================================
        # CLINKER
        # ======================================================

        self.mass_flow.m_dot_clinker = (
            self.mass_flow.m_dot_s_cooler
        )

        # ======================================================
        # GLOBAL MASS BALANCE
        # ======================================================

        self.mass_flow.calculate_global_balance()

        # ======================================================
        # STATE OUTPUTS
        # ======================================================

        self.state.m_dot_s = (
            self.mass_flow.m_dot_s_burning
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
        # ======================================================
        max_iterations = 100

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
                    f"{self.state.Tg_preheater[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Ts_mid = "
                    f"{self.state.Ts_preheater[idx]:.6f} K",
                    flush=True,
                )
                print(
                    f"    Tw_mid = "
                    f"{self.state.Tw_preheater[idx]:.6f} K",
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
                self._validate_co2_species_balance()

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
    state = GlobalState()

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
    