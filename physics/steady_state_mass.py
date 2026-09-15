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

    # ======================================================
    # CHEMICAL MASS GENERATION
    # ======================================================

    m_dot_CO2_generated: float = 0.0
    m_dot_CO2_generated_transition: float = 0.0
    m_dot_H2O_generated: float = 0.0

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

    def calculate_burning_inlet(self):
        """
        Burning receives combustion air and fuel.
        """

        self.m_dot_g_burning = (
            self.m_dot_air
            + self.m_dot_fuel
        )

        return self.m_dot_g_burning

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
    ):
        """
        Calcination transfers CO2 mass from solid phase
        to gas phase.

        CaCO3 -> CaO + CO2
        """

        self.m_dot_CO2_generated = float(m_dot_CO2_generated)

        self.m_dot_s_calciner_out = (
            self.m_dot_s_calciner_in
            - self.m_dot_CO2_generated
        )

        self.m_dot_s_transition_in = (
            self.m_dot_s_calciner_out
        )

        self.m_dot_g_calciner = (
            self.m_dot_g_transition
            + self.m_dot_CO2_generated
        )

        return (
            self.m_dot_s_calciner_out,
            self.m_dot_g_calciner,
        )

    def calculate_global_balance(self):
        """
        Global steady-state mass balance:

            raw meal + fuel + air
            -
            clinker - exhaust
            = 0
        """

        self.mass_flow_in = (
            self.m_dot_raw_meal
            + self.m_dot_fuel
            + self.m_dot_air
        )

        self.mass_flow_out = (
            self.m_dot_clinker
            + self.m_dot_exhaust
        )

        self.steady_state_mass_residual = (
            self.mass_flow_in
            - self.mass_flow_out
        )

        return self.steady_state_mass_residual