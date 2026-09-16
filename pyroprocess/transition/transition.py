import numpy as np

from physics.physics import h_gas
from physics.physics import ZONE_HT_CONFIG

from chemistry.phases import copy_solid_phases
from chemistry.calcination import CalcinationModel

from . import gas_phase
from . import solid_phase
from . import heat_transfer


class Transition:

    def __init__(self, N=5, L=25.0):

        self.N = N
        self.L = L
        self.dz = L / N

        self.chemistry = CalcinationModel()

        # ================= ZONE =================
        self.zone = "transition"

        self.energy_in = 0.0
        self.energy_out = 0.0
        self.energy_residual = 0.0

        # ================= GEOMETRY =================
        self.D = 4.2
        self.A_cross = np.pi * self.D**2 / 4.0
        self.V_total = self.A_cross * self.L
        self.V_cell = self.V_total / self.N

        # ================= INTERFACIAL AREA =================
        self.epsilon_bed = 0.35
        self.k_interfacial = 1.0

        a_gs_base = 6.0 * (1.0 - self.epsilon_bed) / self.D

        self.a_gs = self.k_interfacial * a_gs_base
        self.a_ws = 0.6 * self.a_gs

        # ================= WALL GEOMETRY =================
        self.wall_perimeter = np.pi * self.D
        self.A_wall = self.wall_perimeter * self.L
        self.A_wall_cell = self.A_wall / self.N
        self.a_gw = self.A_wall_cell / self.V_cell

        # ================= REFRACTORY =================
        self.refractory_thickness = 0.05
        self.refractory_conductivity = 1.8

        self.V_wall = self.A_wall * self.refractory_thickness
        self.V_wall_cell = self.V_wall / self.N

        # ================= EXTERNAL WALL =================
        self.h_ext = 12.0
        self.T_ref = 298.15
        self.T_amb = 300.0

        # ================= PROPERTIES =================
        self.rho_g = 0.30
        self.rho_s = 1100.0
        self.rho_wall = 3000.0

        self.Cp_g = 1150.0
        self.Cp_s = 850.0
        self.Cp_wall = 1000.0

        # ================= BED =================
        self.fill_fraction = 0.10

        # ================= FLOW =================
        self.u_g = 0.0
        self.u_s = 0.0

        # ================= HEAT TRANSFER =================
        cfg = ZONE_HT_CONFIG[self.zone]

        self.hv_gs = cfg["hv_gs"]
        self.hv_gw = cfg["hv_gw"]
        self.hv_ws = cfg["hv_ws"]

        # ================= NUMERICAL =================
        self.eps = 1e-9

        # ================= BUFFERS =================
        self._dTg_dz = np.zeros(N)
        self._dTs_dz = np.zeros(N)

        # ================= CACHE =================
        self._rho_g_Vcell_Cp_g = self.rho_g * self.V_cell * self.Cp_g
        self._rho_s_Vcell_Cp_s = self.rho_s * self.V_cell * self.Cp_s
        self._rho_wall_Vwall_cell_Cp = self.rho_wall * self.V_wall_cell * self.Cp_wall


    # ======================================================
    # THERMAL STEP
    #
    # Delegates to heat_transfer.thermal_step(). Kept as a
    # bound method (rather than deleted) so the public
    # interface Transition.thermal_step(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (burning.py, cooler.py, preheater.py, precalciner).
    # ======================================================
    def thermal_step(self, Tg, Ts, Tw, state):

        return heat_transfer.thermal_step(
            self,
            Tg,
            Ts,
            Tw,
            state,
        )


    # ======================================================
    # STATE UPDATE
    # ======================================================
    def apply(self, state):

        # ======================================================
        # STATE INTEGRITY CHECK
        # ======================================================
        if not isinstance(state.Tg_transition, np.ndarray):
            raise TypeError("Tg_transition must be np.ndarray")

        if state.Tg_transition.shape != (5,):
            raise ValueError(
                f"Transition shape corrupted: {state.Tg_transition.shape}"
            )

        # ======================================================
        # FLOW VARIABLES
        # ======================================================
        state.u_g = getattr(
            state,
            "u_g",
            self.u_g,
        )

        state.u_s = getattr(
            state,
            "u_s",
            self.u_s,
        )

        state.m_dot_g_transition = getattr(
            state,
            "m_dot_g_transition",
            0.0,
        )

        state.m_dot_s_transition = getattr(
            state,
            "m_dot_s_transition",
            0.0,
        )

        # ======================================================
        # INLET ENTHALPY
        #
        # GAS:
        # Burning -> Transition
        #
        # SOLID:
        # ILC -> Transition
        # ======================================================

        state.Hgas_transition_in = (
            state.Hgas_burning_out
        )

        state.Hsolid_transition_in = (
            state.Hsolid_calciner_out
        )

        # ======================================================
        # INLET TEMPERATURE FROM ENTHALPY
        # ======================================================
        Tg_in = self.gas_inlet_temperature_from_enthalpy(
            state.Hgas_transition_in,
            state,
        )

        Ts_in = self.solid_inlet_temperature_from_enthalpy(
            state.Hsolid_transition_in,
            state,
        )

        # ======================================================
        # APPLY INLET BOUNDARY CONDITIONS
        # ======================================================


        # ======================================================
        # STEADY-STATE THERMAL STEP
        # ======================================================
        (
            Tg,
            Ts,
            Tw,
            wall_loss,
            wall_debug,
        ) = self.thermal_step(
            state.Tg_transition,
            state.Ts_transition,
            state.Tw_transition,
            state
        )

        # ======================================================
        # UPDATE TEMPERATURE STATES
        # ======================================================
        state.Tg_transition = Tg
        state.Ts_transition = Ts
        state.Tw_transition = Tw

        # ======================================================
        # TRANSITION CHEMISTRY
        # ======================================================



        # ======================================================
        # UPDATE ENTHALPY STATES
        # ======================================================

        state.Hg_transition = (
            state.m_dot_g_transition
            * h_gas(
                state.Tg_transition,
                self.T_ref,
            )
        )

        state.Hs_transition = (
            state.m_dot_s_transition
            * self.Cp_s
            * (
                state.Ts_transition
                - self.T_ref
            )
        )

        # ======================================================
        # WALL LOSS
        # ======================================================
        state.Wall_loss_transition = float(
            wall_loss
        )

        # ======================================================
        # WALL DEBUG
        # ======================================================
        if wall_debug is None:
            wall_debug = {}

        state.wall_debug_transition = {
            "q_loss_mean": wall_debug.get(
                "q_loss_mean",
                0.0,
            ),
            "q_loss_total": wall_debug.get(
                "wall_loss_total",
                0.0,
            ),
            "A_wall": wall_debug.get(
                "A_wall",
                0.0,
            ),
            "V_cell": wall_debug.get(
                "V_cell",
                0.0,
            ),
            "N": wall_debug.get(
                "N",
                0,
            ),
        }

        state.q_loss_mean_transition = (
            state.wall_debug_transition[
                "q_loss_mean"
            ]
        )

        state.A_wall_transition = (
            state.wall_debug_transition[
                "A_wall"
            ]
        )

        state.V_cell_transition = (
            state.wall_debug_transition[
                "V_cell"
            ]
        )

        state.N_transition = (
            state.wall_debug_transition[
                "N"
            ]
        )

        # ======================================================
        # ENERGY OUT
        # ======================================================
        state.Hgas_transition_out = (
            self.gas_enthalpy_out(
                state.Hg_transition
            )
        )

        state.Hsolid_transition_out = (
            self.solid_enthalpy_out(
                state.Hs_transition
            )
        )

        # ======================================================
        # SOLID PHASE HANDOFF
        # Transition -> Burning
        # ======================================================

        copy_solid_phases(
            state.materials["transition"].solids,
            state.materials["burning"].solids,
        )

        # ======================================================
        # SOLID PHASE HANDOFF DIAGNOSTIC
        # ======================================================

        print("\n========== TRANSITION -> BURNING SOLID HANDOFF ==========")

        for phase in [
            "H2O",
            "Bound_H2O",
            "CaCO3",
            "CaO",
            "SiO2",
            "Al2O3",
            "Fe2O3",
            "C2S",
            "C3S",
            "C3A",
            "C4AF",
        ]:
            transition = getattr(
                state.materials["transition"].solids,
                phase,
            )

            burning = getattr(
                state.materials["burning"].solids,
                phase,
            )

            diff = np.sum(burning - transition)

            print(
                f"{phase:10s}: "
                f"transition={np.sum(transition):.6e}, "
                f"burning={np.sum(burning):.6e}, "
                f"diff={diff:.6e}"
            )

        print("==========================================================")

        # ======================================================
        # STEADY-STATE STORED ENERGY
        # ======================================================
        state.Transition_gas_stored = 0.0
        state.Transition_solid_stored = 0.0
        state.Transition_wall_stored = 0.0

        state.Transition_stored_energy_change = 0.0

        # ======================================================
        # STEADY-STATE ENERGY BALANCE
        # ======================================================
        state.Transition_energy_balance = (
            state.Hgas_transition_in
            + state.Hsolid_transition_in
            - state.Hgas_transition_out
            - state.Hsolid_transition_out
            - state.Wall_loss_transition
            - state.Calcination_Q_transition
        )

        return state


    # ======================================================
    # TEMPERATURE FROM INLET ENTHALPY
    #
    # Delegates to gas_phase/solid_phase. Kept as bound
    # methods (rather than deleted) so the public interface
    # is unchanged.
    # ======================================================
    def gas_inlet_temperature_from_enthalpy(self, H, state):
        return gas_phase.gas_inlet_temperature_from_enthalpy(
            self,
            H,
            state,
        )

    def solid_inlet_temperature_from_enthalpy(self, H, state):
        return solid_phase.solid_inlet_temperature_from_enthalpy(
            self,
            H,
            state,
        )

    # ======================================================
    # GAS ENTHALPY TO NEXT ZONE
    # ======================================================
    def gas_enthalpy_out(self, Hg):
        return gas_phase.gas_enthalpy_out(Hg)

    # ======================================================
    # SOLID ENTHALPY TO NEXT ZONE
    # ======================================================
    def solid_enthalpy_out(self, Hs):
        return solid_phase.solid_enthalpy_out(Hs)
