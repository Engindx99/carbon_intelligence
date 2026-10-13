from physics.physics import h_solid
from physics.physics import T_solid_from_h


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Preheater.solid_enthalpy_out()
# (pyroprocess/preheater/preheater.py).
#
# The solid leaving stage 1 has lost the moisture evaporated
# in the stages, so it is that outlet flow
# (preheater.m_dot_s_out, stored by
# heat_transfer.thermal_step()) that multiplies the enthalpy.
# ======================================================
def solid_enthalpy_out(preheater, Ts, state):

    H_solid_out = (
        getattr(preheater, "m_dot_s_out", state.m_dot_s_preheater)
        * h_solid(float(Ts[0]), preheater.T_ref)
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

    H_solid_in = m_dot_s * h_solid(Ts_in, T_ref)

    H_solid_out = (
        H_solid_in
        + Q_gs
        - Q_ws
    )

    Ts_out = T_solid_from_h(
        H_solid_out / max(m_dot_s, eps),
        T_ref,
    )

    return H_solid_in, H_solid_out, Ts_out
