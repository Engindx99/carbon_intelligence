from physics.physics import outlet_face_value
from physics.physics import T_gas_from_h

# The variable-flow gas row moved to physics.variable_flow_rows when
# the calciner adopted it too (Faz 1c). Re-exported here so this
# module stays the transition zone's gas-side entry point.
from physics.variable_flow_rows import apply_gas_energy_balance  # noqa: F401


# ======================================================
# GAS INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Transition.gas_inlet_temperature_from_enthalpy()
# (pyroprocess/transition.py). Logic is unchanged; `self`
# was renamed to `transition` since this is now a free
# function taking the owning Transition instance explicitly.
# ======================================================
def gas_inlet_temperature_from_enthalpy(transition, H, state):

    # The INLET flow, not state.m_dot_g_transition -- that
    # scalar already carries every kg of CO2 this zone will
    # release, so dividing the incoming enthalpy by it invented
    # a colder inlet than Burning actually discharged. H was
    # built by Burning on state.m_dot_g, so the inversion has
    # to use the same flow or the handoff conserves J/s while
    # rescaling K.
    m_dot_g = state.m_dot_g

    if m_dot_g <= transition.eps:
        return transition.T_ref

    h_target = H / m_dot_g

    return T_gas_from_h(
        h_target,
        transition.T_ref,
        transition.T_ref,
        4000.0,
    )


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Transition.gas_enthalpy_out()
# (pyroprocess/transition.py).
#
# This used to return Hg[0], the last CELL CENTRE. The gas
# leaves through the outlet FACE half a cell further
# downstream, so that was a systematic O(dz) bias in the
# handoff to the precalciner. It is the reconstructed
# outlet face value that the second-order flux in
# apply_gas_energy_balance() transports out of cell 0, so
# returning anything else would leak that difference out of
# the zone energy balance. Hg is m_dot_g * h_gas(Tg)
# elementwise, i.e. affine in h, so the extrapolation may be
# taken on Hg directly. Same construction as
# pyroprocess/burning/gas_phase.py.
# ======================================================
def gas_enthalpy_out(Hg):

    return outlet_face_value(Hg, reverse=True)
