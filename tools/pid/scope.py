"""What the P&ID may show: only what the twin models.

Each key is covered by exactly one instrument (or, for the manipulated
variable of the setpoint solve, by the setpoint). A key outside this
list is refused, so nothing the twin does not have is drawn.

Key grammar (see tools/pid/model.py):
    cfg:<dotted>              configs/twin_cfg.yaml                 Input
    mass:<field>              physics.steady_state_mass field       Modelled
    state:<field>[<i>]        GlobalState / attribute set on state  Modelled
    stage:<1..4>.<field>      preheater stage (1 = C4 .. 4 = C1)    Modelled
    attr:<object>.<field>     attribute of a twin object            Modelled
    diag:<fn>.<path>          reporter.diagnostics                  Report-only
"""

_STAGE_NAME = {1: "C4", 2: "C3", 3: "C2", 4: "C1"}

SCOPE = (
    # inputs
    "cfg:feed.Feed_rate_kg_s",
    "cfg:fuel.Fuel_rate_total",
    "cfg:fuel.kiln_fraction",
    "cfg:fuel.O2",
    "cfg:motion.rpm_default",
    "cfg:cooler.grate_speed_m_s",
    "cfg:cooler_air.cooling_air_rate_kg_per_kg_clinker",
    "cfg:burning.primary_air_fraction",
    # flows
    "mass:m_dot_fuel_kiln",
    "mass:m_dot_fuel_calciner",
    "mass:m_dot_primary_air",
    "mass:m_dot_secondary_air",
    "mass:m_dot_tertiary_air",
    "mass:m_dot_air_cooler",
    "mass:m_dot_vent_air",
    "mass:m_dot_clinker",
    "mass:m_dot_exhaust",
    "mass:m_dot_g_preheater",
    "mass:m_dot_g_calciner",
    "mass:m_dot_g_burning_out",
    "mass:m_dot_g_transition",
    "mass:m_dot_s_C5_dust",
    "mass:m_dot_s_calciner_in",
    "mass:m_dot_s_calciner_out",
    "mass:m_dot_s_burning",
    "attr:preheater.m_dot_dust_return",
    # temperatures
    *[f"stage:{k}.gas_outlet_temperature" for k in (1, 2, 3, 4)],
    *[f"stage:{k}.solid_outlet_temperature" for k in (1, 2, 3, 4)],
    "state:Tg_calciner",
    "state:Tg_burning_in",
    "state:Ts_burning_in",
    "state:Tg_transition[0]",
    "state:Ts_burning[-1]",
    "state:Ts_cooler[-1]",
    "state:Tg_secondary_air",
    "state:Tg_tertiary_air",
    "state:Tg_vent_air",
    # shell temperatures
    "state:Preheater_T_shell_max",
    "state:Calciner_T_shell_max",
    "state:Transition_T_shell_max",
    "state:Burning_T_shell_max",
    "state:Cooler_T_shell_max",
    # reports
    "diag:free_lime.free_lime_pct",
    *[f"diag:gas_pressure_losses.rows[{s}].dP" for s in ("calciner", "C5", "C4", "C3", "C2", "C1")],
    "diag:gas_pressure_losses.total_power_W",
)

# the diagnostics' paths a key may name
DIAG_PATHS = {
    "free_lime": {"free_lime_pct"},
    "gas_pressure_losses": {f"rows[{s}].dP" for s in ("calciner", "C5", "C4", "C3", "C2", "C1")}
                           | {"total_power_W"},
}

STATUS_OF_PREFIX = {
    "cfg": "Input",
    "mass": "Modelled",
    "state": "Modelled",
    "stage": "Modelled",
    "attr": "Modelled",
    "diag": "Report-only",
}
