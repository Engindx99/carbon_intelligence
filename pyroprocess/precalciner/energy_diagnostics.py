# ======================================================
# ZONE ENERGY BALANCE
#
# Moved from the end of Calciner.apply()
# (pyroprocess/precalciner.py). Logic is unchanged; this
# is the outer-loop energy closure bookkeeping for the
# calciner zone as a whole, computed from state fields
# already committed by the chemistry/thermal coupling
# loop (as opposed to thermal_solver.thermal_step(), which
# tracks the closure of a single thermal solve).
# ======================================================
def compute_energy_balance(calciner, state):

    # ======================================================
    # STEADY-STATE ENERGY BALANCE
    #
    # Energy in:
    #
    #   Hgas_in
    # + Hsolid_in
    # + Q_calciner (the calciner fuel's heat release)
    #
    # Energy out:
    #
    #   Hgas_out
    # + Hsolid_out
    # + Q_wall_loss
    # + Q_calcination
    # + Q_dehydroxylation
    #
    # Residual:
    #
    #   Energy_in - Energy_out
    #
    # Target:
    #
    #   residual -> 0
    # ======================================================

    # Q_calciner is the calciner fuel's heat release; the zone's own
    # energy_in (thermal_solver) books it, and leaving it out here put
    # this figure off by exactly that, ~ -101.6 MW.
    state.Calciner_energy_balance = (
        state.Hgas_calciner_in
        + state.Hsolid_calciner_in
        + state.Q_calciner
        - state.Hgas_calciner_out
        - state.Hsolid_calciner_out
        - state.Wall_loss_calciner
        - state.Calciner_Q_sink
        - state.Calciner_stored_energy_change
    )

    # ======================================================
    # RELATIVE ENERGY BALANCE
    # ======================================================

    energy_scale = (
        abs(
            state.Hgas_calciner_in
        )
        + abs(
            state.Hsolid_calciner_in
        )
        + abs(
            state.Calciner_Q_sink
        )
        + abs(
            state.Q_calciner
        )
        + calciner.eps
    )

    state.Calciner_energy_balance_relative = (
        state.Calciner_energy_balance
        / energy_scale
    )

    return state
