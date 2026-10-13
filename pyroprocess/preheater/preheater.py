import numpy as np

from physics.physics import h_solid
from physics.kiln_closures import gas_density
from physics.kiln_closures import suspension_gas_solid_coefficient
from physics.physics import interfacial_areas
from physics.physics import ZONE_HT_CONFIG
from physics.shell import wall_stack

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

    def __init__(self, N=5, L=25.0, nodes_per_stage=1, cfg=None):

        # Kept on the instance because the name `cfg` is rebound
        # further down to the ZONE_HT_CONFIG entry for this zone.
        self.plant_cfg = cfg

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

        # Cyclone separation efficiencies. C1 (Stage 5) lets its
        # dust out with the exhaust, the filter returns it with the
        # feed; C2-C4 (identical cyclones) and C5 let theirs up with
        # the gas into the stage above. See heat_transfer.thermal_step.
        # 1.0 = no separation model.
        preheater_cfg = (cfg or {}).get("preheater", {})

        self.c1_separation_efficiency = float(
            preheater_cfg.get("c1_separation_efficiency", 1.0)
        )
        self.c2_c4_separation_efficiency = float(
            preheater_cfg.get("c2_c4_separation_efficiency", 1.0)
        )
        self.c5_separation_efficiency = float(
            preheater_cfg.get("c5_separation_efficiency", 1.0)
        )

        for key in (
            "c1_separation_efficiency",
            "c2_c4_separation_efficiency",
            "c5_separation_efficiency",
        ):
            eta = getattr(self, key)
            if not 0.0 < eta <= 1.0:
                raise ValueError(
                    f"{key} must be in (0, 1], got {eta}"
                )

        # Returned dust flow [kg/s], set by every thermal step.
        self.m_dot_dust_return = 0.0

        # The same in index order: Stage 1 (index 0) is the plant's
        # C5, Stage 5 (index N-1) its C1 (gas_T_bounds_K below).
        if N > 1:
            self.separation_efficiency = np.array(
                [self.c5_separation_efficiency]
                + [self.c2_c4_separation_efficiency] * (N - 2)
                + [self.c1_separation_efficiency]
            )
        else:
            self.separation_efficiency = np.array(
                [self.c1_separation_efficiency]
            )

        # Dust each stage lets up with its gas [kg/s], index order;
        # the last entry is m_dot_dust_return. Set by every thermal
        # step.
        self.m_dot_dust_escape = np.zeros(N)

        # Solid entering each stage, circulating dust included
        # [kg/s]. Set by every thermal step.
        self.m_dot_s_stage_in = np.zeros(N)

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
        #
        # Index i is Stage i+1, numbered along the GAS path as the
        # solver marches it (heat_transfer.thermal_step): Stage 1
        # (index 0) takes the calciner gas and is the plant's hot
        # bottom cyclone C5; Stage 5 (index N-1) takes the fresh
        # feed and is the plant's top cyclone C1, whose gas leaves
        # as exhaust. geometry/ uses the plant C1..C5 names.

        gas_T_bounds_K = [
            (1113.15, 1143.15),  # Stage 1 (C5)
            (1023.15, 1043.15),  # Stage 2 (C4)
            (903.15, 923.15),    # Stage 3 (C3)
            (763.15, 773.15),    # Stage 4 (C2)
            (573.15, 583.15),    # Stage 5 (C1)
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
        #
        # Each stage is its own fluid volume: the riser below the
        # cyclone, where gas and meal exchange co-currently, plus
        # the cyclone (geometry/fluid_volumes.md; configs
        # `preheater.stages`). Per string, times the two identical
        # strings the twin solves as one at the total flow. This
        # replaces five equal slices of a 4.2 m x 25 m rotary
        # cylinder, 346 m3 for the whole tower.
        stage_cfg = preheater_cfg.get("stages")

        if stage_cfg is None or len(stage_cfg) != N:
            raise ValueError(
                f"preheater.stages must list the {N} stages' fluid "
                "volumes (configs/twin_cfg.yaml)"
            )

        strings = int(preheater_cfg.get("strings", 1))

        V_stage = np.empty(N)
        A_stage = np.empty(N)
        H_stage = np.empty(N)

        for i, st in enumerate(stage_cfg):

            n_cyc = int(st["cyclones_per_string"])
            V = n_cyc * float(st["cyclone_volume"])
            A = n_cyc * float(st["cyclone_wall_area"])
            H = float(st["cyclone_height"])

            if "riser_diameter" in st:
                D_r = float(st["riser_diameter"])
                L_r = float(st["riser_length"])
                V += np.pi * D_r**2 / 4.0 * L_r
                A += np.pi * D_r * L_r
                H = max(H, L_r)

            V_stage[i] = strings * V
            A_stage[i] = strings * A
            H_stage[i] = H

        self.V_cell = V_stage
        self.V_total = float(np.sum(V_stage))
        self.A_wall_cell = A_stage
        self.A_wall = float(np.sum(A_stage))
        self.a_gw = A_stage / V_stage

        # ================= INTERFACIAL AREA =================
        #
        # GAS -> MEAL: the SUSPENSION, 6 alpha / d_p at the solids
        # fraction the flow carries, resolved per node from the
        # flow (suspension_gs_coefficient below; the closure and
        # why it replaced the bore formula are in
        # physics.kiln_closures.suspension_gas_solid_coefficient).
        #
        # The meal is the calciner's: same particle size and
        # PARTICLE density (configs `calciner`, sourced there).
        calciner_cfg = (self.plant_cfg or {}).get("calciner", {})

        self.particle_diameter = float(
            calciner_cfg.get("particle_diameter_m", 25.0e-6)
        )

        self.particle_density = float(
            calciner_cfg.get("particle_density_kg_m3", 2700.0)
        )

        # GAS -> WALL and MEAL -> WALL stay on the old closure: the
        # wall areas are the stage geometry above, and a_ws is a
        # perimeter quantity the bore still stands in for (plan
        # step 4, not this change).
        self.bore_placeholder_D = 4.2
        self.epsilon_bed = 0.35
        self.k_interfacial = 1.0

        (
            _,
            self.a_ws,
        ) = interfacial_areas(
            D=self.bore_placeholder_D,
            epsilon_bed=self.epsilon_bed,
            k_interfacial=self.k_interfacial,
        )

        # ================= REFRACTORY / SHELL =================
        #
        # Faz 6. A preheater tower is a LAGGED vessel: castable
        # refractory, mineral wool, thin steel casing. The old
        # 0.20 m / 1.8 W/(m K) plane wall with a constant
        # h_ext = 12 described a bare kiln shell instead, and the
        # 0.27 insulation factor in physics.wall_losses was what
        # kept the resulting flux from being absurd.
        self.wall_stack = wall_stack(self.plant_cfg, self.zone)

        self.refractory_thickness = self.wall_stack.thickness

        # One shell per stage, on the cylinder with the stage's own
        # volume AND wall area: r = 2 V / A, length A / (2 pi r).
        # A riser is exactly that cylinder; a cyclone is a cylinder
        # and a cone, whose mean curvature this carries. Cylindrical
        # conduction is kept (physics/shell.py: a plane wall on the
        # inner area would overstate the lining resistance). The
        # external film is a vertical surface as tall as the
        # stage's tallest piece, riser or cyclone.
        r_stage = 2.0 * V_stage / A_stage

        self.stage_shells = [
            self.wall_stack.geometry(
                r_inner=float(r_stage[i]),
                L_cell=float(A_stage[i] / (2.0 * np.pi * r_stage[i])),
                L_char=float(H_stage[i]),
            )
            for i in range(N)
        ]

        # ================= EXTERNAL WALL =================
        self.T_ref = 298.15
        self.T_amb = 300.0

        # ================= PROPERTIES =================
        self.rho_g = 0.30
        self.rho_s = 1100.0
        self.rho_wall = 3000.0

        self.Cp_g = 1150.0
        # Solid Cp and enthalpy: physics.cp_solid / h_solid, one
        # definition for every solid stream in the plant.
        self.Cp_wall = 1000.0

        # ================= FLOW =================
        #
        # No fill fraction: the meal is CARRIED by the gas, and the
        # slip is a fraction of a percent of u_g for any defensible
        # meal size (tests/test_suspension_transport.py). Its
        # residence in a stage is therefore the gas's, V / Q_g,
        # evaluated per sweep in apply() because Q_g follows the gas
        # temperature. The 0.10 settled-heap fill on the old
        # cylinder put the tower at 342.9 s against 30-60 s.
        self.u_g = 0.0
        self.u_s = 0.0

        # ================= HEAT TRANSFER =================
        cfg = ZONE_HT_CONFIG[self.zone]

        self.hv_gw = cfg["hv_gw"]
        self.hv_ws = cfg["hv_ws"]

        # ================= BUFFERS =================
        self._dTg_dz = np.zeros(N)
        self._dTs_dz = np.zeros(N)

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
    # STAGE RESIDENCE TIME
    #
    # The meal rides the gas (no slip; see FLOW above), so each
    # stage holds it for V / Q_g, at the stage's gas temperature.
    # ======================================================
    def stage_residence_time(self, state):

        m_dot_g = float(state.m_dot_g_preheater)

        if not m_dot_g > 0.0:
            raise ValueError(
                f"preheater gas flow must be > 0, got {m_dot_g}"
            )

        rho_g = gas_density(np.asarray(state.Tg_preheater, dtype=float))

        return self.V_cell * rho_g / m_dot_g

    # ======================================================
    # GAS -> MEAL CONDUCTANCE OF THE SUSPENSION
    # (physics.kiln_closures.suspension_gas_solid_coefficient)
    # ======================================================
    def suspension_gs_coefficient(self, m_dot_s, m_dot_g, Tg, Ts):

        h_gs, a_gs = suspension_gas_solid_coefficient(
            m_dot_s,
            m_dot_g,
            Tg,
            Ts,
            self.particle_diameter,
            self.particle_density,
        )

        return float(h_gs), float(a_gs)

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
            * h_solid(float(state.Feed_temperature), self.T_ref)
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

        state.residence_time_preheater_cells = self.stage_residence_time(
            state
        )

        state = self.chemistry.apply_preheater(
            state,
            state.residence_time_preheater_cells,
        )

        # ======================================================
        # BOUNDARY CONDITIONS
        # ======================================================

        # The calciner's gas leaves at its top, cell N-1 (co-current).
        state.Tg_preheater[0] = state.Tg_calciner[-1]
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
        # ENERGY BALANCE
        # ======================================================

        state.Preheater_energy_balance = (
            state.Hgas_preheater_in
            + state.Hsolid_preheater_in
            - state.Preheater_Q_sink
            - state.Hgas_preheater_out
            - state.Hsolid_preheater_out
            - state.Wall_loss_preheater
            - state.Q_dust_loss_preheater
            - state.Preheater_stored_energy_change
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
    