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
# THE STREAM LOSES MASS. Calcination sends CO2 out of the bed
# cell by cell, so the flow entering a cell is not the flow
# leaving it, and the balance is written on the two flows
# separately:
#
#   Cs_out (Ts_i + D_out - T_ref)
#     - Cs_in (Ts_{i-1} + D_in - T_ref)
#     + dm_gas * h_gas(Ts_i)                 <- CO2 leaving
#     + V K_gs (Ts - Tg) + V K_ws (Ts - Tw)
#   = radiation_solid_source - Q_calcination_cell
#
# Two things follow from the variable flow that do not arise
# with a constant one:
#
#   - T_ref no longer cancels between the two flux terms, so
#     (Cs_out - Cs_in) * T_ref appears explicitly;
#   - the face corrections cannot be pre-differenced, because
#     each face carries its own flow. D_in and D_out come from
#     physics.second_order_upwind_face_corrections.
#
# `dm_gas` is the mass this cell hands to the gas. It leaves
# at the local bed temperature carrying its GAS-phase
# enthalpy h_gas(Ts_i), and the gas row adds exactly the same
# term with the opposite sign, so the two cancel when the zone
# balance is summed and no arbitrary transfer term is needed.
# The reaction enthalpy stays on the solid at T_ref, where
# chemistry.calcination.deltaH is defined.
#
# h_gas(Ts) is nonlinear in Ts, so it is linearised at the
# current iterate the same way the gas row linearises its own
# enthalpy: h_gas(Ts) ~ cp_gas_s * Ts + h_const_s.
#
# With Cs_in == Cs_out and dm_gas == 0 this reduces exactly to
# the constant-flow form it replaces.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Cs_out,
    Cs_in,
    T_ref,
    dm_gas,
    cp_gas_s,
    h_const_s,
    V_cell,
    K_gs,
    K_ws,
    radiation_solid_source,
    Q_calcination_cell,
    Ts_in,
    D_in=0.0,
    D_out=0.0,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    A[row, Ts_i] += (
        Cs_out
        + dm_gas * cp_gas_s
        + V_cell * K_gs
        + V_cell * K_ws
    )

    A[row, Tg_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_ws
    )

    # Constants common to both ends of the cell.
    b_common = (
        radiation_solid_source
        - Q_calcination_cell
        - dm_gas * h_const_s
        - Cs_out * D_out
        + Cs_in * D_in
        + (Cs_out - Cs_in) * T_ref
    )

    if i == 0:
        b[row] = (
            Cs_in * Ts_in
            + b_common
        )
    else:
        Ts_up_i = N + i - 1
        A[row, Ts_up_i] += -Cs_in
        b[row] = b_common

    return row + 1
