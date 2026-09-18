import numpy as np
import yaml

from physics.physics import h_gas
from physics.physics import interfacial_areas
from physics.physics import kiln_geometry
from physics.physics import outlet_face_value
from physics.physics import solid_axial_velocity

from chemistry.phases import get_cell_solid_flow
from chemistry.phases import raw_meal_solid_flow
from chemistry.phases import total_solid_flow
from chemistry.reactions import ChemistryModel
from physics.physics import ZONE_HT_CONFIG

from . import thermal_solver
from . import raw_meal_inlet
from . import energy_diagnostics
from . import combustion


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Calciner:

    def __init__(self, N=5, L=25.0):

        self.N = N
        self.L = L
        self.dz = L / N

        # ================= ZONE =================
        self.zone = "calciner"

        self.energy_in = 0.0
        self.energy_out = 0.0
        self.energy_residual = 0.0

        self.chemistry = ChemistryModel()

        # ================= NUMERICAL =================
        self.eps = 1e-9

        # ================= GEOMETRY =================
        self.D = 4.2

        self.A_cross, self.V_total, self.V_cell = kiln_geometry(
            D=self.D,
            L=self.L,
            N=self.N,
        )

        # ================= INTERFACIAL AREA =================
        self.epsilon_bed = 0.35
        self.k_interfacial = 1.0

        self.a_gs, self.a_ws = interfacial_areas(
            D=self.D,
            epsilon_bed=self.epsilon_bed,
            k_interfacial=self.k_interfacial,
        )

        # ================= WALL GEOMETRY =================
        self.wall_perimeter = np.pi * self.D
        self.A_wall = self.wall_perimeter * self.L
        self.A_wall_cell = self.A_wall / self.N
        self.a_gw = self.A_wall_cell / self.V_cell

        # ================= REFRACTORY =================
        self.refractory_thickness = 0.05      # m
        self.refractory_conductivity = 1.8    # W/mK

        self.V_wall = self.A_wall * self.refractory_thickness
        self.V_wall_cell = self.V_wall / self.N

        # ================= EXTERNAL WALL =================
        self.h_ext = 12.0
        self.T_ref = 298.15   # K
        self.T_amb = 300.0    # K

        # ================= PROPERTIES =================
        self.rho_g = 0.30
        self.rho_s = 1100.0
        self.rho_wall = 3000.0

        self.Cp_g = 1150.0
        self.Cp_s = 850.0
        self.Cp_wall = 1000.0

        # ======================================================
        # CALCINER OPERATING PARAMETERS
        # ======================================================

        self.slope_deg = 3.0
        self.fill_fraction = 0.10
        self.rpm = 3.0

        # ================= FLOW =================
        self.u_g = 0.0

        self.u_s = solid_axial_velocity(
            L=self.L,
            D=self.D,
            slope_deg=self.slope_deg,
            fill_fraction=self.fill_fraction,
            rpm=self.rpm,
            eps=self.eps,
        )

        # ================= HEAT TRANSFER =================
        cfg = ZONE_HT_CONFIG[self.zone]

        self.hv_gs = cfg["hv_gs"]
        self.hv_gw = cfg["hv_gw"]
        self.hv_ws = cfg["hv_ws"]

        # ================= FIRING =================
        #
        # The calciner burns whatever share of the plant's fuel
        # the kiln burner does not. Both zones read the same
        # fuel.kiln_fraction, so the split cannot drift.
        #
        # O2_opt/O2_sigma2 match the kiln burner's: the Gaussian
        # is a combustion-efficiency knob on the plant's single
        # dry stack O2 figure, so the same target applies to both
        # firings, and at the design point it returns exactly 1.
        plant_cfg = load_cfg("configs/twin_cfg.yaml")
        fuel_cfg = plant_cfg.get("fuel", {})

        kiln_fraction = fuel_cfg.get("kiln_fraction", 0.40)

        if not (0.0 < kiln_fraction <= 1.0):
            raise ValueError(
                "fuel.kiln_fraction must be in (0, 1], "
                f"got {kiln_fraction}"
            )

        self.calciner_fuel_fraction = 1.0 - kiln_fraction

        self.O2 = fuel_cfg.get("O2", 3.5)
        self.O2_opt = 3.5
        self.O2_sigma2 = 25.0

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
    # Delegates to thermal_solver.thermal_step(). Kept as a
    # bound method (rather than deleted) so the public
    # interface Calciner.thermal_step(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (burning.py, cooler.py, transition.py, preheater.py).
    # ======================================================
    def thermal_step(
        self,
        Tg,
        Ts,
        Tw,
        state,
        Tg_in,
        Ts_in,
        reaction_sink=0.0,
        reaction_heat_cells=None,
        q_fuel_cells=None,
        Q_calciner=0.0,
    ):

        return thermal_solver.thermal_step(
            self,
            Tg,
            Ts,
            Tw,
            state,
            Tg_in,
            Ts_in,
            reaction_sink=reaction_sink,
            reaction_heat_cells=reaction_heat_cells,
            q_fuel_cells=q_fuel_cells,
            Q_calciner=Q_calciner,
        )

    # ======================================================
    # STATE UPDATE
    # ======================================================
    def apply(self, state):



        # ======================================================
        # STATE INTEGRITY CHECK
        # ======================================================

        if not isinstance(
            state.Tg_calciner,
            np.ndarray,
        ):
            raise TypeError(
                "Tg_calciner must be np.ndarray"
            )

        if state.Tg_calciner.shape != (
            self.N,
        ):
            raise ValueError(
                f"Calciner state corrupted: "
                f"{state.Tg_calciner.shape}"
            )

        # ======================================================
        # INLET CONDITIONS FROM UPSTREAM ENTHALPY HANDOFFS
        #
        # These are physical inlet conditions.
        #
        # Gas:
        #     N-1 -> 0
        #
        # Solid:
        #     0 -> N-1
        # ======================================================

        Tg_in, Ts_in = raw_meal_inlet.resolve_inlet_conditions(
            self,
            state,
        )

        # ======================================================
        # CALCINER SOLID AXIAL VELOCITY
        #
        # Steady-state spatial reaction:
        #
        #     u_s * dm/dz = -r
        #
        # No residence-time chemistry is used here.
        # ======================================================

        rpm = float(
            getattr(
                state,
                "rpm",
                self.rpm,
            )
        )

        self.u_s = solid_axial_velocity(
            L=self.L,
            D=self.D,
            slope_deg=self.slope_deg,
            fill_fraction=self.fill_fraction,
            rpm=rpm,
            eps=self.eps,
        )

        self.u_s = max(
            float(self.u_s),
            self.eps,
        )


        # ======================================================
        # CHEMISTRY <-> THERMAL STEADY-STATE ITERATION
        #
        # Spatial chemistry:
        #
        #     Ts(z)
        #       ↓
        #     k(T)
        #       ↓
        #     X(z)
        #       ↓
        #     Q_reaction(z)
        #       ↓
        #     thermal_step()
        #       ↓
        #     new Ts(z)
        #
        # No dt is used.
        # ======================================================

        max_coupling_iter = 50
        coupling_tol = 1.0e-5
        coupling_relaxation = 0.5

        # ------------------------------------------------------
        # FUEL HEAT RELEASE
        #
        # Fixed across the coupling loop: it depends only on the
        # fuel split and the stack O2 target, neither of which
        # the loop moves. Computed once here rather than inside
        # so the iteration cannot drift it.
        # ------------------------------------------------------

        Q_petcoke_calciner, Q_calciner = combustion.fuel_heat_release_for(
            self,
            state,
        )

        q_fuel_cells = combustion.axial_heat_distribution(
            self.N,
            Q_calciner,
        )

        state.Q_petcoke_calciner = float(Q_petcoke_calciner)
        state.Q_calciner = float(Q_calciner)

        # ------------------------------------------------------
        # INITIAL GUESS
        # ------------------------------------------------------

        Tg_iter = (
            np.asarray(
                state.Tg_calciner,
                dtype=float,
            )
            .copy()
        )

        Ts_iter = (
            np.asarray(
                state.Ts_calciner,
                dtype=float,
            )
            .copy()
        )

        Tw_iter = (
            np.asarray(
                state.Tw_calciner,
                dtype=float,
            )
            .copy()
        )

        previous_Q_reaction = 0.0

        coupling_converged = False

        # ======================================================
        # SOLID SPECIES INLET [kg/s]
        #
        # The calciner receives the single solid stream that
        # leaves cyclone stage 1 (index 0 of the preheater
        # stage flows) -- not a spatial interpolation of all
        # five stages. The preheater fills those flows later in
        # the same step, so on the very first pass they are
        # still zero; the raw-meal stream it would receive
        # before any drying is used then.
        #
        # Its CaCO3 is passed to the kinetics explicitly: with
        # moisture removed upstream, m_dot_s_calciner times the
        # raw-meal CaCO3 fraction no longer equals the CaCO3
        # actually arriving.
        # ======================================================

        calciner_inlet_flow = get_cell_solid_flow(
            state.material_flows["preheater"].solids,
            0,
        )

        if total_solid_flow(calciner_inlet_flow) <= 0.0:
            calciner_inlet_flow = raw_meal_solid_flow(
                state.m_dot_s_preheater
            )

        # ======================================================
        # OUTER STEADY-STATE ITERATION
        # ======================================================

        for coupling_iteration in range(
            max_coupling_iter
        ):

            # ==================================================
            # 1. UPDATE REACTION TEMPERATURE FIELD
            # ==================================================

            state.Ts_calciner = (
                Ts_iter.copy()
            )

            # ==================================================
            # 2. SPATIAL CHEMISTRY
            # ==================================================

            state = self.chemistry.apply_calciner(
                state,
                self.dz,
                self.u_s,
                commit_phases=False,
                m_dot_CaCO3_in=calciner_inlet_flow["CaCO3"],
                m_dot_BoundH2O_in=calciner_inlet_flow["Bound_H2O"],
            )

            Q_reaction = float(
                state.Calciner_Q_sink
            )



            # ==================================================
            # 3. THERMAL SOLUTION
            # ==================================================

            (
                Tg_new,
                Ts_new,
                Tw_new,
                wall_loss_new,
                _,
            ) = self.thermal_step(
                Tg_iter,
                Ts_iter,
                Tw_iter,
                state,
                Tg_in,
                Ts_in,
                reaction_sink=Q_reaction,
                reaction_heat_cells=(
                    state.Calcination_Q_cells
                    + state.Dehydroxylation_Q_sink_cells
                ),
                q_fuel_cells=q_fuel_cells,
                Q_calciner=Q_calciner,
            )

            # ==================================================
            # 4. RELAXATION
            # ==================================================

            Tg_relaxed = (
                coupling_relaxation
                * Tg_new
                +
                (1.0 - coupling_relaxation)
                * Tg_iter
            )

            Ts_relaxed = (
                coupling_relaxation
                * Ts_new
                +
                (1.0 - coupling_relaxation)
                * Ts_iter
            )

            Tw_relaxed = (
                coupling_relaxation
                * Tw_new
                +
                (1.0 - coupling_relaxation)
                * Tw_iter
            )

            # ==================================================
            # 5. CONVERGENCE ERRORS
            # ==================================================

            temperature_error = max(
                np.max(
                    np.abs(
                        Tg_relaxed
                        - Tg_iter
                    )
                ),
                np.max(
                    np.abs(
                        Ts_relaxed
                        - Ts_iter
                    )
                ),
                np.max(
                    np.abs(
                        Tw_relaxed
                        - Tw_iter
                    )
                ),
            )

            reaction_error = abs(
                Q_reaction
                - previous_Q_reaction
            )

            reaction_scale = max(
                abs(Q_reaction),
                1.0,
            )

            reaction_relative_error = (
                reaction_error
                / reaction_scale
            )

            # ==================================================
            # 6. UPDATE ITERATION STATES
            # ==================================================

            Tg_iter = Tg_relaxed
            Ts_iter = Ts_relaxed
            Tw_iter = Tw_relaxed

            previous_Q_reaction = (
                Q_reaction
            )

            # ==================================================
            # 7. STEADY-STATE CONVERGENCE
            # ==================================================

            if (
                temperature_error
                < coupling_tol
                and
                reaction_relative_error
                < coupling_tol
            ):

                coupling_converged = True

                break


        # ======================================================
        # FINAL CHEMISTRY COMMIT
        # ======================================================
        # Coupling has now finished.
        # Run chemistry ONCE more on the final Ts_iter.

        state.Ts_calciner = Ts_iter.copy()

        state = self.chemistry.apply_calciner(
            state,
            self.dz,
            self.u_s,
            commit_phases=True,
            m_dot_CaCO3_in=calciner_inlet_flow["CaCO3"],
            m_dot_BoundH2O_in=calciner_inlet_flow["Bound_H2O"],
        )

        # ======================================================
        # STEADY-STATE SOLID SPECIES FLOWS [kg/s]
        #
        # Profile from the inlet stream resolved above; the
        # CaCO3 marched by the committed kinetics is converted
        # cumulatively, cell by cell. The Bound_H2O profile is
        # applied afterwards since it only overwrites its own
        # column, reading back the CaCO3/CaO already written.
        # ======================================================

        self.chemistry.calcination.solid_flow_profile(
            calciner_inlet_flow,
            state.m_dot_CaCO3_out_cells,
            state.material_flows["calciner"].solids,
            state.material_flows["calciner"].gases,
        )

        self.chemistry.dehydroxylation.solid_flow_profile(
            calciner_inlet_flow,
            state.m_dot_BoundH2O_out_cells,
            state.material_flows["calciner"].solids,
            state.material_flows["calciner"].gases,
        )

        # ======================================================
        # FINAL STATE
        # ======================================================

        state.Tg_calciner = Tg_iter
        state.Ts_calciner = Ts_iter
        state.Tw_calciner = Tw_iter

        state.Wall_loss_calciner = float(
            wall_loss_new
        )

        state.Calciner_coupling_iterations = (
            coupling_iteration + 1
        )

        state.Calciner_coupling_converged = (
            coupling_converged
        )

        state.Calciner_coupling_temperature_error = (
            float(temperature_error)
        )

        state.Calciner_coupling_reaction_error = (
            float(reaction_relative_error)
        )


        # ======================================================
        # UPDATE GAS ENTHALPY
        #
        # Must use the same h_gas() definition
        # used by thermal_step().
        # ======================================================

        state.Hg_calciner = (
            state.m_dot_g_calciner
            * h_gas(
                state.Tg_calciner,
                self.T_ref,
            )
        )


        # ======================================================
        # UPDATE SOLID ENTHALPY
        # ======================================================

        state.Hs_calciner = (
            state.m_dot_s_calciner
            * self.Cp_s
            * (
                state.Ts_calciner
                - self.T_ref
            )
        )


        # ======================================================
        # ENTHALPY TO NEXT ZONE
        # ======================================================

        # Read at the outlet FACE, not at the last cell CENTRE
        # (Hg_calciner[0]) half a cell upstream of it: this is
        # the reconstructed value the second-order flux in
        # thermal_solver.thermal_step() transports out of cell
        # 0, so handing off anything else would leak the
        # difference out of the energy balance. Hg_calciner is
        # m_dot_g * h elementwise, i.e. affine in h, so the
        # extrapolation may be taken on it directly.
        state.Hgas_calciner_out = outlet_face_value(
            state.Hg_calciner,
            reverse=True,
        )


        # ======================================================
        # SOLID ENTHALPY TO NEXT ZONE
        #
        # Outlet FACE for the same reason; Hs_calciner is affine
        # in Ts.
        # ======================================================

        state.Hsolid_calciner_out = outlet_face_value(
            state.Hs_calciner,
            reverse=False,
        )

        # ======================================================
        # STEADY-STATE:
        # NO ACCUMULATION
        # ======================================================

        state.Calciner_gas_stored = 0.0

        state.Calciner_solid_stored = 0.0

        state.Calciner_wall_stored = 0.0

        state.Calciner_stored_energy_change = (
            0.0
        )

        # ======================================================
        # ZONE ENERGY BALANCE
        # ======================================================

        state = energy_diagnostics.compute_energy_balance(
            self,
            state,
        )

        return state
