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
# Cooler's own formulation is preserved exactly: a
# Dirichlet inlet row (Tg[0] = Tg_in) followed by a
# co-current per-cell loop (gas flows 0 -> N-1, same
# direction as the solid). This is intentionally NOT the
# counter-current, enthalpy-linearized formulation used by
# pyroprocess/transition/gas_phase.py and
# pyroprocess/burning/gas_phase.py -- porting that
# formulation onto Cooler would change the numerics, not
# just the file layout.
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
    m_dot_g,
    V_cell,
    K_gs,
    K_gw,
    q_gs,
    q_gw,
):

    # ==================================================
    # Inlet boundary:
    #
    # Tg[0] = Tg_in
    # ==================================================
    A[row, 0] = 1.0
    b[row] = Tg_in

    row += 1

    for i in range(1, N):

        Cg = m_dot_g * float(
            cp_gas(Tg_iter[i])
        )

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        gas_up = i - 1

        # ----------------------------------------------
        # m_dot_g Cp_g (Tg_i - Tg_up)
        #
        # + Q_gs
        # + Q_gw
        # = 0
        # ----------------------------------------------

        A[row, gas_i] += (
            Cg
            + V_cell * K_gs
            + V_cell * K_gw
        )

        A[row, gas_up] += -Cg

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

        b[row] = -V_cell * (
            q_rad_gs
            + q_rad_gw
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
