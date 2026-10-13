import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import h_solid
from physics.physics import outlet_face_value
from physics.physics import radiation
from physics.physics import second_order_upwind_correction
from physics.physics import second_order_upwind_face_corrections
from physics.physics import T_gas_from_h
from physics.gas_thermo import CO2_GAS
from physics.gas_thermo import GasMixture
from physics.gas_thermo import cell_species
from pyroprocess.precalciner.raw_meal_inlet import calciner_inlet_species
from physics.physics import T_solid_from_h
from physics.kiln_closures import suspension_gas_solid_coefficient
from physics.shell import shell_closure
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
    reaction_heat_slope_cells=None,
    q_fuel_cells=None,
    Q_calciner=0.0,
    dm_gas_cells=None,
    tol=1e-6,
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
    # CO-CURRENT: the riser carries meal and gas up together, so
    # both run 0 -> N-1 (bottom to top), entering at the bottom
    # and leaving together for the cyclone above. It used to run
    # the gas N-1 -> 0, counter-current like the kiln: with the
    # suspension's NTU of hundreds that made the riser a perfect
    # counter-current exchanger, the gas leaving at the cold meal
    # inlet at 1033 K where an ILC calciner's gas and meal leave
    # together at ~1150 K (MEASURED 13 Oct 2026).
    #
    # The solid loses dm_gas in each cell and the gas gains it.
    # Both are cumulative sums of the same array, so what leaves
    # one phase is what joins the other, cell for cell.
    #
    # The gas INLET flow is derived as the zone outlet minus
    # everything the bed adds, rather than being reassembled from
    # the transition gas, tertiary air and fuel. That keeps this
    # identical to the scalar chain in physics.steady_state_mass
    # by construction, so the two accountings cannot drift.
    # ======================================================

    # The bed's inlet enthalpy [J/kg]: the inlet face of the
    # solid row (Ts_in is its inverse).
    hs_in = h_solid(Ts_in, T_ref)

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

    # Prefix sum: cell i's outgoing gas carries the mass released
    # by every cell from 0 to i inclusive.
    m_g_out_cells = (
        m_dot_g_in
        + np.cumsum(dm_gas_cells)
    )

    m_g_in_cells = (
        m_g_out_cells
        - dm_gas_cells
    )

    # The gas's COMPOSITION along the riser (physics.gas_thermo).
    # dm_gas_cells is calcination CO2 plus dehydroxylation water
    # (Calciner.apply); the water is the published per-cell H2O,
    # the CO2 the rest. Fixed for this thermal step, so the
    # mixtures are built once.
    dm_H2O_cells = np.asarray(
        getattr(state, "m_dot_H2O_generated_cells", np.zeros(N)),
        dtype=float,
    )
    if dm_H2O_cells.size != N:
        dm_H2O_cells = np.zeros(N)
    dm_H2O_cells = np.minimum(np.maximum(dm_H2O_cells, 0.0), dm_gas_cells)
    dm_CO2_cells = dm_gas_cells - dm_H2O_cells

    released_cells = [
        {"CO2": float(c), "H2O": float(w)}
        for c, w in zip(dm_CO2_cells, dm_H2O_cells)
    ]

    species_in = calciner_inlet_species(state)
    species_cells = cell_species(species_in, released_cells, reverse=False)
    gas_in = GasMixture(species_in)
    gas_cells = [GasMixture(s) for s in species_cells]

    # What each cell's bed releases, as a gas of its own.
    released_gas = [
        GasMixture(r) if r["CO2"] + r["H2O"] > 0.0 else CO2_GAS
        for r in released_cells
    ]

    def h_gas_cells(Tg_cells):
        return np.array(
            [g.h(float(T), T_ref) for g, T in zip(gas_cells, Tg_cells)]
        )

    def h_released_cells(Ts_cells):
        return np.array(
            [g.h(float(T), T_ref) for g, T in zip(released_gas, Ts_cells)]
        )

    V_cell = calciner.V_cell

    V_cell = calciner.V_cell

    # ======================================================
    # HEAT TRANSFER PARAMETERS
    # ======================================================

    hv_gw = calciner.hv_gw
    hv_ws = calciner.hv_ws

    a_gw = calciner.a_gw
    a_ws = calciner.a_ws

    # Gas -> meal over the SUSPENSION, per cell at the iterate
    # (physics.kiln_closures.suspension_gas_solid_coefficient).
    # It replaces hv_gs times 6 (1 - eps) / D on the 6.74 m bore,
    # the packed-bed formula with the vessel where the particle
    # belongs (tests/test_calciner_conversion_chain.py, Link 2).
    m_s_mean_cells = 0.5 * (m_s_in_cells + m_s_out_cells)
    m_g_mean_cells = 0.5 * (m_g_in_cells + m_g_out_cells)

    def suspension_K_gs(Tg_cells, Ts_cells):

        h, a = suspension_gas_solid_coefficient(
            m_s_mean_cells,
            m_g_mean_cells,
            Tg_cells,
            Ts_cells,
            calciner.particle_diameter,
            calciner.particle_density,
        )

        return h * a, a

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

    # Faz 6: per cell, closed on the casing temperature through
    # the lagged layer stack. Refreshed each Picard pass below;
    # this call only supplies the first one.
    R_total, T_shell, shell_info = shell_closure(
        np.asarray(Tw, dtype=float),
        calciner.shell,
        calciner.T_amb,
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
    # REACTION SLOPE DISTRIBUTION
    #
    # reaction_heat_slope_cells[i] : W/K
    #
    # dQ/dTs for the same cell, which the solid row carries on
    # its diagonal instead of leaving the whole temperature
    # dependence of the sink in b. See
    # physics.variable_flow_rows.apply_solid_energy_balance.
    #
    # The non-negativity check is not defensive book-keeping:
    # a negative slope would REMOVE diagonal dominance rather
    # than add it, turning the stabilisation into its opposite,
    # and it is the one property the whole device rests on.
    # ======================================================

    if reaction_heat_slope_cells is None:

        reaction_heat_slope_cells = np.zeros(N)

    else:

        reaction_heat_slope_cells = np.asarray(
            reaction_heat_slope_cells,
            dtype=float,
        )

        if reaction_heat_slope_cells.shape != (N,):

            raise ValueError(
                "reaction_heat_slope_cells must have "
                f"shape ({N},)."
            )

        if not np.all(
            np.isfinite(
                reaction_heat_slope_cells
            )
        ):

            raise ValueError(
                "reaction_heat_slope_cells contains "
                "non-finite values."
            )

        if np.any(
            reaction_heat_slope_cells < 0.0
        ):

            raise ValueError(
                "reaction_heat_slope_cells cannot "
                "contain negative values."
            )

    # ======================================================
    # PICARD ITERATION
    # ======================================================

    # tol is the caller's: the coupling loop in Calciner.apply
    # loosens it while its own iterate is still far from the
    # fixed point (see there). Default 1e-6 K, as before.
    # Stored energy, dynamic solve only: the wall. The riser's
    # suspension holds its solid for ~3 s and its gas for less,
    # against a step of ~10 s, so both stay quasi-steady.
    transient_dt = getattr(state, "transient_dt", None)

    if transient_dt is None:
        C_w_dt = np.zeros(N)
        Tw_old = np.zeros(N)
    else:
        C_w_dt = np.full(
            N, calciner._rho_wall_Vwall_cell_Cp / transient_dt
        )
        Tw_old = np.asarray(state.Tw_calciner_old, dtype=float)

    max_iter = 100
    relaxation = 0.5

    # Inlet face enthalpy of the incoming gas stream. It is a
    # known handoff, not a reconstruction, so it is the one
    # face that carries no second-order correction.
    h_gas_in = gas_in.h(
        float(Tg_in),
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

    # ======================================================
    # LINEARISATION POINT FOR THE REACTION SINK
    #
    # The temperature the CHEMISTRY was evaluated at, frozen
    # here and not advanced with Ts_iter below.
    #
    # This is the one place the calciner differs from the
    # transition. There the calcination march runs inside this
    # Picard loop, so the sink and the row are built from the
    # same iterate and the linearisation point IS Ts_iter. Here
    # the chemistry runs one level up, in Calciner.apply's outer
    # chemistry<->thermal loop, at the Ts handed to this call.
    #
    # Anchoring the slope there is what makes it damp the OUTER
    # loop, which is where this zone's instability lives: the
    # solve then returns a Ts already corrected for how the
    # reaction would respond to it,
    #
    #   Q_used = Q_chem + S (Ts_new - Ts_chem),
    #
    # a Newton step on the coupling rather than a plain
    # substitution. Using Ts_iter instead would cancel to the
    # un-linearised sink at inner convergence and leave the
    # outer loop exactly as it was.
    #
    # At the OUTER fixed point Ts_new == Ts_chem and the
    # correction vanishes, so the converged answer is untouched.
    # ======================================================

    Ts_reaction = (
        np.asarray(
            Ts,
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
        # SHELL LOSS RESISTANCE AT THE CURRENT HOT FACE
        # ==================================================

        R_total, T_shell, shell_info = shell_closure(
            Tw_iter,
            calciner.shell,
            calciner.T_amb,
            T_shell_guess=T_shell,
        )

        # ==================================================
        # RADIATION
        # ==================================================

        # No gas -> particle radiation on the suspension area: it
        # is bounded by the gas emissivity, not the particle
        # surface (kiln_closures, the suspension closure).
        K_gs_cells, a_gs_cells = suspension_K_gs(Tg_iter, Ts_iter)

        q_gs_rad = np.zeros(N)

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
            h_gas_cells(Tg_iter),
            h_gas_in,
            reverse=False,
        )

        Ds_face = second_order_upwind_face_corrections(
            h_solid(Ts_iter, T_ref),
            hs_in,
            reverse=False,
        )

        # h_gas(Ts) for the CO2 and water leaving the bed,
        # linearised at the current iterate exactly as the gas
        # row linearises its own enthalpy. Both phases see the
        # same term with opposite signs, so it cancels over the
        # zone: the released mass crosses phases at the bed
        # temperature it actually left, creating no energy.
        cp_gas_s_cells = np.array(
            [g.cp(float(T)) for g, T in zip(released_gas, Ts_iter)]
        )

        h_const_s_cells = (
            h_released_cells(Ts_iter)
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
            # Gas direction: 0 ---> N-1, with the solid. The gas
            # GAINS the mass
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

            # Co-current, so gas cell i sits at flow position i:
            # inflow face Dg_face[i], outflow face Dg_face[i+1].
            p_gas = i

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
                K_gs_cells[i],
                K_gw,
                radiation_gas_sink,
                Tg_in,
                Dg_face[p_gas],
                Dg_face[p_gas + 1],
                cocurrent=True,
                gas_i=gas_cells[i],
                gas_up=gas_cells[i - 1] if i > 0 else None,
                gas_in=gas_in,
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
                Ts_iter,
                T_ref,
                m_s_out_cells[i],
                m_s_in_cells[i],
                dm_gas_cells[i],
                cp_gas_s_cells[i],
                h_const_s_cells[i],
                V_cell,
                K_gs_cells[i],
                K_ws,
                radiation_solid_source,
                reaction_heat_cells[i],
                hs_in,
                Ds_face[i],
                Ds_face[i + 1],
                reaction_heat_slope_cells[i],
                Ts_reaction[i],
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
                -1.0 / R_total[i]
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
                / R_total[i]
                - radiation_wall_source
            )

            # Dynamic solve: gains - losses = C/dt (Tw - Tw_old).
            if transient_dt is not None:
                A[row, Tw_i] -= C_w_dt[i]
                b[row] -= C_w_dt[i] * Tw_old[i]

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

    # The loss network re-closed on the CONVERGED hot face, so
    # the wall loss reported below is the one the converged state
    # implies rather than the last iterate's.
    R_total, T_shell, shell_info = shell_closure(
        Tw_ss,
        calciner.shell,
        calciner.T_amb,
        T_shell_guess=T_shell,
    )

    # Faz 6 shell state, published rather than reconstructed by
    # whoever reads it. The calciner runs an OUTER coupling loop
    # over this solver, so these are overwritten each pass and
    # the converged pass is what survives -- the same contract
    # every other field written from here already has.
    state.Calciner_R_total_cells = np.asarray(R_total, dtype=float)
    state.Calciner_R_total = float(np.mean(R_total))

    state.Calciner_T_shell_cells = np.asarray(T_shell, dtype=float)
    state.Calciner_T_shell_max = float(np.max(T_shell))
    state.Calciner_shell_h_ext = float(shell_info["h_ext_mean"])
    state.Calciner_shell_h_conv = float(shell_info["h_conv_mean"])
    state.Calciner_shell_h_rad = float(shell_info["h_rad_mean"])
    state.Calciner_shell_flux = float(shell_info["flux_outer_mean"])
    state.Calciner_shell_R_cond = float(shell_info["R_cond"])

    # ======================================================
    # INLET / OUTLET
    #
    # Gas and solid, co-current:
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
        h_gas_cells(Tg_ss),
        reverse=False,
    )

    # Co-current: the gas leaves through cell N-1's outflow face.
    Tg_out = gas_cells[-1].T_from_h(
        h_gas_out_face,
        T_ref,
        200.0,
        4000.0,
    )

    # The solid likewise, in enthalpy: the face enthalpy is what
    # the scheme transported, and Ts_out its inverse.
    hs_out_face = outlet_face_value(
        h_solid(Ts_ss, T_ref),
        reverse=False,
    )

    Ts_out = T_solid_from_h(hs_out_face, T_ref)

    # The wall does not advect, so it has no outlet face.
    Tw_out = Tw_ss[-1]

    # ======================================================
    # FINAL RADIATION
    # ======================================================

    # The conductance the last sweep's rows were built with, so
    # the reported exchange is the one the balance closed on.
    q_gs_rad_final = np.zeros(N)

    state.Calciner_K_gs_cells = np.asarray(K_gs_cells, dtype=float)
    state.Calciner_a_gs = float(np.mean(a_gs_cells))

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
        * K_gs_cells
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
        * gas_in.h(
            float(Tg_in),
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
            * h_released_cells(Ts_ss)
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

    Hs_in = m_dot_s_in * hs_in

    # The bed discharges what is left after every cell has
    # calcined and dehydroxylated, not what it was fed.
    m_s_out_face = (
        m_dot_s_in
        - float(np.sum(dm_gas_cells))
    )

    Hs_out = m_s_out_face * hs_out_face

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

    # Rate of change of the wall's stored energy; zero when steady.
    Q_stored_wall = float(np.sum(C_w_dt * (Tw_ss - Tw_old)))

    state.Calciner_wall_stored = Q_stored_wall

    total_energy_balance = (
        Hg_in
        + Hs_in
        + Q_calciner
        - Hg_out
        - Hs_out
        - Q_wall_loss
        - reaction_sink
        - Q_stored_wall
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
        + Q_stored_wall
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
    #
    # The outlet face is also C5's: the calciner gas carries
    # the meal up the gooseneck into C5, which drops eta of it
    # into the kiln inlet and lets the rest up with the gas into
    # C4 (Stage 1 of the preheater), whose underflow brings it
    # back here (c5_cyclone). The calciner's own outlet is the
    # whole face; C5 splits it by mass, adiabatically for now
    # (its volume and wall are the next step).
    # ======================================================

    state.Hgas_calciner_out = float(Hg_out)
    state.Hsolid_calciner_out = float(Hs_out)

    state.m_dot_g_calciner_in = float(m_dot_g_in)
    state.m_dot_s_calciner_out = float(m_s_out_face)

    eta_C5 = float(calciner.c5_separation_efficiency)

    # Down into the kiln inlet chamber: the transition's inlet.
    state.Hsolid_C5_underflow = eta_C5 * float(Hs_out)
    state.m_dot_s_C5_underflow = eta_C5 * float(m_s_out_face)

    # Up into C4 with the gas, at the outlet temperature.
    state.Hsolid_C5_dust = float(Hs_out) - state.Hsolid_C5_underflow
    state.m_dot_s_C5_dust = (
        float(m_s_out_face) - state.m_dot_s_C5_underflow
    )

    state.m_dot_s_calciner_cells = m_s_out_cells.copy()
    state.m_dot_g_calciner_cells = m_g_out_cells.copy()

    # The gas's composition per cell and through its outlet face
    # (cell N-1, co-current): the preheater takes the latter.
    state.Calciner_gas_species_cells = species_cells
    state.Calciner_gas_species_out = species_cells[-1]

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
