import numpy as np

from physics.physics import heat_transfer
from physics.physics import outlet_face_value
from physics.shell import shell_closure
from physics.physics import h_gas

from . import gas_phase
from . import solid_phase


# ======================================================
# INSULATION FACTOR -- REMOVED (Faz 6)
#
# This zone used to scale its wall rows by a calibration
# factor of 0.27. It existed because the underlying loss
# model was a single plane layer with a constant external
# film and no outer radiation, which over-predicted the flux
# by roughly the reciprocal of that factor. The loss is now
# a cylindrical layer stack closing on a solved casing
# temperature (physics.shell), so there is nothing left for
# a calibration factor to correct, and both places that
# carried it now read 1/R_total directly.
# ======================================================


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
# pyroprocess/burning/heat_transfer.py). Cooler's gas is now
# counter-current to the solid (secondary/tertiary air
# recuperation: cold air enters at the clinker-discharge end
# and exits hottest at the clinker-inlet end), matching the
# gas direction used by the Transition/Burning siblings. Its
# own row-assembly ARCHITECTURE (three separate blocked row
# loops: gas, then solid, then wall, each self-contained) is
# preserved exactly and is NOT converted to the interleaved,
# per-cell-driven formulation used by the Transition/Burning
# siblings -- only the flow direction changed.
# ======================================================
def thermal_step(cooler, Tg, Ts, Tw, state):

    # ======================================================
    # MASS FLOW
    # ======================================================

    m_dot_g = state.m_dot_air_cooler
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

    # Faz 6: per cell, and refreshed inside the Picard loop from
    # the current hot face. This call only seeds the first pass.
    R_total, T_shell, shell_info = shell_closure(
        np.asarray(Tw, dtype=float),
        cooler.shell,
        cooler.T_amb,
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
        # Shell loss resistance at the current hot face
        # --------------------------------------------------

        R_total, T_shell, shell_info = shell_closure(
            Tw_iter,
            cooler.shell,
            cooler.T_amb,
            T_shell_guess=T_shell,
        )

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
            cooler.T_ref,
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
                -1.0 / R_total[i]
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
                -cooler.T_amb / R_total[i]
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
    #
    # Faz 6: the loss network is re-closed on the CONVERGED hot
    # face and the loss read straight off it, rather than handed
    # to a second implementation (physics.wall_losses) that could
    # drift from the matrix. The wall_mismatch guard further down
    # is what used to police that drift; it now compares the
    # matrix against the same R_total the matrix was built from,
    # so it degenerates to the Picard gap, which is what it was
    # really measuring all along.
    # ======================================================

    # Held before the re-solve overwrites it: this is the
    # resistance the LAST assembled matrix actually dissipated
    # through, and the wall_mismatch guard below needs it to stay
    # a test rather than an identity.
    R_total_matrix = R_total

    R_total, T_shell, shell_info = shell_closure(
        Tw_ss,
        cooler.shell,
        cooler.T_amb,
        T_shell_guess=T_shell,
    )

    Q_loss_cells = (Tw_ss - cooler.T_amb) / R_total

    wall_loss = float(np.sum(Q_loss_cells))

    wall_debug = {
        "R_cond": float(shell_info["R_cond"]),
        "R_ext": float(shell_info["R_ext_mean"]),
        "R_total": float(np.mean(R_total)),
        "h_ext": float(shell_info["h_ext_mean"]),
        "T_shell_mean": float(shell_info["T_shell_mean"]),
        "q_loss_mean": float(np.mean(Q_loss_cells / cooler.V_cell)),
        "wall_loss_total": wall_loss,
        "A_wall": float(cooler.A_wall),
        "A_wall_cell": float(cooler.A_wall_cell),
        "V_cell": float(cooler.V_cell),
        "N": int(N),
    }

    state.Cooler_R_total_cells = np.asarray(R_total, dtype=float)
    state.Cooler_R_total = float(np.mean(R_total))

    state.Cooler_T_shell_cells = np.asarray(T_shell, dtype=float)
    state.Cooler_T_shell_max = float(np.max(T_shell))
    state.Cooler_shell_h_ext = float(shell_info["h_ext_mean"])
    state.Cooler_shell_h_conv = float(shell_info["h_conv_mean"])
    state.Cooler_shell_h_rad = float(shell_info["h_rad_mean"])
    state.Cooler_shell_flux = float(shell_info["flux_outer_mean"])
    state.Cooler_shell_R_cond = float(shell_info["R_cond"])

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

    # Outlet values are read at the outlet FACE, not at the
    # last cell CENTRE -- the same reconstructed values the
    # second-order fluxes actually transport out of the end
    # cells, and the same ones gas_phase.gas_enthalpy_out()
    # and solid_phase.solid_enthalpy_out() hand to the next
    # unit. Reading the centres here instead would show up as
    # a spurious gas_gap/solid_gap in the decomposition below.
    Hg_out = (
        m_dot_g
        * gas_phase.hot_end_face_enthalpy(
            cooler,
            Tg_ss,
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
        * (
            outlet_face_value(
                Ts_ss,
                reverse=False,
            )
            - cooler.T_ref
        )
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
    # RESIDUAL DECOMPOSITION (DIAGNOSTIC)
    #
    # Summing the discrete rows of the linear system accounts
    # for the reported residual exactly:
    #
    #     R = -gas_gap - solid_gap + wall_mismatch
    #
    # Nothing else survives: the K_gs/K_gw/K_ws terms cancel
    # identically between the rows and the fluxes. Every cell
    # i = 0..N-1 now carries a gas row, a solid row and a
    # wall row, so the sums below run over the whole array.
    #
    # gas_gap  Closure gap of the gas rows, evaluated at the
    #          converged state against the final fluxes. Zero
    #          at the exact fixed point: the enthalpy-
    #          linearized rows (gas_phase.py) telescope to
    #          m_dot_g*(h_gas(Tg_out) - h_gas(Tg_in)), which is
    #          exactly Hg_out - Hg_in above. What is left is
    #          the Picard gap, bounded by `tol`.
    #
    # solid_gap  Same for the solid rows. Cp_s is constant, so
    #          those telescope exactly too; again only the
    #          Picard gap remains.
    #
    # wall_mismatch  The wall rows dissipate through the
    #          R_total of the LAST Picard iterate; the reported
    #          wall_loss re-closes the same network on the
    #          converged hot face. At the fixed point the two
    #          iterates coincide, so this is the Picard gap of
    #          the wall row and nothing else.
    #
    # This block is purely additive: it reads the converged
    # state and changes no equation, boundary condition or
    # returned value.
    # ======================================================

    gas_gap = (
        Hg_out
        - Hg_in
        + V_cell * float(
            np.sum(
                q_gs
                + q_gw
            )
        )
    )

    solid_gap = (
        Hs_out
        - Hs_in
        - V_cell * float(
            np.sum(
                q_gs
                - q_ws
            )
        )
    )

    wall_loss_matrix = float(
        np.sum(
            (Tw_ss - cooler.T_amb)
            / R_total_matrix
        )
    )

    wall_mismatch = (
        wall_loss_matrix
        - wall_loss
    )

    residual_decomposition_check = (
        -gas_gap
        - solid_gap
        + wall_mismatch
        - total_energy_balance
    )

    cooler.residual_gas_gap = float(
        gas_gap
    )

    cooler.residual_solid_gap = float(
        solid_gap
    )

    cooler.residual_wall_mismatch = float(
        wall_mismatch
    )

    cooler.residual_decomposition_check = float(
        residual_decomposition_check
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
