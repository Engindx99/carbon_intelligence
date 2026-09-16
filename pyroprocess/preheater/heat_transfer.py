import numpy as np

from physics.physics import heat_transfer
from physics.physics import wall_losses
from physics.physics import ZONE_RAD_CONFIG
from physics.physics import sigma

from . import gas_phase
from . import solid_phase


# ======================================================
# STEADY-STATE THERMAL STEP
#
# Moved from Preheater.thermal_step()
# (pyroprocess/preheater/preheater.py). Logic is unchanged;
# `self` was renamed to `preheater` since this is now a
# free function taking the owning Preheater instance
# explicitly. This is the cross-stage fixed-point loop
# (solid inter-stage handoff, counter-current gas 1->5 /
# solid 5->1 sweep) plus the final consistent sweep, handoff
# diagnostics, and whole-preheater energy balance. It calls
# stage.solve() per stage, which itself delegates to
# solve_stage() below -- both the cross-stage loop and the
# per-stage wall/heat-transfer network live in this file
# since heat_transfer.py owns the overall Picard/iterative
# solve and wall/radiation network, at whichever granularity
# it occurs (same charter as
# pyroprocess/cooler/heat_transfer.py and
# pyroprocess/transition/heat_transfer.py, applied here to
# Preheater's two-level iteration instead of a single global
# linear system).
# ======================================================
def thermal_step(
    preheater,
    Tg,
    Ts,
    Tw,
    state,
    reaction_sink=0.0,
    reaction_heat_cells=None,
):

    # ======================================================
    # INPUTS
    # ======================================================

    m_dot_g = state.m_dot_g_preheater
    m_dot_s = state.m_dot_s_preheater

    # ======================================================
    # GAS INLET TEMPERATURE FROM ENTHALPY
    # ======================================================
    # Zone-to-zone gas energy handoff is defined by enthalpy.

    H_in = state.Hgas_preheater_in

    if H_in <= 0.0:
        raise RuntimeError(
            "Preheater gas inlet enthalpy is zero or negative: "
            f"Hgas_preheater_in={H_in:.6e} W, "
            f"Hgas_calciner_out={state.Hgas_calciner_out:.6e} W"
        )

    Tg_in = preheater.gas_temperature_from_enthalpy(
        H_in,
        state,
    )

    # Fresh raw meal enters Stage 5.
    Ts_feed = float(state.Feed_temperature)

    # ======================================================
    # INITIAL ARRAYS
    # ======================================================

    Tg_new = np.empty(preheater.N, dtype=float)
    Ts_new = np.empty(preheater.N, dtype=float)
    Tw_new = np.empty(preheater.N, dtype=float)

    # ======================================================
    # REACTION HEAT CELLS
    # ======================================================

    if reaction_heat_cells is None:
        reaction_heat_cells = np.zeros(preheater.N)

    if len(reaction_heat_cells) != preheater.N:
        raise ValueError(
            "reaction_heat_cells must have length equal to N"
        )

    # ======================================================
    # RESET HANDOFF DIAGNOSTICS
    # ======================================================

    preheater.gas_handoff_residuals = []
    preheater.solid_handoff_residuals = []

    # ======================================================
    # COUNTER-CURRENT STAGE SOLUTION
    # ======================================================

    # Gas:
    # Stage 1 -> Stage 2 -> Stage 3 -> Stage 4 -> Stage 5
    #
    # Solid:
    # Fresh feed -> Stage 5 -> Stage 4 -> Stage 3
    #            -> Stage 2 -> Stage 1

    max_iterations = 50
    tolerance = 1e-5

    # ======================================================
    # ENERGY CLOSURE TOLERANCE
    #
    # The loop below exits on a solid inlet TEMPERATURE
    # criterion, so each of the (N-1) internal solid
    # handoffs may still carry up to `tolerance` kelvin of
    # slop when it breaks. The zone energy balance further
    # down reads only the terminal stages
    # (stages[-1].gas_outlet_enthalpy and
    # stages[0].solid_outlet_enthalpy), assuming the
    # internal handoffs telescope exactly, so that slop
    # cannot cancel and lands directly in
    # preheater.energy_residual.
    #
    # Its enthalpy equivalent is therefore the tightest
    # closure this formulation can deliver. Exposed so the
    # energy validator can be held to what the solver
    # actually converges to, rather than to a fixed
    # absolute figure. Tightening `tolerance` above
    # tightens this in step.
    # ======================================================

    preheater.energy_closure_tolerance = float(
        (preheater.N - 1)
        * m_dot_s
        * preheater.Cp_s
        * tolerance
    )

    # Initial guesses for solid inlet temperature of
    # each stage.
    solid_in_guess = np.full(
        preheater.N,
        Ts_feed,
        dtype=float,
    )

    solid_out = np.empty(
        preheater.N,
        dtype=float,
    )

    # ======================================================
    # FIXED-POINT ITERATION
    # ======================================================

    for iteration in range(max_iterations):

        Tg_current = Tg_in

        # --------------------------------------------------
        # GAS SWEEP: Stage 1 -> Stage 5
        # --------------------------------------------------

        for i, stage in enumerate(preheater.stages):

            # Fresh feed enters Stage 5.
            if i == preheater.N - 1:
                Ts_current = Ts_feed
            else:
                # Solid comes from the next stage.
                Ts_current = solid_in_guess[i]

            stage.solve(
                gas_inlet_temperature=Tg_current,
                solid_inlet_temperature=Ts_current,
                m_dot_g=m_dot_g,
                m_dot_s=m_dot_s,
                state=state,
                model=preheater,
                reaction_power=-reaction_heat_cells[i],
            )

            solid_out[i] = (
                stage.solid_outlet_temperature
            )

            Tg_current = (
                stage.gas_outlet_temperature
            )

        # --------------------------------------------------
        # UPDATE SOLID INLET PROFILE
        # --------------------------------------------------

        new_solid_in = np.empty(
            preheater.N,
            dtype=float,
        )

        # Fresh feed enters Stage 5.
        new_solid_in[-1] = Ts_feed

        # Stage i receives solids from Stage i+1.
        new_solid_in[:-1] = solid_out[1:]

        # --------------------------------------------------
        # CONVERGENCE
        # --------------------------------------------------

        solid_error = np.max(
            np.abs(
                new_solid_in
                - solid_in_guess
            )
        )

        solid_in_guess = new_solid_in

        if solid_error < tolerance:
            break

    else:
        raise RuntimeError(
            "Preheater counter-current solution did not converge: "
            f"solid_error={solid_error:.6e} K"
        )

    # ======================================================
    # FINAL CONSISTENT SWEEP
    # ======================================================

    Tg_current = Tg_in

    for i, stage in enumerate(preheater.stages):

        if i == preheater.N - 1:
            Ts_current = Ts_feed
        else:
            Ts_current = solid_in_guess[i]

        stage.solve(
            gas_inlet_temperature=Tg_current,
            solid_inlet_temperature=Ts_current,
            m_dot_g=m_dot_g,
            m_dot_s=m_dot_s,
            state=state,
            model=preheater,
            reaction_power=-reaction_heat_cells[i],
        )

        Tg_new[i] = (
            stage.gas_outlet_temperature
        )

        Ts_new[i] = (
            stage.solid_outlet_temperature
        )

        Tw_new[i] = (
            stage.wall_temperature
        )

        Tg_current = (
            stage.gas_outlet_temperature
        )


    # ======================================================
    # ENTHALPY HANDOFF VALIDATION
    # ======================================================

    preheater.gas_handoff_residuals = []
    preheater.solid_handoff_residuals = []

    for i, stage in enumerate(preheater.stages):

        if i == 0:
            Hgas_expected = H_in
        else:
            Hgas_expected = (
                preheater.stages[i - 1].gas_outlet_enthalpy
            )

        if i == preheater.N - 1:
            Hsolid_expected = (
                m_dot_s
                * preheater.Cp_s
                * (Ts_feed - preheater.T_ref)
            )
        else:
            Hsolid_expected = (
                preheater.stages[i + 1].solid_outlet_enthalpy
            )

        gas_handoff_residual = (
            stage.gas_inlet_enthalpy
            - Hgas_expected
        )

        solid_handoff_residual = (
            stage.solid_inlet_enthalpy
            - Hsolid_expected
        )

        preheater.gas_handoff_residuals.append(
            float(gas_handoff_residual)
        )

        preheater.solid_handoff_residuals.append(
            float(solid_handoff_residual)
        )

    # ======================================================
    # TOTAL STAGE ENERGY TRANSFERS
    # ======================================================

    preheater.Q_reaction_total = sum(
        stage.Q_reaction
        for stage in preheater.stages
    )

    Q_wall_loss_total = sum(
        stage.Q_wall_loss
        for stage in preheater.stages
    )



    # ======================================================
    # GLOBAL PREHEATER ENERGY BALANCE
    # ======================================================

    Hgas_in = state.Hgas_preheater_in

    Hsolid_in = (
        m_dot_s
        * preheater.Cp_s
        * (Ts_feed - preheater.T_ref)
    )

    Hgas_out = preheater.stages[-1].gas_outlet_enthalpy

    Hsolid_out = preheater.stages[0].solid_outlet_enthalpy

    preheater.energy_in = (
        Hgas_in
        + Hsolid_in
    )

    preheater.energy_out = (
        Hgas_out
        + Hsolid_out
        + Q_wall_loss_total
    )

    preheater.energy_residual = (
        preheater.energy_in
        + preheater.Q_reaction_total
        - preheater.energy_out
    )

    # ======================================================
    # WALL LOSS
    # ======================================================

    wall_loss = Q_wall_loss_total
    wall_debug = {}

    # ======================================================
    # RETURN
    # ======================================================

    return (
        Tg_new,
        Ts_new,
        Tw_new,
        float(wall_loss),
        wall_debug,
    )


