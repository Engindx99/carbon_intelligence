# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Preheater.solid_enthalpy_out()
# (pyroprocess/preheater/preheater.py). Logic is unchanged.
# ======================================================
def solid_enthalpy_out(preheater, Ts, state):

    H_solid_out = (
        state.m_dot_s_preheater
        * preheater.Cp_s
        * (Ts[0] - preheater.T_ref)
    )

    return H_solid_out


# ======================================================
# STAGE SOLID ENERGY BALANCE
#
# Moved from the solid-enthalpy block inside
# PreheaterStage.solve() (pyroprocess/preheater/stage.py).
# Logic is unchanged; this is now a free function that does
# not mutate `stage` itself -- the caller,
# heat_transfer.solve_stage(), stores the returned values
# on `stage` in the same STORE RESULTS section as before.
# ======================================================
def apply_stage_solid_energy_balance(
    model,
    m_dot_s,
    Ts_in,
    Q_gs,
    Q_ws,
    T_ref,
    eps,
):

    H_solid_in = (
        m_dot_s
        * model.Cp_s
        * (Ts_in - T_ref)
    )

    H_solid_out = (
        H_solid_in
        + Q_gs
        - Q_ws
    )

    Ts_out = (
        T_ref
        + H_solid_out
        / (m_dot_s * model.Cp_s + eps)
    )

    return H_solid_in, H_solid_out, Ts_out
