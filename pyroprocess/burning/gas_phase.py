from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import T_gas_from_h


# ======================================================
# GAS INLET HANDOFF
#
# Moved from Burning.apply() (pyroprocess/burning.py);
# `self` was renamed to `burning` since these are now free
# functions taking the owning Burning instance explicitly.
#
# The kiln's inlet gas is now a mix of two streams: primary
# air (ambient T, carries the fuel, sized by
# burning.primary_air_fraction) and secondary air (preheated
# by the cooler, pyroprocess/cooler/gas_phase.py's hot-end
# split). Both masses sum to state.m_dot_air by construction
# (main.py::_update_steady_state_mass_flow), so mixing is a
# plain enthalpy sum -- no new mixing formula is needed.
# ======================================================
def resolve_gas_inlet(burning, state):

    H_secondary = getattr(
        state,
        "Hgas_cooler_secondary",
        0.0,
    )

    H_primary = (
        state.m_dot_primary_air
        * float(
            h_gas(
                burning.T_amb,
                burning.T_ref,
            )
        )
    )

    state.Hgas_burning_in = H_primary + H_secondary

    state.Tg_burning_in = gas_inlet_temperature_from_enthalpy(
        burning,
        state.Hgas_burning_in,
        state,
    )

    return state.Tg_burning_in


def gas_inlet_temperature_from_enthalpy(burning, H, state):

    m_dot_g = state.m_dot_g

    if m_dot_g <= burning.eps:
        return burning.T_ref

    h_target = H / m_dot_g

    return T_gas_from_h(
        h_target,
        burning.T_ref,
        burning.T_ref,
        4000.0,
    )


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Burning.gas_enthalpy_out()
# (pyroprocess/burning.py).
#
# This used to return Hg[0], the last CELL CENTRE. The gas
# leaves through the outlet FACE, which sits half a cell
# further downstream, so that was a systematic O(dz) bias
# in the handoff itself -- independent of how well the
# interior profile was resolved. It is the reconstructed
# outlet face value that the second-order flux in
# apply_gas_energy_balance() actually transports out of
# cell 0, so returning anything else would leak exactly
# that difference out of the zone energy balance.
#
# Hg is m_dot_g * h_gas(Tg) elementwise, i.e. affine in the
# reconstructed enthalpy, so the extrapolation may be taken
# on Hg directly.
# ======================================================
def gas_enthalpy_out(Hg):

    return outlet_face_value(Hg, reverse=True)


# ======================================================
# GAS PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Burning.thermal_step()
# (pyroprocess/burning.py). Builds the gas-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged.
#
# Gas direction: N-1 -> 0.
#
# `advection_correction` is the per-cell van Leer deferred
# correction from physics.second_order_upwind_correction,
# in enthalpy units (J/kg). It is zero by default, which
# leaves this row exactly first-order upwind as before. The
# matrix A is untouched by it on purpose: the correction is
# frozen at the Picard iterate and enters b only, so the
# implicit operator stays the diagonally dominant upwind
# M-matrix the Picard loop relies on, while the converged
# fixed point satisfies the second-order equation.
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
    q_cell,
    reaction_q_cell,
    radiation_gas_sink,
    Tg_in,
    advection_correction=0.0,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    Cp_g_i = cp_gas(Tg_iter[i])

    Cg_i = m_dot_g * Cp_g_i

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
            q_cell[i]
            - reaction_q_cell[i]
            - radiation_gas_sink
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
            q_cell[i]
            - reaction_q_cell[i]
            - radiation_gas_sink
            - m_dot_g * h_linear_const_i
            + m_dot_g * h_linear_const_up
            - m_dot_g * advection_correction
        )

    return row + 1
