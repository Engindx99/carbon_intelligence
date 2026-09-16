from physics.physics import h_gas
from physics.physics import T_gas_from_h


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

    m_dot_g = state.m_dot_g_calciner

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

    return T_gas_from_h(
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

    return (
        H
        / (
            state.m_dot_s_calciner
            * calciner.Cp_s
            + calciner.eps
        )
        + calciner.T_ref
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
