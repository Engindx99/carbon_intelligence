import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import radiation
from physics.physics import second_order_upwind_correction
from physics.physics import second_order_upwind_face_corrections
from physics.physics import T_gas_from_h
from physics.physics import wall_thermal_resistance
from physics.variable_flow_rows import apply_gas_energy_balance
from physics.variable_flow_rows import apply_solid_energy_balance


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
    q_fuel_cells=None,
    Q_calciner=0.0,
    dm_gas_cells=None,
):

    # ======================================================
    # INPUTS
    # ======================================================

    T_ref = calciner.T_ref

    # state.m_dot_g_calciner is the flow LEAVING the zone and
    # state.m_dot_s_calciner the flow ENTERING it; neither is
    # the flow in a general cell, because calcination and
    # dehydroxylation move mass from the bed to the gas all the
    # way along. The per-cell profiles are built below.
    m_dot_g_out = state.m_dot_g_calciner
    m_dot_s_in = state.m_dot_s_calciner

    # ======================================================
    # FUEL HEAT RELEASE
    #
    # Per-cell [W], from precalciner.combustion. Enters the GAS
    # row, like the kiln burner's does: the fuel burns in the
    # gas stream and the bed receives it through the gas-solid
    # network, not as a source on the solid.
    # ======================================================

    if q_fuel_cells is None:
        q_fuel_cells = np.zeros(len(Tg))

    q_fuel_cells = np.asarray(q_fuel_cells, dtype=float)

    if q_fuel_cells.size != len(Tg):
        raise ValueError(
            "q_fuel_cells has wrong length: "
            f"{q_fuel_cells.size}, expected N={len(Tg)}"
        )

    # ======================================================
    # GEOMETRY
    # ======================================================

    N = len(Tg)

    # ======================================================
    # PER-CELL STREAM FLOWS
    #
    # The bed calcines and dehydroxylates along this zone, so a
    # single scalar flow is the true flow in at most one cell.
    # Used as one it was also, at the outlet, the INLET value --
    # which is how the calciner handed the transition an
    # enthalpy that inverted 110 K too hot while every energy
    # balance still closed to machine precision.
    #
    # Solid runs 0 -> N-1 and loses dm_gas in each cell; gas runs
    # N-1 -> 0 and gains it. Both are cumulative sums of the same
    # array, so what leaves one phase is what joins the other,
    # cell for cell.
    #
    # The gas INLET flow is derived as the zone outlet minus
    # everything the bed adds, rather than being reassembled from
    # the transition gas, tertiary air and fuel. That keeps this
    # identical to the scalar chain in physics.steady_state_mass
    # by construction, so the two accountings cannot drift.
    # ======================================================

    Cp_s = calciner.Cp_s

    if dm_gas_cells is None:
        dm_gas_cells = np.zeros(N)

    dm_gas_cells = np.asarray(dm_gas_cells, dtype=float)

    if dm_gas_cells.size != N:
        raise ValueError(
            "dm_gas_cells has wrong length: "
            f"{dm_gas_cells.size}, expected N={N}"
        )

    m_s_out_cells = (
        m_dot_s_in
        - np.cumsum(dm_gas_cells)
    )

    m_s_in_cells = np.concatenate(
        (
            [m_dot_s_in],
            m_s_out_cells[:-1],
        )
    )

    m_dot_g_in = (
        m_dot_g_out
        - float(np.sum(dm_gas_cells))
    )

    # Suffix sum: cell i's outgoing gas carries the mass released
    # by every cell from i to N-1 inclusive.
    m_g_out_cells = (
        m_dot_g_in
        + np.cumsum(dm_gas_cells[::-1])[::-1]
    )

    m_g_in_cells = (
        m_g_out_cells
        - dm_gas_cells
    )

    V_cell = calciner.V_cell

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

    # Inlet face enthalpy of the incoming gas stream. It is a
    # known handoff, not a reconstruction, so it is the one
    # face that carries no second-order correction.
    h_gas_in = h_gas(
        Tg_in,
        T_ref,
    )

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
        # SECOND-ORDER ADVECTION CORRECTION
        #
        # van Leer limited reconstruction of the axial face
        # values, applied by deferred correction: A stays the
        # first-order upwind operator and these per-cell terms
        # enter b only, frozen at the current iterate. The
        # convergence test below compares successive iterates,
        # so it is only satisfied once the frozen correction
        # has stopped moving too, i.e. at the fixed point of
        # the second-order equation. Gas is reconstructed in
        # ENTHALPY (its flux is m_dot_g * h), solid in
        # TEMPERATURE (its flux is affine in Ts). Same
        # construction as pyroprocess/burning/heat_transfer.py;
        # see physics.second_order_upwind_correction.
        # ==================================================

        # Per FACE, not pre-differenced: each face of a cell
        # carries a different mass flow here, so the two
        # corrections cannot be collapsed into one per-cell term
        # (physics.second_order_upwind_face_corrections). Both
        # arrays are in FLOW order and have N+1 entries.
        Dg_face = second_order_upwind_face_corrections(
            h_gas(Tg_iter, T_ref),
            h_gas_in,
            reverse=True,
        )

        Ds_face = second_order_upwind_face_corrections(
            Ts_iter,
            Ts_in,
            reverse=False,
        )

        # h_gas(Ts) for the CO2 and water leaving the bed,
        # linearised at the current iterate exactly as the gas
        # row linearises its own enthalpy. Both phases see the
        # same term with opposite signs, so it cancels over the
        # zone: the released mass crosses phases at the bed
        # temperature it actually left, creating no energy.
        cp_gas_s_cells = cp_gas(Ts_iter)

        h_const_s_cells = (
            h_gas(Ts_iter, T_ref)
            - cp_gas_s_cells * Ts_iter
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
            # GAS ENERGY BALANCE
            #
            # Gas direction: N-1 ---> 0. The gas GAINS the mass
            # the bed releases, so it enters and leaves each cell
            # with different flows; the row is built on both.
            # ==================================================

            radiation_gas_sink = (
                V_cell
                * (
                    q_gs_rad[i]
                    + q_gw_rad[i]
                )
            )

            # Gas cell i sits at flow position p = N-1-i, so its
            # inflow face is Dg_face[p] and its outflow face
            # Dg_face[p+1].
            p_gas = N - 1 - i

            row = apply_gas_energy_balance(
                A,
                b,
                row,
                i,
                N,
                Tg_iter,
                T_ref,
                m_g_out_cells[i],
                m_g_in_cells[i],
                dm_gas_cells[i],
                cp_gas_s_cells[i],
                h_const_s_cells[i],
                V_cell,
                K_gs,
                K_gw,
                radiation_gas_sink,
                Tg_in,
                Dg_face[p_gas],
                Dg_face[p_gas + 1],
            )

            # The fuel burns in the gas stream, exactly as the
            # kiln burner's does, so its heat is a source on the
            # gas row. apply_gas_energy_balance() is shared with
            # the transition zone, which has no firing, so the
            # term is added here rather than passed into it.
            b[row - 1] += q_fuel_cells[i]

            # ==================================================
            # SOLID ENERGY BALANCE
            #
            # Solid direction: 0 ---> N-1. The bed LOSES the CO2
            # of calcination and the water of dehydroxylation as
            # it goes.
            # ==================================================

            radiation_solid_source = (
                V_cell
                * (
                    q_gs_rad[i]
                    - q_ws_rad[i]
                )
            )

            row = apply_solid_energy_balance(
                A,
                b,
                row,
                i,
                N,
                m_s_out_cells[i] * Cp_s,
                m_s_in_cells[i] * Cp_s,
                T_ref,
                dm_gas_cells[i],
                cp_gas_s_cells[i],
                h_const_s_cells[i],
                V_cell,
                K_gs,
                K_ws,
                radiation_solid_source,
                reaction_heat_cells[i],
                Ts_in,
                Ds_face[i],
                Ds_face[i + 1],
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

    # Outlet values are taken at the outlet FACE, not at the
    # last cell CENTRE half a cell upstream of it. These are
    # the reconstructed values the second-order fluxes
    # actually transport out of the end cells, and the same
    # ones Calciner.apply() hands to the next unit, so using
    # them keeps this balance consistent with the handoff.
    #
    # The gas is reconstructed in enthalpy, so Hg_out below
    # comes straight from the face enthalpy and Tg_out is its
    # inverse, reporting the temperature the preheater sees.
    h_gas_out_face = outlet_face_value(
        h_gas(Tg_ss, T_ref),
        reverse=True,
    )

    Tg_out = T_gas_from_h(
        h_gas_out_face,
        T_ref,
        200.0,
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

    # Each end carries the flow that end actually has: the gas
    # arrives with what the transition and the tertiary air
    # brought and leaves with that plus everything the bed
    # released. Using one scalar for both was what rescaled the
    # temperature across the handoff.
    Hg_in = (
        m_dot_g_in
        * h_gas(
            Tg_in,
            T_ref,
        )
    )

    # Taken from the reconstructed face enthalpy directly
    # rather than from h_gas(Tg_out): the two agree only to
    # the inversion tolerance of T_gas_from_h, and this is the
    # quantity the flux and the handoff both use.
    Hg_out = (
        m_dot_g_out
        * h_gas_out_face
    )

    # Energy carried across the phase boundary by the CO2 and
    # the water, at the bed temperature they left. It is a
    # SOURCE for the gas and a SINK for the solid of exactly
    # the same size, so it cancels in the total balance below
    # and appears only in the two per-phase checks.
    H_phase_change = float(
        np.sum(
            dm_gas_cells
            * h_gas(
                Ts_ss,
                T_ref,
            )
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
        + H_phase_change
    )

    gas_energy_balance = (
        gas_energy_change
        - gas_expected
    )

    # ======================================================
    # SOLID ENTHALPY BALANCE
    # ======================================================

    Hs_in = (
        m_dot_s_in
        * Cp_s
        * (
            Ts_in
            - T_ref
        )
    )

    # The bed discharges what is left after every cell has
    # calcined and dehydroxylated, not what it was fed.
    m_s_out_face = (
        m_dot_s_in
        - float(np.sum(dm_gas_cells))
    )

    Hs_out = (
        m_s_out_face
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
        - H_phase_change
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
        + Q_calciner
        - Hg_out
        - Hs_out
        - Q_wall_loss
        - reaction_sink
    )

    calciner.energy_in = (
        Hg_in
        + Hs_in
        + Q_calciner
    )

    calciner.energy_out = (
        Hg_out
        + Hs_out
        + Q_wall_loss
        + reaction_sink
    )

    calciner.energy_residual = total_energy_balance

    # ======================================================
    # HANDOFF FLUXES AND PER-CELL FLOWS
    #
    # Published here so Calciner.apply() hands downstream
    # exactly the flux this balance booked, rather than
    # re-deriving it from a cell-centre array and a scalar
    # flow -- extrapolating the product of two varying
    # profiles is not the product of their extrapolations.
    # ======================================================

    state.Hgas_calciner_out = float(Hg_out)
    state.Hsolid_calciner_out = float(Hs_out)

    state.m_dot_g_calciner_in = float(m_dot_g_in)
    state.m_dot_s_calciner_out = float(m_s_out_face)

    state.m_dot_s_calciner_cells = m_s_out_cells.copy()
    state.m_dot_g_calciner_cells = m_g_out_cells.copy()

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
