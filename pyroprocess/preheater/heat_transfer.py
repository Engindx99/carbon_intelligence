import numpy as np

from physics.physics import heat_transfer
from physics.shell import loss_conductance
from physics.shell import shell_closure
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

    # ======================================================
    # PER-STAGE MASS FLOWS
    #
    # Free moisture evaporated in stage i
    # (state.material_flows["preheater"].gases.H2O[i], from
    # ChemistryModel.apply_preheater) leaves the solid and
    # joins the gas there. Solid enters stage 5 (index N-1)
    # as fresh feed and flows towards stage 1; gas enters
    # stage 1 (index 0) and flows towards stage 5. Hence, for
    # the flows ENTERING stage i,
    #
    #   m_dot_s_in[i] = m_dot_s - sum(vapor[j], j > i)
    #   m_dot_g_in[i] = m_dot_g + sum(vapor[j], j < i)
    #
    # With no evaporation both reduce to the zone flows.
    # ======================================================

    vapor = np.asarray(
        state.material_flows["preheater"].gases.H2O,
        dtype=float,
    )

    if vapor.shape != (preheater.N,):
        raise ValueError(
            "preheater vapor flows must have length equal to N"
        )

    vapor_downstream_of_gas = np.concatenate(
        ([0.0], np.cumsum(vapor)[:-1])
    )

    vapor_upstream_of_solid = np.concatenate(
        (np.cumsum(vapor[::-1])[::-1][1:], [0.0])
    )

    m_dot_g_in = m_dot_g + vapor_downstream_of_gas

    m_dot_s_in = m_dot_s - vapor_upstream_of_solid

    # Outlet flows handed to the next units: exhaust gas from
    # stage 5, solid to the calciner from stage 1.
    preheater.m_dot_g_out = float(m_dot_g + np.sum(vapor))

    preheater.m_dot_s_out = float(m_dot_s - np.sum(vapor))

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
                m_dot_g=m_dot_g_in[i],
                m_dot_s=m_dot_s_in[i],
                state=state,
                model=preheater,
                reaction_power=-reaction_heat_cells[i],
                m_dot_vapor=vapor[i],
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
            m_dot_g=m_dot_g_in[i],
            m_dot_s=m_dot_s_in[i],
            state=state,
            model=preheater,
            reaction_power=-reaction_heat_cells[i],
            m_dot_vapor=vapor[i],
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
    # SHELL STATE (Faz 6)
    #
    # A stage's shell_temperature is the LAST node's, because
    # solve_stage marches the nodes and each one overwrites it.
    # The hottest stage is the one the casing bound applies to,
    # so that is what is published.
    # ======================================================
    state.Preheater_T_shell_cells = np.array(
        [stage.shell_temperature for stage in preheater.stages],
        dtype=float,
    )

    state.Preheater_T_shell_max = float(
        np.max(state.Preheater_T_shell_cells)
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
# SOLVE ONE PREHEATER STAGE (NODAL)
#
# A stage is marched through preheater.nodes_per_stage equal
# sub-volumes, gas and solid co-current inside the stage
# (riser duct); the stages themselves stay counter-current
# (thermal_step above). Each node is the lumped balance of
# solve_stage_node() on 1/n of the stage volume and wall
# area, fed by the previous node's outlet temperatures.
#
# Why: the lumped balance evaluates the gas-solid, gas-wall
# and solid-wall fluxes at the stage INLET temperatures over
# the whole stage volume. With a large inlet temperature
# difference that overshoots equilibrium (solid could leave
# a stage hotter than the gas with no heat source). Marching
# the same equations in n nodes integrates the decaying
# driving force, so stage outlets converge as n grows.
# n = 1 reproduces the lumped stage exactly.
#
# The stage's free-moisture evaporation and its (negative)
# reaction power are spread uniformly over the nodes, so
# the stage totals are unchanged.
#
# Stage-level results are those of the stage boundaries:
# inlet from the first node, outlet from the last node,
# transfer rates summed; wall_temperature is the node
# (equal-volume) mean. Node outlet temperatures are kept on
# the stage as diagnostics.
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
    m_dot_vapor=0.0,
):

    # Local import: stage.py imports this module at load time.
    from .stage import PreheaterStage

    n = model.nodes_per_stage
    volume_fraction = 1.0 / n

    stage.reset_diagnostics()

    Tg = float(gas_inlet_temperature)
    Ts = float(solid_inlet_temperature)

    # None at the stage inlet: the stage boundary handoff is unchanged.
    H_gas = None

    nodes = []

    for k in range(n):

        node = PreheaterStage(stage_id=stage.stage_id)

        solve_stage_node(
            node,
            Tg,
            Ts,
            m_dot_g + k * m_dot_vapor * volume_fraction,
            m_dot_s - k * m_dot_vapor * volume_fraction,
            state,
            model,
            reaction_power * volume_fraction,
            m_dot_vapor * volume_fraction,
            volume_fraction,
            H_gas,
        )

        nodes.append(node)

        Tg = node.gas_outlet_temperature
        Ts = node.solid_outlet_temperature
        H_gas = node.gas_outlet_enthalpy

    first = nodes[0]
    last = nodes[-1]

    stage.gas_inlet_temperature = first.gas_inlet_temperature
    stage.solid_inlet_temperature = first.solid_inlet_temperature

    stage.gas_outlet_temperature = last.gas_outlet_temperature
    stage.solid_outlet_temperature = last.solid_outlet_temperature

    stage.gas_inlet_enthalpy = first.gas_inlet_enthalpy
    stage.solid_inlet_enthalpy = first.solid_inlet_enthalpy

    stage.gas_outlet_enthalpy = last.gas_outlet_enthalpy
    stage.solid_outlet_enthalpy = last.solid_outlet_enthalpy

    stage.wall_temperature = float(
        np.mean([node.wall_temperature for node in nodes])
    )

    # The casing bound is a LIMIT, so the stage carries the
    # hottest node's skin, not the mean -- a mean would hide a
    # single hot node behind four cool ones. The hot face takes
    # the mean because it is reported as a stage state, not
    # checked against a limit.
    stage.shell_temperature = float(
        np.max([node.shell_temperature for node in nodes])
    )

    stage.Q_gs = float(sum(node.Q_gs for node in nodes))
    stage.Q_gw = float(sum(node.Q_gw for node in nodes))
    stage.Q_ws = float(sum(node.Q_ws for node in nodes))
    stage.Q_wall_loss = float(sum(node.Q_wall_loss for node in nodes))
    stage.Q_reaction = float(sum(node.Q_reaction for node in nodes))

    stage.energy_in = float(
        stage.gas_inlet_enthalpy
        + stage.solid_inlet_enthalpy
    )

    stage.energy_out = float(
        stage.gas_outlet_enthalpy
        + stage.solid_outlet_enthalpy
        + stage.Q_wall_loss
        - stage.Q_reaction
    )

    stage.energy_residual = stage.energy_in - stage.energy_out

    stage.gas_T_min = min(
        stage.gas_inlet_temperature,
        stage.gas_outlet_temperature,
    )
    stage.gas_T_max = max(
        stage.gas_inlet_temperature,
        stage.gas_outlet_temperature,
    )

    stage.node_gas_temperatures = np.array(
        [node.gas_outlet_temperature for node in nodes]
    )
    stage.node_solid_temperatures = np.array(
        [node.solid_outlet_temperature for node in nodes]
    )
    stage.node_wall_temperatures = np.array(
        [node.wall_temperature for node in nodes]
    )

    return stage


