from dataclasses import dataclass, field

import numpy as np

from . import heat_transfer


@dataclass
class PreheaterStage:
    """
    Common physical model for a single preheater stage.

    The stage contains the existing lumped thermal model:
        gas ↔ solid
        gas ↔ wall
        solid ↔ wall
        wall heat loss
        reaction heat/sink
        energy balance

    NOTE:
        This class intentionally does not model cyclone separation
        or raw-meal transport explicitly yet.
    """

    stage_id: int

    gas_inlet_temperature: float = 0.0
    gas_outlet_temperature: float = 0.0

    gas_inlet_enthalpy: float = 0.0
    gas_outlet_enthalpy: float = 0.0

    solid_inlet_temperature: float = 0.0
    solid_outlet_temperature: float = 0.0

    solid_inlet_enthalpy: float = 0.0
    solid_outlet_enthalpy: float = 0.0

    wall_temperature: float = 0.0

    # Faz 6: outer casing temperature of the stage, solved by
    # physics.shell alongside the hot face. Published so the
    # plausibility check reads it instead of rebuilding it from a
    # resistance ratio.
    shell_temperature: float = 0.0

    Q_gs: float = 0.0
    Q_gw: float = 0.0
    Q_ws: float = 0.0

    Q_wall_loss: float = 0.0
    Q_reaction: float = 0.0

    energy_in: float = 0.0
    energy_out: float = 0.0
    energy_residual: float = 0.0

    gas_T_min: float = 0.0
    gas_T_max: float = 0.0

    # Node outlet temperatures [K] along the stage (co-current
    # march in heat_transfer.solve_stage); diagnostics only.
    node_gas_temperatures: np.ndarray = field(
        default_factory=lambda: np.zeros(0)
    )
    node_solid_temperatures: np.ndarray = field(
        default_factory=lambda: np.zeros(0)
    )
    node_wall_temperatures: np.ndarray = field(
        default_factory=lambda: np.zeros(0)
    )

    def __post_init__(self):
        if self.stage_id < 1:
            raise ValueError("stage_id must be >= 1")

    def reset_diagnostics(self):
        self.Q_gs = 0.0
        self.Q_gw = 0.0
        self.Q_ws = 0.0
        self.Q_wall_loss = 0.0
        self.Q_reaction = 0.0

        self.energy_in = 0.0
        self.energy_out = 0.0
        self.energy_residual = 0.0

        self.gas_T_min = 0.0
        self.gas_T_max = 0.0

    # ======================================================
    # SOLVE
    #
    # Delegates to heat_transfer.solve_stage(). Kept as a
    # bound method (rather than deleted) so the public
    # interface PreheaterStage.solve(...) is unchanged,
    # matching the pattern used by the other zone classes
    # (burning.py, transition.py, cooler.py, precalciner).
    # ======================================================
    def solve(
        self,
        gas_inlet_temperature,
        solid_inlet_temperature,
        m_dot_g,
        m_dot_s,
        state,
        model,
        reaction_power=0.0,
        m_dot_vapor=0.0,
    ):

        return heat_transfer.solve_stage(
            self,
            gas_inlet_temperature,
            solid_inlet_temperature,
            m_dot_g,
            m_dot_s,
            state,
            model,
            reaction_power,
            m_dot_vapor,
        )