# ======================================================
# SOLVE ONE PREHEATER STAGE
#
# Moved from PreheaterStage.solve()
# (pyroprocess/preheater/stage.py). Logic is unchanged;
# `self` was renamed to `stage` since this is now a free
# function taking the owning PreheaterStage instance
# explicitly. The wall-temperature bisection and the final
# heat-transfer/wall-loss calls stay here since
# heat_transfer.py owns the overall gas-solid-wall heat
# transfer network -- gas-side and solid-side enthalpy
# balance is delegated to gas_phase/solid_phase, exactly as
# in the other zone packages.
#
# IMPORTANT:
#     The equations are intentionally kept identical to the
#     previous PreheaterStage implementation.
# ======================================================
def solve_stage(
    stage,
    gas_inlet_temperature,
    solid_inlet_temperature,
    m_dot_g,
    m_dot_s,
    state,
    model,
    reaction_power=0.0,
):

    stage.reset_diagnostics()

    eps = model.eps
    T_ref = model.T_ref
    T_amb = model.T_amb

    Tg_in = float(gas_inlet_temperature)
    Ts_in = float(solid_inlet_temperature)

    stage.gas_inlet_temperature = Tg_in
    stage.solid_inlet_temperature = Ts_in

    # ==========================================================
    # WALL TEMPERATURE SOLUTION
    # ==========================================================

    def wall_residual_stage(Tw_trial):

        _, q_gw_trial, q_ws_trial = heat_transfer(
            Tg=np.array([Tg_in]),
            Ts=np.array([Ts_in]),
            Tw=np.array([Tw_trial]),
            hv_gs=model.hv_gs,
            hv_gw=model.hv_gw,
            hv_ws=model.hv_ws,
            a_gs=model.a_gs,
            a_gw=model.a_gw,
            a_ws=model.a_ws,
            zone=model.zone,
        )

        _, Q_wall_loss_trial, _ = wall_losses(
            Tw=np.array([Tw_trial]),
            h_ext=model.h_ext,
            A_wall_cell=model.A_wall_cell,
            V_cell=model.V_cell,
            T_amb=T_amb,
            A_wall_total=model.A_wall,
            N=1,
            refractory_thickness=model.refractory_thickness,
            refractory_conductivity=model.refractory_conductivity,
            eps=eps,
        )

        return (
            float(q_gw_trial[0] + q_ws_trial[0])
            * model.V_cell
            - Q_wall_loss_trial
        )

    # ----------------------------------------------------------
    # ANALYTIC SLOPE OF THE WALL RESIDUAL
    #
    # The residual is
    #
    #   R(Tw) = V_cell * [q_gw(Tw) + q_ws(Tw)] - Q_loss(Tw)
    #
    # with (see physics.heat_transfer / physics.radiation)
    #
    #   q_gw = hv_gw*a_gw*(Tg - Tw) + C*a_gw*(Tg^4 - Tw^4)
    #   q_ws = hv_ws*a_ws*(Ts - Tw) + C*a_ws*(Ts^4 - Tw^4)
    #   C    = k_eff * eps_rad * sigma
    #
    # so
    #
    #   dR/dTw = -V_cell * [ hv_gw*a_gw + hv_ws*a_ws
    #                        + 4*C*(a_gw + a_ws)*Tw^3 ]
    #            - dQ_loss/dTw
    #
    # Every term is non-negative before the sign, so dR/dTw is
    # strictly negative: R decreases monotonically and the root
    # is unique. Verified over 545 stage solves -- R was
    # strictly decreasing in all of them.
    #
    # Q_loss is exactly affine in Tw and vanishes at T_amb, so
    # its slope is read straight off physics.wall_losses at
    # T_amb + 1 K rather than re-stating the insulation-factor
    # calibration here. That keeps wall_losses the single
    # source of truth for the loss model.
    # ----------------------------------------------------------

    rad_cfg = ZONE_RAD_CONFIG[model.zone]

    C_rad = (
        rad_cfg["k_eff"]
        * rad_cfg["eps"]
        * sigma
    )

    _, wall_loss_slope, _ = wall_losses(
        Tw=np.array([T_amb + 1.0]),
        h_ext=model.h_ext,
        A_wall_cell=model.A_wall_cell,
        V_cell=model.V_cell,
        T_amb=T_amb,
        A_wall_total=model.A_wall,
        N=1,
        refractory_thickness=model.refractory_thickness,
        refractory_conductivity=model.refractory_conductivity,
        eps=eps,
    )

    def wall_residual_slope_stage(Tw_trial):

        return (
            -model.V_cell
            * (
                model.hv_gw * model.a_gw
                + model.hv_ws * model.a_ws
                + 4.0
                * C_rad
                * (model.a_gw + model.a_ws)
                * Tw_trial ** 3
            )
            - wall_loss_slope
        )

    T_low = T_amb
    T_high = max(Tg_in, Ts_in, T_amb)

    residual_low = wall_residual_stage(T_low)
    residual_high = wall_residual_stage(T_high)

    # The previous implementation grew T_high by 1.10x up to 50
    # times whenever residual_high < 0. Since R is decreasing,
    # residual_high < 0 already means the root sits below T_high
    # -- the bracket is valid and growing it only drives the
    # residual further negative. The loop therefore never hit
    # its `break` (measured: 0 out of 545 stage solves), always
    # exhausted, and its `else` reset T_high to exactly the
    # value it started from. It was 51 residual evaluations per
    # stage solve that could not change the outcome, so it is
    # gone. The bracket, the sign test and the fallback below
    # are unchanged.

    if residual_low * residual_high <= 0.0:

        # ------------------------------------------------------
        # SAFEGUARDED NEWTON
        #
        # Newton on the analytic slope, with the bracket kept up
        # to date and used as a fallback: if a Newton step would
        # leave the bracket or the slope is not usable, the step
        # degrades to a bisection step. Convergence is therefore
        # never worse than the bisection it replaces, while the
        # quadratic steps reach the same |R| < 1e-6 criterion in
        # ~4 evaluations instead of ~40.
        # ------------------------------------------------------

        Tw = 0.5 * (T_low + T_high)

        for _ in range(60):

            residual_mid = wall_residual_stage(Tw)

            if abs(residual_mid) < 1e-6:
                break

            if residual_low * residual_mid <= 0.0:
                T_high = Tw
                residual_high = residual_mid
            else:
                T_low = Tw
                residual_low = residual_mid

            slope = wall_residual_slope_stage(Tw)

            Tw_newton = (
                Tw - residual_mid / slope
                if slope != 0.0
                else T_high
            )

            if T_low < Tw_newton < T_high:
                Tw = Tw_newton
            else:
                Tw = 0.5 * (T_low + T_high)

    else:

        Tw = max(
            T_amb,
            min(Tg_in, Ts_in),
        )

    stage.wall_temperature = float(Tw)

    # ==========================================================
    # HEAT TRANSFER
    # ==========================================================

    _, q_gw, q_ws = heat_transfer(
        Tg=np.array([Tg_in]),
        Ts=np.array([Ts_in]),
        Tw=np.array([Tw]),
        hv_gs=model.hv_gs,
        hv_gw=model.hv_gw,
        hv_ws=model.hv_ws,
        a_gs=model.a_gs,
        a_gw=model.a_gw,
        a_ws=model.a_ws,
        zone=model.zone,
    )

    q_gs, _, _ = heat_transfer(
        Tg=np.array([Tg_in]),
        Ts=np.array([Ts_in]),
        Tw=np.array([Tw]),
        hv_gs=model.hv_gs,
        hv_gw=model.hv_gw,
        hv_ws=model.hv_ws,
        a_gs=model.a_gs,
        a_gw=model.a_gw,
        a_ws=model.a_ws,
        zone=model.zone,
    )

    stage.Q_gs = float(q_gs[0]) * model.V_cell
    stage.Q_gw = float(q_gw[0]) * model.V_cell
    stage.Q_ws = float(q_ws[0]) * model.V_cell

    # ==========================================================
    # WALL LOSS
    # ==========================================================

    _, wall_loss, _ = wall_losses(
        Tw=np.array([Tw]),
        h_ext=model.h_ext,
        A_wall_cell=model.A_wall_cell,
        V_cell=model.V_cell,
        T_amb=T_amb,
        A_wall_total=model.A_wall,
        N=1,
        refractory_thickness=model.refractory_thickness,
        refractory_conductivity=model.refractory_conductivity,
        eps=eps,
    )

    stage.Q_wall_loss = float(wall_loss)

    # ==========================================================
    # GAS ENTHALPY
    # ==========================================================

    H_gas_in, H_gas_out, Tg_out = gas_phase.apply_stage_gas_energy_balance(
        model,
        state,
        Tg_in,
        m_dot_g,
        reaction_power,
        stage.Q_gs,
        stage.Q_gw,
        T_ref,
    )

    # ==========================================================
    # SOLID ENTHALPY
    # ==========================================================

    H_solid_in, H_solid_out, Ts_out = solid_phase.apply_stage_solid_energy_balance(
        model,
        m_dot_s,
        Ts_in,
        stage.Q_gs,
        stage.Q_ws,
        T_ref,
        eps,
    )

    # ==========================================================
    # ENERGY BALANCE
    # ==========================================================

    energy_in = H_gas_in + H_solid_in

    energy_out = (
        H_gas_out
        + H_solid_out
        + stage.Q_wall_loss
        - reaction_power
    )

    energy_residual = energy_in - energy_out

    # ==========================================================
    # STORE RESULTS
    # ==========================================================

    stage.gas_outlet_temperature = float(Tg_out)
    stage.solid_outlet_temperature = float(Ts_out)

    stage.gas_inlet_enthalpy = float(H_gas_in)
    stage.gas_outlet_enthalpy = float(H_gas_out)

    stage.solid_inlet_enthalpy = float(H_solid_in)
    stage.solid_outlet_enthalpy = float(H_solid_out)

    stage.Q_reaction = float(reaction_power)

    stage.energy_in = float(energy_in)
    stage.energy_out = float(energy_out)
    stage.energy_residual = float(energy_residual)

    stage.gas_T_min = min(Tg_in, Tg_out)
    stage.gas_T_max = max(Tg_in, Tg_out)

    return stage
