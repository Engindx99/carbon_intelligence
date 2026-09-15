import numpy as np

from physics.physics import heat_transfer
from physics.physics import wall_losses
from physics.physics import wall_thermal_resistance
from physics.physics import h_gas

from . import gas_phase
from . import solid_phase


# ======================================================
# THERMAL STEP
#
# Moved from Cooler.thermal_step() (pyroprocess/cooler.py).
# Logic is unchanged; `self` was renamed to `cooler` since
# this is now a free function taking the owning Cooler
# instance explicitly. Gas-row and solid-row construction
# (including each side's own Dirichlet inlet row) is
# delegated to gas_phase/solid_phase, but the Picard loop,
# the wall-row assembly, and the final energy balance stay
# here since heat_transfer.py owns the overall gas-solid-wall
# heat transfer network (same split boundary used by
# pyroprocess/transition/heat_transfer.py and
# pyroprocess/burning/heat_transfer.py). Cooler's own
# co-current, Dirichlet-inlet formulation (three separate
# blocked row loops: gas, then solid, then wall) is preserved
# exactly and is NOT converted to the interleaved,
# counter-current, enthalpy-linearized formulation used by
# the Transition/Burning siblings.
# ======================================================
def thermal_step(cooler, Tg, Ts, Tw, state):

    # ======================================================
    # MASS FLOW
    # ======================================================

    m_dot_g = state.m_dot_g
    m_dot_s = state.m_dot_s

    N = cooler.N
    V_cell = cooler.V_cell

    # ======================================================
    # INLET BOUNDARY CONDITIONS
    # ======================================================

    Tg_in = state.Tg_cooler_in
    Ts_in = state.Ts_cooler_in

    # ======================================================
    # HEAT TRANSFER COEFFICIENTS
    # ======================================================

    K_gs = cooler.hv_gs * cooler.a_gs
    K_gw = cooler.hv_gw * cooler.a_gw
    K_ws = cooler.hv_ws * cooler.a_ws

    # ======================================================
    # WALL THERMAL RESISTANCE
    # ======================================================

    _, _, R_total = wall_thermal_resistance(
        refractory_thickness=cooler.refractory_thickness,
        refractory_conductivity=cooler.refractory_conductivity,
        h_ext=cooler.h_ext,
        A_wall_cell=cooler.A_wall_cell,
    )

    # ======================================================
    # PICARD ITERATION
    # ======================================================

    max_iter = 100
    tol = 1e-6
    relaxation = 0.5

    Tg_iter = np.asarray(
        Tg,
        dtype=float,
    ).copy()

    Ts_iter = np.asarray(
        Ts,
        dtype=float,
    ).copy()

    Tw_iter = np.asarray(
        Tw,
        dtype=float,
    ).copy()

    for iteration in range(max_iter):

        # --------------------------------------------------
        # Existing heat-transfer model
        # --------------------------------------------------

        q_gs, q_gw, q_ws = heat_transfer(
            Tg=Tg_iter,
            Ts=Ts_iter,
            Tw=Tw_iter,
            hv_gs=cooler.hv_gs,
            hv_gw=cooler.hv_gw,
            hv_ws=cooler.hv_ws,
            a_gs=cooler.a_gs,
            a_gw=cooler.a_gw,
            a_ws=cooler.a_ws,
            zone=cooler.zone,
        )

        # ==================================================
        # LINEAR SYSTEM
        # ==================================================

        n_unknowns = 3 * N

        A = np.zeros(
            (n_unknowns, n_unknowns),
            dtype=float,
        )

        b = np.zeros(
            n_unknowns,
            dtype=float,
        )

        row = 0

        # ==================================================
        # GAS
        # ==================================================

        row = gas_phase.apply_gas_energy_balance(
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
        )

        # ==================================================
        # SOLID
        # ==================================================

        Cs = m_dot_s * cooler.Cp_s

        row = solid_phase.apply_solid_energy_balance(
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
        )

        # ==================================================
        # WALL
        # ==================================================

        for i in range(N):

            gas_i = i
            solid_i = N + i
            wall_i = 2 * N + i

            # ----------------------------------------------
            # Q_gw + Q_ws - Q_loss = 0
            # ----------------------------------------------

            A[row, gas_i] += (
                V_cell * K_gw
            )

            A[row, solid_i] += (
                V_cell * K_ws
            )

            A[row, wall_i] += (
                -V_cell * K_gw
                -V_cell * K_ws
                -0.27 / R_total
            )

            q_rad_gw = (
                q_gw[i]
                - K_gw * (
                    Tg_iter[i]
                    - Tw_iter[i]
                )
            )

            q_rad_ws = (
                q_ws[i]
                - K_ws * (
                    Ts_iter[i]
                    - Tw_iter[i]
                )
            )

            b[row] = (
                -V_cell * (
                    q_rad_gw
                    + q_rad_ws
                )
                -0.27 * cooler.T_amb / R_total
            )

            row += 1

        # ==================================================
        # SOLVE
        # ==================================================

        solution = np.linalg.solve(
            A,
            b,
        )

        Tg_new = solution[:N]

        Ts_new = solution[N:2 * N]

        Tw_new = solution[2 * N:3 * N]

        # ==================================================
        # PICARD RELAXATION
        # ==================================================

        Tg_next = (
            relaxation * Tg_new
            + (1.0 - relaxation) * Tg_iter
        )

        Ts_next = (
            relaxation * Ts_new
            + (1.0 - relaxation) * Ts_iter
        )

        Tw_next = (
            relaxation * Tw_new
            + (1.0 - relaxation) * Tw_iter
        )

        error = max(
            np.max(
                np.abs(
                    Tg_next - Tg_iter
                )
            ),
            np.max(
                np.abs(
                    Ts_next - Ts_iter
                )
            ),
            np.max(
                np.abs(
                    Tw_next - Tw_iter
                )
            ),
        )

        Tg_iter = Tg_next
        Ts_iter = Ts_next
        Tw_iter = Tw_next

        if error < tol:
            break

    else:
        raise RuntimeError(
            "Cooler steady-state thermal solution "
            f"did not converge after {max_iter} iterations. "
            f"error={error:.6e} K"
        )

    # ======================================================
    # FINAL STATE
    # ======================================================

    Tg_ss = Tg_iter
    Ts_ss = Ts_iter
    Tw_ss = Tw_iter

    # ======================================================
    # FINAL HEAT TRANSFER
    # ======================================================

    q_gs, q_gw, q_ws = heat_transfer(
        Tg=Tg_ss,
        Ts=Ts_ss,
        Tw=Tw_ss,
        hv_gs=cooler.hv_gs,
        hv_gw=cooler.hv_gw,
        hv_ws=cooler.hv_ws,
        a_gs=cooler.a_gs,
        a_gw=cooler.a_gw,
        a_ws=cooler.a_ws,
        zone=cooler.zone,
    )

    # q_* are volumetric [W/m3]
    Qgs = float(
        np.sum(q_gs * V_cell)
    )

    Qgw = float(
        np.sum(q_gw * V_cell)
    )

    Qws = float(
        np.sum(q_ws * V_cell)
    )

    # ======================================================
    # FINAL WALL LOSS
    # ======================================================

    (
        _,
        wall_loss,
        wall_debug,
    ) = wall_losses(
        Tw=Tw_ss,
        h_ext=cooler.h_ext,
        A_wall_cell=cooler.A_wall_cell,
        V_cell=cooler.V_cell,
        T_amb=cooler.T_amb,
        A_wall_total=cooler.A_wall,
        N=N,
        refractory_thickness=cooler.refractory_thickness,
        refractory_conductivity=cooler.refractory_conductivity,
        eps=cooler.eps,
    )

    # ======================================================
    # ENTHALPY
    # ======================================================

    Hg_in = (
        m_dot_g
        * float(
            h_gas(
                Tg_in,
                cooler.T_ref,
            )
        )
    )

    Hg_out = (
        m_dot_g
        * float(
            h_gas(
                Tg_ss[-1],
                cooler.T_ref,
            )
        )
    )

    Hs_in = (
        m_dot_s
        * cooler.Cp_s
        * (Ts_in - cooler.T_ref)
    )

    Hs_out = (
        m_dot_s
        * cooler.Cp_s
        * (Ts_ss[-1] - cooler.T_ref)
    )

    # ======================================================
    # ENERGY BALANCE
    # ======================================================

    energy_in = (
        Hg_in
        + Hs_in
    )

    energy_out = (
        Hg_out
        + Hs_out
        + wall_loss
    )

    total_energy_balance = (
        energy_in
        - energy_out
    )

    # ======================================================
    # STORE DIAGNOSTICS
    # ======================================================

    cooler.energy_in = float(
        energy_in
    )

    cooler.energy_out = float(
        energy_out
    )

    cooler.energy_residual = float(
        total_energy_balance
    )

    # ======================================================
    # RETURN
    # ======================================================

    return (
        Tg_ss,
        Ts_ss,
        Tw_ss,
        wall_loss,
        wall_debug,
        Qgs,
        Qgw,
        Qws,
        energy_in,
        energy_out,
        total_energy_balance,
    )
