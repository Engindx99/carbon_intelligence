import numpy as np

from physics.physics import cp_gas, h_gas
from physics.physics import outlet_face_value
from physics.physics import radiation
from physics.physics import second_order_upwind_correction
from physics.physics import T_gas_from_h
from physics.physics import wall_thermal_resistance

from . import combustion
from . import gas_phase
from . import solid_phase


# ======================================================
# THERMAL STEP
#
# Moved from Burning.thermal_step() (pyroprocess/burning.py).
# Logic is unchanged; `self` was renamed to `burning` since
# this is now a free function taking the owning Burning
# instance explicitly. Gas-side and solid-side row
# construction is delegated to gas_phase/solid_phase, and
# fuel/reaction heat source terms to combustion, but the
# Picard loop, wall/radiation network and per-cell wall
# balance stay here since heat_transfer.py owns the overall
# gas-solid-wall heat transfer network.
# ======================================================
def thermal_step(burning, Tg, Ts, Tw, state, inputs, u_g, u_s):

    # ======================================================
    # INPUTS
    # ======================================================

    T_ref = burning.T_ref

    # ======================================================
    # MASS FLOW / THERMAL CAPACITY
    # ======================================================

    # m_dot_g is calculated centrally in main.py.
    m_dot_g = state.m_dot_g

    m_dot_s = state.m_dot_s

    # ======================================================
    # SOLID THERMAL CAPACITY
    # ======================================================

    Cp_s = burning.Cp_s
    Cs = m_dot_s * Cp_s

    # ======================================================
    # GEOMETRY
    # ======================================================

    N = len(Tg)
    V_cell = burning.V_cell

    # ======================================================
    # HEAT TRANSFER PARAMETERS
    # ======================================================

    hv_gs = burning.hv_gs
    hv_gw = burning.hv_gw
    hv_ws = burning.hv_ws

    a_gs = burning.a_gs
    a_gw = burning.a_gw
    a_ws = burning.a_ws

    K_gs = hv_gs * a_gs
    K_gw = hv_gw * a_gw
    K_ws = hv_ws * a_ws

    # ======================================================
    # FUEL HEAT RELEASE
    # ======================================================

    (
        Q_petcoke,
        Q_burning
    ) = combustion.fuel_heat_release_for(
        burning,
        inputs,
    )

    # ======================================================
    # BURNING REACTION ENERGY SINK
    # ======================================================

    Burning_Q_sink = combustion.reaction_heat_sink(state)

    # ======================================================
    # AXIAL ENERGY DISTRIBUTION
    # ======================================================

    q_cell, reaction_q_cell = combustion.axial_heat_distribution(
        N,
        Q_burning,
        Burning_Q_sink,
    )

    # ======================================================
    # WALL THERMAL RESISTANCE
    # ======================================================

    R_ref, R_conv, R_total = wall_thermal_resistance(
        refractory_thickness=burning.refractory_thickness,
        refractory_conductivity=burning.refractory_conductivity,
        h_ext=burning.h_ext,
        A_wall_cell=burning.A_wall_cell,
    )

    # ======================================================
    # PICARD ITERATION
    # ======================================================

    max_iter = 100
    tol = 1e-6
    relaxation = 0.5

    # Inlet face enthalpy of the incoming gas stream. It is a
    # known handoff, not a reconstruction, so it is the one
    # face that carries no second-order correction.
    h_gas_in = h_gas(
        state.Tg_burning_in,
        T_ref,
    )

    Tg_iter = np.asarray(Tg, dtype=float).copy()
    Ts_iter = np.asarray(Ts, dtype=float).copy()
    Tw_iter = np.asarray(Tw, dtype=float).copy()

    converged = False
    error = np.inf

    for iteration in range(max_iter):

        # ==================================================
        # GAS PROPERTIES AT CURRENT ITERATE
        # ==================================================

        Cp_g_iter = cp_gas(Tg_iter)

        # ==================================================
        # RADIATION
        # ==================================================

        q_gs_rad = radiation(
            Tg_iter,
            Ts_iter,
            zone="burning",
            area=a_gs
        )

        q_gw_rad = radiation(
            Tg_iter,
            Tw_iter,
            zone="burning",
            area=a_gw
        )

        q_ws_rad = radiation(
            Ts_iter,
            Tw_iter,
            zone="burning",
            area=a_ws
        )

        # ==================================================
        # SECOND-ORDER ADVECTION CORRECTION
        #
        # van Leer limited reconstruction of the axial face
        # values, applied by deferred correction: A stays the
        # first-order upwind operator and these per-cell terms
        # enter b only, frozen at the current iterate. At the
        # fixed point the iterate equals the solution, so the
        # converged answer satisfies the second-order
        # equation. See physics.second_order_upwind_correction.
        #
        # The gas is reconstructed in ENTHALPY, since the gas
        # flux is m_dot_g * h and h is cubic in T; the solid
        # is reconstructed in TEMPERATURE, since its flux
        # Cs * (Ts - T_ref) is affine in Ts.
        # ==================================================

        adv_corr_g = second_order_upwind_correction(
            h_gas(Tg_iter, T_ref),
            h_gas_in,
            reverse=True,
        )

        adv_corr_s = second_order_upwind_correction(
            Ts_iter,
            state.Ts_burning_in,
            reverse=False,
        )

        # ==================================================
        # LINEAR SYSTEM
        # ==================================================

        n_unknowns = 3 * N

        A = np.zeros((n_unknowns, n_unknowns))
        b = np.zeros(n_unknowns)

        row = 0

        # ==================================================
        # CELL LOOP
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
                q_cell,
                reaction_q_cell,
                radiation_gas_sink,
                state.Tg_burning_in,
                adv_corr_g[i],
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
                state.Ts_burning_in,
                adv_corr_s[i],
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
                -burning.T_amb / R_total
                -radiation_wall_source
            )

            row += 1

        # ==================================================
        # SOLVE LINEAR SYSTEM
        # ==================================================

        x_solution = np.linalg.solve(
            A,
            b
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
            + (1.0 - relaxation) * Tg_iter
        )

        Ts_iter = (
            relaxation * Ts_new
            + (1.0 - relaxation) * Ts_iter
        )

        Tw_iter = (
            relaxation * Tw_new
            + (1.0 - relaxation) * Tw_iter
        )


    # ======================================================
    # STEADY-STATE TEMPERATURES
    # ======================================================

    Tg_ss = Tg_iter
    Ts_ss = Ts_iter
    Tw_ss = Tw_iter

    # ======================================================
    # OUTLET TEMPERATURES
    #
    # Gas flows from N-1 -> 0
    # Solid flows from 0 -> N-1
    # ======================================================

    Tg_in = state.Tg_burning_in
    Ts_in = state.Ts_burning_in

    # Outlet values are taken at the outlet FACE, not at the
    # last cell CENTRE. The face sits half a cell downstream
    # of that centre, so reading the centre biased every
    # handoff by O(dz) no matter how well the interior was
    # resolved. These are the same reconstructed values the
    # second-order flux actually transports out of the end
    # cells, so using them here keeps this energy balance
    # consistent with gas_phase.gas_enthalpy_out() and
    # solid_phase.solid_enthalpy_out(); reading the centres
    # instead would leak exactly that difference.
    #
    # The gas is reconstructed in enthalpy (its flux is
    # m_dot_g * h), so Hg_out comes straight from the face
    # enthalpy below and Tg_out is its inverse -- reporting
    # the outlet temperature the next zone actually sees.
    h_gas_out_face = outlet_face_value(
        h_gas(Tg_ss, T_ref),
        reverse=True,
    )

    Tg_out = T_gas_from_h(
        h_gas_out_face,
        T_ref,
        T_ref,
        4000.0,
    )

    # The solid flux is affine in Ts, so extrapolating the
    # temperature is identical to extrapolating its enthalpy.
    Ts_out = outlet_face_value(
        Ts_ss,
        reverse=False,
    )

    # The wall does not advect, so it has no outlet face.
    Tw_out = Tw_ss[-1]

    # ======================================================
    # FINAL RADIATION
    # ======================================================

    q_gs_rad_final = radiation(
        Tg_ss,
        Ts_ss,
        zone="burning",
        area=a_gs
    )

    q_gw_rad_final = radiation(
        Tg_ss,
        Tw_ss,
        zone="burning",
        area=a_gw
    )

    q_ws_rad_final = radiation(
        Ts_ss,
        Tw_ss,
        zone="burning",
        area=a_ws
    )

    # ======================================================
    # CONVECTIVE HEAT TRANSFER
    # ======================================================

    Qgs_conv = (
        V_cell
        * K_gs
        * (Tg_ss - Ts_ss)
    )

    Qgw_conv = (
        V_cell
        * K_gw
        * (Tg_ss - Tw_ss)
    )

    Qws_conv = (
        V_cell
        * K_ws
        * (Ts_ss - Tw_ss)
    )

    # ======================================================
    # TOTAL HEAT TRANSFER
    # ======================================================

    Qgs = np.sum(
        Qgs_conv
        + V_cell * q_gs_rad_final
    )

    Qgw = np.sum(
        Qgw_conv
        + V_cell * q_gw_rad_final
    )

    Qws = np.sum(
        Qws_conv
        + V_cell * q_ws_rad_final
    )

    # ======================================================
    # WALL LOSS
    # ======================================================

    Q_wall_loss = np.sum(
        (
            Tw_ss - burning.T_amb
        ) / R_total
    )

    # ======================================================
    # GAS ENTHALPY BALANCE
    # ======================================================

    Hg_in = (
        m_dot_g
        * h_gas(
            Tg_in,
            T_ref
        )
    )

    # Taken from the reconstructed face enthalpy directly
    # rather than from h_gas(Tg_out): the two agree only to
    # the inversion tolerance of T_gas_from_h, and this is the
    # quantity the flux and the handoff both use.
    Hg_out = (
        m_dot_g
        * h_gas_out_face
    )

    gas_energy_change = (
        Hg_out
        - Hg_in
    )

    gas_expected = (
        Q_burning
        - Qgs
        - Qgw
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
            Ts_in - T_ref
        )
    )

    Hs_out = (
        m_dot_s
        * Cp_s
        * (
            Ts_out - T_ref
        )
    )

    solid_energy_change = (
        Hs_out
        - Hs_in
    )

    solid_expected = (
        Qgs
        - Qws
    )

    solid_energy_balance = (
        solid_energy_change
        - solid_expected
    )

    # ======================================================
    # TOTAL ENERGY BALANCE
    # ======================================================

    Burning_Q_sink = combustion.reaction_heat_sink(state)

    energy_in = (
        Hg_in
        + Hs_in
        + Q_burning
    )

    energy_out = (
        Hg_out
        + Hs_out
        + Q_wall_loss
        + Burning_Q_sink
    )

    total_energy_balance = (
        energy_in
        - energy_out
    )

    burning.energy_in = float(energy_in)
    burning.energy_out = float(energy_out)
    burning.energy_residual = float(total_energy_balance)


    for i in range(N):

        # ==================================================
        # GAS -> SOLID
        # ==================================================

        Qgs_conv_cell = Qgs_conv[i]

        Qgs_rad_cell = (
            V_cell
            * q_gs_rad_final[i]
        )

        Qgs_cell = (
            Qgs_conv_cell
            + Qgs_rad_cell
        )

        # ==================================================
        # GAS -> WALL
        # ==================================================

        Qgw_conv_cell = Qgw_conv[i]

        Qgw_rad_cell = (
            V_cell
            * q_gw_rad_final[i]
        )

        Qgw_cell = (
            Qgw_conv_cell
            + Qgw_rad_cell
        )

        # ==================================================
        # SOLID -> WALL
        # ==================================================

        Qws_conv_cell = Qws_conv[i]

        Qws_rad_cell = (
            V_cell
            * q_ws_rad_final[i]
        )

        Qws_cell = (
            Qws_conv_cell
            + Qws_rad_cell
        )

        # ==================================================
        # WALL LOSS
        # ==================================================

        Qloss_cell = (
            (
                Tw_ss[i]
                - burning.T_amb
            )
            / R_total
        )


    # ======================================================
    # RETURN
    # ======================================================

    return (
        Tg_ss,
        Ts_ss,
        Tw_ss,
        Q_petcoke,
        Q_burning,
        energy_in,
        energy_out,
        total_energy_balance,
        Q_wall_loss,
    )
