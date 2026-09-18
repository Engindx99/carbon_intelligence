from physics.physics import outlet_face_value

# The variable-flow solid row moved to physics.variable_flow_rows when
# the calciner adopted it too (Faz 1c). Re-exported here so this
# module stays the transition zone's solid-side entry point.
from physics.variable_flow_rows import apply_solid_energy_balance  # noqa: F401


# ======================================================
# SOLID INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Transition.solid_inlet_temperature_from_enthalpy()
# (pyroprocess/transition.py). Logic is unchanged; `self`
# was renamed to `transition` since this is now a free
# function taking the owning Transition instance explicitly.
# ======================================================
def solid_inlet_temperature_from_enthalpy(transition, H, state):

    return (
        H
        / (
            state.m_dot_s_transition
            * transition.Cp_s
            + transition.eps
        )
        + transition.T_ref
    )


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Transition.solid_enthalpy_out()
# (pyroprocess/transition.py).
#
# This used to return Hs[-1], the last CELL CENTRE, while
# the solid leaves through the outlet FACE half a cell
# further on -- an O(dz) bias in the handoff to Burning. It
# is also the flux the second-order scheme in
# apply_solid_energy_balance() transports out of the last
# cell, so it must be the value handed off or the
# difference leaks. Hs is affine in Ts, so the extrapolation
# may be taken on Hs directly. Same construction as
# pyroprocess/burning/solid_phase.py.
# ======================================================
def solid_enthalpy_out(Hs):

    return outlet_face_value(Hs, reverse=False)
