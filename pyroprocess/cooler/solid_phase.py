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

    # ==================================================
    # Inlet boundary:
    #
    # Ts[0] = Ts_in
    # ==================================================
    A[row, N] = 1.0
    b[row] = Ts_in

    row += 1

    for i in range(1, N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        solid_up = N + i - 1

        # ----------------------------------------------
        # m_dot_s Cp_s (Ts_i - Ts_up)
        #
        # - Q_gs
        # + Q_ws
        # = 0
        # ----------------------------------------------

        A[row, gas_i] += (
            -V_cell * K_gs
        )

        A[row, solid_i] += (
            Cs
            + V_cell * K_gs
            + V_cell * K_ws
        )

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
