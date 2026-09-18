import numpy as np
import yaml

from physics.physics import h_gas
from physics.physics import kiln_geometry
from physics.physics import wall_geometry
from physics.physics import ZONE_HT_CONFIG

from chemistry.reactions import ChemistryModel

from . import combustion
from . import burner
from . import gas_phase
from . import solid_phase
from . import heat_transfer


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Burning:
    def __init__(self, N=5, L=60.0, chemistry=None):
        cfg = load_cfg("configs/twin_cfg.yaml")
        plant = cfg.get("plant", {})
        motion = cfg.get("motion", {})
        op = cfg.get("operational", {})

        self.zone = "burning"
        self.chemistry = chemistry or ChemistryModel()
        self.eps = 1e-9

        # ======================================================
        # GEOMETRY
        # ======================================================
        self.N = plant.get("N", N)
        self.L = plant.get("length", L)

        self.dz = self.L / self.N
        self.D = 4.2

        self.A_cross, self.V_total, self.V_cell = kiln_geometry(
            D=self.D,
            L=self.L,
            N=self.N
        )

        # ======================================================
        # ENERGY DIAGNOSTICS
        # ======================================================
        self.energy_in = 0.0
        self.energy_out = 0.0
        self.energy_residual = 0.0

        # ======================================================
        # INTERFACIAL AREAS
        #
        # Not set here any more. a_gs, a_ws and a_gw are derived
        # per solve from the bed cross-section in
        # heat_transfer.thermal_step (bed_segment_geometry on the
        # fill fraction from mass continuity), because they depend
        # on how much material is in the kiln and so cannot be
        # fixed at construction time.
        # ======================================================

        # ======================================================
        # REFRACTORY
        # ======================================================
        self.refractory_thickness = op.get(
            "refractory_thickness",
            0.20
        )

        self.refractory_conductivity = op.get(
            "refractory_conductivity",
            1.8
        )

        self.h_ext = op.get(
            "h_ext",
            10.0
        )

        # ======================================================
        # WALL GEOMETRY
        # ======================================================
        # wall_geometry's fourth return is the gas-wall area density
        # over the full perimeter. It is discarded: a_gw is now the
        # exposed arc only, split from a_ws by bed_segment_geometry in
        # thermal_step. A_wall_cell and V_wall below are unaffected --
        # those are refractory conduction quantities and the whole
        # perimeter is the right area for them.
        (
            self.wall_perimeter,
            self.A_wall_total,
            self.A_wall_cell,
            _a_gw_full_perimeter,
            self.V_wall
        ) = wall_geometry(
            D=self.D,
            L=self.L,
            N=self.N,
            V_cell=self.V_cell,
            refractory_thickness=self.refractory_thickness
        )

        # ======================================================
        # PHYSICAL PROPERTIES
        # ======================================================
        self.rho_g = 0.30
        self.rho_s = 1100.0
        self.rho_wall = 3000.0

        self.Cp_g = 1150.0
        self.Cp_s = 850.0
        self.Cp_wall = 1000.0

        # ======================================================
        # MOTION
        # ======================================================
        self.rpm_default = motion.get(
            "rpm_default",
            1.5
        )

        self.rpm_min = motion.get(
            "rpm_min",
            1.0
        )

        self.rpm_max = motion.get(
            "rpm_max",
            3.0
        )

        self.slope_deg = motion.get(
            "inclination_deg",
            3.0
        )

        # No fill_fraction here. It used to be read from
        # operational.kiln_load -- a capacity-utilisation figure the
        # config sets to 1.0 -- and handed to residence_time() as if it
        # were the bed cross-section fraction. The bed fill is now
        # solved with the transit time from mass continuity in
        # solid_phase.resolve_solid_motion and published as
        # state.bed_fill_fraction, so there is nothing to set here and
        # nothing left to confuse with kiln_load.

        self.u_s = 0.0
        self.u_g = 0.0

        # ======================================================
        # HEAT TRANSFER
        # ======================================================
        ht = ZONE_HT_CONFIG[self.zone]

        self.hv_gs = ht["hv_gs"]
        self.hv_gw = ht["hv_gw"]
        self.hv_ws = ht["hv_ws"]

        self.h_ext = op.get(
            "h_ext",
            12.0
        )

        self.T_ref = op.get(
            "T_ref",
            298.15
        )

        self.T_amb = op.get(
            "T_amb",
            300.0
        )

        # ======================================================
        # FUEL
        # ======================================================

        self.O2_opt = 3.5
        self.O2_sigma2 = 25.0

        # ======================================================
        # SECONDARY AIR (primary/secondary split at kiln inlet)
        # ======================================================
        burning_cfg = cfg.get("burning", {})

        self.primary_air_fraction = burning_cfg.get(
            "primary_air_fraction",
            0.10
        )

        if not (0.0 <= self.primary_air_fraction <= 1.0):
            raise ValueError(
                "burning.primary_air_fraction must be in [0, 1], "
                f"got {self.primary_air_fraction}"
            )

        # Under-relaxation on the kiln's own calcination CO2.
        # Numerical only: at the fixed point the blend is the
        # identity, so this cannot change the converged answer.
        # See the comment at its use in apply().
        self.calcination_relaxation = burning_cfg.get(
            "calcination_relaxation",
            0.45,
        )

        if not (0.0 < self.calcination_relaxation <= 1.0):
            raise ValueError(
                "burning.calcination_relaxation must be in (0, 1], "
                f"got {self.calcination_relaxation}"
            )

        # ======================================================
        # FUEL SPLIT (kiln burner vs precalciner)
        #
        # Lives on Burning because this is the zone that spends
        # it, but it partitions a plant-level input, so the
        # precalciner reads the complement from the same key.
        # ======================================================
        fuel_cfg = cfg.get("fuel", {})

        self.kiln_fuel_fraction = fuel_cfg.get(
            "kiln_fraction",
            0.40,
        )

        if not (0.0 < self.kiln_fuel_fraction <= 1.0):
            raise ValueError(
                "fuel.kiln_fraction must be in (0, 1], "
                f"got {self.kiln_fuel_fraction}"
            )

        # ======================================================
        # BUFFERS & CACHE
        # ======================================================
        self._dTg_dz = np.zeros(self.N)
        self._dTs_dz = np.zeros(self.N)

        self._rho_g_Vcell_Cp_g = (
            self.rho_g
            * self.V_cell
            * self.Cp_g
        )

        self._rho_s_Vcell_Cp_s = (
            self.rho_s
            * self.V_cell
            * self.Cp_s
        )

        self.V_wall_cell = self.V_wall / self.N

        self._rho_wall_Vwall_cell_Cp = (
            self.rho_wall
            * self.V_wall_cell
            * self.Cp_wall
        )


    # ======================================================
    # THERMAL STEP
    #
    # Delegates to heat_transfer.thermal_step(). Kept as a
    # bound method (rather than deleted) so the public
    # interface Burning.thermal_step(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (cooler.py, transition.py, preheater.py, precalciner).
    # ======================================================
    def thermal_step(self, Tg, Ts, Tw, state, inputs, u_g, u_s):

        return heat_transfer.thermal_step(
            self,
            Tg,
            Ts,
            Tw,
            state,
            inputs,
            u_g,
            u_s,
        )


    # ======================================================
    # STATE UPDATE
    # ======================================================

    def apply(self, state, inputs):

        # ======================================================
        # STATE INTEGRITY CHECK
        # ======================================================
        if not isinstance(state.Tg_burning, np.ndarray):
            raise TypeError("Tg_burning must be np.ndarray")

        if state.Tg_burning.shape != (self.N,):
            raise ValueError(
                f"Burning shape corrupted: {state.Tg_burning.shape}"
            )

        # ======================================================
        # SOLID MOTION & MASS FLOW
        # ======================================================
        u_s = solid_phase.resolve_solid_motion(self, state, inputs)

        # ======================================================
        # GAS MASS FLOW & VELOCITY
        # ======================================================
        u_g = burner.resolve_gas_flow(self, state, inputs)

        # ======================================================
        # GAS INLET HANDOFF
        # ======================================================
        gas_phase.resolve_gas_inlet(self, state)

        # ======================================================
        # SOLID INLET HANDOFF
        # ======================================================
        solid_phase.resolve_solid_inlet(self, state)

        # ======================================================
        # BURNING CHEMISTRY
        # ======================================================

        # Steady-state flow form: reacts the solid stream
        # handed over by Transition over this zone's own cell
        # residence time dz / u_s.
        def _previous(name, N):
            """Last sweep's per-cell array, or zeros on the first."""

            prev = getattr(state, name, None)

            if prev is None:
                return np.zeros(N)

            prev = np.asarray(prev, dtype=float)

            if prev.size != N:
                return np.zeros(N)

            return prev

        N_cells = len(state.Ts_burning)

        dm_previous = _previous(
            "m_dot_CO2_generated_burning_cells",
            N_cells,
        )

        Q_calc_previous = _previous(
            "Calcination_Q_burning_cells",
            N_cells,
        )

        state = self.chemistry.apply_burning(
            state,
            self.dz,
            u_s,
        )

        # ======================================================
        # UNDER-RELAXED CALCINATION, PER CELL
        #
        # PATH ONLY -- this cannot move the answer. At the fixed
        # point the new arrays equal the previous ones and the
        # blend is the identity, so the converged solution is
        # exactly the un-relaxed one. It changes only how the
        # iteration gets there.
        #
        # Two separate instabilities made it necessary, and the
        # second is why the blend is ELEMENTWISE rather than a
        # single factor on the totals:
        #
        #   1. MAGNITUDE. The term goes from zero to its full
        #      value in one sweep. The kiln really does finish
        #      the calcination, but on the first sweeps the
        #      upstream zones have not calcined yet, so all of
        #      the meal's CaCO3 arrives here and decomposes at
        #      once. Clinker collapsed to 14.3 kg/s against the
        #      15.2 kg/s floor the cooler air split imposes, and
        #      the run died on an iterate nowhere near the
        #      solution. The fixed point is comfortably feasible
        #      (clinker 16.9, vent 3.8 kg/s).
        #
        #   2. SHAPE. Damping only the totals left a period-2
        #      cycle in which the total sink barely moved (5.498
        #      vs 5.455 kg/s CO2) while its AXIAL PLACEMENT
        #      flipped between two profiles each sweep. Scaling a
        #      profile by one number preserves its shape, so that
        #      oscillation survived untouched. Calcination is
        #      very sharp in temperature -- it runs to completion
        #      wherever the bed is hot enough -- so the cell it
        #      lands in is what oscillates, and the blend has to
        #      act cell by cell to damp it.
        #
        # Mass and heat are relaxed with the SAME weights,
        # because they are the same reaction: damping one and not
        # the other is what produced instability 2's predecessor,
        # a period-3 cycle between 917 K and 1662 K with the mass
        # residual already at 1e-14.
        # ======================================================

        w = self.calcination_relaxation

        dm_new = np.asarray(
            state.m_dot_CO2_generated_burning_cells,
            dtype=float,
        )

        Q_calc_new = np.asarray(
            state.Calcination_Q_burning_cells,
            dtype=float,
        )

        dm_relaxed = w * dm_new + (1.0 - w) * dm_previous

        Q_calc_relaxed = (
            w * Q_calc_new
            + (1.0 - w) * Q_calc_previous
        )

        # The four clinkering reactions are not relaxed, so their
        # heat is taken out at the new value and the calcination
        # term put back at the relaxed one.
        state.Burning_Q_sink_cells = (
            np.asarray(state.Burning_Q_sink_cells, dtype=float)
            - Q_calc_new
            + Q_calc_relaxed
        )

        state.Burning_Q_sink = float(
            np.sum(state.Burning_Q_sink_cells)
        )

        state.Calcination_Q_burning_cells = Q_calc_relaxed
        state.Calcination_Q_burning = float(np.sum(Q_calc_relaxed))

        state.m_dot_CO2_generated_burning_cells = dm_relaxed
        state.m_dot_CO2_generated_burning = float(np.sum(dm_relaxed))

        # ======================================================
        # STEADY-STATE THERMAL SOLUTION
        # ======================================================

        (
            Tg_new,
            Ts_new,
            Tw_new,
            Q_petcoke,
            Q_burning,
            _,
            _,
            total_energy_balance,
            Q_wall_loss,
        ) = self.thermal_step(
            state.Tg_burning,
            state.Ts_burning,
            state.Tw_burning,
            state,
            inputs,
            u_g,
            u_s,
        )

        # ======================================================
        # UPDATE TEMPERATURE STATES
        # ======================================================

        state.Tg_burning = Tg_new
        state.Ts_burning = Ts_new
        state.Tw_burning = Tw_new



        # ======================================================
        # ENTHALPY STATES
        # ======================================================
        # Per-cell flow: the meal finishes calcining here, so the
        # bed loses CO2 and the gas gains it along the zone and a
        # single scalar would be the true flow in at most one
        # cell. thermal_step publishes the profiles it solved on.
        state.Hg_burning = (
            state.m_dot_g_burning_cells
            * h_gas(
                state.Tg_burning,
                self.T_ref
            )
        )

        state.Hs_burning = (
            state.m_dot_s_burning_cells
            * self.Cp_s
            * (state.Ts_burning - self.T_ref)
        )

        # ======================================================
        # FUEL HEAT RELEASE STATES
        # ======================================================
        state.Q_petcoke = Q_petcoke
        state.Q_burning = Q_burning

        # ======================================================
        # WALL LOSS
        # ======================================================
        state.Wall_loss_burning = float(Q_wall_loss)

        # ======================================================
        # ENTHALPY OUT
        #
        # Hgas_burning_out / Hsolid_burning_out are set by
        # thermal_step, which multiplies each reconstructed
        # outlet face by the flow that face carries. Re-deriving
        # them here by extrapolating the Hg/Hs arrays would give
        # a different number, because extrapolating a product of
        # two varying profiles is not the product of their
        # extrapolations -- and it is the flux thermal_step
        # booked in its own energy balance that the cooler must
        # receive.
        # ======================================================

        # ======================================================
        # STEADY-STATE STORED ENERGY
        # ======================================================
        state.Burning_gas_stored = 0.0
        state.Burning_solid_stored = 0.0
        state.Burning_wall_stored = 0.0

        state.Burning_stored_energy_change = 0.0

        # ======================================================
        # STEADY-STATE ENERGY BALANCE
        # ======================================================
        Hg_in = state.m_dot_g * h_gas(
            state.Tg_burning_in,
            self.T_ref
        )

        Hs_in = state.m_dot_s * self.Cp_s * (
            state.Ts_burning_in - self.T_ref
        )

        state.Burning_energy_balance = total_energy_balance

        # ======================================================
        # BURNING ITERATION DIAGNOSTIC
        # ======================================================

        Burning_Q_sink = combustion.reaction_heat_sink(state)

        Q_wall_loss = getattr(
            state,
            "Wall_loss_burning",
            np.nan,
        )

        print("\n========== BURNING THERMAL DIAGNOSTIC ==========")

        print(
            f"Tg_in                = "
            f"{state.Tg_burning_in:.6f} K"
        )

        print(
            f"Tg_out               = "
            f"{state.Tg_burning[-1]:.6f} K"
        )

        print(
            f"Ts_in                = "
            f"{state.Ts_burning_in:.6f} K"
        )

        print(
            f"Ts_out               = "
            f"{state.Ts_burning[-1]:.6f} K"
        )

        print(
            f"Hg_in                = "
            f"{Hg_in:.12e} W"
        )

        print(
            f"Hg_out               = "
            f"{state.Hgas_burning_out:.12e} W"
        )

        print(
            f"Hs_in                = "
            f"{Hs_in:.12e} W"
        )

        print(
            f"Hs_out               = "
            f"{state.Hsolid_burning_out:.12e} W"
        )

        print(
            f"Q_burning            = "
            f"{state.Q_burning:.12e} W"
        )

        print(
            f"Burning_Q_sink       = "
            f"{Burning_Q_sink:.12e} W"
        )

        print(
            f"Q_wall_loss          = "
            f"{Q_wall_loss:.12e} W"
        )

        print(
            f"Burning_energy_balance = "
            f"{state.Burning_energy_balance:.12e} W"
        )

        print("================================================")

        return state


    # ======================================================
    # GAS ENTHALPY TO NEXT ZONE
    #
    # Delegates to gas_phase/solid_phase. Kept as bound
    # methods (rather than deleted) so the public interface
    # is unchanged.
    # ======================================================
    def gas_enthalpy_out(self, Hg):
        return gas_phase.gas_enthalpy_out(Hg)

    # ======================================================
    # SOLID ENTHALPY TO NEXT ZONE
    # ======================================================
    def solid_enthalpy_out(self, Hs):

        return solid_phase.solid_enthalpy_out(Hs)
