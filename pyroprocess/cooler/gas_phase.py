from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import second_order_upwind_correction


# ======================================================
# GAS PHASE ENERGY BALANCE ROWS
#
# Moved from the gas block inside Cooler.thermal_step()
# (pyroprocess/cooler.py). Logic is unchanged; `self` was
# renamed to `cooler` since this is now a free function
# taking the owning Cooler instance explicitly.
#
# Cooler gas is now counter-current to the solid (secondary/
# tertiary air recuperation): a Dirichlet inlet row
# (Tg[N-1] = Tg_in) at the clinker-discharge end, followed by
# a per-cell loop sweeping N-1 -> 0 toward the hot
# clinker-inlet end, where the gas exits hottest. This matches
# the gas direction already used by
# pyroprocess/transition/gas_phase.py and
# pyroprocess/burning/gas_phase.py (gas N-1 -> 0); the solid
# still flows 0 -> N-1 (pyroprocess/cooler/solid_phase.py,
# unchanged), so the two phases are counter-current. Cooler's
# own row-assembly architecture (a self-contained per-cell
# loop here, rather than Burning/Transition's externally
# driven per-cell call) is otherwise preserved as-is; only the
# sweep direction and inlet cell changed.
#
# The convective term is written in ENTHALPY like those two
# siblings. It used to be a bare right-endpoint
# m_dot_g*cp_gas(Tg_i)*(Tg_i - Tg_up), whose fixed point does
# not satisfy the finite-control-volume first law
# m_dot_g*(h_out - h_in) = Q that heat_transfer.py's energy
# balance assumes. That gap was the dominant part of the
# Cooler energy residual; the residual decomposition
# diagnostic in heat_transfer.py now reports what is left of
# it as `gas_gap`.
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

    # ----------------------------------------------
    # SECOND-ORDER ADVECTION CORRECTION
    #
    # The face enthalpies below are upstream cell centres,
    # i.e. first-order upwind, whose O(dz) truncation error
    # acts as a numerical diffusion across the steep axial
    # gradient the recuperator is made of. These per-cell
    # terms upgrade the faces to a van Leer limited linear
    # reconstruction by deferred correction: they enter
    # b[row] only, so A stays the diagonally dominant upwind
    # M-matrix, and the converged fixed point satisfies the
    # second-order equation. See
    # physics.second_order_upwind_correction.
    #
    # The gas is reconstructed in ENTHALPY, since the gas
    # flux is m_dot_g * h and h is cubic in T. The inlet face
    # carries no correction: its value is the known incoming
    # cooling-air stream, not a reconstruction.
    # ----------------------------------------------

    h_iter = h_gas(
        Tg_iter,
        T_ref,
    )

    advection_correction = second_order_upwind_correction(
        h_iter,
        float(
            h_gas(
                Tg_in,
                T_ref,
            )
        ),
        reverse=True,
    )

    for i in range(N - 1, -1, -1):

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
        # taken as i + 1 for Cooler's counter-current flow
        # (gas sweeps N-1 -> 0).
        #
        # Cell N-1 is a full control volume like every other
        # cell, not a boundary node: its upstream enthalpy
        # is the known inlet stream h_gas(Tg_in), injected
        # as a flux in b[row]. Tg[N-1] is therefore the cell
        # average, which is warmer than Tg_in; Tg[0] is the
        # hottest cell and is what leaves the cooler as
        # secondary/tertiary/vent air.
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

        if i == N - 1:

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
                - m_dot_g * advection_correction[i]
            )

        else:

            gas_up = i + 1

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
                - m_dot_g * advection_correction[i]
            )

        row += 1

    return row


# ======================================================
# HOT-END FACE ENTHALPY
#
# Specific enthalpy of the gas where it actually leaves the
# cooler: the OUTLET FACE at the clinker-inlet end, not the
# centre of cell 0. The face sits half a cell further
# downstream, so reading the centre understated the
# recuperated air enthalpy by O(dz) no matter how fine the
# mesh was -- and that value is the secondary air the kiln
# burns with, so the bias propagated straight into
# Hgas_burning_in.
#
# This is also the flux the second-order scheme in
# apply_gas_energy_balance() transports out of cell 0, so
# using anything else here would leak exactly that
# difference out of the cooler energy balance.
#
# Shared by gas_enthalpy_out() and gas_enthalpy_split()
# below so the two cannot drift apart: the file's own
# invariant is that the three split streams sum to the
# outlet, which holds only if both read the same h_hot.
# ======================================================
def hot_end_face_enthalpy(cooler, Tg):

    return outlet_face_value(
        h_gas(
            Tg,
            cooler.T_ref,
        ),
        reverse=True,
    )


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Cooler.gas_enthalpy_out()
# (pyroprocess/cooler.py). Logic is unchanged apart from two
# things: the counter-current direction flip (the gas now
# exits hottest at Tg[0], the clinker-inlet end, not Tg[-1])
# and the mass-flow source, which is now the cooler's own
# independent air flow (state.m_dot_air_cooler) rather than
# the kiln's combustion gas flow (state.m_dot_g) -- the two
# are no longer the same quantity. This takes the temperature
# array `Tg` and recomputes the enthalpy from it directly,
# unlike pyroprocess/transition/gas_phase.py's same-named
# function, which indexes a pre-computed enthalpy array --
# that signature difference is intentional and preserved.
# ======================================================
def gas_enthalpy_out(cooler, Tg, state):

    H_gas_out = (
        state.m_dot_air_cooler
        * hot_end_face_enthalpy(
            cooler,
            Tg,
        )
    )

    return H_gas_out


# ======================================================
# GAS ENTHALPY SPLIT (secondary / tertiary / vent)
#
# The cooler is a single lumped 1-D gas stream with one
# outlet temperature (Tg[0], the hot end), so secondary,
# tertiary and vent air are modeled as three mass shares of
# that same hot-end gas state: same T, split only by mass.
# The mass split itself (m_dot_secondary_air/m_dot_tertiary_air
# /m_dot_vent_air) is computed centrally in
# main.py::_update_steady_state_mass_flow, not here, so this
# function only converts those masses to enthalpy flows at the
# cooler's own outlet temperature. By construction,
# H_secondary + H_tertiary + H_vent == gas_enthalpy_out(...)
# above, since the three masses sum to m_dot_air_cooler and
# all three use the same h_hot.
# ======================================================
def gas_enthalpy_split(cooler, Tg, state):

    h_hot = hot_end_face_enthalpy(
        cooler,
        Tg,
    )

    H_secondary = state.m_dot_secondary_air * h_hot
    H_tertiary = state.m_dot_tertiary_air * h_hot
    H_vent = state.m_dot_vent_air * h_hot

    return H_secondary, H_tertiary, H_vent
