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
    #
    # Energy out:
    #
    #   Hgas_out
    # + Hsolid_out
    # + Q_wall_loss
    # + Q_calcination
    #
    # Residual:
    #
    #   Energy_in - Energy_out
    #
    # Target:
    #
    #   residual -> 0
    # ======================================================

    state.Calciner_energy_balance = (
        state.Hgas_calciner_in
        + state.Hsolid_calciner_in
        - state.Hgas_calciner_out
        - state.Hsolid_calciner_out
        - state.Wall_loss_calciner
        - state.Calcination_Q_sink
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
            state.Calcination_Q_sink
        )
        + calciner.eps
    )

    state.Calciner_energy_balance_relative = (
        state.Calciner_energy_balance
        / energy_scale
    )

    # ======================================================
    # ENERGY IN
    # ======================================================

    calciner_energy_in = (
        state.Hgas_calciner_in
        + state.Hsolid_calciner_in
    )

    # ======================================================
    # ENERGY OUT
    #
    # Includes:
    #   gas
    #   solid
    #   wall loss
    #   calcination reaction
    # ======================================================

    calciner_energy_out = (
        state.Hgas_calciner_out
        + state.Hsolid_calciner_out
        + state.Wall_loss_calciner
        + state.Calcination_Q_sink
    )

    # ======================================================
    # ENERGY RESIDUAL
    # ======================================================

    calciner_residual = (
        calciner_energy_in
        - calciner_energy_out
    )

    return state