# ======================================================
# SOLVE ONE PREHEATER STAGE NODE
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
#     The heat-transfer and wall equations are kept identical
#     to the previous PreheaterStage implementation.
#
# NODE VOLUME:
#     The balance is applied to volume_fraction of the stage:
#     V_cell, A_wall_cell and A_wall are scaled by it. All
#     volumetric fluxes and the wall loss are linear in these,
#     so volume_fraction = 1 is the whole lumped stage.
#
# OPEN-SYSTEM STAGE (moisture evaporation):
#     m_dot_g and m_dot_s are the gas and solid mass flows
#     ENTERING the stage; m_dot_vapor [kg/s] of free moisture
#     leaves the solid and joins the gas inside it, so the
#     outlet flows are m_dot_s - m_dot_vapor and
#     m_dot_g + m_dot_vapor. The solid energy balance on the
#     inlet mass gives the common outlet temperature Ts_out;
#     the vapor leaves the solid at Ts_out carrying
#     H_vapor = m_dot_vapor * Cp_s * (Ts_out - T_ref) into the
#     gas, and the latent heat is the (negative)
#     reaction_power drawn from the gas as before. Summing the
#     two balances, H_vapor cancels and the stage closes
#     exactly as the closed stage did. With m_dot_vapor = 0
#     every expression reduces to the previous one.
# ======================================================
def solve_stage_node(
    stage,
    gas_inlet_temperature,
    solid_inlet_temperature,
    m_dot_g,
    m_dot_s,
    state,
    model,
    reaction_power=0.0,
    m_dot_vapor=0.0,
    volume_fraction=1.0,
    gas_inlet_enthalpy=None,
):

    stage.reset_diagnostics()

    eps = model.eps
    T_ref = model.T_ref
    T_amb = model.T_amb

    V_cell = model.V_cell * volume_fraction
    A_wall_cell = model.A_wall_cell * volume_fraction
    A_wall = model.A_wall * volume_fraction

    # ==========================================================
    # SHELL GEOMETRY FOR THIS NODE
    #
    # A node is volume_fraction of a stage, so it owns that
    # fraction of the stage's wall length. The conduction
    # resistance scales as 1/L and the outer area as L, which is
    # exactly what re-resolving the stack on the node's own cell
    # length does -- the two would NOT come out right by scaling
    # a stage-level resistance, because the external film sees an
    # area and the stack sees a length.
    #
    # Resolved once per node rather than per residual evaluation:
    # nothing in it moves while the wall temperature is solved.
    # ==========================================================
    node_shell = model.wall_stack.geometry(
        r_inner=model.shell.r_inner,
        L_cell=model.shell.L_cell * volume_fraction,
        L_char=model.shell.L_char,
    )

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

        R_total_trial, _, _ = shell_closure(
            float(Tw_trial),
            node_shell,
            T_amb,
        )

        Q_wall_loss_trial = (
            float(Tw_trial) - T_amb
        ) / R_total_trial

        return (
            float(q_gw_trial[0] + q_ws_trial[0])
            * V_cell
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
    # Faz 6: Q_loss is NO LONGER AFFINE in Tw. The external film
    # carries the casing temperature through h_rad ~ T^3 and
    # h_conv ~ dT^(1/3), so the slope has to be evaluated where
    # the Newton step is taken, not once at T_amb + 1 K. It comes
    # from physics.shell.loss_conductance, which differentiates
    # the same series network shell_closure solves -- so the
    # slope and the residual still cannot describe different
    # walls, which is what reading it off wall_losses bought.
    # ----------------------------------------------------------

    rad_cfg = ZONE_RAD_CONFIG[model.zone]

    C_rad = (
        rad_cfg["k_eff"]
        * rad_cfg["eps"]
        * sigma
    )

    def wall_residual_slope_stage(Tw_trial):

        _, T_shell_trial, _ = shell_closure(
            float(Tw_trial),
            node_shell,
            T_amb,
        )

        wall_loss_slope = loss_conductance(
            T_shell_trial,
            node_shell,
            T_amb,
        )

        return (
            -V_cell
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

    stage.Q_gs = float(q_gs[0]) * V_cell
    stage.Q_gw = float(q_gw[0]) * V_cell
    stage.Q_ws = float(q_ws[0]) * V_cell

    # ==========================================================
    # WALL LOSS
    # ==========================================================

    R_total, T_shell, _ = shell_closure(
        float(Tw),
        node_shell,
        T_amb,
    )

    wall_loss = (float(Tw) - T_amb) / R_total

    stage.Q_wall_loss = float(wall_loss)
    stage.shell_temperature = float(T_shell)

    # ==========================================================
    # SOLID ENTHALPY
    #
    # Solved before the gas: the evaporated moisture leaves the
    # solid at Ts_out and its enthalpy is a gas-side input.
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

    H_vapor = (
        m_dot_vapor
        * model.Cp_s
        * (Ts_out - T_ref)
    )

    # Enthalpy of the solid stream actually leaving the stage.
    H_solid_out = H_solid_out - H_vapor

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
        m_dot_vapor,
        H_vapor,
        gas_inlet_enthalpy,
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
