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
        state = self.chemistry.apply_burning(
            state,
            self.dz,
            u_s,
        )

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
        state.Hg_burning = (
            state.m_dot_g
            * h_gas(
                state.Tg_burning,
                self.T_ref
            )
        )

        state.Hs_burning = (
            state.m_dot_s
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
        # GAS ENTHALPY OUT
        # ======================================================
        state.Hgas_burning_out = (
            self.gas_enthalpy_out(
                state.Hg_burning
            )
        )

        # ======================================================
        # SOLID ENTHALPY OUT
        # ======================================================
        state.Hsolid_burning_out = (
            self.solid_enthalpy_out(
                state.Hs_burning
            )
        )

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
