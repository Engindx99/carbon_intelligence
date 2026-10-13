import math

import numpy as np

from physics.physics import cp_gas
from physics.physics import cp_solid
from physics.physics import h_solid
from physics.physics import T_solid_from_h
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
def circulating_solid_flows(m_dot_s_in, vapor, separation_efficiency):
    """
    Solid flows through the stages with cyclone separation (see
    CYCLONE SEPARATION AND DUST CIRCULATION in thermal_step).

    m_dot_s_in: solid entering each stage without separation;
    vapor: free moisture leaving each stage; separation_efficiency:
    eta per stage, index order. Returns the solid entering each
    stage with the circulating dust, and the dust each stage lets
    up with its gas (the last entry goes to the filter and back
    with the feed). All eta = 1 returns m_dot_s_in unchanged and
    no dust, exactly.
    """
    m_dot_s_in = np.asarray(m_dot_s_in, dtype=float)
    vapor = np.asarray(vapor, dtype=float)
    k = 1.0 - np.asarray(separation_efficiency, dtype=float)

    N = m_dot_s_in.shape[0]

    if k.shape != (N,) or vapor.shape != (N,):
        raise ValueError(
            "separation_efficiency and vapor must have length equal to N"
        )

    O0 = m_dot_s_in - vapor

    A = np.eye(N)
    b = np.zeros(N)

    for i in range(N - 1):
        A[i, i + 1] += -1.0 + k[i + 1]
        b[i] += -k[i + 1] * O0[i + 1]
        if i > 0:
            A[i, i - 1] += -k[i - 1]
            b[i] += k[i - 1] * O0[i - 1]

    A[N - 1, N - 1] -= k[N - 1]
    b[N - 1] += k[N - 1] * O0[N - 1]
    if N > 1:
        A[N - 1, N - 2] -= k[N - 2]
        b[N - 1] += k[N - 2] * O0[N - 2]

    x_extra = np.linalg.solve(A, b) if np.any(b) else np.zeros(N)

    m_dot_s_in = m_dot_s_in + x_extra

    return m_dot_s_in, k * (m_dot_s_in - vapor)


def _cp_scale(Ts, Ts_feed):
    """The largest solid Cp over the stage temperatures, to turn
    the inner loop's kelvin tolerance into watts."""

    T = np.append(np.asarray(Ts, dtype=float), float(Ts_feed))

    return float(np.max(cp_solid(T)))


