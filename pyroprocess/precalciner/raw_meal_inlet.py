from physics.physics import h_gas
from physics.physics import T_gas_from_h
from physics.physics import T_solid_from_h
from physics.physics import FUEL_COMPOSITION
from physics.gas_thermo import GasMixture
from physics.gas_thermo import add
from physics.gas_thermo import air
from physics.gas_thermo import burn_in


# ======================================================
# THE GAS ENTERING THE CALCINER
#
# ONE definition, because there are now two consumers: the
# enthalpy inversion below, and the riser velocity in
# Calciner.apply(). Keeping a second copy of this sum is exactly
# how the inlet divisor went stale in the first place -- see the
# note on gas_temperature_from_enthalpy -- and a second copy of a
# flow is a second thing to forget to update.
#
# The fuel mass belongs here because the scalar chain puts it in
# the zone outlet. Its ENTHALPY does not: fuel enters the gas row
# as q_fuel_cells along the zone.
# ======================================================
def inlet_gas_flow(state):

    return (
        state.m_dot_g_transition
        + state.m_dot_tertiary_air
        + getattr(state, "m_dot_fuel_calciner", 0.0)
    )


# ======================================================
# ITS COMPOSITION
#
# Kiln gas as the transition discharged it, plus tertiary air,
# with the calciner fuel burned in that mixture's O2
# (physics.gas_thermo). Taken as fully burned from the inlet face
# on, as the kiln's: the fuel's mass is already in inlet_gas_flow,
# its heat stays axial (q_fuel_cells). Shared by the inversion
# below and the zone's inlet flux (thermal_solver), so the round
# trip H -> Tg_in -> H stays exact.
# ======================================================
def calciner_inlet_species(state):

    kiln_gas = getattr(state, "Transition_gas_species_out", None)

    if kiln_gas is None:
        from pyroprocess.transition.gas_phase import inlet_species
        kiln_gas = inlet_species(state)

    return burn_in(
        add(kiln_gas, air(float(state.m_dot_tertiary_air))),
        float(getattr(state, "m_dot_fuel_calciner", 0.0)),
        FUEL_COMPOSITION,
    )


# ======================================================
# TEMPERATURE FROM ENTHALPY
#
# Moved from Calciner.gas_temperature_from_enthalpy() and
# Calciner.solid_temperature_from_enthalpy()
# (pyroprocess/precalciner.py). Logic is unchanged; `self`
# was renamed to `calciner` since these are now free
# functions taking the owning Calciner instance explicitly.
# ======================================================
def gas_temperature_from_enthalpy(calciner, H, state):

    # The INLET flow, not state.m_dot_g_calciner -- that scalar
    # already carries every kg of CO2 and water this zone will
    # release, so dividing the incoming enthalpy by it invented
    # a colder inlet than the transition and the tertiary air
    # actually delivered. H is built from Hgas_transition_out
    # plus the tertiary air, so the inversion has to use the
    # flow those two carry or the handoff conserves J/s while
    # rescaling K.
    #
    # ASSEMBLED FROM THE LIVE SCALAR CHAIN, not read back from
    # state.m_dot_g_calciner_in. That attribute is published by
    # thermal_step as (zone outlet - everything the bed adds),
    # so it is a full sweep STALE by the time this runs: the
    # outlet flow it was built from has since been recomputed
    # by _update_steady_state_mass_flow. The two agree at the
    # fixed point -- test_diagnostics asserts exactly this
    # identity -- but NOT on the path to it, and a divisor is
    # the one place a lag cannot be tolerated.
    #
    # MEASURED, literature calcination kinetics, sweep 2: the
    # calciner outlet flow moves 16.42 -> 46.77 kg/s as
    # calcination lights off, while the lagged divisor stays at
    # 16.42 - 9.47 = 6.95 kg/s. Dividing an enthalpy carried by
    # 35.80 kg/s of gas by 6.95 gave 5.887536e+06 J/kg -- a gas
    # above 4000 K at the calciner inlet, five times its true
    # specific enthalpy. Assembled live it is 1.142591e+06 J/kg
    # and 1274 K, which is the riser gas mixed with tertiary
    # air and is what an ILC calciner inlet actually looks like.
    #
    # The fuel mass belongs here because the scalar chain puts
    # it in the zone outlet, so the subtraction this replaces
    # carried it too. Its ENTHALPY is not in H -- fuel enters
    # the gas row as q_fuel_cells along the zone -- which makes
    # the inlet ~4% cold in specific terms. That asymmetry is
    # real and predates this; it is not corrected here because
    # it is a different question from the lag.
    m_dot_g = inlet_gas_flow(state)

    # H = m_dot_g * h_gas(T, T_ref)
    #
    # Therefore solve:
    #
    # h_gas(T, T_ref) = H / m_dot_g
    #
    # using numerical inversion.

    h_target = (
        H
        / (
            m_dot_g
            + calciner.eps
        )
    )

    return GasMixture(calciner_inlet_species(state)).T_from_h(
        h_target,
        calciner.T_ref,
        200.0,
        4000.0,
    )


def solid_temperature_from_enthalpy(
    calciner,
    H,
    state,
):

    return T_solid_from_h(
        H / float(state.m_dot_s_calciner),
        calciner.T_ref,
    )


# ======================================================
# INLET CONDITIONS
#
# Moved from the beginning of Calciner.apply()
# (pyroprocess/precalciner.py). Pulls the incoming
# enthalpy handoffs from the upstream zones (gas from
# Transition, solid from Preheater) and converts them to
# the physical inlet temperatures used by thermal_step().
# ======================================================
def resolve_inlet_conditions(calciner, state):

    state.Hgas_calciner_in = (
        state.Hgas_transition_out
        + getattr(state, "Hgas_cooler_tertiary", 0.0)
    )

    state.Hsolid_calciner_in = (
        state.Hsolid_preheater_out
    )

    Tg_in = gas_temperature_from_enthalpy(
        calciner,
        state.Hgas_calciner_in,
        state,
    )

    Ts_in = solid_temperature_from_enthalpy(
        calciner,
        state.Hsolid_calciner_in,
        state,
    )

    return Tg_in, Ts_in
