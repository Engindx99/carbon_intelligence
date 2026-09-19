import numpy as np

from physics.physics import bed_segment_geometry
from physics.kiln_closures import fuel_combustion_products
from physics.kiln_closures import kiln_transfer_coefficients
from physics.kiln_closures import radiating_partial_pressure
from physics.physics import cp_gas, h_gas
from physics.physics import fill_fraction_from_holdup
from physics.physics import outlet_face_value
from physics.physics import second_order_upwind_correction
from physics.physics import second_order_upwind_face_corrections
from physics.variable_flow_rows import apply_gas_energy_balance
from physics.variable_flow_rows import apply_solid_energy_balance
from physics.physics import T_gas_from_h
from physics.shell import shell_closure

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

    # m_dot_g is calculated centrally in main.py. It is the gas
    # ENTERING the kiln -- burner air plus fuel -- and the stream
    # grows along the zone, because the meal arrives still partly
    # carbonated and finishes calcining here.
    m_dot_g_in = state.m_dot_g

    # The bed ENTERS with what the transition discharged. It is
    # not state.m_dot_s: that is the clinker, i.e. the outlet.
    m_dot_s_in = float(
        getattr(
            state,
            "m_dot_s_burning_in",
            state.m_dot_s,
        )
    )

    Cp_s = burning.Cp_s

    # ======================================================
    # GEOMETRY
    # ======================================================

    N = len(Tg)
    V_cell = burning.V_cell

    # ======================================================
    # PER-CELL STREAM FLOWS
    #
    # Same treatment the transition (Faz 1b) and the calciner
    # (Faz 1c) already carry, for the same reason: a stream that
    # loses mass as it goes has no single flow, and using one --
    # at the outlet, the INLET value -- conserves J/s while
    # rescaling K across the handoff.
    # ======================================================

    dm_gas_cells = np.asarray(
        getattr(
            state,
            "m_dot_CO2_generated_burning_cells",
            np.zeros(N),
        ),
        dtype=float,
    )

    if dm_gas_cells.size != N:
        dm_gas_cells = np.zeros(N)

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

    # Suffix sum: cell i's outgoing gas carries the CO2 of every
    # cell from i to N-1 inclusive.
    m_g_out_cells = (
        m_dot_g_in
        + np.cumsum(dm_gas_cells[::-1])[::-1]
    )

    m_g_in_cells = (
        m_g_out_cells
        - dm_gas_cells
    )

    # ======================================================
    # HEAT TRANSFER PARAMETERS
    # ======================================================

    # ======================================================
    # INTERFACIAL AREAS FROM THE BED CROSS-SECTION
    #
    # The bed occupies a circular segment of the kiln bore, so
    # the three exchange areas follow from how much material is
    # actually in the kiln: the gas sees the bed across its top
    # chord, the covered arc carries wall->bed contact, and the
    # remaining exposed arc carries gas->wall. The fill fraction
    # itself comes from steady-state mass continuity,
    # m_dot_s = rho_bulk * u_s * A_bed.
    #
    # This replaces burning.a_gs / a_ws / a_gw, which came from
    # interfacial_areas() -- the packed-bed specific-surface
    # correlation 6(1-eps)/d_p with the 4.2 m kiln bore
    # substituted for the particle diameter. That form never saw
    # the fill fraction, so it was a constant fixed at __init__
    # and the heat transfer could not respond to kiln loading.
    # It also double-counted the wall: a_gw was the full
    # perimeter 4/D while a_ws was charged on top of it, for
    # 1.51 m2/m3 against a physical ceiling of 4/D = 0.95.
    # bed_segment_geometry splits the perimeter exactly, so
    # a_ws + a_gw == 4/D holds by construction.
    #
    # Computed once per thermal_step, outside the Picard loop:
    # m_dot_s and u_s are set by the outer loop and are constant
    # within one Picard sweep, so re-deriving them per iteration
    # would only add cost and a path to oscillation.
    #
    # D_e (gas-side hydraulic diameter) is returned but not used
    # yet -- it is the length scale for the Reynolds number once
    # hv_gs stops being a constant.
    # ======================================================

    # Same quantity solid_phase.resolve_solid_motion already solved
    # alongside the transit time, recomputed here from the u_s it
    # handed down rather than read back off state, so the areas follow
    # whatever u_s this call is actually given. Both go through the
    # identical continuity expression, so they agree to machine
    # precision.
    bed_fill_fraction = fill_fraction_from_holdup(
        # The clinker flow, i.e. the bed at the DISCHARGE end.
        # The bed is heavier at the feed end now that it calcines
        # along the zone, so a single fill fraction is an
        # approximation -- but it is the same one this closure
        # always made, kept unchanged here so Faz 4 does not
        # silently move the area closure as well. Making the
        # areas follow the per-cell holdup belongs with Faz 3.
        m_dot_s=state.m_dot_s,
        rho_bulk=burning.rho_s,
        u_s=u_s,
        A_cross=burning.A_cross,
    )

    # The geometry is still resolved here, outside the Picard loop,
    # because it depends only on the fill fraction. Faz 5 keeps the
    # split areas and adds D_e, which is no longer "returned but not
    # used": it is the length scale of both Reynolds numbers and,
    # through L_m = 0.9 D_e, of the gas emissivity.
    (
        bed_angle,
        a_gs,
        a_ws,
        a_gw,
        D_e,
    ) = bed_segment_geometry(
        burning.D,
        bed_fill_fraction,
    )

    # ======================================================
    # RADIATING GAS COMPOSITION
    #
    # Only CO2 and H2O radiate. In this zone the gas enters at the
    # burner as combustion products and picks up the bed's
    # calcination CO2 on the way to the kiln inlet, so the radiating
    # mass is per-cell even though the fuel term is not.
    #
    # m_g_out_cells was already built as a suffix sum of dm_gas_cells
    # on top of m_dot_g_in, and every kilogram of that suffix sum is
    # calcination CO2 -- so the CO2 a cell's gas carries is the
    # fuel's CO2 plus exactly that increment. No new bookkeeping.
    # ======================================================
    m_dot_fuel_kiln = (
        burning.kiln_fuel_fraction
        * inputs.get("Fuel_rate_total", 0.0)
    )

    (
        m_CO2_fuel,
        m_H2O_fuel,
    ) = fuel_combustion_products(m_dot_fuel_kiln)

    m_CO2_gas_cells = (
        m_CO2_fuel
        + (m_g_out_cells - m_dot_g_in)
    )

    p_rad_cells = radiating_partial_pressure(
        m_CO2_gas_cells,
        np.full(N, float(m_H2O_fuel)),
        m_g_out_cells,
    )

    # ======================================================
    # FAZ 5 CLOSURE, EVALUATED PER PICARD ITERATE
    #
    # K_gs / K_gw / K_ws used to be three scalars formed once from
    # three literal constants. They are now per-cell arrays rebuilt
    # inside the loop from the current temperatures, because every
    # term in them moves with temperature: the Nusselt numbers
    # through the gas properties, the gas emissivity through T, and
    # the radiation coefficients through T^3.
    #
    # Radiation is now INSIDE K rather than an explicit source in b.
    # That is deliberate. It is ~80x larger than the k_eff = 0.005
    # version it replaces, and an explicit source of that size
    # oscillates; linearised into the matrix it is unconditionally
    # stable, keeps A an M-matrix (every h_rad >= 0), and is exact at
    # the fixed point because h_rad (T1 - T2) == eps sigma
    # (T1^4 - T2^4) identically.
    # ======================================================
    def closure_at(Tg_at, Ts_at, Tw_at):

        return kiln_transfer_coefficients(
            Tg=Tg_at,
            Ts=Ts_at,
            Tw=Tw_at,
            D=burning.D,
            fill_fraction=bed_fill_fraction,
            rpm=burning.rpm_default,
            m_dot_gas=m_g_out_cells,
            p_rad=p_rad_cells,
            eps_bed=burning.closure.bed_emissivity,
            eps_wall=burning.closure.wall_emissivity,
            bed_conductivity=burning.closure.bed_conductivity,
            bed_density=burning.rho_s,
            bed_cp=burning.Cp_s,
            particle_diameter=burning.closure.particle_diameter,
            contact_chi=burning.closure.contact_chi,
        )

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
    #
    # The clinkering reactions (C2S/C3S/C3A/C4AF) run in the
    # bed, so their enthalpy is drawn from the solid phase --
    # the same way the calciner and the transition zone draw
    # calcination heat from their solid rows. It used to be
    # subtracted from the gas row here, which left the bed
    # temperature unaffected by the reactions consuming its
    # energy.
    #
    # The per-cell profile is the kinetic one built by
    # ChemistryModel.apply_burning (cell by cell, from the
    # local Ts), not the flame shape. Its sum equals the
    # scalar Burning_Q_sink to machine precision, because
    # both accumulate the identical per-reaction terms.
    # ======================================================

    reaction_q_cell = np.asarray(
        state.Burning_Q_sink_cells,
        dtype=float,
    )

    if reaction_q_cell.size != N:

        raise ValueError(
            "state.Burning_Q_sink_cells has length "
            f"{reaction_q_cell.size}, expected N={N}"
        )

    # ======================================================
    # AXIAL COMBUSTION HEAT DISTRIBUTION
    # ======================================================

    q_cell = combustion.axial_heat_distribution(
        N,
        Q_burning,
    )

    # ======================================================
    # WALL THERMAL RESISTANCE
    #
    # Faz 6: no longer a constant. R_total now closes on the
    # SHELL temperature -- cylindrical series conduction through
    # the layer stack, then natural convection plus radiation off
    # the steel skin -- so it is solved inside the Picard loop
    # from the current hot-face iterate, exactly like the K_gw /
    # K_ws coefficients above. The array below is only the
    # starting value for the first pass; it is overwritten every
    # iteration and is exact at the fixed point.
    # ======================================================

    R_total, T_shell, shell_info = shell_closure(
        np.asarray(Tw, dtype=float),
        burning.shell,
        burning.T_amb,
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
    iterations_to_tol = None

    for iteration in range(max_iter):

        # ==================================================
        # GAS PROPERTIES AT CURRENT ITERATE
        # ==================================================

        Cp_g_iter = cp_gas(Tg_iter)

        # ==================================================
        # RADIATION
        # ==================================================

        closure = closure_at(Tg_iter, Ts_iter, Tw_iter)

        K_gs = closure["K_gs"]
        K_gw = closure["K_gw"]
        K_ws = closure["K_ws"]

        # ==================================================
        # SHELL LOSS RESISTANCE AT THE CURRENT HOT FACE
        #
        # Seeded with the previous pass's shell field, so the
        # inner solve converges in two or three passes instead
        # of eight.
        # ==================================================

        R_total, T_shell, shell_info = shell_closure(
            Tw_iter,
            burning.shell,
            burning.T_amb,
            T_shell_guess=T_shell,
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

        # Per FACE, not pre-differenced: each face of a cell
        # carries a different mass flow once the bed calcines,
        # so the two corrections cannot be collapsed into one
        # per-cell term. Both arrays are in FLOW order with N+1
        # entries.
        Dg_face = second_order_upwind_face_corrections(
            h_gas(Tg_iter, T_ref),
            h_gas_in,
            reverse=True,
        )

        Ds_face = second_order_upwind_face_corrections(
            Ts_iter,
            state.Ts_burning_in,
            reverse=False,
        )

        # h_gas(Ts) for the CO2 leaving the bed, linearised at
        # the current iterate exactly as the gas row linearises
        # its own enthalpy. Both phases carry this term with
        # opposite signs, so it cancels over the zone.
        cp_gas_s_cells = cp_gas(Ts_iter)

        h_const_s_cells = (
            h_gas(Ts_iter, T_ref)
            - cp_gas_s_cells * Ts_iter
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

            # Faz 5: radiation is carried implicitly inside
            # K_gs / K_gw, so there is no explicit radiative
            # source left on any row. The parameter stays in the
            # shared builder because the calciner -- which is not
            # a rotating cylinder and keeps the old closure --
            # still uses it.
            radiation_gas_sink = 0.0

            # Gas cell i sits at flow position p = N-1-i, so
            # its inflow face is Dg_face[p] and its outflow
            # face Dg_face[p+1].
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
                K_gs[i],
                K_gw[i],
                radiation_gas_sink,
                state.Tg_burning_in,
                Dg_face[p_gas],
                Dg_face[p_gas + 1],
            )

            # The burner's heat is a source on the gas row. The
            # shared builder is used by zones that do not fire,
            # so the term is added here rather than passed in.
            b[row - 1] += q_cell[i]

            # ==================================================
            # SOLID ENERGY BALANCE
            # ==================================================

            radiation_solid_source = 0.0

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
                K_gs[i],
                K_ws[i],
                radiation_solid_source,
                reaction_q_cell[i],
                state.Ts_burning_in,
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

            # Faz 5: the wall's radiative gains are inside
            # K_gw and K_ws now, so the only explicit term left
            # on this row is the ambient loss.
            b[row] = -burning.T_amb / R_total[i]

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
        # CONVERGENCE MEASUREMENT (DIAGNOSTIC, NON-BINDING)
        #
        # tol/converged/error were assigned here and never
        # read, so the loop has always run all max_iter passes
        # and no convergence was ever verified. They are now
        # measured and reported.
        #
        # Deliberately NO break: stopping early would change
        # the answer at the 1e-7 level and this instrumentation
        # increment must leave the solution bit-identical.
        # Wiring the break is a separate, later change.
        # ==================================================

        error = max(
            float(np.max(np.abs(Tg_new - Tg_iter))),
            float(np.max(np.abs(Ts_new - Ts_iter))),
            float(np.max(np.abs(Tw_new - Tw_iter))),
        )

        if not converged and error < tol:

            converged = True
            iterations_to_tol = iteration + 1

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

    # ======================================================
    # MECHANISM SPLIT AT THE SOLUTION
    #
    # Re-evaluated at the converged temperatures rather than
    # reusing the last iterate, and split with the SAME
    # conductances the matrix was assembled from, so D4 reports
    # the model's own numbers instead of a parallel calculation.
    #
    # Note which area each piece is charged on: the solid <-> wall
    # path is contact over the covered arc a_ws PLUS radiation
    # across the bed surface a_gs. Those are different areas, which
    # is precisely why they cannot share one lumped hv_ws.
    # ======================================================
    closure_ss = closure_at(Tg_ss, Ts_ss, Tw_ss)

    K_gs = closure_ss["K_gs"]
    K_gw = closure_ss["K_gw"]
    K_ws = closure_ss["K_ws"]

    # Same re-evaluation for the loss network: the shell closes
    # on the CONVERGED hot face, not on the last iterate that
    # built the matrix. At the fixed point the two agree; making
    # the reported loss read the converged state is what keeps
    # the energy balance below from carrying the Picard gap.
    R_total, T_shell, shell_info = shell_closure(
        Tw_ss,
        burning.shell,
        burning.T_amb,
        T_shell_guess=T_shell,
    )

    dT_gs = Tg_ss - Ts_ss
    dT_gw = Tg_ss - Tw_ss
    dT_ws = Ts_ss - Tw_ss

    Qgs_conv = V_cell * closure_ss["K_gs_conv"] * dT_gs
    Qgs_rad = V_cell * closure_ss["K_gs_rad"] * dT_gs

    Qgw_conv = V_cell * closure_ss["K_gw_conv"] * dT_gw
    Qgw_rad = V_cell * closure_ss["K_gw_rad"] * dT_gw

    # "conv" on this pair is CONTACT, not convection: the covered
    # wall touches the bed, it does not blow past it.
    Qws_conv = V_cell * closure_ss["K_ws_cont"] * dT_ws
    Qws_rad = V_cell * closure_ss["K_ws_rad"] * dT_ws

    Qgs = np.sum(Qgs_conv + Qgs_rad)
    Qgw = np.sum(Qgw_conv + Qgw_rad)
    Qws = np.sum(Qws_conv + Qws_rad)

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

    # Each end carries the flow that end actually has: the kiln
    # gas arrives as burner air plus fuel and leaves with the
    # calcination CO2 on top.
    Hg_in = (
        m_dot_g_in
        * h_gas(
            Tg_in,
            T_ref
        )
    )

    m_g_out_face = (
        m_dot_g_in
        + float(np.sum(dm_gas_cells))
    )

    # Taken from the reconstructed face enthalpy directly
    # rather than from h_gas(Tg_out): the two agree only to
    # the inversion tolerance of T_gas_from_h, and this is the
    # quantity the flux and the handoff both use.
    Hg_out = (
        m_g_out_face
        * h_gas_out_face
    )

    gas_energy_change = (
        Hg_out
        - Hg_in
    )

    # Energy carried across the phase boundary by the CO2, at
    # the bed temperature it left. A SOURCE for the gas and a
    # SINK of the same size for the solid, so it cancels in the
    # zone total and appears only in these two per-phase checks.
    H_phase_change = float(
        np.sum(
            dm_gas_cells
            * h_gas(
                Ts_ss,
                T_ref,
            )
        )
    )

    gas_expected = (
        Q_burning
        - Qgs
        - Qgw
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
            Ts_in - T_ref
        )
    )

    # The bed discharges what is left after every cell has
    # finished calcining.
    m_s_out_face = (
        m_dot_s_in
        - float(np.sum(dm_gas_cells))
    )

    Hs_out = (
        m_s_out_face
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
        - H_phase_change
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


    # ======================================================
    # PER-CELL MECHANISM SPLIT (DIAGNOSTIC)
    #
    # These six per-cell arrays were already being computed
    # here, one cell at a time, and then thrown away. They are
    # now published on state so the mechanism split can be
    # read without re-deriving it outside the solver.
    #
    # This block is pure bookkeeping: every term is built from
    # the already-converged Tg_ss/Ts_ss/Tw_ss and the same
    # K_* / q_*_rad_final used by the balance above, so it
    # cannot change the solution. The loop it replaces is the
    # vectorised form of the identical arithmetic.
    #
    # Sign convention, per cell, in W:
    #   Qgs_cells > 0  gas   -> solid
    #   Qgw_cells > 0  gas   -> wall
    #   Qws_cells > 0  solid -> wall
    #   Qloss_cells    wall  -> ambient (always >= 0 here)
    # ======================================================

    Qgs_rad_cells = Qgs_rad
    Qgw_rad_cells = Qgw_rad
    Qws_rad_cells = Qws_rad

    state.Burning_Qgs_conv_cells = Qgs_conv
    state.Burning_Qgw_conv_cells = Qgw_conv
    state.Burning_Qws_conv_cells = Qws_conv

    state.Burning_Qgs_rad_cells = Qgs_rad_cells
    state.Burning_Qgw_rad_cells = Qgw_rad_cells
    state.Burning_Qws_rad_cells = Qws_rad_cells

    state.Burning_Qgs_cells = Qgs_conv + Qgs_rad_cells
    state.Burning_Qgw_cells = Qgw_conv + Qgw_rad_cells
    state.Burning_Qws_cells = Qws_conv + Qws_rad_cells

    state.Burning_Qloss_cells = (
        Tw_ss - burning.T_amb
    ) / R_total

    state.Burning_q_fuel_cells = q_cell
    state.Burning_q_reaction_cells = reaction_q_cell

    # Energy the CO2 carries from the bed into the gas, at the
    # bed temperature it left. Published because the gas balance
    # is no longer closed by the fuel and the two transfer terms
    # alone: anything reconstructing it from the per-cell arrays
    # needs this term, and must read the SAME number the balance
    # used rather than recompute it.
    state.Burning_H_phase_change = H_phase_change

    # ======================================================
    # CLOSURE STATE (DIAGNOSTIC)
    #
    # The volumetric conductances and the interfacial area
    # densities that produced the split above. Published so
    # NTU and the wall-area identity a_ws + a_gw == 4/D can be
    # checked against the values the solver actually used,
    # rather than recomputed from config and assumed equal.
    # ======================================================

    # Per-cell now: Faz 5 made every conductance a function of the
    # local temperature, so a single float would be a zone average
    # masquerading as a coefficient. Diagnostics that want one number
    # take the mean explicitly.
    state.Burning_K_gs_cells = K_gs
    state.Burning_K_gw_cells = K_gw
    state.Burning_K_ws_cells = K_ws

    state.Burning_K_gs = float(np.mean(K_gs))
    state.Burning_K_gw = float(np.mean(K_gw))
    state.Burning_K_ws = float(np.mean(K_ws))

    state.Burning_a_gs = float(a_gs)
    state.Burning_a_gw = float(a_gw)
    state.Burning_a_ws = float(a_ws)

    # Faz 5 closure detail, for D4 and for the report.
    state.Burning_D_e = float(D_e)
    state.Burning_bed_angle = float(bed_angle)
    state.Burning_mean_beam_length = float(closure_ss["L_m"])
    state.Burning_eps_gas_cells = closure_ss["eps_gas"]
    state.Burning_p_rad_cells = p_rad_cells

    # Radiating species handed on to the transition zone. The gas
    # leaves at cell 0 (it flows N-1 -> 0), so that cell's outgoing
    # gas is what crosses the boundary. Published rather than
    # re-derived downstream so the two zones cannot disagree about
    # what is in the same stream.
    state.Burning_m_dot_CO2_gas_out = float(m_CO2_gas_cells[0])
    state.Burning_m_dot_H2O_gas_out = float(m_H2O_fuel)
    state.Burning_h_conv_gs_cells = closure_ss["h_conv_gs"]
    state.Burning_h_rad_gs_cells = closure_ss["h_rad_gs"]
    state.Burning_h_conv_gw_cells = closure_ss["h_conv_gw"]
    state.Burning_h_rad_gw_cells = closure_ss["h_rad_gw"]
    state.Burning_h_cont_ws_cells = closure_ss["h_cont_ws"]
    state.Burning_h_rad_sw_cells = closure_ss["h_rad_sw"]

    state.Burning_V_cell = float(V_cell)

    # ======================================================
    # SHELL STATE (Faz 6)
    #
    # The shell temperature is PUBLISHED, not left for a reader
    # to rebuild. D2 used to reconstruct it from a plane-wall
    # resistance ratio of its own making, which is how it came to
    # report 868 K for a wall the solver was running at 550 K.
    # R_total is per cell now, so the scalar below is an explicit
    # mean rather than a coefficient pretending to be one.
    # ======================================================
    state.Burning_R_total_cells = np.asarray(R_total, dtype=float)
    state.Burning_R_total = float(np.mean(R_total))

    state.Burning_T_shell_cells = np.asarray(T_shell, dtype=float)
    state.Burning_T_shell_max = float(np.max(T_shell))
    state.Burning_shell_h_ext = float(shell_info["h_ext_mean"])
    state.Burning_shell_h_conv = float(shell_info["h_conv_mean"])
    state.Burning_shell_h_rad = float(shell_info["h_rad_mean"])
    state.Burning_shell_flux = float(shell_info["flux_outer_mean"])
    state.Burning_shell_R_cond = float(shell_info["R_cond"])

    # Picard convergence, measured not enforced (see the loop).
    state.Burning_picard_max_iter = int(max_iter)
    state.Burning_picard_tol = float(tol)
    state.Burning_picard_error = float(error)
    state.Burning_picard_converged = bool(converged)
    state.Burning_picard_iterations_to_tol = iterations_to_tol

    # Capacity rates, for NTU. The gas side is evaluated at the
    # converged profile rather than at a single temperature,
    # since cp_gas varies by ~25% across this zone.
    state.Burning_C_solid = float(m_s_out_face * Cp_s)
    state.Burning_C_gas_cells = m_g_out_cells * cp_gas(Tg_ss)

    # ======================================================
    # HANDOFF FLUXES AND PER-CELL FLOWS
    #
    # Published here so Burning.apply() hands the cooler
    # exactly the flux this balance booked. Extrapolating the
    # product of two varying profiles is not the product of
    # their extrapolations, so re-deriving it from a cell-centre
    # array and a scalar flow would give a different number.
    # ======================================================

    state.Hgas_burning_out = float(Hg_out)
    state.Hsolid_burning_out = float(Hs_out)

    state.m_dot_s_burning_out = float(m_s_out_face)
    state.m_dot_g_burning_out = float(m_g_out_face)

    state.m_dot_s_burning_cells = m_s_out_cells.copy()
    state.m_dot_g_burning_cells = m_g_out_cells.copy()

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
