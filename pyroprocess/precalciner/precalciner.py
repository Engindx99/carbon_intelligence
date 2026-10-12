import numpy as np
import yaml

from physics.physics import h_gas
from physics.physics import interfacial_areas
from physics.physics import kiln_geometry
from physics.physics import mu_gas
from physics.physics import outlet_face_value
from physics.physics import suspension_transport
from physics.kiln_closures import gas_density

from chemistry.phases import get_cell_solid_flow
from chemistry.phases import raw_meal_solid_flow
from chemistry.phases import total_solid_flow
from chemistry.reactions import ChemistryModel
from physics.physics import ZONE_HT_CONFIG
from physics.shell import wall_stack

from . import thermal_solver
from . import raw_meal_inlet
from . import energy_diagnostics
from . import combustion


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Calciner:

    def __init__(self, N=5, L=25.0, cfg=None):

        # cfg is read for the Faz 6 wall stack and the vessel's
        # diameter; None falls back to physics.shell.DEFAULT_WALL_STACKS
        # and the old 4.2 m, so a caller that builds this zone on its
        # own still works.
        self.cfg = cfg

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
        # The vessel's own diameter, read the way the kiln reads its
        # bore (burning.py): `calciner.diameter`, the 5000 t/d plant's
        # PF5000 calciner (geometry/calciner/calciner.md). It used to
        # be a literal 4.2 shared by accident with the preheater and
        # cooler placeholders.
        self.D = float((cfg or {}).get("calciner", {}).get("diameter", 4.2))

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

        # ================= REFRACTORY / SHELL =================
        #
        # Faz 6. A calciner is not a bare kiln shell: it is a
        # lagged vessel -- castable refractory, ceramic fibre,
        # thin steel casing -- and the insulation is what sets
        # its loss. The old 0.05 m / 1.8 W/(m K) plane wall with
        # h_ext = 12 gave it a shell flux near 10 kW/m^2, an
        # order of magnitude above a lagged surface, and it was
        # the single largest wall-loss term in the plant.
        self.wall_stack = wall_stack(self.cfg, self.zone)

        self.refractory_thickness = self.wall_stack.thickness

        self.V_wall = self.A_wall * self.refractory_thickness
        self.V_wall_cell = self.V_wall / self.N

        # The calciner is a VERTICAL vessel, so the external film
        # takes its height as the characteristic length. The
        # height used is the zone length, which is still the
        # Faz 3 placeholder geometry (Faz 6 item 3 replaces it
        # with the real riser); the closure follows whatever
        # geometry the zone ends up with.
        self.shell = self.wall_stack.geometry(
            r_inner=0.5 * self.D,
            L_cell=self.L / self.N,
            L_char=self.L,
        )

        # ================= EXTERNAL WALL =================
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
        #
        # THE CALCINER DOES NOT ROTATE AND IS NOT INCLINED. It is
        # a vertical riser: meal is fed in and carried up by the
        # process gas. It used to carry
        #
        #     self.slope_deg = 3.0
        #     self.fill_fraction = 0.10
        #     self.rpm = 3.0
        #
        # and put them through physics.solid_axial_velocity, a
        # ROTARY KILN transit correlation, while apply() read the
        # kiln's own `state.rpm` on top -- so turning the kiln
        # faster made the calciner's meal move faster, which is
        # not a thing that happens. That gave a 670 s solids
        # transit against the 2-5 s an ILC calciner runs.
        #
        # What replaces it is transport, not a correlation:
        # u_s = u_g - u_t, resolved per sweep in apply() because
        # it depends on the gas flow and temperature. Nothing is
        # set here except the material property the slip needs.
        # ======================================================

        # Raw meal particle diameter and PARTICLE density, for the
        # Stokes slip in physics.suspension_transport. rho_s above
        # is the BULK density of a settled heap and is the wrong
        # one for a particle falling through gas.
        #
        # Cement raw meal is ground to 12-14 % residue on 90 um,
        # so the mass-mean particle is tens of microns. IT DOES
        # NOT MATTER, and that is the point -- measured on the
        # converged calciner stream:
        #
        #   d_p     u_t        slip      transit
        #   10 um   0.0028 m/s 0.023 %    2.02 s
        #   25 um   0.0175 m/s 0.142 %    2.03 s
        #   50 um   0.0701 m/s 0.567 %    2.03 s
        #   90 um   0.2271 m/s 1.838 %    2.06 s
        #
        # Every defensible meal size lands within 2 % of the same
        # answer, because the slip is a fraction of a percent of
        # the gas velocity. That plateau is what makes this a
        # mechanism being corrected and not a parameter being
        # fitted.
        calciner_cfg = (cfg or {}).get("calciner", {})

        self.particle_diameter = float(
            calciner_cfg.get("particle_diameter_m", 25.0e-6)
        )

        self.particle_density = float(
            calciner_cfg.get("particle_density_kg_m3", 2700.0)
        )

        if not (1.0e-6 <= self.particle_diameter <= 5.0e-4):
            raise ValueError(
                "calciner.particle_diameter_m outside the range "
                "raw meal is ground to (1 um - 0.5 mm), got "
                f"{self.particle_diameter}"
            )

        if not (1500.0 <= self.particle_density <= 4000.0):
            raise ValueError(
                "calciner.particle_density_kg_m3 must be a mineral "
                "PARTICLE density, not a bulk density, got "
                f"{self.particle_density}"
            )

        # ================= FLOW =================
        # Both are resolved in apply(); there is no gas stream yet.
        self.u_g = 0.0
        self.u_s = 0.0
        self.u_t = 0.0
        self.solids_volume_fraction = 0.0

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
        reaction_heat_slope_cells=None,
        q_fuel_cells=None,
        Q_calciner=0.0,
        dm_gas_cells=None,
        tol=1e-6,
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
            reaction_heat_slope_cells=reaction_heat_slope_cells,
            q_fuel_cells=q_fuel_cells,
            Q_calciner=Q_calciner,
            dm_gas_cells=dm_gas_cells,
            tol=tol,
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
        # so u_s is what turns the kinetics into a conversion
        # along the riser, and it is the whole residence time.
        #
        # PNEUMATIC TRANSPORT, not rotation. The meal is carried
        # up by the process gas at u_g less the slip its own
        # weight costs it. This used to run a rotary-kiln transit
        # correlation on a hard-coded 3 degree inclination and
        # 3 rpm -- and read `state.rpm`, the KILN's speed, on top
        # of that -- for a 670 s transit against the 2-5 s an ILC
        # calciner runs.
        #
        # Evaluated per sweep because it follows the gas: the gas
        # flow is the inlet stream and the density is taken at the
        # inlet temperature this same handoff just solved, which
        # is the coldest and therefore densest the gas gets in
        # this zone -- so u_g here is the SLOWEST it is anywhere
        # along the riser and the transit is an upper bound.
        # ======================================================

        m_dot_g_in = raw_meal_inlet.inlet_gas_flow(state)

        rho_g_in = gas_density(Tg_in)

        (
            self.u_s,
            self.u_g,
            self.u_t,
            self.solids_volume_fraction,
        ) = suspension_transport(
            m_dot_g=m_dot_g_in,
            m_dot_s=float(state.m_dot_s_calciner),
            rho_g=rho_g_in,
            A_cross=self.A_cross,
            d_p=self.particle_diameter,
            rho_particle=self.particle_density,
            mu=mu_gas(Tg_in),
            eps=self.eps,
        )

        state.u_s_calciner = float(self.u_s)
        state.residence_time_calciner = float(self.L / self.u_s)
        state.solids_volume_fraction_calciner = float(
            self.solids_volume_fraction
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
        # Loosened to the plant's tolerance hint while the plant
        # is far from its fixed point; zero on the sweep that may
        # declare convergence (see Twin.run, INEXACT INNER SOLVES).
        coupling_tol = max(
            1.0e-5,
            float(getattr(state, "inner_tolerance_hint", 0.0)),
        )
        # No under-relaxation (was 0.5). The thermal solve takes
        # the reaction heat's slope in Ts (reaction_heat_slope_
        # cells), so a pass already anticipates the sink's
        # response and the undamped iteration converges; halving
        # each pass's step only doubled the passes from a warm
        # start. Measured: same fixed point to 1e-8 K, the same 31
        # plant sweeps cold, calciner time 5.3 -> 2.9 s.
        coupling_relaxation = 1.0

        # ------------------------------------------------------
        # INEXACT INNER SOLVE
        #
        # Each coupling pass used to converge the thermal solve
        # to 1e-6 K although the reaction profile it was solving
        # for would move by kelvins on the next pass -- ~11
        # passes x ~23 inner iterations per plant sweep, the
        # largest single cost of a plant solve. The inner
        # tolerance now follows the coupling error: a tenth of
        # the last pass's temperature change, floored at the old
        # 1e-6 K. The last passes are therefore solved exactly as
        # tightly as before, so the fixed point is unchanged; only
        # the iterations spent refining a profile that was about
        # to be thrown away are saved.
        # ------------------------------------------------------
        inner_tol_floor = 1.0e-6
        inner_tol = inner_tol_floor

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
            # MASS LEAVING THE BED, CELL BY CELL
            #
            # Both reactions in this zone move mass out of the
            # solid and into the gas: calcination as CO2,
            # dehydroxylation as water vapour. The thermal
            # solver needs to know WHERE it leaves, not just how
            # much left in total, or it has to use one scalar
            # flow for a stream that does not have one.
            #
            # Taken from the same per-cell arrays the chemistry
            # just wrote, so the mass transfer and the heat sink
            # are derived from one and the same conversion.
            # ==================================================

            dm_gas_cells = (
                np.asarray(
                    state.m_dot_CaCO3_reacted_cells,
                    dtype=float,
                )
                * self.chemistry.calcination.CO2_ratio
                + np.asarray(
                    state.m_dot_H2O_generated_cells,
                    dtype=float,
                )
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
                # Both reactions respond to the same solid
                # temperature, so their slopes add exactly as
                # their heats do.
                reaction_heat_slope_cells=(
                    state.Calcination_Q_slope_cells
                    + state.Dehydroxylation_Q_slope_cells
                ),
                q_fuel_cells=q_fuel_cells,
                Q_calciner=Q_calciner,
                dm_gas_cells=dm_gas_cells,
                tol=inner_tol,
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

            # The pass just solved at inner_tol; the next one is
            # solved to a tenth of how far this pass moved. A pass
            # counts as tight once its inner tolerance is a tenth
            # of the coupling tolerance -- at the plant's final
            # coupling_tol of 1e-5 that is the old 1e-6 K floor.
            solved_tight = inner_tol <= max(
                inner_tol_floor,
                0.1 * coupling_tol,
            )

            inner_tol = max(
                inner_tol_floor,
                0.1 * float(temperature_error),
            )

            # ==================================================
            # 7. STEADY-STATE CONVERGENCE
            # ==================================================

            # Only a tight pass may end the loop, so the converged
            # state is as tight as it was before the inner solve
            # became inexact.
            if (
                temperature_error
                < coupling_tol
                and
                reaction_relative_error
                < coupling_tol
                and
                solved_tight
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

        # Per-cell flow: both reactions move mass out of the bed
        # along this zone, so a single scalar would be the true
        # flow in at most one cell. thermal_step publishes the
        # profiles it solved on.
        state.Hg_calciner = (
            state.m_dot_g_calciner_cells
            * h_gas(
                state.Tg_calciner,
                self.T_ref,
            )
        )


        # ======================================================
        # UPDATE SOLID ENTHALPY
        # ======================================================

        state.Hs_calciner = (
            state.m_dot_s_calciner_cells
            * self.Cp_s
            * (
                state.Ts_calciner
                - self.T_ref
            )
        )


        # ======================================================
        # ENTHALPY TO NEXT ZONE
        # ======================================================

        # Hgas_calciner_out / Hsolid_calciner_out are set by
        # thermal_step, which multiplies each reconstructed
        # outlet face by the flow that face carries. Re-deriving
        # them here by extrapolating the Hg/Hs arrays would give
        # a different number, because extrapolating a product of
        # two varying profiles is not the product of their
        # extrapolations -- and it is the flux thermal_step
        # booked in its own energy balance that the next zone
        # must receive.

        # ======================================================
        # STORED ENERGY
        #
        # Gas and solid are quasi-steady (seconds of transit).
        # The wall's rate is set by thermal_step: zero in the
        # steady solve, C/dt (Tw - Tw_old) in the dynamic one.
        # ======================================================

        state.Calciner_gas_stored = 0.0

        state.Calciner_solid_stored = 0.0

        state.Calciner_stored_energy_change = (
            state.Calciner_wall_stored
        )

        # ======================================================
        # ZONE ENERGY BALANCE
        # ======================================================

        state = energy_diagnostics.compute_energy_balance(
            self,
            state,
        )

        return state
