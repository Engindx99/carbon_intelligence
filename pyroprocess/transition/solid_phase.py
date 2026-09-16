from physics.physics import outlet_face_value


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


# ======================================================
# SOLID PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Transition.thermal_step()
# (pyroprocess/transition.py). Builds the solid-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged. Takes the calcination
# heat sink for this cell as an explicit parameter instead of
# computing it inline.
#
# Solid direction: 0 -> N-1.
#
# `advection_correction` is the per-cell van Leer deferred
# correction from physics.second_order_upwind_correction,
# in temperature units (K); the solid flux Cs * (Ts - T_ref)
# is affine in Ts. It defaults to zero (exactly first-order
# upwind) and enters b only. Same construction as
# pyroprocess/burning/solid_phase.py.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Cs,
    V_cell,
    K_gs,
    K_ws,
    radiation_solid_source,
    Q_calcination_cell,
    Ts_in,
    advection_correction=0.0,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    A[row, Ts_i] += (
        Cs
        + V_cell * K_gs
        + V_cell * K_ws
    )

    A[row, Tg_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_ws
    )

    if i == 0:
        b[row] = (
            Cs * Ts_in
            + radiation_solid_source
            - Q_calcination_cell
            - Cs * advection_correction
        )
    else:
        Ts_up_i = N + i - 1
        A[row, Ts_up_i] += -Cs
        b[row] = (
            radiation_solid_source
            - Q_calcination_cell
            - Cs * advection_correction
        )

    return row + 1
