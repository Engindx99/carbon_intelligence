import numpy as np

from physics.physics import h_gas
from physics.physics import wall_thermal_resistance
from physics.physics import radiation

from . import gas_phase
from . import solid_phase
from . import calcination


# ======================================================
# THERMAL STEP
#
# Moved from Transition.thermal_step() (pyroprocess/transition.py).
# Logic is unchanged; `self` was renamed to `transition` since
# this is now a free function taking the owning Transition
# instance explicitly. Gas-row and solid-row construction is
# delegated to gas_phase/solid_phase, and calcination kinetics
# to calcination, but the Picard loop, radiation network and
# per-cell wall balance stay here since heat_transfer.py owns
# the overall gas-solid-wall heat transfer network (same split
# boundary used by pyroprocess/burning/heat_transfer.py).
# ======================================================
def thermal_step(transition, Tg, Ts, Tw, state):

    # ======================================================
    # FLOW / MASS FLOW
    # ======================================================

    u_g = state.u_g
    u_s = state.u_s

    m_dot_g = state.m_dot_g_transition
    m_dot_s = state.m_dot_s_transition

    # ======================================================
    # SOLID THERMAL CAPACITY
    # ======================================================

    Cp_s = transition.Cp_s

    Cs = (
        m_dot_s
        * Cp_s
    )

    # ======================================================
    # INLET TEMPERATURES FROM ENTHALPY
    #
    # Burning -> Transition
    #
    # Gas inlet:
    #   i = N-1
    #
    # Solid inlet:
    #   i = 0
    # ======================================================

    Tg_in = gas_phase.gas_inlet_temperature_from_enthalpy(
        transition,
        state.Hgas_transition_in,
        state,
    )

    Ts_in = solid_phase.solid_inlet_temperature_from_enthalpy(
        transition,
        state.Hsolid_transition_in,
        state,
    )

    # ======================================================
    # GEOMETRY
    # ======================================================

    N = len(Tg)
    T_ref = transition.T_ref

    V_cell = transition.V_cell

    # ======================================================
    # HEAT TRANSFER COEFFICIENTS
    # ======================================================

    hv_gs = transition.hv_gs
    hv_gw = transition.hv_gw
    hv_ws = transition.hv_ws

    a_gs = transition.a_gs
    a_gw = transition.a_gw
    a_ws = transition.a_ws

    K_gs = hv_gs * a_gs
    K_gw = hv_gw * a_gw
    K_ws = hv_ws * a_ws

    # ======================================================
    # WALL THERMAL RESISTANCE
    # ======================================================

    R_ref, R_conv, R_total = wall_thermal_resistance(
        refractory_thickness=transition.refractory_thickness,
        refractory_conductivity=transition.refractory_conductivity,
        h_ext=transition.h_ext,
        A_wall_cell=transition.A_wall_cell,
    )

    # ======================================================
    # STEADY-STATE ITERATION
    # ======================================================

    max_iter = 100
    tol = 1.0e-6
    relaxation = 0.5

    Tg_iter = np.asarray(Tg, dtype=float).copy()
    Ts_iter = np.asarray(Ts, dtype=float).copy()
    Tw_iter = np.asarray(Tw, dtype=float).copy()

    m_dot_CaCO3_out_cells = np.zeros(N)

    converged = False
    error = np.inf

    # ======================================================
    # PICARD ITERATION
    # ======================================================

    for iteration in range(max_iter):

        # ==================================================
        # RESET CHEMISTRY FLOW FOR THIS PICARD ITERATION
        # ==================================================
        m_dot_CaCO3_out_cells[:] = 0.0

        # ==================================================
        # RADIATION
        # ==================================================

        q_gs_rad = radiation(
            Tg_iter,
            Ts_iter,
            zone=transition.zone,
            area=a_gs,
        )

        q_gw_rad = radiation(
            Tg_iter,
            Tw_iter,
            zone=transition.zone,
            area=a_gw,
        )

        q_ws_rad = radiation(
            Ts_iter,
            Tw_iter,
            zone=transition.zone,
            area=a_ws,
        )

        # ==================================================
        # LINEAR SYSTEM
        # ==================================================

        n_unknowns = 3 * N

        A = np.zeros(
            (n_unknowns, n_unknowns)
        )

        b = np.zeros(n_unknowns)

        row = 0

        # ==================================================
        # CELL EQUATIONS
        # ==================================================

        for i in range(N):

            Tg_i = i
            Ts_i = N + i
            Tw_i = 2 * N + i

            # ==================================================
            # GAS ENERGY BALANCE
            # ==================================================

            radiation_gas_sink = (
                V_cell
                * (
                    q_gs_rad[i]
                    + q_gw_rad[i]
                )
            )

            row = gas_phase.apply_gas_energy_balance(
                A,
                b,
                row,
                i,
                N,
                Tg_iter,
                T_ref,
                m_dot_g,
                V_cell,
                K_gs,
                K_gw,
                radiation_gas_sink,
                Tg_in,
            )

            # ======================================================
            # TRANSITION CALCINATION
            # ======================================================
            m_dot_CaCO3_transition_in = getattr(
                state,
                "m_dot_CaCO3_out_calciner",
                0.0,
            )

            if i == 0:
                m_CaCO3_in_cell = m_dot_CaCO3_transition_in
            else:
                m_CaCO3_in_cell = (
                    m_dot_CaCO3_out_cells[i - 1]
                )

            (
                k_reaction,
                m_CaCO3_out_cell,
                m_CaCO3_reacted_cell,
                Q_calcination_cell,
            ) = calcination.compute_cell_calcination(
                transition,
                Ts_iter[i],
                m_CaCO3_in_cell,
                transition.dz,
                u_s,
            )

            # Sonraki hücreye aktarılacak CaCO3 debisi
            m_dot_CaCO3_out_cells[i] = (
                m_CaCO3_out_cell
            )

            # ==================================================
            # SOLID ENERGY BALANCE
            # ==================================================

            radiation_solid_source = (
                V_cell
                * (
                    q_gs_rad[i]
                    - q_ws_rad[i]
                )
            )

            row = solid_phase.apply_solid_energy_balance(
                A,
                b,
                row,
                i,
                N,
                Cs,
                V_cell,
                K_gs,
                K_ws,
                radiation_solid_source,
                Q_calcination_cell,
                Ts_in,
            )

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
                -transition.T_amb / R_total
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

        Tg_new = x_solution[:N]

        Ts_new = x_solution[
            N:2 * N
        ]

        Tw_new = x_solution[
            2 * N:3 * N
        ]

        # ==================================================
        # RELAXATION
        # ==================================================

        Tg_iter = (
            relaxation * Tg_new
            + (1.0 - relaxation)
            * Tg_iter
        )

        Ts_iter = (
            relaxation * Ts_new
            + (1.0 - relaxation)
            * Ts_iter
        )

        Tw_iter = (
            relaxation * Tw_new
            + (1.0 - relaxation)
            * Tw_iter
        )

    # ======================================================
    # FINAL STEADY-STATE TEMPERATURES
    # ======================================================

    Tg_ss = Tg_iter
    Ts_ss = Ts_iter
    Tw_ss = Tw_iter

    # ======================================================
    # FINAL RADIATION
    # ======================================================

    q_gs_rad = radiation(
        Tg_ss,
        Ts_ss,
        zone=transition.zone,
        area=a_gs,
    )

    q_gw_rad = radiation(
        Tg_ss,
        Tw_ss,
        zone=transition.zone,
        area=a_gw,
    )

    q_ws_rad = radiation(
        Ts_ss,
        Tw_ss,
        zone=transition.zone,
        area=a_ws,
    )

    # ======================================================
    # FINAL TRANSITION CALCINATION
    # ======================================================

    (
        m_dot_CaCO3_transition_in,
        m_dot_CaCO3_in_cells,
        m_dot_CaCO3_reacted_cells,
        m_dot_CaCO3_out_cells,
        reaction_heat_cells,
        reaction_rate_cells,
        Q_calcination_transition,
        m_dot_CaCO3_out_transition,
        X_calcination_transition,
        cell_conversion,
    ) = calcination.resolve_transition_calcination(
        transition,
        state,
        Ts_ss,
        u_s,
    )

    # ======================================================
    # SOLID PHASE STATE UPDATE
    # CaCO3 -> CaO
    # ======================================================

    calcination.update_solid_phase_composition(
        transition,
        state,
        cell_conversion,
    )

    # ======================================================
    # FINAL CONVECTION
    # ======================================================

    q_gs_conv = (
        K_gs
        * (
            Tg_ss
            - Ts_ss
        )
    )

    q_gw_conv = (
        K_gw
        * (
            Tg_ss
            - Tw_ss
        )
    )

    q_ws_conv = (
        K_ws
        * (
            Ts_ss
            - Tw_ss
        )
    )

    # ======================================================
    # TOTAL CELL HEAT TRANSFER
    # ======================================================

    q_gs_cell = (
        q_gs_conv
        + q_gs_rad
    )

    q_gw_cell = (
        q_gw_conv
        + q_gw_rad
    )

    q_ws_cell = (
        q_ws_conv
        + q_ws_rad
    )

    # ======================================================
    # WALL LOSS
    # ======================================================

    Q_loss_cell = (
        Tw_ss
        - transition.T_amb
    ) / R_total

    wall_loss = np.sum(
        Q_loss_cell
    )

    # ======================================================
    # WALL DEBUG
    # ======================================================

    wall_debug = {

        "R_ref": float(
            R_ref
        ),

        "R_conv": float(
            R_conv
        ),

        "R_total": float(
            R_total
        ),

        "q_loss_mean": float(
            np.mean(
                Q_loss_cell
                / V_cell
            )
        ),

        "wall_loss_total": float(
            wall_loss
        ),

        "A_wall": float(
            transition.A_wall
        ),

        "A_wall_cell": float(
            transition.A_wall_cell
        ),

        "V_cell": float(
            V_cell
        ),

        "N": int(N),
    }

    # ======================================================
    # ENTHALPY DEBUG
    # ======================================================

    Hg_in = (
        state.Hgas_transition_in
    )

    Hs_in = (
        state.Hsolid_transition_in
    )

    Hg_out = (
        m_dot_g
        * h_gas(
            Tg_ss[0],
            T_ref
        )
    )

    Hs_out = (
        m_dot_s
        * Cp_s
        * (
            Ts_ss[-1]
            - T_ref
        )
    )

    # ======================================================
    # HEAT TRANSFER TOTALS
    # ======================================================

    Q_gs = (
        V_cell
        * np.sum(q_gs_cell)
    )

    Q_gw = (
        V_cell
        * np.sum(q_gw_cell)
    )

    Q_ws = (
        V_cell
        * np.sum(q_ws_cell)
    )

    # ======================================================
    # ENERGY BALANCE
    # ======================================================
    total_energy_balance = (
        Hg_in
        + Hs_in
        - Hg_out
        - Hs_out
        - wall_loss
        - Q_calcination_transition
    )

    transition.energy_in = (
        Hg_in
        + Hs_in
    )

    transition.energy_out = (
        Hg_out
        + Hs_out
        + wall_loss
        + Q_calcination_transition
    )

    transition.energy_residual = total_energy_balance

    state.Calcination_Q_transition = float(
        Q_calcination_transition
    )

    state.X_CaCO3_transition = float(
        X_calcination_transition
    )

    state.m_dot_CaCO3_in_transition = float(
        m_dot_CaCO3_transition_in
    )

    state.m_dot_CaCO3_out_transition = float(
        m_dot_CaCO3_out_transition
    )

    state.m_dot_CaCO3_reacted_transition = float(
        m_dot_CaCO3_transition_in
        - m_dot_CaCO3_out_transition
    )

    state.m_dot_CO2_generated_transition = float(
        state.m_dot_CaCO3_reacted_transition
        * transition.chemistry.CO2_ratio
    )

    state.Calcination_Q_transition_cells = (
        reaction_heat_cells.copy()
    )

    state.m_dot_CaCO3_in_transition_cells = (
        m_dot_CaCO3_in_cells.copy()
    )

    state.m_dot_CaCO3_reacted_transition_cells = (
        m_dot_CaCO3_reacted_cells.copy()
    )

    state.m_dot_CaCO3_out_transition_cells = (
        m_dot_CaCO3_out_cells.copy()
    )

    state.reaction_rate_CaCO3_transition_cells = (
        reaction_rate_cells.copy()
    )

    return (
        Tg_ss,
        Ts_ss,
        Tw_ss,
        wall_loss,
        wall_debug,
    )
