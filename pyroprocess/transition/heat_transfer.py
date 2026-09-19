import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import second_order_upwind_face_corrections
from physics.physics import fill_fraction_from_holdup
from physics.physics import bed_segment_geometry
from physics.shell import shell_closure
from physics.kiln_closures import kiln_transfer_coefficients
from physics.kiln_closures import radiating_partial_pressure

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

    # ======================================================
    # STREAM MASS FLOWS
    #
    # The bed calcines along this zone, so neither stream has
    # a single mass flow: the solid sheds CO2 cell by cell and
    # the gas picks it up. state.m_dot_s_transition is the flow
    # ENTERING (the calciner's outlet) and state.m_dot_g_transition
    # the flow LEAVING (it already includes all the CO2), so
    # each is used only at the end where it is the true flow.
    # The per-cell profiles are built inside the Picard loop
    # from the same calcination march that feeds the heat sink,
    # so the mass and energy the reaction moves always agree.
    # ======================================================

    m_dot_s_in = m_dot_s

    # The gas arriving is the stream Burning discharged, which
    # is also the stream whose enthalpy Hgas_transition_in
    # carries; taking it from state.m_dot_g keeps the flow and
    # the enthalpy at this boundary from drifting apart.
    m_dot_g_in = state.m_dot_g

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

    # ======================================================
    # FAZ 5 / FAZ 3 -- AREAS AND COEFFICIENTS
    #
    # a_gs / a_ws / a_gw used to be frozen in __init__ from an
    # inlined packed-bed correlation that over-counted the wall by
    # 58.5%, and K was that times three literal constants. Both now
    # follow the state: the areas from the bed's circular segment,
    # the coefficients from the local temperatures.
    #
    # The fill fraction comes from the same continuity relation the
    # burning zone uses, m_dot_s = rho_bulk * u_s * A_bed, rather
    # than the hard-coded transition.fill_fraction = 0.10 that
    # nothing solved for. It is taken at the zone INLET flow, which
    # is the heavier end here because the bed calcines along the
    # zone -- the same single-fill-fraction approximation the
    # burning zone makes, and the same one Faz 3 will remove.
    # ======================================================
    bed_fill_fraction = fill_fraction_from_holdup(
        m_dot_s=m_dot_s_in,
        rho_bulk=transition.rho_s,
        u_s=u_s,
        A_cross=transition.A_cross,
    )

    (
        bed_angle,
        a_gs,
        a_ws,
        a_gw,
        D_e,
    ) = bed_segment_geometry(
        transition.D,
        bed_fill_fraction,
    )

    # Radiating species arriving from the kiln, plus whatever this
    # zone's own calcination adds on the way. Read off state so the
    # two zones describe the same stream with the same numbers.
    m_CO2_gas_in = getattr(state, "Burning_m_dot_CO2_gas_out", 0.0)
    m_H2O_gas_in = getattr(state, "Burning_m_dot_H2O_gas_out", 0.0)

    def closure_at(Tg_at, Ts_at, Tw_at, m_g_cells, p_rad):

        return kiln_transfer_coefficients(
            Tg=Tg_at,
            Ts=Ts_at,
            Tw=Tw_at,
            D=transition.D,
            fill_fraction=bed_fill_fraction,
            rpm=transition.rpm_default,
            m_dot_gas=m_g_cells,
            p_rad=p_rad,
            eps_bed=transition.closure.bed_emissivity,
            eps_wall=transition.closure.wall_emissivity,
            bed_conductivity=transition.closure.bed_conductivity,
            bed_density=transition.rho_s,
            bed_cp=transition.Cp_s,
            particle_diameter=transition.closure.particle_diameter,
            contact_chi=transition.closure.contact_chi,
        )

    # ======================================================
    # WALL THERMAL RESISTANCE
    # ======================================================

    # Faz 6: solved per cell from the shell energy balance and
    # refreshed inside the Picard loop, like every other
    # temperature-dependent conductance in this zone. The call
    # here only supplies the first pass's value.
    R_total, T_shell, shell_info = shell_closure(
        np.asarray(Tw, dtype=float),
        transition.shell,
        transition.T_amb,
    )

    # ======================================================
    # STEADY-STATE ITERATION
    # ======================================================

    max_iter = 100
    tol = 1.0e-6
    relaxation = 0.5

    # Inlet face enthalpy of the incoming gas stream. It is a
    # known handoff, not a reconstruction, so it is the one
    # face that carries no second-order correction.
    h_gas_in = h_gas(
        Tg_in,
        T_ref,
    )

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

        # Faz 5: the transfer coefficients are built further down,
        # after the calcination march has produced this iterate's
        # per-cell gas flow -- the closure needs it for both the
        # local gas velocity and the radiating partial pressure.

        # ==================================================
        # SECOND-ORDER ADVECTION CORRECTION
        #
        # van Leer limited reconstruction of the axial face
        # values, applied by deferred correction: A stays the
        # first-order upwind operator and these per-cell terms
        # enter b only, frozen at the current iterate, so the
        # converged fixed point satisfies the second-order
        # equation. Gas is reconstructed in ENTHALPY (its flux
        # is m_dot_g * h), solid in TEMPERATURE (its flux is
        # affine in Ts). Same construction as
        # pyroprocess/burning/heat_transfer.py; see
        # physics.second_order_upwind_correction.
        # ==================================================

        # Per FACE, not pre-differenced: each face of a cell
        # carries a different mass flow here, so the two
        # corrections cannot be collapsed into one per-cell
        # term (physics.second_order_upwind_face_corrections).
        # Both arrays are in FLOW order and have N+1 entries.
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

        # ==================================================
        # CALCINATION MARCH
        #
        # Run over the whole zone BEFORE the rows are
        # assembled. The gas flow in a cell depends on the CO2
        # released by every cell downstream of it on the gas
        # path, which the old cell-by-cell interleaving could
        # not know yet. Marching first also keeps the mass
        # transfer and the heat sink derived from one and the
        # same conversion.
        # ==================================================

        m_dot_CaCO3_transition_in = getattr(
            state,
            "m_dot_CaCO3_out_calciner",
            0.0,
        )

        dm_gas_cells = np.zeros(N)
        Q_calcination_cells = np.zeros(N)

        m_CaCO3_in_cell = m_dot_CaCO3_transition_in

        for i in range(N):

            (
                _k_reaction,
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

            m_dot_CaCO3_out_cells[i] = m_CaCO3_out_cell

            dm_gas_cells[i] = (
                m_CaCO3_reacted_cell
                * transition.chemistry.CO2_ratio
            )

            Q_calcination_cells[i] = Q_calcination_cell

            m_CaCO3_in_cell = m_CaCO3_out_cell

        # ==================================================
        # PER-CELL STREAM FLOWS
        #
        # Solid runs 0 -> N-1 and loses dm_gas in each cell;
        # gas runs N-1 -> 0 and gains it. Both are exact
        # cumulative sums of the same array, so what leaves one
        # phase is what joins the other, cell for cell.
        # ==================================================

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

        # Suffix sum: cell i's outgoing gas carries the CO2 of
        # every cell from i to N-1 inclusive.
        m_g_out_cells = (
            m_dot_g_in
            + np.cumsum(dm_gas_cells[::-1])[::-1]
        )

        m_g_in_cells = (
            m_g_out_cells
            - dm_gas_cells
        )

        # h_gas(Ts) for the CO2 leaving the bed, linearised at
        # the current iterate exactly as the gas row linearises
        # its own enthalpy.
        cp_gas_s_cells = cp_gas(Ts_iter)

        h_const_s_cells = (
            h_gas(Ts_iter, T_ref)
            - cp_gas_s_cells * Ts_iter
        )

        # ==================================================
        # FAZ 5 CLOSURE AT THIS ITERATE
        #
        # Built here, not at the top of the loop, because the gas
        # flow it needs only exists after the calcination march.
        # Radiation goes INSIDE K rather than into b: linearised
        # as h_rad = eps_eff sigma (T1 + T2)(T1^2 + T2^2) it is
        # algebraically identical to eps_eff sigma (T1^4 - T2^4)
        # at the fixed point, keeps A an M-matrix, and is stable
        # at a magnitude an explicit source would oscillate at.
        # ==================================================
        p_rad_cells = radiating_partial_pressure(
            m_CO2_gas_in + (m_g_out_cells - m_dot_g_in),
            np.full(N, float(m_H2O_gas_in)),
            m_g_out_cells,
        )

        closure = closure_at(
            Tg_iter,
            Ts_iter,
            Tw_iter,
            m_g_out_cells,
            p_rad_cells,
        )

        K_gs = closure["K_gs"]
        K_gw = closure["K_gw"]
        K_ws = closure["K_ws"]

        # ==================================================
        # SHELL LOSS RESISTANCE AT THE CURRENT HOT FACE
        # ==================================================

        R_total, T_shell, shell_info = shell_closure(
            Tw_iter,
            transition.shell,
            transition.T_amb,
            T_shell_guess=T_shell,
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

            # Faz 5: radiation lives inside K now.
            radiation_gas_sink = 0.0

            # Gas cell i sits at flow position p = N-1-i, so its
            # inflow face is Dg_face[p] and its outflow face
            # Dg_face[p+1].
            p_gas = N - 1 - i

            row = gas_phase.apply_gas_energy_balance(
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
                K_gs[i],
                K_gw[i],
                radiation_gas_sink,
                Tg_in,
                Dg_face[p_gas],
                Dg_face[p_gas + 1],
            )

            # ==================================================
            # SOLID ENERGY BALANCE
            # ==================================================

            radiation_solid_source = 0.0

            row = solid_phase.apply_solid_energy_balance(
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
                K_gs[i],
                K_ws[i],
                radiation_solid_source,
                Q_calcination_cells[i],
                Ts_in,
                Ds_face[i],
                Ds_face[i + 1],
            )

            # ==================================================
            # WALL ENERGY BALANCE
            # ==================================================

            A[row, Tg_i] += (
                V_cell * K_gw[i]
            )

            A[row, Ts_i] += (
                V_cell * K_ws[i]
            )

            A[row, Tw_i] += (
                -V_cell * K_gw[i]
                -V_cell * K_ws[i]
                -1.0 / R_total[i]
            )

            # --------------------------------------------------
            # WALL RADIATION SOURCE
            # --------------------------------------------------

            radiation_wall_source = 0.0

            b[row] = (
                -transition.T_amb / R_total[i]
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
    # MECHANISM SPLIT AT THE SOLUTION
    #
    # Re-evaluated at the converged field and split with the SAME
    # conductances the matrix used, so a diagnostic reads the
    # model's own numbers rather than a parallel calculation.
    # ======================================================
    closure_ss = closure_at(
        Tg_ss,
        Ts_ss,
        Tw_ss,
        m_g_out_cells,
        p_rad_cells,
    )

    # The loss network re-closed on the CONVERGED hot face, so
    # the reported wall loss does not carry the Picard gap.
    R_total, T_shell, shell_info = shell_closure(
        Tw_ss,
        transition.shell,
        transition.T_amb,
        T_shell_guess=T_shell,
    )

    K_gs = closure_ss["K_gs"]
    K_gw = closure_ss["K_gw"]
    K_ws = closure_ss["K_ws"]

    q_gs_rad = closure_ss["K_gs_rad"] * (Tg_ss - Ts_ss)
    q_gw_rad = closure_ss["K_gw_rad"] * (Tg_ss - Tw_ss)
    q_ws_rad = closure_ss["K_ws_rad"] * (Ts_ss - Tw_ss)

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

    q_gs_conv = closure_ss["K_gs_conv"] * (Tg_ss - Ts_ss)
    q_gw_conv = closure_ss["K_gw_conv"] * (Tg_ss - Tw_ss)

    # Contact, not convection: the covered wall touches the bed.
    q_ws_conv = closure_ss["K_ws_cont"] * (Ts_ss - Tw_ss)

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

        # Faz 6: R_ref / R_conv are gone -- the stack has more
        # than one conduction layer now, and the external film is
        # not a constant, so neither name meant anything. What
        # replaces them is the cylindrical conduction resistance
        # of the whole stack and the solved external film.
        "R_cond": float(
            shell_info["R_cond"]
        ),

        "R_ext": float(
            shell_info["R_ext_mean"]
        ),

        "R_total": float(
            np.mean(R_total)
        ),

        "h_ext": float(
            shell_info["h_ext_mean"]
        ),

        "T_shell_mean": float(
            shell_info["T_shell_mean"]
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

    # Outlet values are read at the outlet FACE, not at the
    # last cell CENTRE: these are the reconstructed values the
    # second-order fluxes actually transport out of the end
    # cells, and the same ones gas_phase.gas_enthalpy_out()
    # and solid_phase.solid_enthalpy_out() hand to the next
    # unit. Reading the centres here would leak exactly that
    # difference out of this balance.
    #
    # The flow multiplying each face is the flow that face
    # actually carries, taken from the converged calcination
    # march: the solid discharges what is left after every cell
    # has calcined, the gas discharges what it arrived with
    # plus all the CO2. Using one scalar for both ends was what
    # rescaled temperature across the handoff.

    dm_gas_final = (
        m_dot_CaCO3_reacted_cells
        * transition.chemistry.CO2_ratio
    )

    m_s_out_face = (
        m_dot_s_in
        - float(np.sum(dm_gas_final))
    )

    m_g_out_face = (
        m_dot_g_in
        + float(np.sum(dm_gas_final))
    )

    Ts_out_face = outlet_face_value(
        Ts_ss,
        reverse=False,
    )

    h_gas_out_face = outlet_face_value(
        h_gas(
            Tg_ss,
            T_ref
        ),
        reverse=True,
    )

    Hg_out = (
        m_g_out_face
        * h_gas_out_face
    )

    Hs_out = (
        m_s_out_face
        * Cp_s
        * (
            Ts_out_face
            - T_ref
        )
    )

    # Published so Transition.apply() hands downstream exactly
    # the flux this balance booked, rather than re-deriving it
    # from a cell-centre array and a scalar flow.
    state.Hsolid_transition_out = float(Hs_out)
    state.Hgas_transition_out = float(Hg_out)
    state.m_dot_s_transition_out = float(m_s_out_face)
    state.m_dot_g_transition_out = float(m_g_out_face)

    # Per-cell flows at the converged state, so anything
    # building an enthalpy array from the temperature profile
    # multiplies each cell by the flow that cell carries.
    state.m_dot_s_transition_cells = (
        m_dot_s_in
        - np.cumsum(dm_gas_final)
    )

    state.m_dot_g_transition_cells = (
        m_dot_g_in
        + np.cumsum(dm_gas_final[::-1])[::-1]
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

    # ======================================================
    # FAZ 5 CLOSURE STATE (DIAGNOSTIC)
    #
    # Same names, same meaning, same sign convention as the burning
    # zone publishes, so D4 and D8 can read both zones through one
    # code path instead of special-casing each.
    #
    #   Qgs_cells > 0  gas   -> solid
    #   Qgw_cells > 0  gas   -> wall
    #   Qws_cells > 0  solid -> wall
    # ======================================================
    state.Transition_Qgs_conv_cells = V_cell * q_gs_conv
    state.Transition_Qgw_conv_cells = V_cell * q_gw_conv
    state.Transition_Qws_conv_cells = V_cell * q_ws_conv

    state.Transition_Qgs_rad_cells = V_cell * q_gs_rad
    state.Transition_Qgw_rad_cells = V_cell * q_gw_rad
    state.Transition_Qws_rad_cells = V_cell * q_ws_rad

    state.Transition_Qgs_cells = V_cell * q_gs_cell
    state.Transition_Qgw_cells = V_cell * q_gw_cell
    state.Transition_Qws_cells = V_cell * q_ws_cell

    state.Transition_Qloss_cells = Q_loss_cell

    state.Transition_K_gs_cells = K_gs
    state.Transition_K_gw_cells = K_gw
    state.Transition_K_ws_cells = K_ws

    state.Transition_K_gs = float(np.mean(K_gs))
    state.Transition_K_gw = float(np.mean(K_gw))
    state.Transition_K_ws = float(np.mean(K_ws))

    state.Transition_a_gs = float(a_gs)
    state.Transition_a_gw = float(a_gw)
    state.Transition_a_ws = float(a_ws)

    state.Transition_V_cell = float(V_cell)

    # Faz 6 shell state, published rather than reconstructed.
    state.Transition_R_total_cells = np.asarray(R_total, dtype=float)
    state.Transition_R_total = float(np.mean(R_total))

    state.Transition_T_shell_cells = np.asarray(T_shell, dtype=float)
    state.Transition_T_shell_max = float(np.max(T_shell))
    state.Transition_shell_h_ext = float(shell_info["h_ext_mean"])
    state.Transition_shell_h_conv = float(shell_info["h_conv_mean"])
    state.Transition_shell_h_rad = float(shell_info["h_rad_mean"])
    state.Transition_shell_flux = float(shell_info["flux_outer_mean"])
    state.Transition_shell_R_cond = float(shell_info["R_cond"])

    state.Transition_D_e = float(D_e)
    state.Transition_bed_angle = float(bed_angle)
    state.Transition_bed_fill_fraction = float(bed_fill_fraction)
    state.Transition_mean_beam_length = float(closure_ss["L_m"])
    state.Transition_eps_gas_cells = closure_ss["eps_gas"]
    state.Transition_p_rad_cells = p_rad_cells
    state.Transition_h_conv_gs_cells = closure_ss["h_conv_gs"]
    state.Transition_h_rad_gs_cells = closure_ss["h_rad_gs"]
    state.Transition_h_conv_gw_cells = closure_ss["h_conv_gw"]
    state.Transition_h_rad_gw_cells = closure_ss["h_rad_gw"]
    state.Transition_h_cont_ws_cells = closure_ss["h_cont_ws"]
    state.Transition_h_rad_sw_cells = closure_ss["h_rad_sw"]

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
