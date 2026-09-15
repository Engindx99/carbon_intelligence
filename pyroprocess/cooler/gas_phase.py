from physics.physics import cp_gas
from physics.physics import h_gas


# ======================================================
# GAS PHASE ENERGY BALANCE ROWS
#
# Moved from the gas block inside Cooler.thermal_step()
# (pyroprocess/cooler.py). Logic is unchanged; `self` was
# renamed to `cooler` since this is now a free function
# taking the owning Cooler instance explicitly.
#
# Cooler keeps its own co-current geometry: a Dirichlet
# inlet row (Tg[0] = Tg_in) followed by a per-cell loop
# (gas flows 0 -> N-1, same direction as the solid), unlike
# the counter-current sweep of
# pyroprocess/transition/gas_phase.py and
# pyroprocess/burning/gas_phase.py.
#
# The convective term, however, is now written in ENTHALPY
# like those two siblings. It used to be a bare
# right-endpoint m_dot_g*cp_gas(Tg_i)*(Tg_i - Tg_up), whose
# fixed point does not satisfy the finite-control-volume
# first law m_dot_g*(h_out - h_in) = Q that
# heat_transfer.py's energy balance assumes. That gap was
# the dominant part of the Cooler energy residual; the
# residual decomposition diagnostic in heat_transfer.py now
# reports what is left of it as `gas_gap`.
# ======================================================
def apply_gas_energy_balance(
    A,
    b,
    row,
    N,
    Tg_in,
    Tg_iter,
    Ts_iter,
    Tw_iter,
    T_ref,
    m_dot_g,
    V_cell,
    K_gs,
    K_gw,
    q_gs,
    q_gw,
):

    for i in range(N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        # ----------------------------------------------
        # m_dot_g (h_g,i - h_g,up)
        #
        # + Q_gs
        # + Q_gw
        # = 0
        #
        # h_gas is cubic in T, so it cannot enter the
        # linear system directly. Each node instead carries
        # a first-order Taylor expansion of h_gas about the
        # frozen Picard iterate,
        #
        #   h_lin(T) = Cp_g * T + h_linear_const
        #
        # which is EXACT at the fixed point, where
        # T == Tg_iter and h_lin collapses back onto
        # h_gas. The linearization slope therefore sets the
        # convergence rate, not the converged answer.
        # Summed over the cells this telescopes exactly to
        # m_dot_g * (h_gas(Tg[-1]) - h_gas(Tg_in)), which is
        # what heat_transfer.py uses for Hg_out - Hg_in.
        #
        # Same construction as burning/gas_phase.py and
        # transition/gas_phase.py, with the upstream node
        # taken as i - 1 for Cooler's co-current flow.
        #
        # Cell 0 is a full control volume like every other
        # cell, not a boundary node: its upstream enthalpy
        # is the known inlet stream h_gas(Tg_in), injected
        # as a flux in b[row]. Tg[0] is therefore the cell
        # average, which is warmer than Tg_in.
        # ----------------------------------------------

        Cp_g_i = float(
            cp_gas(Tg_iter[i])
        )

        Cg_i = m_dot_g * Cp_g_i

        h_linear_const_i = (
            float(
                h_gas(
                    Tg_iter[i],
                    T_ref,
                )
            )
            - Cp_g_i * Tg_iter[i]
        )

        A[row, gas_i] += (
            Cg_i
            + V_cell * K_gs
            + V_cell * K_gw
        )

        A[row, solid_i] += (
            -V_cell * K_gs
        )

        A[row, wall_i] += (
            -V_cell * K_gw
        )

        # Radiation part is already contained in
        # heat_transfer(). Freeze nonlinear radiation
        # contribution at current Picard iteration.

        q_rad_gs = (
            q_gs[i]
            - K_gs * (
                Tg_iter[i]
                - Ts_iter[i]
            )
        )

        q_rad_gw = (
            q_gw[i]
            - K_gw * (
                Tg_iter[i]
                - Tw_iter[i]
            )
        )

        if i == 0:

            # Inlet face: the upstream enthalpy is the known
            # inlet stream, so it is a constant flux rather
            # than a coupling to a neighbouring cell.

            h_in = float(
                h_gas(
                    Tg_in,
                    T_ref,
                )
            )

            b[row] = (
                -V_cell * (
                    q_rad_gs
                    + q_rad_gw
                )
                - m_dot_g * h_linear_const_i
                + m_dot_g * h_in
            )

        else:

            gas_up = i - 1

            Cp_g_up = float(
                cp_gas(Tg_iter[gas_up])
            )

            Cg_up = m_dot_g * Cp_g_up

            h_linear_const_up = (
                float(
                    h_gas(
                        Tg_iter[gas_up],
                        T_ref,
                    )
                )
                - Cp_g_up * Tg_iter[gas_up]
            )

            A[row, gas_up] += -Cg_up

            b[row] = (
                -V_cell * (
                    q_rad_gs
                    + q_rad_gw
                )
                - m_dot_g * h_linear_const_i
                + m_dot_g * h_linear_const_up
            )

        row += 1

    return row


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Cooler.gas_enthalpy_out()
# (pyroprocess/cooler.py). Logic is unchanged. Note this
# takes the temperature array `Tg` and recomputes the
# enthalpy from `Tg[-1]`, unlike
# pyroprocess/transition/gas_phase.py's same-named
# function, which indexes a pre-computed enthalpy array --
# that signature difference is intentional and preserved.
# ======================================================
def gas_enthalpy_out(cooler, Tg, state):

    H_gas_out = (
        state.m_dot_g
        * float(
            h_gas(
                Tg[-1],
                cooler.T_ref,
            )
        )
    )

    return H_gas_out
