import numpy as np

from physics.physics import heat_transfer
from physics.physics import wall_losses
from physics.physics import wall_thermal_resistance
from physics.physics import h_gas

from . import gas_phase
from . import solid_phase


# ======================================================
# INSULATION FACTOR
#
# Wall-loss calibration factor used by the wall rows of the
# linear system. Previously written as the literal 0.27 in
# two separate places in the wall-row assembly; bound to a
# single name here so the matrix and the residual
# decomposition diagnostic cannot silently diverge. Value is
# unchanged, and matches the `insulation_factor=0.27` default
# of physics.wall_losses().
# ======================================================
_INSULATION_FACTOR = 0.27


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
                -_INSULATION_FACTOR / R_total
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
                -_INSULATION_FACTOR * cooler.T_amb / R_total
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
    # eps=0.0: wall_losses() divides by (R_total + eps) and
    # by (V_cell + eps), while the wall rows of the matrix
    # above divide by R_total alone. Passing cooler.eps
    # (1e-9) therefore biased the reported wall loss away
    # from the energy the matrix actually removes, by
    # eps/R_total ~ 4e-7 relative. Both denominators are
    # strictly positive for any physical geometry
    # (R_total = t/(k*A) + 1/(h*A), V_cell > 0), so the
    # guard protects against nothing and is dropped here.
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
        eps=0.0,
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
                Tg_ss[0],
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
    # wall_mismatch  The wall rows dissipate via
    #          _INSULATION_FACTOR/R_total while the reported
    #          wall_loss comes from physics.wall_losses().
    #          Kept as a guard that the two stay in step.
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

    wall_loss_matrix = (
        _INSULATION_FACTOR
        / R_total
        * float(
            np.sum(Tw_ss - cooler.T_amb)
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
