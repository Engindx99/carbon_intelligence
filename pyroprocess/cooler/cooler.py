import numpy as np
import yaml

from physics.shell import wall_stack
from physics.physics import ZONE_HT_CONFIG
from physics.physics import h_gas
from physics.physics import T_solid_from_h

from chemistry.phases import get_cell_solid_flow
from chemistry.phases import set_cell_solid_flow

from . import gas_phase
from . import solid_phase
from . import heat_transfer


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Cooler:

    def __init__(self, N=5, L=20.0, cfg=None):

        # Kept on the instance because the name `cfg` is rebound
        # further down to the ZONE_HT_CONFIG entry for this zone.
        self.plant_cfg = cfg

        self.N = N
        self.L = L
        self.dz = L / N

        # ================= ZONE =================
        self.zone = "cooler"

        # ================= NUMERICAL =================
        self.eps = 1e-9

        # ================= GRATE GEOMETRY =================
        #
        # A grate cooler, not the rotary cylinder (D = 4.2 m) this
        # zone carried as a placeholder. The fluid volume is a box,
        # width x length x casing height, with the clinker bed as
        # its bottom slice (geometry/cooler/cooler.md):
        #
        #   width 4.0 m, casing 3.0 m, porosity 0.4: the FLS
        #   reference cooler (Svensen et al. 2024, arXiv:2409.09076)
        #   length: the PF5000 grate area 119.6 m2 / width
        #   solid density: their Table II on their clinker
        #   grate speed: the design bed 0.409 m at 5000 t/d
        #
        # The bed depth is not a dimension: the grate speed is the
        # operator's input, so the bed is as deep as the clinker
        # flow makes it, h = m_dot / (rho_bulk w v) (bed_depth).
        cooler_cfg = (cfg or {}).get("cooler", {})

        self.width = float(cooler_cfg.get("width", 4.0))
        self.casing_height = float(cooler_cfg.get("casing_height", 3.0))
        self.grate_speed = float(cooler_cfg.get("grate_speed_m_s", 0.01854))

        self.epsilon_bed = float(cooler_cfg.get("bed_porosity", 0.4))
        self.rho_solid = float(cooler_cfg.get("solid_density", 3178.0))

        # Bulk density of the bed [kg/m3]: what the hold-up is.
        self.rho_s = (1.0 - self.epsilon_bed) * self.rho_solid

        for name, value in (
            ("width", self.width),
            ("casing_height", self.casing_height),
            ("grate_speed_m_s", self.grate_speed),
            ("solid_density", self.rho_solid),
        ):
            if not value > 0.0:
                raise ValueError(
                    f"cooler.{name} must be > 0, got {value}"
                )

        if not (0.0 < self.epsilon_bed < 1.0):
            raise ValueError(
                "cooler.bed_porosity must be in (0, 1), "
                f"got {self.epsilon_bed}"
            )

        # ================= INTERFACIAL AREA =================
        self.k_interfacial = 1.0

        # The gas->solid area is a PACKED-BED specific surface and
        # its d_p is the clinker nodule. See configs/twin_cfg.yaml
        # cooler.particle_diameter_m for the value, its source and
        # the measured plateau that makes it a mechanism rather
        # than a knob.
        self.particle_diameter = float(
            cooler_cfg.get(
                "particle_diameter_m",
                0.015,
            )
        )

        if not (0.0 < self.particle_diameter < self.casing_height):
            raise ValueError(
                "cooler.particle_diameter_m must be positive and "
                "smaller than the casing height "
                f"{self.casing_height} m, got {self.particle_diameter}"
            )

        # Per unit BED volume [m2/m3]:
        #   a_gs  nodule surface, 6(1-eps)/d_p
        #   a_ws  the bed against the two side walls: 2 h dz over
        #         w h dz. The grate under it is swept by the air,
        #         not a lined wall.
        # a_gw (the walls and roof above the bed) depends on the
        # bed depth, so bed_geometry() forms it.
        self.a_gs = (
            6.0
            * (1.0 - self.epsilon_bed)
            * self.k_interfacial
            / self.particle_diameter
        )

        self.a_ws = 2.0 / self.width

        # ================= CASING (WALL) GEOMETRY =================
        # The lined casing per cell: two side walls and the roof.
        # The grate is not a wall, and the two end walls are left
        # out like a tube's ends.
        self.wall_perimeter = 2.0 * self.casing_height + self.width
        self.A_wall_cell = self.wall_perimeter * self.dz
        self.A_wall = self.wall_perimeter * self.L

        # ================= REFRACTORY / SHELL =================
        #
        # Faz 6. A grate cooler is a lagged steel casing, not a
        # bare shell: castable refractory, mineral wool, thin
        # plate (physics.shell). The casing is flat, so the stack
        # is resolved as a plane wall, and its outer film is a
        # vertical plate's on the casing height.
        self.wall_stack = wall_stack(self.plant_cfg, self.zone)

        self.refractory_thickness = self.wall_stack.thickness

        self.shell = self.wall_stack.planar_geometry(
            A_cell=self.A_wall_cell,
            L_cell=self.dz,
            L_char=self.casing_height,
        )

        # ================= THERMODYNAMIC REFERENCE =================
        self.T_ref = 298.15
        self.T_amb = 300.0

        # ================= PROPERTIES =================
        self.rho_g = 1.2
        self.rho_wall = 3000.0

        self.Cp_g = 1005.0
        # Solid Cp and enthalpy: physics.cp_solid / h_solid, one
        # definition for every solid stream in the plant.
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
    # BED
    # ======================================================
    def bed_depth(self, m_dot_s):
        """Depth [m] of the bed a clinker flow [kg/s] makes on the
        grate at the grate speed: m_dot = rho_bulk w h v."""

        return float(m_dot_s) / (
            self.rho_s * self.width * self.grate_speed
        )

    def bed_geometry(self, h_cells):
        """Per-cell bed volume [m3] and the gas->wall area per unit
        bed volume [m2/m3] for bed depths h_cells [m].

        The exchanges are written per unit BED volume (a_gs, a_ws,
        a_gw), so V_bed is the volume they multiply. The gas above
        the bed sees the side walls over (H - h) and the roof."""

        h = np.asarray(h_cells, dtype=float)

        if np.any(h <= 0.0) or np.any(h >= self.casing_height):
            raise ValueError(
                "cooler bed depth must be in (0, "
                f"{self.casing_height}) m, got {h.min():.4g} .. "
                f"{h.max():.4g}"
            )

        V_bed = self.width * h * self.dz

        a_gw = (
            2.0 * (self.casing_height - h) + self.width
        ) / (self.width * h)

        return V_bed, a_gw

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

        # Clinker species flows [kg/s]: no reaction in the
        # cooler, so every cell carries the stream discharged
        # by the last Burning cell unchanged.
        burning_solid_flows = state.material_flows["burning"].solids

        clinker_flow = get_cell_solid_flow(
            burning_solid_flows,
            burning_solid_flows.CaCO3.size - 1,
        )

        for cooler_cell in range(self.N):
            set_cell_solid_flow(
                state.material_flows["cooler"].solids,
                cooler_cell,
                clinker_flow,
            )

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
        Ts_in = T_solid_from_h(
            state.Hsolid_cooler_in / state.m_dot_s,
            self.T_ref,
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

        # Reporting only. D2 bounds secondary air, so secondary
        # air has to exist as a number somewhere; before this it
        # did not, and the bound was being applied to the burner
        # mixture instead. See gas_phase.stream_temperatures.
        (
            state.Tg_secondary_air,
            state.Tg_tertiary_air,
            state.Tg_vent_air,
        ) = gas_phase.stream_temperatures(
            self,
            state.Hgas_cooler_secondary,
            state.Hgas_cooler_tertiary,
            state.Hgas_cooler_vent,
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
