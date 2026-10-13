import numpy as np

from physics.physics import cp_solid
from physics.physics import h_solid
from physics.physics import outlet_face_value
from physics.physics import second_order_upwind_face_corrections


# ======================================================
# SOLID PHASE ENERGY BALANCE ROWS
#
# The clinker bed, cell by cell (solid flows 0 -> N-1), in
# ENTHALPY like every other solid row in the plant
# (physics/variable_flow_rows.py):
#
#   ms_out (h_i + D_out) - ms_in (h_{i-1} + D_in)
#     - Q_gs + Q_ws + M/dt (h_i - h_old) + H_mass_stored = 0
#
# with h = physics.h_solid linearised at the iterate and the
# face corrections D reconstructed on h. Cell 0 is a full
# control volume: its upstream term is the known kiln
# discharge, hs_in [J/kg], on the inlet flow.
#
# ms_out / ms_in are per-cell arrays (or scalars). In the steady
# solve both are the clinker flow; a dynamic step passes the
# parcel train's face flows, whose difference is the hold-up's
# dM/dt, with the stored enthalpy d(M h)/dt = M/dt (h - h_old)
# + H_mass_stored. Left at None the storage terms are zero.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    N,
    hs_in,
    Tg_iter,
    Ts_iter,
    Tw_iter,
    ms_out,
    ms_in,
    V_cell,
    K_gs,
    K_ws,
    q_gs,
    q_ws,
    T_ref,
    M_dt=None,
    hs_old=None,
    H_mass_stored=None,
):

    V_cell = np.broadcast_to(np.asarray(V_cell, dtype=float), (N,))
    K_gs = np.broadcast_to(np.asarray(K_gs, dtype=float), (N,))
    K_ws = np.broadcast_to(np.asarray(K_ws, dtype=float), (N,))
    ms_out = np.broadcast_to(np.asarray(ms_out, dtype=float), (N,))
    ms_in = np.broadcast_to(np.asarray(ms_in, dtype=float), (N,))

    zeros = np.zeros(N)
    M_dt = zeros if M_dt is None else np.broadcast_to(
        np.asarray(M_dt, dtype=float), (N,)
    )
    hs_old = zeros if hs_old is None else np.broadcast_to(
        np.asarray(hs_old, dtype=float), (N,)
    )
    H_mass_stored = zeros if H_mass_stored is None else np.broadcast_to(
        np.asarray(H_mass_stored, dtype=float), (N,)
    )

    Ts_iter = np.asarray(Ts_iter, dtype=float)

    h_iter = h_solid(Ts_iter, T_ref)
    cp_iter = cp_solid(Ts_iter)
    hc_iter = h_iter - cp_iter * Ts_iter

    # Per FACE (N + 1), in flow order: the inlet face carries no
    # correction, it is the known kiln-discharge handoff.
    D_face = second_order_upwind_face_corrections(
        h_iter,
        hs_in,
        reverse=False,
    )

    for i in range(N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        A[row, gas_i] += -V_cell[i] * K_gs[i]

        A[row, solid_i] += (
            ms_out[i] * cp_iter[i]
            + V_cell[i] * K_gs[i]
            + V_cell[i] * K_ws[i]
            + M_dt[i] * cp_iter[i]
        )

        A[row, wall_i] += -V_cell[i] * K_ws[i]

        q_rad_gs = q_gs[i] - K_gs[i] * (Tg_iter[i] - Ts_iter[i])
        q_rad_ws = q_ws[i] - K_ws[i] * (Ts_iter[i] - Tw_iter[i])

        b_common = (
            V_cell[i] * (q_rad_gs - q_rad_ws)
            - ms_out[i] * (hc_iter[i] + D_face[i + 1])
            + ms_in[i] * D_face[i]
            - M_dt[i] * (hc_iter[i] - hs_old[i])
            - H_mass_stored[i]
        )

        if i == 0:
            b[row] = b_common + ms_in[i] * hs_in
        else:
            A[row, N + i - 1] += -ms_in[i] * cp_iter[i - 1]
            b[row] = b_common + ms_in[i] * hc_iter[i - 1]

        row += 1

    return row


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Cooler.solid_enthalpy_out()
# (pyroprocess/cooler.py). Note this takes the temperature
# array `Ts` and recomputes the enthalpy from it, unlike
# pyroprocess/transition/solid_phase.py's same-named
# function, which indexes a pre-computed enthalpy array --
# that signature difference is intentional and preserved.
#
# This used to read Ts[-1], the last CELL CENTRE, while the
# clinker actually discharges through the outlet FACE half a
# cell further on -- a systematic O(dz) bias in the cooled
# clinker enthalpy. It is also the flux the second-order
# scheme in apply_solid_energy_balance() transports out of
# the last cell, so it must be the value handed off or the
# difference leaks out of the energy balance.
# ======================================================
def solid_enthalpy_out(cooler, Ts, state):

    # The flux through the grate's outlet face, which a dynamic
    # step sets apart from the kiln's discharge (heat_transfer).
    H_solid_out = (
        getattr(state, "Cooler_m_dot_s_out", state.m_dot_s)
        * outlet_face_value(
            h_solid(Ts, cooler.T_ref),
            reverse=False,
        )
    )

    return H_solid_out
