import numpy as np
import yaml

from physics.physics import interfacial_areas
from physics.physics import kiln_geometry
from physics.physics import wall_geometry
from physics.physics import ZONE_HT_CONFIG
from physics.physics import h_gas

from . import gas_phase
from . import solid_phase
from . import heat_transfer


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Cooler:

    def __init__(self, N=5, L=20.0):

        self.N = N
        self.L = L
        self.dz = L / N

        # ================= ZONE =================
        self.zone = "cooler"

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
        self.refractory_thickness = 0.15
        self.refractory_conductivity = 1.5

        # ================= EXTERNAL =================
        self.h_ext = 18.0

        # ================= THERMODYNAMIC REFERENCE =================
        self.T_ref = 298.15
        self.T_amb = 300.0

        # ================= PROPERTIES =================
        self.rho_g = 1.2
        self.rho_s = 1100.0
        self.rho_wall = 3000.0

        self.Cp_g = 1005.0
        self.Cp_s = 850.0
        self.Cp_wall = 1000.0

        # ================= HEAT TRANSFER =================
        cfg = ZONE_HT_CONFIG[self.zone]

        self.hv_gs = cfg["hv_gs"]
        self.hv_gw = cfg["hv_gw"]
        self.hv_ws = cfg["hv_ws"]

        # ================= COOLER AIR (secondary/tertiary/vent split) =================
        cooler_air_cfg = load_cfg("configs/twin_cfg.yaml").get("cooler_air", {})

        self.cooling_air_rate = cooler_air_cfg.get(
            "cooling_air_rate_kg_per_kg_clinker",
            2.2
        )

        self.tertiary_air_fraction = cooler_air_cfg.get(
            "tertiary_air_fraction",
            0.0
        )

        if self.cooling_air_rate <= 0.0:
            raise ValueError(
                "cooler_air.cooling_air_rate_kg_per_kg_clinker must be > 0, "
                f"got {self.cooling_air_rate}"
            )

        if not (0.0 <= self.tertiary_air_fraction < 1.0):
            raise ValueError(
                "cooler_air.tertiary_air_fraction must be in [0, 1), "
                f"got {self.tertiary_air_fraction}"
            )


    # ======================================================
    # THERMAL STEP
    #
    # Delegates to heat_transfer.thermal_step(). Kept as a
    # bound method (rather than deleted) so the public
    # interface Cooler.thermal_step(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (burning.py, transition.py, preheater.py, precalciner).
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

        if not isinstance(state.Tg_cooler, np.ndarray):
            raise TypeError("Tg_cooler must be np.ndarray")

        if state.Tg_cooler.shape != (self.N,):
            raise ValueError("Cooler state corrupted")

        # ======================================================
        # INLET / OUTLET HANDOFF
        # ======================================================

        Tg_in = self.T_amb

        state.Hgas_cooler_in = state.m_dot_air_cooler * float(h_gas(Tg_in, self.T_ref))
        state.Hsolid_cooler_in = state.Hsolid_burning_out

        # Clinker inlet temperature is derived from the ENTHALPY
        # handoff rather than read back from state.Ts_burning[-1].
        # The two were the same number only as long as the kiln
        # handed off its last cell CENTRE. Burning now discharges
        # through its reconstructed outlet FACE
        # (pyroprocess/burning/solid_phase.py), so reading the
        # centre would start the cooler from a hotter stream than
        # the enthalpy it is credited with and create energy at
        # the handoff -- worth 2.3 MW, 2.8% of fuel input, at
        # N=20. Deriving T from H is also what every other zone
        # already does; see burning/solid_phase.resolve_solid_inlet
        # and precalciner/raw_meal_inlet.solid_temperature_from_enthalpy.
        Ts_in = (
            self.T_ref
            + state.Hsolid_cooler_in
            / (state.m_dot_s * self.Cp_s)
        )

        state.Tg_cooler_in = Tg_in
        state.Ts_cooler_in = Ts_in

        # Cells are control volumes, not boundary nodes: the
        # inlet streams enter their balance as a flux
        # (gas_phase/solid_phase), so temperatures at the
        # inlet cell are cell averages and must NOT be
        # overwritten with the inlet temperatures here. Gas
        # is counter-current to the solid: gas enters (Tg_in)
        # at Tg_cooler[N-1] (clinker-discharge end) and exits
        # hottest at Tg_cooler[0]; solid enters (Ts_in) at
        # Ts_cooler[0] (clinker-inlet end) and exits coolest
        # at Ts_cooler[-1].

        # ======================================================
        # STEADY-STATE THERMAL SOLVE
        # ======================================================

        (
            Tg,
            Ts,
            Tw,
            wall_loss,
            _,
            Qgs,
            Qgw,
            Qws,
            energy_in,
            energy_out,
            total_energy_balance,
        ) = self.thermal_step(
            state.Tg_cooler,
            state.Ts_cooler,
            state.Tw_cooler,
            state,
        )

        # ======================================================
        # UPDATE STATE
        # ======================================================

        state.Tg_cooler = Tg
        state.Ts_cooler = Ts
        state.Tw_cooler = Tw

        state.Wall_loss_cooler = float(wall_loss)

        # ======================================================
        # ENTHALPY
        # ======================================================

        state.Hgas_cooler_out = self.gas_enthalpy_out(
            state.Tg_cooler,
            state,
        )

        (
            state.Hgas_cooler_secondary,
            state.Hgas_cooler_tertiary,
            state.Hgas_cooler_vent,
        ) = self.gas_enthalpy_split(
            state.Tg_cooler,
            state,
        )

        state.Hsolid_cooler_out = self.solid_enthalpy_out(
            state.Ts_cooler,
            state,
        )

        # ======================================================
        # HEAT-TRANSFER DIAGNOSTICS
        # ======================================================

        state.Q_gs_cooler = Qgs
        state.Q_gw_cooler = Qgw
        state.Q_ws_cooler = Qws

        # ======================================================
        # ENERGY BALANCE
        # ======================================================

        state.Cooler_energy_in = energy_in
        state.Cooler_energy_out = energy_out
        state.Cooler_energy_balance = total_energy_balance

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
    # GAS ENTHALPY SPLIT (secondary / tertiary / vent)
    #
    # Delegates to gas_phase.gas_enthalpy_split(). See that
    # function for the split model.
    # ======================================================
    def gas_enthalpy_split(self, Tg, state):

        return gas_phase.gas_enthalpy_split(
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
