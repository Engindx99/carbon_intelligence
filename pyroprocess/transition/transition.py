import numpy as np

from physics.physics import h_gas
from physics.closure_config import closure_settings

from chemistry.phases import copy_solid_phases
from chemistry.phases import get_cell_solid_flow
from chemistry.calcination import CalcinationModel

from . import gas_phase
from . import solid_phase
from . import heat_transfer


class Transition:

    def __init__(self, N=5, L=25.0, cfg=None):

        if cfg is None:
            import yaml

            with open("configs/twin_cfg.yaml") as handle:
                cfg = yaml.safe_load(handle)

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
        #
        # Faz 5 / Faz 3. The three area densities are no longer set
        # here. They came from an INLINED copy of the packed-bed
        # correlation 6(1 - eps)/d_p with the 4.2 m kiln bore
        # substituted for the particle diameter, plus a_ws = 0.6 a_gs
        # and a_gw taken as the FULL perimeter on top of it. That
        # charged the wall twice: (a_ws + a_gw) D/4 came to 1.585
        # against a physical ceiling of 1, a 58.5% over-count, and it
        # gave this 25 m zone a larger gas -> solid exchange capacity
        # (144.7 kW/K) than the 60 m kiln itself (121.0 kW/K).
        #
        # They now come per thermal_step from bed_segment_geometry,
        # which splits the perimeter exactly, so a_ws + a_gw == 4/D
        # holds by construction and the areas follow the actual bed
        # loading instead of being frozen at construction.
        # ================= WALL GEOMETRY =================
        self.wall_perimeter = np.pi * self.D
        self.A_wall = self.wall_perimeter * self.L
        self.A_wall_cell = self.A_wall / self.N

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
        # fill_fraction used to be pinned here at 0.10 and nothing
        # solved for it. It now comes from mass continuity per
        # thermal_step, so there is nothing to set.

        # ================= FLOW =================
        self.u_g = 0.0
        self.u_s = 0.0

        # ================= MOTION =================
        # The same kiln tube as the burning zone, so the same
        # rotation. Read from the same config block rather than
        # copied, so the two cannot drift apart.
        motion = cfg.get("motion", {})

        self.rpm_default = motion.get("rpm_default", 1.5)
        self.slope_deg = motion.get("inclination_deg", 3.0)

        # ================= HEAT TRANSFER =================
        # Faz 5: hv_gs / hv_gw / hv_ws are gone from this zone, the
        # same way they are gone from burning. ZONE_HT_CONFIG no
        # longer carries a "transition" entry.
        self.closure = closure_settings(cfg)

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

        if state.Tg_transition.shape != (self.N,):
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
            state.m_dot_g_transition_cells
            * h_gas(
                state.Tg_transition,
                self.T_ref,
            )
        )

        # Per-cell flow: the bed calcines along this zone, so a
        # single scalar would be the true flow in at most one
        # cell. thermal_step publishes the profile it solved on.
        state.Hs_transition = (
            state.m_dot_s_transition_cells
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
        # Hgas_transition_out / Hsolid_transition_out are set by
        # thermal_step, which multiplies each reconstructed
        # outlet face by the flow that face carries. Re-deriving
        # them here by extrapolating the Hg/Hs arrays would give
        # a different number, because extrapolating a product of
        # two varying profiles is not the product of their
        # extrapolations -- and it is the flux thermal_step
        # booked in its own energy balance that the next zone
        # must receive.

        # ======================================================
        # STEADY-STATE SOLID SPECIES FLOWS [kg/s]
        #
        # Inlet: the flow leaving the last calciner cell.
        # Residual in-flight calcination is converted
        # cumulatively along the CaCO3 flow marched by
        # calcination.resolve_transition_calcination(); the
        # flow leaving the last cell is what Burning receives.
        # ======================================================

        calciner_solid_flows = state.material_flows["calciner"].solids

        self.chemistry.solid_flow_profile(
            get_cell_solid_flow(
                calciner_solid_flows,
                calciner_solid_flows.CaCO3.size - 1,
            ),
            state.m_dot_CaCO3_out_transition_cells,
            state.material_flows["transition"].solids,
            state.material_flows["transition"].gases,
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
    # GAS ENTHALPY TO NEXT ZONE
    # ======================================================
    def gas_enthalpy_out(self, Hg):
        return gas_phase.gas_enthalpy_out(Hg)

    # ======================================================
    # SOLID ENTHALPY TO NEXT ZONE
    # ======================================================
    def solid_enthalpy_out(self, Hs):
        return solid_phase.solid_enthalpy_out(Hs)
