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
):

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
            -V_cell * K_gs
        )

        A[row, solid_i] += (
            Cs
            + V_cell * K_gs
            + V_cell * K_ws
        )

        if i > 0:
            solid_up = N + i - 1

            A[row, solid_up] += -Cs

        A[row, wall_i] += (
            -V_cell * K_ws
        )

        q_rad_gs = (
            q_gs[i]
            - K_gs * (
                Tg_iter[i]
                - Ts_iter[i]
            )
        )

        q_rad_ws = (
            q_ws[i]
            - K_ws * (
                Ts_iter[i]
                - Tw_iter[i]
            )
        )

        if i == 0:

            b[row] = (
                V_cell * (
                    q_rad_gs
                    - q_rad_ws
                )
                + Cs * Ts_in
            )

        else:

            b[row] = V_cell * (
                q_rad_gs
                - q_rad_ws
            )

        row += 1

    return row


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Cooler.solid_enthalpy_out()
# (pyroprocess/cooler.py). Logic is unchanged. Note this
# takes the temperature array `Ts` and recomputes the
# enthalpy from `Ts[-1]`, unlike
# pyroprocess/transition/solid_phase.py's same-named
# function, which indexes a pre-computed enthalpy array --
# that signature difference is intentional and preserved.
# ======================================================
def solid_enthalpy_out(cooler, Ts, state):

    H_solid_out = (
        state.m_dot_s
        * cooler.Cp_s
        * (Ts[-1] - cooler.T_ref)
    )

    return H_solid_out
