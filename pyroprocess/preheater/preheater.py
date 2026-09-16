import numpy as np

from physics.physics import interfacial_areas
from physics.physics import kiln_geometry
from physics.physics import wall_geometry
from physics.physics import ZONE_HT_CONFIG

from chemistry.phases import resample_solid_phases
from chemistry.reactions import ChemistryModel

from . import gas_phase
from . import solid_phase
from . import heat_transfer

from .stage1 import Stage1
from .stage2 import Stage2
from .stage3 import Stage3
from .stage4 import Stage4
from .stage5 import Stage5


class Preheater:

    def __init__(self, N=5, L=25.0, nodes_per_stage=20):

        self.N = N
        self.L = L
        self.dz = L / N

        # Equal sub-volumes each stage's heat transfer is marched
        # through (heat_transfer.solve_stage). Numerical, not a
        # stage count: N stays the number of cyclone stages.
        if int(nodes_per_stage) != nodes_per_stage or nodes_per_stage < 1:
            raise ValueError("nodes_per_stage must be an integer >= 1")

        self.nodes_per_stage = int(nodes_per_stage)

        self.zone = "preheater"
        
        self.stages = [
            Stage1(),
            Stage2(),
            Stage3(),
            Stage4(),
            Stage5(),
        ]
        
        # ======================================================
        # ENERGY DIAGNOSTICS
        # ======================================================
        self.energy_in = 0.0
        self.energy_out = 0.0
        self.energy_residual = 0.0
        self.Q_reaction_total = 0.0
        
        # ======================================================
        # STAGE REFERENCE GAS TEMPERATURE RANGES
        # ======================================================
        # These are operating reference bounds only.
        # They are NOT hard temperature constraints.

        gas_T_bounds_K = [
            (573.15, 583.15),    # Stage 1
            (763.15, 773.15),    # Stage 2
            (903.15, 923.15),    # Stage 3
            (1023.15, 1043.15),  # Stage 4
            (1113.15, 1143.15),  # Stage 5
        ]

        for stage, (T_min, T_max) in zip(
            self.stages,
            gas_T_bounds_K,
        ):
            stage.gas_T_min = T_min
            stage.gas_T_max = T_max


        self.chemistry = ChemistryModel()

        # ================= NUMERICAL =================
        self.eps = 1e-9

        # ================= GEOMETRY =================
        self.D = 4.2

        (
            self.A_cross,
            self.V_total,
            self.V_cell,
        ) = kiln_geometry(
            D=self.D,
            L=self.L,
            N=self.N,
        )

        # ================= INTERFACIAL AREA =================
        self.epsilon_bed = 0.35
        self.k_interfacial = 1.0

        (
            self.a_gs,
            self.a_ws,
        ) = interfacial_areas(
            D=self.D,
            epsilon_bed=self.epsilon_bed,
            k_interfacial=self.k_interfacial,
        )

        # ================= WALL GEOMETRY =================
        (
            self.wall_perimeter,
            self.A_wall,
            self.A_wall_cell,
            self.a_gw,
            self.V_wall,
        ) = wall_geometry(
            D=self.D,
            L=self.L,
            N=self.N,
            V_cell=self.V_cell,
        )

        # ================= REFRACTORY =================
        self.refractory_thickness = 0.20
        self.refractory_conductivity = 1.8

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

        # ================= FLOW =================
        self.u_g = 0.0
        self.u_s = 0.0
        self.fill_fraction = 0.10

        # Solid held up in one stage [kg]. Sets the stage solid
        # residence time (hold-up / solid mass flow) used by the
        # steady-state drying kinetics; derived from the stage
        # geometry and bed properties above, no new parameter.
        self.solid_holdup_mass = (
            self.rho_s
            * self.fill_fraction
            * self.V_cell
        )

        # ================= HEAT TRANSFER =================
        cfg = ZONE_HT_CONFIG[self.zone]

        self.hv_gs = cfg["hv_gs"]
        self.hv_gw = cfg["hv_gw"]
        self.hv_ws = cfg["hv_ws"]

        # ================= BUFFERS =================
        self._dTg_dz = np.zeros(N)
        self._dTs_dz = np.zeros(N)

        # ================= CACHE (AFTER V_CELL) =================
        self._rho_g_Vcell_Cp_g = (
            self.rho_g * self.V_cell * self.Cp_g
        )

        self._rho_s_Vcell_Cp_s = (
            self.rho_s * self.V_cell * self.Cp_s
        )

        self.V_wall_cell = self.V_wall / self.N

        self._rho_wall_Vwall_cell_Cp = (
            self.rho_wall * self.V_wall_cell * self.Cp_wall
        )
        
        # ======================================================
        # HANDOFF DIAGNOSTICS
        # ======================================================

        self.gas_handoff_residuals = []
        self.solid_handoff_residuals = []

        # Enthalpy equivalent of the inter-stage handoff
        # convergence criterion. Recomputed every solve in
        # heat_transfer.thermal_step(), where the criterion
        # itself lives; the validator reads it from there.
        self.energy_closure_tolerance = 0.0

    # ======================================================
    # STEADY-STATE THERMAL STEP
    #
    # Delegates to heat_transfer.thermal_step(). Kept as a
    # bound method (rather than deleted) so the public
    # interface Preheater.thermal_step(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (burning.py, transition.py, cooler.py, precalciner).
    # ======================================================
    def thermal_step(
        self,
        Tg,
        Ts,
        Tw,
        state,
        reaction_sink=0.0,
        reaction_heat_cells=None,
    ):

        return heat_transfer.thermal_step(
            self,
            Tg,
            Ts,
            Tw,
            state,
            reaction_sink,
            reaction_heat_cells,
        )


    # ======================================================
    # GAS INLET TEMPERATURE FROM ENTHALPY
    #
    # Delegates to gas_phase.gas_temperature_from_enthalpy().
    # Kept as a bound method (rather than deleted) so the
    # public interface is unchanged.
    # ======================================================
    def gas_temperature_from_enthalpy(self, H, state, m_dot_g=None):

        return gas_phase.gas_temperature_from_enthalpy(
            self,
            H,
            state,
            m_dot_g,
        )


    # ======================================================
    # STATE UPDATE
    # ======================================================
    def apply(self, state):

        # ======================================================
        # STATE CHECK
        # ======================================================

        if not isinstance(state.Tg_preheater, np.ndarray):
            raise TypeError("Tg_preheater must be np.ndarray")

        if state.Tg_preheater.shape != (self.N,):
            raise ValueError("Preheater state corrupted")

        # ======================================================
        # ENERGY IN
        # ======================================================

        state.Hgas_preheater_in = state.Hgas_calciner_out

        state.Hsolid_preheater_in = (
            state.m_dot_s_preheater
            * self.Cp_s
            * (state.Feed_temperature - self.T_ref)
        )

        # ======================================================
        # PREHEATER CHEMISTRY (STEADY-STATE DRYING)
        #
        # Species flows through the five stages, with free
        # moisture evaporated per stage into the gas stream.
        # Runs BEFORE the boundary assignments below: those
        # overwrite Ts_preheater[-1] with the feed temperature,
        # which would evaluate stage 5's drying kinetics at the
        # cold feed (below the drying window) instead of at the
        # stage's own solid temperature. The thermal step does
        # not read those two entries (it takes the gas inlet
        # from enthalpy and the feed temperature directly), so
        # moving the chemistry ahead of them changes nothing
        # else.
        # ======================================================

        state = self.chemistry.apply_preheater(
            state,
            self.solid_holdup_mass,
        )

        # ======================================================
        # BOUNDARY CONDITIONS
        # ======================================================

        state.Tg_preheater[0] = state.Tg_calciner[0]
        state.Ts_preheater[-1] = state.Feed_temperature

        # ======================================================
        # THERMAL STEP
        # ======================================================

        (
            Tg_new,
            Ts_new,
            Tw_new,
            wall_loss,
            _,
        ) = self.thermal_step(
            state.Tg_preheater,
            state.Ts_preheater,
            state.Tw_preheater,
            state,
            reaction_sink=state.Preheater_Q_sink,
            reaction_heat_cells=state.Drying_Q_sink_cells,
        )

        # Reaction energy accounting is validated through
        # self.Q_reaction_total and Preheater_energy_balance.

        state.Tg_preheater = Tg_new
        state.Ts_preheater = Ts_new
        state.Tw_preheater = Tw_new

        state.Wall_loss_preheater = float(wall_loss)

        # ======================================================
        # ENERGY OUT
        # ======================================================

        state.Hgas_preheater_out = self.gas_enthalpy_out(
            state.Tg_preheater,
            state,
        )

        state.Hsolid_preheater_out = self.solid_enthalpy_out(
            state.Ts_preheater,
            state,
        )

        # ======================================================
        # SOLID PHASE HANDOFF: PREHEATER -> CALCINER
        # ======================================================

        resample_solid_phases(
            state.materials["preheater"].solids,
            state.materials["calciner"].solids,
        )

        # ======================================================
        # SOLID PHASE HANDOFF DIAGNOSTIC
        # ======================================================

        print("\n========== SOLID PHASE HANDOFF ==========")

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
            preheater = getattr(
                state.materials["preheater"].solids,
                phase,
            )

            calciner = getattr(
                state.materials["calciner"].solids,
                phase,
            )

            diff = np.sum(calciner) - np.sum(preheater)

            print(
                f"{phase:10s}: "
                f"preheater={np.sum(preheater):.6e}, "
                f"calciner={np.sum(calciner):.6e}, "
                f"diff={diff:.6e}"
            )

        # ======================================================
        # ENERGY BALANCE
        # ======================================================

        state.Preheater_energy_balance = (
            state.Hgas_preheater_in
            + state.Hsolid_preheater_in
            - state.Preheater_Q_sink
            - state.Hgas_preheater_out
            - state.Hsolid_preheater_out
            - state.Wall_loss_preheater
        )

        return state


    # ======================================================
    # GAS ENTHALPY TO NEXT ZONE
    #
    # Delegates to gas_phase.gas_enthalpy_out(). Kept as a
    # bound method (rather than deleted) so the public
    # interface is unchanged.
    # ======================================================
    def gas_enthalpy_out(self, Tg, state):

        return gas_phase.gas_enthalpy_out(
            self,
            Tg,
            state,
        )


    # ======================================================
    # SOLID ENTHALPY TO NEXT ZONE
    #
    # Delegates to solid_phase.solid_enthalpy_out(). Kept as
    # a bound method (rather than deleted) so the public
    # interface is unchanged.
    # ======================================================
    def solid_enthalpy_out(self, Ts, state):

        return solid_phase.solid_enthalpy_out(
            self,
            Ts,
            state,
        )
    