from dataclasses import dataclass


@dataclass
class SteadyStateMassFlow:
    """
    Steady-state process mass-flow model.

    All flow rates are SI:
        kg/s
    """

    # ======================================================
    # EXTERNAL INPUTS
    # ======================================================

    m_dot_raw_meal: float = 0.0
    m_dot_fuel: float = 0.0
    m_dot_air: float = 0.0

    # ======================================================
    # SOLID STREAM
    # ======================================================

    m_dot_s_preheater: float = 0.0
    m_dot_s_calciner_in: float = 0.0
    m_dot_s_calciner_out: float = 0.0
    m_dot_s_transition_in: float = 0.0
    m_dot_s_transition: float = 0.0
    m_dot_s_burning: float = 0.0
    m_dot_s_cooler: float = 0.0
    m_dot_clinker: float = 0.0

    # ======================================================
    # GAS STREAM
    # ======================================================

    m_dot_g_burning: float = 0.0
    m_dot_g_transition: float = 0.0
    m_dot_g_calciner: float = 0.0
    m_dot_g_preheater: float = 0.0
    m_dot_exhaust: float = 0.0

    # ================= SECONDARY / TERTIARY AIR =================
    m_dot_air_cooler: float = 0.0
    m_dot_primary_air: float = 0.0
    m_dot_secondary_air: float = 0.0
    m_dot_tertiary_air: float = 0.0
    m_dot_vent_air: float = 0.0

    # ======================================================
    # CHEMICAL MASS GENERATION
    # ======================================================

    m_dot_CO2_generated: float = 0.0
    m_dot_CO2_generated_transition: float = 0.0
    m_dot_H2O_generated: float = 0.0
    m_dot_H2O_generated_calciner: float = 0.0

    # ======================================================
    # GLOBAL BALANCE
    # ======================================================

    mass_flow_in: float = 0.0
    mass_flow_out: float = 0.0
    steady_state_mass_residual: float = 0.0

    def set_external_inputs(
        self,
        m_dot_raw_meal,
        m_dot_fuel,
        m_dot_air,
    ):
        self.m_dot_raw_meal = float(m_dot_raw_meal)
        self.m_dot_fuel = float(m_dot_fuel)
        self.m_dot_air = float(m_dot_air)

    def calculate_transition_flow(
        self,
        m_dot_CO2_generated,
    ):
        """
        Residual (in-flight) calcination continuing in the
        transition zone transfers additional CO2 mass from
        solid phase to gas phase.

        CaCO3 -> CaO + CO2
        """

        self.m_dot_CO2_generated_transition = float(
            m_dot_CO2_generated
        )

        self.m_dot_g_transition = (
            self.m_dot_g_burning
            + self.m_dot_CO2_generated_transition
        )

        return self.m_dot_g_transition

    def calculate_calciner_flow(
        self,
        m_dot_CO2_generated,
        m_dot_tertiary_air=0.0,
        m_dot_H2O_generated=0.0,
    ):
        """
        Calcination transfers CO2 mass from solid phase to gas
        phase; dehydroxylation transfers Bound_H2O mass from
        solid phase to gas phase the same way. Tertiary air from
        the cooler is ducted directly into the calciner's gas
        inlet (mass + enthalpy only; no calciner combustion
        model).

        CaCO3 -> CaO + CO2
        Bound_H2O -> H2O
        """

        self.m_dot_CO2_generated = float(m_dot_CO2_generated)
        self.m_dot_H2O_generated_calciner = float(m_dot_H2O_generated)
        self.m_dot_tertiary_air = float(m_dot_tertiary_air)

        self.m_dot_s_calciner_out = (
            self.m_dot_s_calciner_in
            - self.m_dot_CO2_generated
            - self.m_dot_H2O_generated_calciner
        )

        self.m_dot_s_transition_in = (
            self.m_dot_s_calciner_out
        )

        self.m_dot_g_calciner = (
            self.m_dot_g_transition
            + self.m_dot_CO2_generated
            + self.m_dot_H2O_generated_calciner
            + self.m_dot_tertiary_air
        )

        return (
            self.m_dot_s_calciner_out,
            self.m_dot_g_calciner,
        )

    def calculate_global_balance(self):
        """
        Global steady-state mass balance:

            raw meal + fuel + primary_air + air_cooler
            -
            clinker - exhaust - vent_air
            = 0

        Kiln combustion air (self.m_dot_air = primary + secondary)
        is no longer an independent ambient intake on its own:
        secondary air's mass already originates from the cooler's
        own ambient draw (self.m_dot_air_cooler = secondary +
        tertiary + vent), so the two independent ambient intakes
        are primary_air (at the burner) and air_cooler (at the
        cooler fan) -- self.m_dot_air is intentionally NOT added
        here to avoid double-counting secondary air's mass.
        vent_air appears on both sides (drawn in at the cooler,
        exhausted straight back to atmosphere without ever
        entering the process gas train), which is a deliberate,
        transparent pass-through, not a bug.
        """

        self.mass_flow_in = (
            self.m_dot_raw_meal
            + self.m_dot_fuel
            + self.m_dot_primary_air
            + self.m_dot_air_cooler
        )

        self.mass_flow_out = (
            self.m_dot_clinker
            + self.m_dot_exhaust
            + self.m_dot_vent_air
        )

        self.steady_state_mass_residual = (
            self.mass_flow_in
            - self.mass_flow_out
        )

        return self.steady_state_mass_residual