from dataclasses import dataclass, field, fields
import numpy as np
from typing import Dict
from chemistry.phases import SolidPhases, GasPhases
from physics.zone_material import build_zone_material
from chemistry.composition import RAW_MEAL_COMPOSITION


@dataclass
class GlobalState:

    # ======================================================
    # SIMULATION
    # ======================================================
    t: float = 0.0
    dt: float = 0.05

    # ======================================================
    # DISCRETIZATION
    #
    # N: shared axial cell count for the continuous kiln
    # zones (Precalciner, Transition, Burning, Cooler).
    #
    # N_preheater: number of preheater cyclone stages. This
    # is a physical equipment count (5 real stages, each with
    # its own operating temperature band — see
    # pyroprocess/preheater/preheater.py), not a numerical
    # mesh resolution, so it is kept independent of N.
    # ======================================================
    N: int = 5
    N_preheater: int = 5

    # ======================================================
    # OPERATION
    # ======================================================
    Feed_temperature: float = 300.0  # K
    Feed_rate: float = 40.0 # kg/s
    Inventory_kg: float = 0.0 # kg/s
    Residence_time_target: float = 0.0 #min
    Fuel_rate_total: float = 2.0 # kg/s
    rpm: float = 0.0
    residence_time: float = 0.0 #min
    solid_velocity: float = 0.0 #m/s
    # Bed cross-section fraction, solved together with the transit
    # time from mass continuity (physics.bed_motion_from_continuity).
    # Distinct from operational.kiln_load, which is a capacity figure.
    bed_fill_fraction: float = 0.0 # -

    # ======================================================
    # FUEL ENERGY (W)
    # ======================================================
    Q_petcoke: float = 0.0
    Q_burning: float = 0.0
    
    
    # ======================================================
    # GLOBAL MASS BALANCE
    # ======================================================

    Initial_total_mass: float = 0.0

    Cumulative_feed_mass: float = 0.0
    Cumulative_clinker_mass: float = 0.0

    Total_solid_inventory: float = 0.0
    Total_gas_inventory: float = 0.0

    Global_mass_balance: float = 0.0
    Global_mass_balance_relative: float = 0.0

    feed_mass_in_step: float = 0.0
    feed_mass_in_rate: float = 0.0

    clinker_mass_out_step: float = 0.0
    clinker_mass_out_rate: float = 0.0

    # ======================================================
    # GAS / MASS FLOW STATE
    # ======================================================
    m_dot_g: float = 0.0
    m_dot_g_transition: float = 0.0
    m_dot_g_calciner: float = 0.0
    m_dot_g_preheater: float = 0.0
    rho_g: float = 1.2

    # ================= SECONDARY / TERTIARY AIR =================
    m_dot_air: float = 0.0
    m_dot_air_cooler: float = 0.0
    m_dot_primary_air: float = 0.0
    m_dot_secondary_air: float = 0.0
    m_dot_tertiary_air: float = 0.0
    m_dot_vent_air: float = 0.0

    Hgas_cooler_secondary: float = 0.0
    Hgas_cooler_tertiary: float = 0.0
    Hgas_cooler_vent: float = 0.0

    Hgas_burning_in: float = 0.0
    Hgas_burning_out: float = 0.0

    Hgas_transition_in: float = 0.0
    Hgas_transition_out: float = 0.0

    Hgas_calciner_in: float = 0.0
    Hgas_calciner_out: float = 0.0

    Hgas_preheater_in: float = 0.0
    Hgas_preheater_out: float = 0.0

    Hgas_cooler_in: float = 0.0
    Hgas_cooler_out: float = 0.0
    
    # ======================================================
    # SOLID ENERGY FLOW (W)
    # ======================================================

    Hsolid_burning_in: float = 0.0
    Hsolid_burning_out: float = 0.0

    Hsolid_transition_in: float = 0.0
    Hsolid_transition_out: float = 0.0

    Hsolid_calciner_in: float = 0.0
    Hsolid_calciner_out: float = 0.0

    Hsolid_preheater_in: float = 0.0
    Hsolid_preheater_out: float = 0.0

    Hsolid_cooler_in: float = 0.0
    Hsolid_cooler_out: float = 0.0

    
    # ================= BURNING STORED ENERGY =================
    Burning_gas_stored: float = 0.0
    Burning_solid_stored: float = 0.0
    Burning_wall_stored: float = 0.0
    Burning_stored_energy_change: float = 0.0

    # ================= TRANSITION STORED ENERGY =================
    Transition_gas_stored: float = 0.0
    Transition_solid_stored: float = 0.0
    Transition_wall_stored: float = 0.0
    Transition_stored_energy_change: float = 0.0

    # ================= CALCINER STORED ENERGY =================
    Calciner_gas_stored: float = 0.0
    Calciner_solid_stored: float = 0.0
    Calciner_wall_stored: float = 0.0
    Calciner_stored_energy_change: float = 0.0

    # ================= PREHEATER STORED ENERGY =================
    Preheater_gas_stored: float = 0.0
    Preheater_solid_stored: float = 0.0
    Preheater_wall_stored: float = 0.0
    Preheater_stored_energy_change: float = 0.0

    # ================= COOLER STORED ENERGY =================
    Cooler_gas_stored: float = 0.0
    Cooler_solid_stored: float = 0.0
    Cooler_wall_stored: float = 0.0
    Cooler_stored_energy_change: float = 0.0
    

    # ======================================================
    # ZONE ENERGY BALANCE (W)
    # ======================================================
    Burning_energy_balance: float = 0.0
    Transition_energy_balance: float = 0.0
    Calciner_energy_balance: float = 0.0
    Preheater_energy_balance: float = 0.0
    Cooler_energy_balance: float = 0.0

    # ======================================================
    # WALL HEAT LOSSES (W)
    # ======================================================

    Wall_loss_burning: float = 0.0
    Wall_loss_transition: float = 0.0
    Wall_loss_calciner: float = 0.0
    Wall_loss_preheater: float = 0.0
    Wall_loss_cooler: float = 0.0

    Total_wall_loss: float = 0.0
    
    # ================= WALL LOSS DEBUG =================
    q_loss_mean_burning: float = 0.0
    A_wall_burning: float = 0.0
    V_cell_burning: float = 0.0
    N_burning: int = 0

    q_loss_mean_transition: float = 0.0
    A_wall_transition: float = 0.0
    V_cell_transition: float = 0.0
    N_transition: int = 0
    

    # ======================================================
    # GLOBAL MASS & ENERGY
    # ======================================================

    Total_mass: float = 0.0
    Total_enthalpy: float = 0.0

    Total_heat_input: float = 0.0
    Total_heat_output: float = 0.0

    Reaction_heat_total: float = 0.0
    Stored_energy_total: float = 0.0

    Mass_balance_error: float = 0.0
    Energy_balance_error: float = 0.0

    Global_energy_residual: float = 0.0

    
    # ======================================================
    # GAS PHASE
    # ======================================================
    O2: float = 3.5  # %
    N2: float = 0.0
    

    # ======================================================
    # SOLID PHASE
    # ======================================================
    m_dot_s: float = 0.0
    m_dot_s_preheater: float = 0.0
    m_dot_s_calciner: float = 0.0
    m_dot_s_transition: float = 0.0

    
    # ======================================================
    # OLD PREHEATER STATES
    # ======================================================

    Tg_preheater_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 573.15
    )

    Ts_preheater_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 573.15
    )

    Tw_preheater_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 523.15
    )

    
    # ======================================================
    # PREHEATER INITIAL GUESSES (5 CELL) (K)
    # ======================================================
    Tg_preheater: np.ndarray = field(default_factory=lambda: np.ones(5) * 573.15)

    Ts_preheater: np.ndarray = field(default_factory=lambda: np.ones(5) * 573.15)

    Tw_preheater: np.ndarray = field(default_factory=lambda: np.ones(5) * 523.15)
    
    # ======================================================
    # TRANSITION INITIAL GUESSES (5 CELL) (K)
    # ------------------------------------------------------
    # Numerical initial guesses only.
    # ======================================================
    Tg_transition: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1650.0
    )

    Ts_transition: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1400.0
    )

    Tw_transition: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 800.0
    )
    

    # ======================================================
    # OLD TEMPERATURE STATES (5 CELL) (K)
    # ======================================================

    Tg_transition_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1650.0
    )

    Ts_transition_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1400.0
    )

    Tw_transition_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 800.0
    )

    Tg_calciner_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1473.15
    )

    Ts_calciner_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1223.15
    )

    Tw_calciner_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 773.15
    )


    # ======================================================
    # CALCINER INITIAL GUESSES (5 CELL) (K)
    # ======================================================

    Tg_calciner: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1473.15
    )

    Ts_calciner: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1223.15
    )

    Tw_calciner: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 773.15
    )

    # ======================================================
    # BURNING ZONE INLET TEMPERATURES (K)
    # ======================================================

    Tg_burning_in: float = 300.0
    Ts_burning_in: float = 300.0
    
    # ======================================================
    # BURNING INITIAL GUESSES (5 CELL) (K)
    # ------------------------------------------------------
    # These values are numerical initial guesses only.
    # They are NOT external energy inputs.
    # ======================================================

    Tg_burning_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1773.15
    )

    Ts_burning_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1673.15
    )

    Tw_burning_old: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 873.15
    )

    Tg_burning: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1773.15
    )

    Ts_burning: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 1673.15
    )

    Tw_burning: np.ndarray = field(
        default_factory=lambda: np.ones(5) * 873.15
    )




    # ======================================================
    # COOLER INITIAL GUESSES (5 CELL) (K)
    # ======================================================

    Tg_cooler_old: np.ndarray = field(default_factory=lambda: np.ones(5) * 423.15)
    Ts_cooler_old: np.ndarray = field(default_factory=lambda: np.ones(5) * 393.15)
    Tw_cooler_old: np.ndarray = field(default_factory=lambda: np.ones(5) * 353.15)


    Tg_cooler: np.ndarray = field(default_factory=lambda: np.ones(5) * (423.15))

    Ts_cooler: np.ndarray = field(default_factory=lambda: np.ones(5) * (393.15))

    Tw_cooler: np.ndarray = field(default_factory=lambda: np.ones(5) * (353.15))
    
    
    # ======================================================
    # SOLID - GASES
    # ======================================================

    def __post_init__(self):

        # ======================================================
        # RESIZE PER-CELL ARRAYS TO N / N_preheater
        #
        # Field defaults above are declared at a reference
        # length of 5 purely to document each array's initial
        # value; the arrays are resized here to their actual
        # zone cell count while preserving that same initial
        # value (arr[0] is uniform across the default array).
        # ======================================================

        def _resize(name, n):
            arr = getattr(self, name)
            setattr(self, name, np.full(n, arr[0]))

        for name in (
            "Tg_burning", "Ts_burning", "Tw_burning",
            "Tg_burning_old", "Ts_burning_old", "Tw_burning_old",
            "Hg_burning", "Hs_burning",
            "Hg_burning_old", "Hs_burning_old",

            "Tg_transition", "Ts_transition", "Tw_transition",
            "Tg_transition_old", "Ts_transition_old", "Tw_transition_old",
            "Hg_transition", "Hs_transition",
            "Hg_transition_old", "Hs_transition_old",

            "Tg_calciner", "Ts_calciner", "Tw_calciner",
            "Tg_calciner_old", "Ts_calciner_old", "Tw_calciner_old",
            "Hg_calciner", "Hs_calciner",
            "Hg_calciner_old", "Hs_calciner_old",

            "Tg_cooler", "Ts_cooler", "Tw_cooler",
            "Tg_cooler_old", "Ts_cooler_old", "Tw_cooler_old",
            "Hg_cooler", "Hs_cooler",
            "Hg_cooler_old", "Hs_cooler_old",

            "Burning_Q_sink_cells",
        ):
            _resize(name, self.N)

        for name in (
            "Tg_preheater", "Ts_preheater", "Tw_preheater",
            "Tg_preheater_old", "Ts_preheater_old", "Tw_preheater_old",
            "Hg_preheater", "Hs_preheater",
            "Hg_preheater_old", "Hs_preheater_old",
            "Drying_Q_sink_cells",
        ):
            _resize(name, self.N_preheater)

        N = self.N

        # ======================================================
        # TOTAL PYROPROCESS SOLID INVENTORY
        # ======================================================
        total_solid_inventory = 100_000.0  # kg

        n_zones = 5

        zone_inventory = (
            total_solid_inventory / n_zones
        )

        # ======================================================
        # INITIALIZE MATERIALS
        # ======================================================
        def make_cell(key):

            component_mass = (
                zone_inventory
                * RAW_MEAL_COMPOSITION[key]
                / 100_000.0
            )

            return np.full(
                self.N_preheater,
                component_mass / self.N_preheater,
                dtype=float,
            )

        # ======================================================
        # ZONE MATERIAL STATES
        # ------------------------------------------------------
        # Only the Preheater receives fresh raw meal.
        # Downstream zones receive solid-phase state through
        # upstream -> downstream handoff.
        # ======================================================

        empty_cell = lambda key: np.zeros(N, dtype=float)

        self.materials = {
            "preheater": build_zone_material(self.N_preheater, make_cell),

            "calciner": build_zone_material(N, empty_cell),

            "transition": build_zone_material(N, empty_cell),

            "burning": build_zone_material(N, empty_cell),

            "cooler": build_zone_material(N, empty_cell),
        }

        # ======================================================
        # STEADY-STATE SPECIES MASS FLOWS [kg/s]
        # ------------------------------------------------------
        # Same SolidPhases/GasPhases layout as `materials`, but
        # each entry is the species mass FLOW leaving that cell
        # (or cyclone stage), not a held-up mass. This is the
        # track the clinkering chemistry runs on: its reacted
        # amounts are kg/s and its heats W, which is what the
        # steady-state energy balances consume.
        #
        # `materials` above is a held-up inventory advanced by
        # state.dt. Feeding it into the steady-state balances
        # made the clinkering heat scale with dt (a J-per-step
        # figure read as W) and with 1/N (a per-cell local
        # conversion applied to an inventory spread over N
        # cells), so it did not converge under mesh refinement.
        # It is kept unchanged for its existing diagnostics.
        #
        # Solids: flow leaving the cell. Gases: flow GENERATED in
        # the cell. Populated by the zones during a step; zeros
        # until the first pass through each zone.
        # ======================================================

        empty_flow = lambda key: np.zeros(N, dtype=float)

        empty_stage_flow = lambda key: np.zeros(
            self.N_preheater,
            dtype=float,
        )

        self.material_flows = {
            "preheater": build_zone_material(self.N_preheater, empty_stage_flow),

            "calciner": build_zone_material(N, empty_flow),

            "transition": build_zone_material(N, empty_flow),

            "burning": build_zone_material(N, empty_flow),

            "cooler": build_zone_material(N, empty_flow),
        }

        
        
        # ======================================================
        # INITIAL GLOBAL MASS
        # ======================================================

        initial_solid_mass = 0.0

        for material in self.materials.values():

            for f in fields(SolidPhases):

                values = getattr(
                    material.solids,
                    f.name,
                )

                initial_solid_mass += np.sum(
                    np.maximum(values, 0.0)
                )

        initial_gas_mass = 0.0

        for material in self.materials.values():

            for f in fields(GasPhases):

                values = getattr(
                    material.gases,
                    f.name,
                )

                initial_gas_mass += np.sum(
                    np.maximum(values, 0.0)
                )

        self.Initial_total_mass = (
            initial_solid_mass
            + initial_gas_mass
        )

        self.Total_solid_inventory = (
            initial_solid_mass
        )

        self.Total_gas_inventory = (
            initial_gas_mass
        )


    # ======================================================
    # ENTHALPY STATE VARIABLES
    # ======================================================

    Hg_burning: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_burning: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_transition: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_transition: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_calciner: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_calciner: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_preheater: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_preheater: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_cooler: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_cooler: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    # ======================================================
    # OLD ENTHALPY STATES
    # ======================================================

    Hg_burning_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_burning_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_transition_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_transition_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_calciner_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_calciner_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_preheater_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_preheater_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    Hg_cooler_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Hs_cooler_old: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )


    # ======================================================
    # REACTION HEAT SINKS
    # ======================================================

    Drying_Q_sink: float = 0.0

    # Free moisture evaporated in the preheater [kg/s]; leaves
    # the solid stream and joins the exhaust gas.
    m_dot_H2O_evaporated_preheater: float = 0.0
    
    Drying_Q_sink_cells: np.ndarray = field(
    default_factory=lambda: np.zeros(5)
    )

    Dehydroxylation_Q_sink: float = 0.0

    Calcination_Q_sink: float = 0.0

    Belite_Q_sink: float = 0.0

    Alite_Q_sink: float = 0.0

    C3A_Q_sink: float = 0.0

    C4AF_Q_sink: float = 0.0

    # Clinkering heat absorbed in each burning cell [W]
    # (sum of the four reactions above, per cell).
    Burning_Q_sink_cells: np.ndarray = field(
        default_factory=lambda: np.zeros(5)
    )

    Reaction_Q_sink: float = 0.0
    
    # ======================================================
    # ZONE HEAT SINKS
    # ======================================================
    
    Calciner_Q_sink: float = 0.0


    # ======================================================
    # API
    # ======================================================
    Inputs: Dict = field(default_factory=dict)
    Outputs: Dict = field(default_factory=dict)
    
    