def _mixed_solid_inlet(solid_out, Ts_feed, dust_from_below, T_ref):
    """
    Solid inlet temperature of every stage: the stream from above
    (the next stage's underflow, or the feed into Stage 5, which
    the returned C1 dust joins at the feed temperature) mixed with
    the dust share dust_from_below[i] coming up from stage i-1.
    Mixed in enthalpy, mass-weighted, then read back as a
    temperature; with no dust it is the stream from above exactly.
    """
    base = np.empty_like(solid_out)
    base[:-1] = solid_out[1:]
    base[-1] = Ts_feed

    below = base.copy()
    below[1:] = solid_out[:-1]

    h_base = h_solid(base, T_ref)

    return T_solid_from_h(
        h_base + dust_from_below * (h_solid(below, T_ref) - h_base),
        T_ref,
    )


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

    # Dynamic solve: each stage's wall starts the step at its
    # Tw_preheater_old entry. None in the steady solve.
    def wall_old(i):
        if getattr(state, "transient_dt", None) is None:
            return None
        return float(np.asarray(state.Tw_preheater_old)[i])

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

    # The inner loop's error trajectory. Published so a caller
    # that gets a raise can tell a near-miss from a divergence
    # without re-running the plant, and so the contraction ratio
    # is a measurement rather than an assumption.
    preheater.solid_error_history = []

    # ======================================================
    # COUNTER-CURRENT STAGE SOLUTION
    # ======================================================

    # Gas:
    # Stage 1 -> Stage 2 -> Stage 3 -> Stage 4 -> Stage 5
    #
    # Solid:
    # Fresh feed -> Stage 5 -> Stage 4 -> Stage 3
    #            -> Stage 2 -> Stage 1

    # This is plain Picard on the solid inlet profile, so its
    # error sequence is geometric and the budget is a NUMERICAL
    # resource, not a physical parameter. 50 was too small and had
    # already produced two false negatives: a plant that missed
    # this tolerance looks, from outside, exactly like one that
    # diverged, and both were reported to a fuel experiment as
    # infeasible operating points.
    #
    # MEASURED on the literature-kinetics tree at nodes_per_stage
    # = 1, with the budget lifted so the loop could finish:
    #
    #   fuel 1.6 kg/s -> converged in 51 iterations, rho = 0.708
    #   fuel 1.3 kg/s -> converged in 62 iterations, rho = 0.758
    #
    # 1.6 missed by ONE iteration. The error fell 421 K -> 9.6e-6 K
    # monotonically over eight orders; nothing was diverging.
    #
    # 200 is derived, not guessed: the worst contraction still
    # worth calling convergent is taken as rho = 0.9, and the
    # initial error spans feed to exhaust, order 1e3 K, so
    # log(1e-5 / 1e3) / log(0.9) = 175 iterations. Rounded up.
    max_iterations = 200

    # NOT loosened. preheater.energy_closure_tolerance below is
    # derived from this figure, so relaxing it would silently
    # relax the energy validator with it -- buying convergence by
    # lowering the bar the result is checked against.
    tolerance = 1e-5

    # The loop STOPS at stop_tolerance, which is looser only while
    # the plant itself is far from its fixed point (Twin.run's
    # inner_tolerance_hint, zero on the sweep that may declare
    # convergence). The validator above keeps reading `tolerance`,
    # so its bar is the same on every sweep, and the sweep the
    # plant converges on is solved to it exactly as before.
    stop_tolerance = max(
        tolerance,
        float(getattr(state, "inner_tolerance_hint", 0.0)),
    )

    # A budget four times larger makes a GENUINE divergence four
    # times more expensive, so pay that back: a sequence that has
    # stopped contracting is not going to start, and saying so
    # early costs one comparison per iteration.
    divergence_window = 20

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
        * _cp_scale(Ts, Ts_feed)
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

    # ======================================================
    # CYCLONE SEPARATION AND DUST CIRCULATION
    #
    # Each stage's cyclone sends eta_i of the solid leaving the
    # stage down (to Stage i-1, or to the calciner from Stage 1)
    # and lets E_i = (1 - eta_i) of it up with its gas:
    #
    #   - from Stages 1-4 (plant C5-C2) into the stage above,
    #     where it joins that stage's solid: an internal loop;
    #   - from Stage 5 (plant C1) out with the exhaust; the
    #     filter catches it and it comes back with the feed.
    #
    # At steady state the solid reaching the calciner is still
    # the fresh feed less its moisture: the loops add flow
    # through the stages, not mass to the plant. The dust is dry
    # (the feed's free moisture leaves in Stage 5) and carries no
    # species change: it costs heat, not mass. Its heat is real:
    # dust from a hotter stage reheats the cooler solid above,
    # and C1's dust leaves at the Stage 5 solid outlet
    # temperature and returns at the feed temperature.
    #
    # With x_i the extra solid entering stage i and O0_i the
    # stage outflow without separation (O0_i = m_dot_s_in[i]
    # - vapor[i]),
    #
    #   E_i = (1 - eta_i) (O0_i + x_i)
    #   x_i     = x_{i+1} - E_{i+1} + E_{i-1}     i < N-1
    #   x_{N-1} = E_{N-1} + E_{N-2}
    #
    # (E_{-1} = 0): stage i gets the underflow O_{i+1} - E_{i+1}
    # from above and the dust E_{i-1} from below; Stage 5 gets
    # its own dust back with the feed. All eta = 1 gives a zero
    # right-hand side and x = 0 exactly: the model without
    # separation. C1 alone gives x_{N-1} = (1-eta)/eta O0_{N-1}.
    # ======================================================

    m_dot_s_in, m_dot_escape = circulating_solid_flows(
        m_dot_s_in, vapor, preheater.separation_efficiency
    )

    m_dot_dust = float(m_dot_escape[-1])

    preheater.m_dot_dust_return = m_dot_dust

    preheater.m_dot_dust_escape = m_dot_escape.copy()

    preheater.m_dot_s_stage_in = m_dot_s_in.copy()

    N = preheater.N

    # The circulating dust adds flow through the stages, and with
    # it handoff slop; scale the closure tolerance (above) by the
    # largest stage flow. Without separation that is m_dot_s.
    preheater.energy_closure_tolerance = float(
        (preheater.N - 1)
        * max(m_dot_s, float(np.max(m_dot_s_in)))
        * _cp_scale(Ts, Ts_feed)
        * tolerance
    )

    # Share of each stage's solid inlet that is dust from the
    # stage below; the rest comes from above (or is feed).
    dust_from_below = np.zeros(N)
    dust_from_below[1:] = m_dot_escape[:-1] / m_dot_s_in[1:]

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

            # Feed (Stage 5) or the next stage's solid, mixed with
            # the dust from the stage below.
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
                wall_temperature_old=wall_old(i),
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

        new_solid_in = _mixed_solid_inlet(
            solid_out, Ts_feed, dust_from_below, preheater.T_ref
        )

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

        preheater.solid_error_history.append(float(solid_error))

        if solid_error < stop_tolerance:
            break

        # A contraction that has made no progress across a whole
        # window is not converging slowly, it is not converging.
        # Compared against the START of the window rather than the
        # previous step, so the ordinary non-monotone wobble of a
        # counter-current sweep does not trip it.
        if len(preheater.solid_error_history) > divergence_window:

            reference = preheater.solid_error_history[
                -divergence_window - 1
            ]

            if solid_error >= reference:
                raise RuntimeError(
                    "Preheater counter-current solution is not "
                    "contracting: solid_error="
                    f"{solid_error:.6e} K after {iteration + 1} "
                    f"iterations, against {reference:.6e} K "
                    f"{divergence_window} iterations earlier "
                    f"(tolerance {tolerance:.1e} K). This is a "
                    "divergence, not an exhausted budget."
                )

    else:
        # Report the ATTAINED error and the rate, so a caller can
        # tell "two iterations short" from "nowhere near". The
        # first costs a fuel experiment a feasible operating point
        # if it is reported as infeasible; the second is a real
        # statement about the plant.
        ratio = float("nan")

        if len(preheater.solid_error_history) >= 2:
            previous = preheater.solid_error_history[-2]
            if previous > 0.0:
                ratio = solid_error / previous

        shortfall = solid_error / stop_tolerance

        message = (
            "Preheater counter-current solution did not converge: "
            f"solid_error={solid_error:.6e} K after "
            f"{max_iterations} iterations, which is "
            f"{shortfall:.2f}x the {stop_tolerance:.1e} K tolerance "
            f"(last contraction ratio {ratio:.4f})."
        )

        # ratio == ratio rejects NaN, which is what an empty or
        # zero-valued history leaves behind.
        if ratio == ratio and ratio < 1.0:
            message += (
                " Budget exhausted while still contracting -- "
                "this is not a divergence."
            )

        raise RuntimeError(message)

    # ======================================================
    # FINAL CONSISTENT SWEEP
    # ======================================================

    Tg_current = Tg_in

    for i, stage in enumerate(preheater.stages):

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
            wall_temperature_old=wall_old(i),
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

    # Every stage's escaping dust leaves it at its solid outlet
    # temperature: Stages 1-4's joins the stage above, Stage 5's
    # (H_dust_out) goes to the filter and is fed back at the feed
    # temperature (H_dust_in). A stage's solid outlet enthalpy
    # carries its dust; the stage below receives the rest.
    H_escape = m_dot_escape * h_solid(Ts_new, preheater.T_ref)

    H_dust_out = m_dot_dust * h_solid(
        float(Ts_new[-1]), preheater.T_ref
    )

    H_dust_in = m_dot_dust * h_solid(Ts_feed, preheater.T_ref)

    for i, stage in enumerate(preheater.stages):

        if i == 0:
            Hgas_expected = H_in
        else:
            Hgas_expected = (
                preheater.stages[i - 1].gas_outlet_enthalpy
            )

        if i == preheater.N - 1:
            Hsolid_expected = (
                m_dot_s * h_solid(Ts_feed, preheater.T_ref)
                + H_dust_in
            )
        else:
            Hsolid_expected = (
                preheater.stages[i + 1].solid_outlet_enthalpy
                - H_escape[i + 1]
            )

        if i > 0:
            Hsolid_expected += H_escape[i - 1]

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

    # Rate of change of the walls' stored energy; zero when steady.
    Q_wall_stored_total = float(sum(
        stage.Q_wall_stored
        for stage in preheater.stages
    ))

    state.Preheater_wall_stored = Q_wall_stored_total
    state.Preheater_stored_energy_change = Q_wall_stored_total

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

    Hsolid_in = m_dot_s * h_solid(Ts_feed, preheater.T_ref)

    Hgas_out = preheater.stages[-1].gas_outlet_enthalpy

    # Stage 1's underflow; its escaping dust stays in the loop.
    Hsolid_out = (
        preheater.stages[0].solid_outlet_enthalpy
        - H_escape[0]
    )

    preheater.energy_in = (
        Hgas_in
        + Hsolid_in
        + H_dust_in
    )

    preheater.energy_out = (
        Hgas_out
        + Hsolid_out
        + Q_wall_loss_total
        + H_dust_out
        + Q_wall_stored_total
    )

    # Net heat the returned dust takes out of the plant: the
    # zone and global balances book it next to the wall loss.
    state.Q_dust_loss_preheater = float(H_dust_out - H_dust_in)

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
    wall_temperature_old=None,
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

    # Each node's converged (Tw, Tg_bar, Ts_bar) from the last
    # solve of this stage, as its warm start (solve_stage_node).
    starts = getattr(stage, "node_starts", None)

    if starts is None or len(starts) != n:
        starts = [None] * n

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
            # One start-of-step wall per stage: exact at one node
            # per stage (the default); with more, every node of
            # the stage starts the step from the stage's mean.
            wall_temperature_old,
            start=starts[k],
        )

        nodes.append(node)

        Tg = node.gas_outlet_temperature
        Ts = node.solid_outlet_temperature
        H_gas = node.gas_outlet_enthalpy

    stage.node_starts = [node.node_start for node in nodes]

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
    stage.Q_wall_stored = float(sum(node.Q_wall_stored for node in nodes))

    stage.energy_in = float(
        stage.gas_inlet_enthalpy
        + stage.solid_inlet_enthalpy
    )

    stage.energy_out = float(
        stage.gas_outlet_enthalpy
        + stage.solid_outlet_enthalpy
        + stage.Q_wall_loss
        - stage.Q_reaction
        + stage.Q_wall_stored
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
#     H_vapor = m_dot_vapor * h_solid(Ts_out) into the
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
    wall_temperature_old=None,
    start=None,
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
    # EXACT NODE EXCHANGE
    #
    # Gas and solid flow co-currently through the node, so over
    # its volume v in [0, V]
    #
    #   Cg dTg/dv = -Kgs (Tg - Ts) - Kgw (Tg - Tw) + r
    #   Cs dTs/dv =  Kgs (Tg - Ts) - Kws (Ts - Tw)
    #
    # with r = reaction_power / V on the gas, as the gas balance
    # books it. With the coefficients and Tw held over the node
    # this is linear with constant coefficients and is integrated
    # EXACTLY (_node_mean_affine); the exchanged heats are
    # the coefficients times the node-mean temperature
    # differences.
    #
    # It replaces a forward-Euler step that evaluated every flux
    # at the node INLET. At this stage's NTU_gs ~ 0.3 that
    # overstated the exchange by ~15 % per node and converged
    # only at first order: one node per stage put stage 1's gas
    # outlet 38 K off and the calciner's solid inlet enthalpy
    # 12 % off; five nodes, 5 K; twenty, still ~1.5 K. The exact
    # form has no such error to converge away, and it stays
    # exact when the suspension area -- today the vessel-bore
    # stand-in -- makes NTU large, where forward Euler would not
    # even keep the order of the temperatures.
    #
    # What is still approximate: radiation (k_eff = 0.005 here)
    # is linearised at the node-mean temperatures, and cp_gas is
    # taken at the node-mean gas temperature for the exponent.
    # Both are iterated to self-consistency below. Neither
    # touches conservation: the heats go through the same
    # enthalpy balances as before, which close exactly whatever
    # the profile was.
    #
    # Tw is one value per node, as before. For fixed
    # coefficients Q_gw + Q_ws is AFFINE in Tw, so the wall
    # balance against the (nonlinear) shell loss is a scalar
    # root with an exact slope.
    # ==========================================================

    rad_cfg = ZONE_RAD_CONFIG[model.zone]

    C_rad = (
        rad_cfg["k_eff"]
        * rad_cfg["eps"]
        * sigma
    )

    def h_rad(T1, T2):
        # Exact rewrite of C (T1^4 - T2^4) as h (T1 - T2).
        return C_rad * (T1 + T2) * (T1 * T1 + T2 * T2)

    r_gas = reaction_power / V_cell

    T_low = T_amb
    T_high = max(Tg_in, Ts_in, T_amb)

    # Stored energy, dynamic solve only: the node's share of the
    # lagged lining (stack thickness x rho cp) on its wall node.
    transient_dt = getattr(state, "transient_dt", None)

    if transient_dt is None or wall_temperature_old is None:
        C_w_dt = 0.0
        Tw_old = 0.0
    else:
        C_w_dt = (
            A_wall_cell
            * model.refractory_thickness
            * model.rho_wall
            * model.Cp_wall
            / transient_dt
        )
        Tw_old = float(wall_temperature_old)

    Tw = max(T_amb, min(Tg_in, Ts_in))
    Tg_bar = Tg_in
    Ts_bar = Ts_in

    # Warm start: (Tw, Tg_bar, Ts_bar) this node converged to on
    # the previous solve. Between sweeps, and between dynamic
    # steps, they move by far less than the ~1e3 K the cold guess
    # above is off, which cost two of the node's ~five
    # coefficient passes and most of its shell solves. Only the
    # starting point: the passes run to the same 1e-7 K.
    if start is not None and all(map(math.isfinite, start)):
        Tw = min(max(start[0], T_low), T_high)
        Tg_bar, Ts_bar = float(start[1]), float(start[2])

    # The last skin solved, as the next shell solve's start: the
    # wall root and the coefficient passes move Tw by less each
    # time, and from the midpoint guess every shell solve took
    # ~10 Newton passes.
    shell_guess = [None]

    for _ in range(50):

        Cg = m_dot_g * float(cp_gas(Tg_bar)) + eps

        # The solid's Cp frozen at the node mean, as cp_gas is: it
        # sets only the exponent of the exact exchange. The heat
        # balances below close on h_solid whatever it is.
        Cs = m_dot_s * float(cp_solid(float(Ts_bar))) + eps

        Kgs = (model.hv_gs + h_rad(Tg_bar, Ts_bar)) * model.a_gs
        Kgw = (model.hv_gw + h_rad(Tg_bar, Tw)) * model.a_gw
        Kws = (model.hv_ws + h_rad(Ts_bar, Tw)) * model.a_ws

        # Node means as an affine function of Tw:
        #   (Tg_m, Ts_m) = mean_0 + Tw * mean_1
        mean_0, mean_1 = _node_mean_affine(
            Tg_in, Ts_in, Cg, Cs, Kgs, Kgw, Kws, r_gas, V_cell,
        )

        def exchange(Tw_trial):

            Tg_m = mean_0[0] + Tw_trial * mean_1[0]
            Ts_m = mean_0[1] + Tw_trial * mean_1[1]

            return (
                Tg_m,
                Ts_m,
                Kgs * V_cell * (Tg_m - Ts_m),
                Kgw * V_cell * (Tg_m - Tw_trial),
                Kws * V_cell * (Ts_m - Tw_trial),
            )

        # Q_gw + Q_ws = q0 + q1 Tw, exactly, for these coefficients.
        q0 = V_cell * (Kgw * mean_0[0] + Kws * mean_0[1])
        q1 = V_cell * (
            Kgw * (mean_1[0] - 1.0)
            + Kws * (mean_1[1] - 1.0)
        )

        def wall_residual(Tw_trial):

            R_total_trial, T_shell_trial, _ = shell_closure(
                float(Tw_trial),
                node_shell,
                T_amb,
                T_shell_guess=shell_guess[0],
            )

            shell_guess[0] = T_shell_trial

            residual = (
                q0 + q1 * Tw_trial
                - (Tw_trial - T_amb) / R_total_trial
                - C_w_dt * (Tw_trial - Tw_old)
            )

            # q1 < 0 and the loss rises with Tw, so the residual
            # falls strictly: the root is unique.
            slope = q1 - loss_conductance(
                T_shell_trial,
                node_shell,
                T_amb,
            ) - C_w_dt

            return residual, slope

        Tw_new = _safeguarded_root(
            wall_residual,
            Tw,
            T_low,
            T_high,
        )

        if Tw_new is None:
            # The previous solver's fallback, kept as it was.
            Tw_new = max(T_amb, min(Tg_in, Ts_in))

        Tg_new, Ts_new, _, _, _ = exchange(Tw_new)

        change = max(
            abs(Tw_new - Tw),
            abs(Tg_new - Tg_bar),
            abs(Ts_new - Ts_bar),
        )

        Tw, Tg_bar, Ts_bar = Tw_new, Tg_new, Ts_new

        # The coefficients move only through radiation and
        # cp_gas; 1e-7 K is far inside every tolerance that reads
        # this node, and conservation does not depend on it.
        if change < 1e-7:
            break

    stage.wall_temperature = float(Tw)
    stage.node_start = (float(Tw), float(Tg_bar), float(Ts_bar))

    # ==========================================================
    # HEAT TRANSFER
    # ==========================================================

    _, _, Q_gs, Q_gw, Q_ws = exchange(Tw)

    stage.Q_gs = float(Q_gs)
    stage.Q_gw = float(Q_gw)
    stage.Q_ws = float(Q_ws)

    # ==========================================================
    # WALL LOSS
    # ==========================================================

    R_total, T_shell, _ = shell_closure(
        float(Tw),
        node_shell,
        T_amb,
        T_shell_guess=shell_guess[0],
    )

    wall_loss = (float(Tw) - T_amb) / R_total

    stage.Q_wall_loss = float(wall_loss)
    stage.shell_temperature = float(T_shell)
    stage.Q_wall_stored = float(C_w_dt * (float(Tw) - Tw_old))

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

    H_vapor = m_dot_vapor * h_solid(Ts_out, T_ref)

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
        + stage.Q_wall_stored
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


# ======================================================
# EXACT CO-CURRENT NODE PROFILE
#
# y = (Tg, Ts) obeys y' = A y + b over the node volume, with
#
#   A = [[-(Kgs + Kgw)/Cg,   Kgs/Cg        ],
#        [  Kgs/Cs,        -(Kgs + Kws)/Cs ]]
#   b = [ (Kgw Tw + r)/Cg,   Kws Tw / Cs   ]
#
# so y(v) = e^{Av} y0 + int_0^v e^{As} ds b and the node mean is
#
#   ybar = ( Phi1(A) y0 + Phi2(A) b ) / V
#   Phi1(l) = int_0^V e^{lv} dv          = expm1(lV) / l
#   Phi2(l) = int_0^V (V - s) e^{ls} ds  = (expm1(lV) - lV) / l^2
#
# A 2x2 matrix function is exact through its two eigenvalues
# (Sylvester). A is a diagonal similarity of a symmetric matrix,
# so they are real; equal eigenvalues take the confluent form.
# No inverse of A is needed, so a wall-less node (Kgw = Kws = 0,
# A singular) is handled by the same formula.
# ======================================================
def _phi1(l, V):
    x = l * V
    if abs(x) < 1e-8:
        return V * (1.0 + 0.5 * x)
    return np.expm1(x) / l


def _phi2(l, V):
    x = l * V
    if abs(x) < 1e-4:
        return V * V * (0.5 + x / 6.0 + x * x / 24.0)
    return (np.expm1(x) - x) / (l * l)


def _matrix_function(f, A, V):

    a, b = A[0]
    c, d = A[1]

    half_trace = 0.5 * (a + d)
    disc = max(0.25 * (a - d) ** 2 + b * c, 0.0)
    root = disc ** 0.5

    l1 = half_trace + root
    l2 = half_trace - root

    I = np.eye(2)

    if root > 1e-9 * max(abs(l1), abs(l2), 1e-300):
        return (
            f(l1, V) * (A - l2 * I)
            - f(l2, V) * (A - l1 * I)
        ) / (l1 - l2)

    # Confluent: f(l) I + f'(l) (A - l I), f' by central difference.
    h = 1e-6 * max(abs(half_trace), 1e-12)
    df = (f(half_trace + h, V) - f(half_trace - h, V)) / (2.0 * h)
    return f(half_trace, V) * I + df * (A - half_trace * I)


def _node_mean_affine(
    Tg_in, Ts_in, Cg, Cs, Kgs, Kgw, Kws, r_gas, V,
):
    """Node-mean (Tg, Ts) = mean_0 + Tw * mean_1.

    b is affine in Tw, b = b_0 + Tw b_1, so splitting the
    Phi2 term gives the wall dependence without evaluating the
    matrix functions more than once per coefficient set."""

    A = np.array(
        [
            [-(Kgs + Kgw) / Cg, Kgs / Cg],
            [Kgs / Cs, -(Kgs + Kws) / Cs],
        ]
    )

    P1 = _matrix_function(_phi1, A, V) / V
    P2 = _matrix_function(_phi2, A, V) / V

    b_0 = np.array([r_gas / Cg, 0.0])
    b_1 = np.array([Kgw / Cg, Kws / Cs])

    mean_0 = P1 @ np.array([Tg_in, Ts_in]) + P2 @ b_0
    mean_1 = P2 @ b_1

    return mean_0, mean_1


def _safeguarded_root(fun, x0, lo, hi, tol=1e-6, max_iter=60):
    """Newton on fun -> (residual, slope) for a strictly falling
    residual, kept inside [lo, hi] by bisection. Stops on
    |residual| < tol [W], the criterion the node used before.
    None when [lo, hi] does not bracket a root."""

    # The ends are evaluated only if Newton has to fall back on
    # them: from a warm start it rarely does, and each end is a
    # full shell solve.
    bracket_checked = False

    x = min(max(x0, lo), hi)

    for _ in range(max_iter):

        f, slope = fun(x)

        if abs(f) < tol:
            return x

        if f > 0.0:
            lo = x
        else:
            hi = x

        x_newton = x - f / slope if slope != 0.0 else hi

        if lo < x_newton < hi:
            x = x_newton
            continue

        if not bracket_checked:
            f_lo, _ = fun(lo)
            f_hi, _ = fun(hi)
            if f_lo * f_hi > 0.0:
                return None
            bracket_checked = True

        x = 0.5 * (lo + hi)

    return x
