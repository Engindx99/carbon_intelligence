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
    mg_out,
    mg_in,
    dm_gas,
    cp_gas_s,
    h_const_s,
    V_cell,
    K_gs,
    K_gw,
    radiation_gas_sink,
    Tg_in,
    D_in=0.0,
    D_out=0.0,
):
    """
    THE STREAM GAINS MASS. The CO2 the bed releases in this cell
    joins the gas here, so the flow leaving the cell is not the
    flow that entered it:

      mg_out (h_i + D_out) - mg_in (h_{i+1} + D_in)
        - dm_gas * h_gas(Ts_i)                 <- CO2 arriving
        + V K_gs (Tg - Ts) + V K_gw (Tg - Tw)
      = -radiation_gas_sink

    The `dm_gas * h_gas(Ts_i)` term is the same one the solid
    row subtracts, so summing the two rows over the zone leaves
    only the stream boundaries: the CO2 crosses phases without
    creating or destroying energy, at the bed temperature it
    actually left.

    Each face carries its own flow, so D_in and D_out are taken
    per face (physics.second_order_upwind_face_corrections)
    rather than pre-differenced. The gas inlet face carries no
    correction -- it is a known handoff, not a reconstruction --
    which is D[0] == 0 by construction there.

    With mg_in == mg_out and dm_gas == 0 this reduces exactly to
    the constant-flow form it replaces.
    """

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    Cp_g_i = cp_gas(
        Tg_iter[i]
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
        mg_out * Cp_g_i
        + V_cell * K_gs
        + V_cell * K_gw
    )

    A[row, Ts_i] += (
        -V_cell * K_gs
        - dm_gas * cp_gas_s
    )

    A[row, Tw_i] += (
        -V_cell * K_gw
    )

    b_common = (
        -radiation_gas_sink
        - mg_out * h_linear_const_i
        - mg_out * D_out
        + dm_gas * h_const_s
    )

    if i == N - 1:

        h_in = h_gas(
            Tg_in,
            T_ref
        )

        b[row] = (
            b_common
            + mg_in * h_in
            + mg_in * D_in
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
            -mg_in * Cp_g_up
        )

        b[row] = (
            b_common
            + mg_in * h_linear_const_up
            + mg_in * D_in
        )

    return row + 1
