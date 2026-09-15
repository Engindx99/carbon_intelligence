import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import radiation
from physics.physics import wall_thermal_resistance


# ======================================================
# THERMAL STEP
#
# Moved from Calciner.thermal_step() (pyroprocess/precalciner.py).
# Logic is unchanged; `self` was renamed to `calciner` since this
# is now a free function taking the owning Calciner instance
# explicitly instead of being a bound method.
# ======================================================
def thermal_step(
    calciner,
    Tg,
    Ts,
    Tw,
    state,
    Tg_in,
    Ts_in,
    reaction_sink=0.0,
    reaction_heat_cells=None,
):

    # ======================================================
    # INPUTS
    # ======================================================

    T_ref = calciner.T_ref

    m_dot_g = state.m_dot_g_calciner
    m_dot_s = state.m_dot_s_calciner

    # ======================================================
    # SOLID THERMAL CAPACITY
    # ======================================================

    Cp_s = calciner.Cp_s

    Cs = (
        m_dot_s
        * Cp_s
    )

    # ======================================================
    # GEOMETRY
    # ======================================================

    N = len(Tg)

    V_cell = calciner.V_cell

    # ======================================================
    # HEAT TRANSFER PARAMETERS
    # ======================================================

    hv_gs = calciner.hv_gs
    hv_gw = calciner.hv_gw
    hv_ws = calciner.hv_ws

    a_gs = calciner.a_gs
    a_gw = calciner.a_gw
    a_ws = calciner.a_ws

    K_gs = (
        hv_gs
        * a_gs
    )

    K_gw = (
        hv_gw
        * a_gw
    )

    K_ws = (
        hv_ws
        * a_ws
    )

    # ======================================================
    # WALL THERMAL RESISTANCE
    # ======================================================

    R_ref, R_conv, R_total = wall_thermal_resistance(
        refractory_thickness=calciner.refractory_thickness,
        refractory_conductivity=calciner.refractory_conductivity,
        h_ext=calciner.h_ext,
        A_wall_cell=calciner.A_wall_cell,
    )

    # ======================================================
    # REACTION DISTRIBUTION
    #
    # reaction_heat_cells[i] : W
    #
    # Each cell receives the actual local
    # calcination heat sink.
    # ======================================================

    if reaction_heat_cells is None:

        reaction_heat_cells = np.zeros(N)

    else:

        reaction_heat_cells = np.asarray(
            reaction_heat_cells,
            dtype=float,
        )

        if reaction_heat_cells.shape != (N,):

            raise ValueError(
                "reaction_heat_cells must have "
                f"shape ({N},)."
            )

        if not np.all(
            np.isfinite(
                reaction_heat_cells
            )
        ):

            raise ValueError(
                "reaction_heat_cells contains "
                "non-finite values."
            )

        if np.any(
            reaction_heat_cells < 0.0
        ):

            raise ValueError(
                "reaction_heat_cells cannot "
                "contain negative values."
            )

    # ======================================================
    # PICARD ITERATION
    # ======================================================

    max_iter = 100
    tol = 1e-6
    relaxation = 0.5

    Tg_iter = (
        np.asarray(
            Tg,
            dtype=float,
        )
        .copy()
    )

    Ts_iter = (
        np.asarray(
            Ts,
            dtype=float,
        )
        .copy()
    )

    Tw_iter = (
        np.asarray(
            Tw,
            dtype=float,
        )
        .copy()
    )

    converged = False
    error = np.inf

    # ======================================================
    # PICARD LOOP
    # ======================================================

    for iteration in range(max_iter):

        # ==================================================
        # GAS PROPERTIES
        # ==================================================

        Cp_g_iter = cp_gas(
            Tg_iter
        )

        # ==================================================
        # RADIATION
        # ==================================================

        q_gs_rad = radiation(
            Tg_iter,
            Ts_iter,
            zone=calciner.zone,
            area=a_gs,
        )

        q_gw_rad = radiation(
            Tg_iter,
            Tw_iter,
            zone=calciner.zone,
            area=a_gw,
        )

        q_ws_rad = radiation(
            Ts_iter,
            Tw_iter,
            zone=calciner.zone,
            area=a_ws,
        )

        # ==================================================
        # LINEAR SYSTEM
        # ==================================================

        n_unknowns = (
            3 * N
        )

        A = np.zeros(
            (
                n_unknowns,
                n_unknowns,
            )
        )

        b = np.zeros(
            n_unknowns
        )

        row = 0

        # ==================================================
        # CELL LOOP
        # ==================================================

        for i in range(N):

            Tg_i = i

            Ts_i = (
                N + i
            )

            Tw_i = (
                2 * N + i
            )

            # ==================================================
            # GAS LOCAL HEAT CAPACITY
            # ==================================================

            Cp_g_i = cp_gas(
                Tg_iter[i]
            )

            Cg_i = (
                m_dot_g
                * Cp_g_i
            )

            # ==================================================
            # GAS ENTHALPY LINEARIZATION
            #
            # h(T) ≈ Cp*T + constant
            # ==================================================

            h_i_iter = h_gas(
                Tg_iter[i],
                T_ref,
            )

            h_linear_const_i = (
                h_i_iter
                - Cp_g_i
                * Tg_iter[i]
            )

            # ==================================================
            # GAS ENERGY BALANCE
            #
            # Gas direction:
            #
            # N-1  --->  0
            #
            # Gas receives no reaction sink directly.
            # Calcination reaction is a solid-phase sink.
            # ==================================================

            A[row, Tg_i] += (
                Cg_i
                + V_cell * K_gs
                + V_cell * K_gw
            )

            A[row, Ts_i] += (
                -V_cell * K_gs
            )

            A[row, Tw_i] += (
                -V_cell * K_gw
            )

            # --------------------------------------------------
            # GAS RADIATION SINK
            # --------------------------------------------------

            radiation_gas_sink = (
                V_cell
                * (
                    q_gs_rad[i]
                    + q_gw_rad[i]
                )
            )

            # --------------------------------------------------
            # GAS INLET CELL
            #
            # Gas enters at cell N-1
            # --------------------------------------------------

            if i == N - 1:

                h_in = h_gas(
                    Tg_in,
                    T_ref,
                )

                b[row] = (
                    m_dot_g * h_in
                    - m_dot_g
                    * h_linear_const_i
                    - radiation_gas_sink
                )

            # --------------------------------------------------
            # INTERNAL GAS CELLS
            # --------------------------------------------------

            else:

                Tg_up_i = (
                    i + 1
                )

                Cp_g_up = cp_gas(
                    Tg_iter[i + 1]
                )

                h_up_iter = h_gas(
                    Tg_iter[i + 1],
                    T_ref,
                )

                h_linear_const_up = (
                    h_up_iter
                    - Cp_g_up
                    * Tg_iter[i + 1]
                )

                A[row, Tg_up_i] += (
                    -m_dot_g
                    * Cp_g_up
                )

                b[row] = (
                    -m_dot_g
                    * h_linear_const_i
                    + m_dot_g
                    * h_linear_const_up
                    - radiation_gas_sink
                )

            row += 1

            # ==================================================
            # SOLID ENERGY BALANCE
            #
            # Solid direction:
            #
            # 0  --->  N-1
            #
            # Calcination reaction is a solid-phase
            # energy sink.
            # ==================================================

            A[row, Ts_i] += (
                Cs
                + V_cell * K_gs
                + V_cell * K_ws
            )

            A[row, Tg_i] += (
                -V_cell * K_gs
            )

            A[row, Tw_i] += (
                -V_cell * K_ws
            )

            # --------------------------------------------------
            # SOLID RADIATION
            # --------------------------------------------------

            radiation_solid_source = (
                V_cell
                * (
                    q_gs_rad[i]
                    - q_ws_rad[i]
                )
            )

            # --------------------------------------------------
            # SOLID INLET CELL
            # --------------------------------------------------

            if i == 0:

                b[row] = (
                    Cs * Ts_in
                    + radiation_solid_source
                    - reaction_heat_cells[i]
                )

            # --------------------------------------------------
            # INTERNAL SOLID CELLS
            # --------------------------------------------------

            else:

                Ts_up_i = (
                    N + i - 1
                )

                A[row, Ts_up_i] += (
                    -Cs
                )

                b[row] = (
                    radiation_solid_source
                    - reaction_heat_cells[i]
                )

            row += 1

            # ==================================================
            # WALL ENERGY BALANCE
            # ==================================================

            A[row, Tg_i] += (
                V_cell * K_gw
            )

            A[row, Ts_i] += (
                V_cell * K_ws
            )

            A[row, Tw_i] += (
                -V_cell * K_gw
                -V_cell * K_ws
                -1.0 / R_total
            )

            # --------------------------------------------------
            # WALL RADIATION SOURCE
            # --------------------------------------------------

            radiation_wall_source = (
                V_cell
                * (
                    q_gw_rad[i]
                    + q_ws_rad[i]
                )
            )

            b[row] = (
                -calciner.T_amb
                / R_total
                - radiation_wall_source
            )

            row += 1

        # ======================================================
        # SOLVE LINEAR SYSTEM
        # ======================================================

        x_solution = np.linalg.solve(
            A,
            b,
        )

        Tg_new = (
            x_solution[:N]
        )

        Ts_new = (
            x_solution[
                N:2 * N
            ]
        )

        Tw_new = (
            x_solution[
                2 * N:3 * N
            ]
        )

        # ======================================================
        # CONVERGENCE ERROR
        # ======================================================

        error = max(
            np.max(
                np.abs(
                    Tg_new
                    - Tg_iter
                )
            ),
            np.max(
                np.abs(
                    Ts_new
                    - Ts_iter
                )
            ),
            np.max(
                np.abs(
                    Tw_new
                    - Tw_iter
                )
            ),
        )

        # ======================================================
        # RELAXATION
        # ======================================================

        Tg_iter = (
            relaxation
            * Tg_new
            + (
                1.0
                - relaxation
            )
            * Tg_iter
        )

        Ts_iter = (
            relaxation
            * Ts_new
            + (
                1.0
                - relaxation
            )
            * Ts_iter
        )

        Tw_iter = (
            relaxation
            * Tw_new
            + (
                1.0
                - relaxation
            )
            * Tw_iter
        )

        # ======================================================
        # CONVERGENCE
        # ======================================================

        if error < tol:

            converged = True

            break


    # ======================================================
    # STEADY-STATE TEMPERATURES
    # ======================================================

    Tg_ss = Tg_iter
    Ts_ss = Ts_iter
    Tw_ss = Tw_iter

    # ======================================================
    # INLET / OUTLET
    #
    # Gas:
    #     N-1 -> 0
    #
    # Solid:
    #     0 -> N-1
    # ======================================================

    Tg_out = Tg_ss[0]

    Ts_out = Ts_ss[-1]

    Tw_out = Tw_ss[-1]

    # ======================================================
    # FINAL RADIATION
    # ======================================================

    q_gs_rad_final = radiation(
        Tg_ss,
        Ts_ss,
        zone=calciner.zone,
        area=a_gs,
    )

    q_gw_rad_final = radiation(
        Tg_ss,
        Tw_ss,
        zone=calciner.zone,
        area=a_gw,
    )

    q_ws_rad_final = radiation(
        Ts_ss,
        Tw_ss,
        zone=calciner.zone,
        area=a_ws,
    )

    # ======================================================
    # CONVECTIVE HEAT TRANSFER
    # ======================================================

    Qgs_conv = (
        V_cell
        * K_gs
        * (
            Tg_ss
            - Ts_ss
        )
    )

    Qgw_conv = (
        V_cell
        * K_gw
        * (
            Tg_ss
            - Tw_ss
        )
    )

    Qws_conv = (
        V_cell
        * K_ws
        * (
            Ts_ss
            - Tw_ss
        )
    )

    # ======================================================
    # TOTAL HEAT TRANSFER
    # ======================================================

    Qgs = np.sum(
        Qgs_conv
        + V_cell
        * q_gs_rad_final
    )

    Qgw = np.sum(
        Qgw_conv
        + V_cell
        * q_gw_rad_final
    )

    Qws = np.sum(
        Qws_conv
        + V_cell
        * q_ws_rad_final
    )

    # ======================================================
    # WALL LOSS
    # ======================================================

    Q_wall_loss = np.sum(
        (
            Tw_ss
            - calciner.T_amb
        )
        / R_total
    )

    # ======================================================
    # GAS ENTHALPY BALANCE
    # ======================================================

    Hg_in = (
        m_dot_g
        * h_gas(
            Tg_in,
            T_ref,
        )
    )

    Hg_out = (
        m_dot_g
        * h_gas(
            Tg_out,
            T_ref,
        )
    )

    gas_energy_change = (
        Hg_out
        - Hg_in
    )

    # ------------------------------------------------------
    # Gas only exchanges energy through:
    #
    #   gas -> solid
    #   gas -> wall
    #
    # Reaction is NOT a gas sink.
    # ------------------------------------------------------

    gas_expected = (
        -Qgs
        -Qgw
    )

    gas_energy_balance = (
        gas_energy_change
        - gas_expected
    )

    # ======================================================
    # SOLID ENTHALPY BALANCE
    # ======================================================

    Hs_in = (
        m_dot_s
        * Cp_s
        * (
            Ts_in
            - T_ref
        )
    )

    Hs_out = (
        m_dot_s
        * Cp_s
        * (
            Ts_out
            - T_ref
        )
    )

    solid_energy_change = (
        Hs_out
        - Hs_in
    )

    # ------------------------------------------------------
    # Solid receives:
    #
    #   +Qgs
    #   -Qws
    #   -Qcalcination
    # ------------------------------------------------------

    solid_expected = (
        Qgs
        - Qws
        - reaction_sink
    )

    solid_energy_balance = (
        solid_energy_change
        - solid_expected
    )

    # ======================================================
    # TOTAL EQUIPMENT ENERGY BALANCE
    #
    # Hgas_in
    # + Hsolid_in
    #
    # =
    #
    # Hgas_out
    # + Hsolid_out
    # + Q_wall_loss
    # + Q_calcination
    #
    # Therefore:
    #
    # residual -> 0
    # ======================================================

    total_energy_balance = (
        Hg_in
        + Hs_in
        - Hg_out
        - Hs_out
        - Q_wall_loss
        - reaction_sink
    )

    calciner.energy_in = (
        Hg_in
        + Hs_in
    )

    calciner.energy_out = (
        Hg_out
        + Hs_out
        + Q_wall_loss
        + reaction_sink
    )

    calciner.energy_residual = total_energy_balance


    # ======================================================
    # RETURN
    # ======================================================

    return (
        Tg_ss,
        Ts_ss,
        Tw_ss,
        Q_wall_loss,
        {
            "Q_gs": Qgs,
            "Q_gw": Qgw,
            "Q_ws": Qws,
            "Q_wall_loss": Q_wall_loss,
            "Q_reaction": reaction_sink,
            "gas_energy_balance": gas_energy_balance,
            "solid_energy_balance": solid_energy_balance,
            "total_energy_balance": total_energy_balance,
            "iterations": iteration + 1,
            "converged": converged,
        },
    )
