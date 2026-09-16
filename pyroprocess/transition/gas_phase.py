from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import T_gas_from_h


# ======================================================
# GAS INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Transition.gas_inlet_temperature_from_enthalpy()
# (pyroprocess/transition.py). Logic is unchanged; `self`
# was renamed to `transition` since this is now a free
# function taking the owning Transition instance explicitly.
# ======================================================
def gas_inlet_temperature_from_enthalpy(transition, H, state):

    m_dot_g = state.m_dot_g_transition

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


# ======================================================
# GAS PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Transition.thermal_step()
# (pyroprocess/transition.py). Builds the gas-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged.
#
# Gas direction: N-1 -> 0.
#
# `advection_correction` is the per-cell van Leer deferred
# correction from physics.second_order_upwind_correction,
# in enthalpy units (J/kg). It defaults to zero, which
# leaves this row exactly first-order upwind, and it enters
# b only so that A stays the diagonally dominant upwind
# M-matrix. Same construction as
# pyroprocess/burning/gas_phase.py.
# ======================================================
def apply_gas_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Tg_iter,
    T_ref,
    m_dot_g,
    V_cell,
    K_gs,
    K_gw,
    radiation_gas_sink,
    Tg_in,
    advection_correction=0.0,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    Cp_g_i = cp_gas(
        Tg_iter[i]
    )

    Cg_i = (
        m_dot_g
        * Cp_g_i
    )

    h_i_iter = h_gas(
        Tg_iter[i],
        T_ref
    )

    h_linear_const_i = (
        h_i_iter
        - Cp_g_i * Tg_iter[i]
    )

    A[row, Tg_i] += (
        Cg_i
        + V_cell * K_gs
        + V_cell * K_gw
    )

    A[row, Ts_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_gw
    )

    if i == N - 1:

        h_in = h_gas(
            Tg_in,
            T_ref
        )

        b[row] = (
            -radiation_gas_sink
            + m_dot_g * h_in
            - m_dot_g * h_linear_const_i
            - m_dot_g * advection_correction
        )

    else:

        Tg_up_i = i + 1

        Cp_g_up = cp_gas(
            Tg_iter[i + 1]
        )

        h_up_iter = h_gas(
            Tg_iter[i + 1],
            T_ref
        )

        h_linear_const_up = (
            h_up_iter
            - Cp_g_up * Tg_iter[i + 1]
        )

        A[row, Tg_up_i] += (
            -m_dot_g * Cp_g_up
        )

        b[row] = (
            -radiation_gas_sink
            - m_dot_g * h_linear_const_i
            + m_dot_g * h_linear_const_up
            - m_dot_g * advection_correction
        )

    return row + 1
