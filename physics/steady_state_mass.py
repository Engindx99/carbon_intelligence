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

    # Fuel and combustion air split between the two firings.
    # The totals above stay the plant's; these partition them in
    # the same ratio, so both firings run at one excess-air level
    # and the dry stack O2 target is unaffected by where the fuel
    # burns (see main._update_steady_state_mass_flow).
    m_dot_fuel_kiln: float = 0.0
    m_dot_fuel_calciner: float = 0.0
    m_dot_air_kiln: float = 0.0
    m_dot_air_calciner: float = 0.0

    # ======================================================
    # SOLID STREAM
    # ======================================================

    m_dot_s_preheater: float = 0.0
    m_dot_s_calciner_in: float = 0.0
    m_dot_s_calciner_out: float = 0.0
    m_dot_s_C5_dust: float = 0.0
    m_dot_s_transition_in: float = 0.0
    m_dot_s_transition: float = 0.0
    m_dot_s_burning: float = 0.0
    m_dot_s_cooler: float = 0.0
    m_dot_clinker: float = 0.0

    # ======================================================
    # GAS STREAM
    # ======================================================

    m_dot_g_burning: float = 0.0
    m_dot_g_burning_out: float = 0.0
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
    m_dot_CO2_generated_burning: float = 0.0
    m_dot_H2O_generated: float = 0.0
    m_dot_H2O_generated_calciner: float = 0.0

    # ======================================================
    # KILN SOLID HOLD-UP RATES [kg/s]
    #
    # Dynamic step only (chemistry/parcels.py): the rate at which
    # each kiln zone's bed gains mass. Zero at steady state, where
    # every solid stream is its inflow minus what it releases.
    # ======================================================

    m_dot_stored_transition: float = 0.0
    m_dot_stored_burning: float = 0.0
    m_dot_stored_cooler: float = 0.0

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

    def calculate_burning_flow(
        self,
        m_dot_CO2_generated,
    ):
        """
        Residual calcination inside the KILN.

        The meal reaches the burning zone still partly
        carbonated, so calcination finishes there. Until this
        was modelled the kiln passed CaCO3 through untouched and
        it was counted as clinker, which inflated the product
        stream and hid the largest endothermic load in the kiln.

        CaCO3 -> CaO + CO2

        The CO2 leaves the bed and joins the kiln gas, so it
        both REDUCES the clinker leaving to the cooler and
        INCREASES the gas handed to the transition zone.
        """

        self.m_dot_CO2_generated_burning = float(
            m_dot_CO2_generated
        )

        self.m_dot_g_burning_out = (
            self.m_dot_g_burning
            + self.m_dot_CO2_generated_burning
        )

        self.m_dot_s_cooler = (
            self.m_dot_s_burning
            - self.m_dot_CO2_generated_burning
            - self.m_dot_stored_burning
        )

        return self.m_dot_s_cooler

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

        # Starts from the gas LEAVING the kiln, which now
        # carries the kiln's own calcination CO2 as well as the
        # burner's combustion products.
        self.m_dot_g_transition = (
            self.m_dot_g_burning_out
            + self.m_dot_CO2_generated_transition
        )

        return self.m_dot_g_transition

    def calculate_calciner_flow(
        self,
        m_dot_CO2_generated,
        m_dot_tertiary_air=0.0,
        m_dot_H2O_generated=0.0,
        m_dot_fuel_calciner=0.0,
        c5_separation_efficiency=1.0,
    ):
        """
        Calcination transfers CO2 mass from solid phase to gas
        phase; dehydroxylation transfers Bound_H2O mass from
        solid phase to gas phase the same way. Tertiary air from
        the cooler is ducted into the calciner's gas inlet, and
        the calciner's own fuel is injected there and burns, so
        both add to the gas stream leaving this unit.

        CaCO3 -> CaO + CO2
        Bound_H2O -> H2O
        """

        self.m_dot_CO2_generated = float(m_dot_CO2_generated)
        self.m_dot_H2O_generated_calciner = float(m_dot_H2O_generated)
        self.m_dot_tertiary_air = float(m_dot_tertiary_air)
        self.m_dot_fuel_calciner = float(m_dot_fuel_calciner)

        self.m_dot_s_calciner_out = (
            self.m_dot_s_calciner_in
            - self.m_dot_CO2_generated
            - self.m_dot_H2O_generated_calciner
        )

        # C5 (pyroprocess/precalciner/c5_cyclone) sends eta of
        # the calciner's outlet into the kiln and lets the rest
        # up into C4, whose underflow returns it to the calciner
        # (already in m_dot_s_calciner_in).
        eta = float(c5_separation_efficiency)

        self.m_dot_s_transition_in = (
            eta * self.m_dot_s_calciner_out
        )

        self.m_dot_s_C5_dust = (
            self.m_dot_s_calciner_out
            - self.m_dot_s_transition_in
        )

        self.m_dot_g_calciner = (
            self.m_dot_g_transition
            + self.m_dot_CO2_generated
            + self.m_dot_H2O_generated_calciner
            + self.m_dot_tertiary_air
            + self.m_dot_fuel_calciner
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

        Combustion air (self.m_dot_air is the PLANT total; the
        kiln's share is self.m_dot_air_kiln, and THAT is what
        primary + secondary sum to -- main.py:862, :1074-1082.
        This line used to say m_dot_air = primary + secondary,
        which is wrong by the calciner's share. The balance
        arithmetic below was never affected; only this sentence.)
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

        # Mass going into the kiln's bed hold-up books as an
        # outflow, as stored energy does; zero at steady state.
        self.mass_flow_out = (
            self.m_dot_clinker
            + self.m_dot_exhaust
            + self.m_dot_vent_air
            + self.m_dot_stored_transition
            + self.m_dot_stored_burning
            + self.m_dot_stored_cooler
        )

        self.steady_state_mass_residual = (
            self.mass_flow_in
            - self.mass_flow_out
        )

        return self.steady_state_mass_residual