import numpy as np

from physics.physics import outlet_face_value
from physics.physics import second_order_upwind_correction
from physics.physics import second_order_upwind_face_corrections


# ======================================================
# SOLID PHASE ENERGY BALANCE ROWS
#
# Moved from the solid block inside Cooler.thermal_step()
# (pyroprocess/cooler.py). Logic is unchanged; `self` was
# renamed to `cooler` since this is now a free function
# taking the owning Cooler instance explicitly.
#
# Cooler's own formulation is preserved exactly: a
# Dirichlet inlet row (Ts[0] = Ts_in) followed by a
# per-cell loop (solid flows 0 -> N-1). This mirrors the
# split boundary used by pyroprocess/transition/solid_phase.py
# and pyroprocess/burning/solid_phase.py, but the arithmetic
# itself stays Cooler's own.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    N,
    Ts_in,
    Tg_iter,
    Ts_iter,
    Tw_iter,
    Cs,
    V_cell,
    K_gs,
    K_ws,
    q_gs,
    q_ws,
    Cs_in=None,
    T_ref=0.0,
    C_dt=None,
    Ts_old=None,
    H_mass_stored=None,
):
    # Cs_in .. H_mass_stored -- DYNAMIC STEP ONLY (the clinker bed's
    # parcel train, chemistry/parcels.py). With them the bed carries
    # a different flow into and out of each cell, Cs_in[i] and
    # Cs[i], because its hold-up changes over the step; the row is
    # then written per FACE, so the second-order corrections and the
    # T_ref terms telescope, and it gains the stored enthalpy
    # d(M h)/dt = C/dt (Ts - Ts_old) + H_mass_stored (as
    # physics.variable_flow_rows). Left at None, the steady row
    # below is unchanged.
    if Cs_in is not None:
        return _apply_solid_energy_balance_dynamic(
            A, b, row, N, Ts_in, Tg_iter, Ts_iter, Tw_iter,
            Cs, V_cell, K_gs, K_ws, q_gs, q_ws,
            Cs_in, T_ref, C_dt, Ts_old, H_mass_stored,
        )

    # Per-cell bed volumes and coefficients (Cooler.bed_geometry);
    # a scalar is taken as the same value in every cell.
    V_cell = np.broadcast_to(np.asarray(V_cell, dtype=float), (N,))
    K_gs = np.broadcast_to(np.asarray(K_gs, dtype=float), (N,))
    K_ws = np.broadcast_to(np.asarray(K_ws, dtype=float), (N,))

    # ----------------------------------------------
    # SECOND-ORDER ADVECTION CORRECTION
    #
    # van Leer limited reconstruction of the clinker-side
    # face values, applied by deferred correction so that A
    # stays the first-order upwind M-matrix. The solid flux
    # Cs * (Ts - T_ref) is affine in Ts, so the
    # reconstruction is done on TEMPERATURE directly. The
    # inlet face carries no correction: Ts_in is the known
    # kiln-discharge handoff, not a reconstruction. See
    # physics.second_order_upwind_correction.
    # ----------------------------------------------

    advection_correction = second_order_upwind_correction(
        Ts_iter,
        Ts_in,
        reverse=False,
    )

    for i in range(N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        # ----------------------------------------------
        # m_dot_s Cp_s (Ts_i - Ts_up)
        #
        # - Q_gs
        # + Q_ws
        # = 0
        #
        # Cell 0 is a full control volume like every other
        # cell, not a boundary node: its upstream term is
        # the known inlet stream, injected as the constant
        # flux Cs * Ts_in in b[row]. Same form as
        # burning/solid_phase.py and
        # transition/solid_phase.py. T_ref cancels because
        # the interior rows are a pure Cs*(Ts_i - Ts_up)
        # difference, so no reference offset is needed here.
        #
        # Ts[0] is therefore the cell average, which is
        # cooler than Ts_in.
        # ----------------------------------------------

        A[row, gas_i] += (
            -V_cell[i] * K_gs[i]
        )

        A[row, solid_i] += (
            Cs
            + V_cell[i] * K_gs[i]
            + V_cell[i] * K_ws[i]
        )

        if i > 0:
            solid_up = N + i - 1

            A[row, solid_up] += -Cs

        A[row, wall_i] += (
            -V_cell[i] * K_ws[i]
        )

        q_rad_gs = (
            q_gs[i]
            - K_gs[i] * (
                Tg_iter[i]
                - Ts_iter[i]
            )
        )

        q_rad_ws = (
            q_ws[i]
            - K_ws[i] * (
                Ts_iter[i]
                - Tw_iter[i]
            )
        )

        if i == 0:

            b[row] = (
                V_cell[i] * (
                    q_rad_gs
                    - q_rad_ws
                )
                + Cs * Ts_in
                - Cs * advection_correction[i]
            )

        else:

            b[row] = (
                V_cell[i] * (
                    q_rad_gs
                    - q_rad_ws
                )
                - Cs * advection_correction[i]
            )

        row += 1

    return row


def _apply_solid_energy_balance_dynamic(
    A, b, row, N, Ts_in, Tg_iter, Ts_iter, Tw_iter,
    Cs_out, V_cell, K_gs, K_ws, q_gs, q_ws,
    Cs_in, T_ref, C_dt, Ts_old, H_mass_stored,
):
    """The dynamic-step solid row: per-face flows and stored
    enthalpy. See apply_solid_energy_balance."""

    V_cell = np.broadcast_to(np.asarray(V_cell, dtype=float), (N,))
    K_gs = np.broadcast_to(np.asarray(K_gs, dtype=float), (N,))
    K_ws = np.broadcast_to(np.asarray(K_ws, dtype=float), (N,))
    Cs_out = np.broadcast_to(np.asarray(Cs_out, dtype=float), (N,))
    Cs_in = np.broadcast_to(np.asarray(Cs_in, dtype=float), (N,))
    C_dt = np.broadcast_to(np.asarray(C_dt, dtype=float), (N,))
    Ts_old = np.broadcast_to(np.asarray(Ts_old, dtype=float), (N,))
    H_mass_stored = np.broadcast_to(
        np.asarray(H_mass_stored, dtype=float), (N,)
    )

    # Per FACE (N + 1), in flow order: each face carries its own
    # flow, so the corrections cannot be pre-differenced.
    D_face = second_order_upwind_face_corrections(
        Ts_iter,
        Ts_in,
        reverse=False,
    )

    for i in range(N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        # Cs_out (Ts_i - T_ref) - Cs_in (Ts_up - T_ref)
        #   - Q_gs + Q_ws + C/dt (Ts_i - Ts_old) + H_mass = 0
        A[row, gas_i] += -V_cell[i] * K_gs[i]

        A[row, solid_i] += (
            Cs_out[i]
            + V_cell[i] * K_gs[i]
            + V_cell[i] * K_ws[i]
            + C_dt[i]
        )

        if i > 0:
            A[row, N + i - 1] += -Cs_in[i]

        A[row, wall_i] += -V_cell[i] * K_ws[i]

        q_rad_gs = q_gs[i] - K_gs[i] * (Tg_iter[i] - Ts_iter[i])
        q_rad_ws = q_ws[i] - K_ws[i] * (Ts_iter[i] - Tw_iter[i])

        b[row] = (
            V_cell[i] * (q_rad_gs - q_rad_ws)
            - Cs_out[i] * D_face[i + 1]
            + Cs_in[i] * D_face[i]
            + (Cs_out[i] - Cs_in[i]) * T_ref
            + C_dt[i] * Ts_old[i]
            - H_mass_stored[i]
            + (Cs_in[i] * Ts_in if i == 0 else 0.0)
        )

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
        * cooler.Cp_s
        * (
            outlet_face_value(
                Ts,
                reverse=False,
            )
            - cooler.T_ref
        )
    )

    return H_solid_out
