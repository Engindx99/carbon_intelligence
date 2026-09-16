import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas


# ======================================================
# GAS INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Preheater.gas_temperature_from_enthalpy()
# (pyroprocess/preheater/preheater.py). Logic is unchanged;
# `self` was renamed to `preheater` since this is now a
# free function taking the owning Preheater instance
# explicitly.
#
# `m_dot_g` [kg/s] is the gas mass flow carrying H; it
# defaults to the preheater gas inlet flow. Stages downstream
# of evaporating moisture carry more gas than that and pass
# their own flow.
# ======================================================
def gas_temperature_from_enthalpy(preheater, H, state, m_dot_g=None):

    if m_dot_g is None:
        m_dot_g = state.m_dot_g_preheater

    target_h = H / (m_dot_g + preheater.eps)

    T = 1200.0

    for _ in range(50):

        h = float(h_gas(T, preheater.T_ref))
        cp = float(cp_gas(T))

        residual = h - target_h

        if abs(residual) < 1e-6:
            break

        T_new = T - residual / (cp + preheater.eps)

        T = np.clip(
            T_new,
            250.0,
            4000.0,
        )

    return float(T)


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Preheater.gas_enthalpy_out()
# (pyroprocess/preheater/preheater.py).
#
# The exhaust leaving stage 5 carries the moisture
# evaporated in the stages (heat_transfer.thermal_step()
# stores that outlet flow as preheater.m_dot_g_out), so it is
# that flow, not the gas inlet flow, that multiplies h.
# ======================================================
def gas_enthalpy_out(preheater, Tg, state):

    H_gas_out = (
        getattr(preheater, "m_dot_g_out", state.m_dot_g_preheater)
        * float(h_gas(Tg[-1], preheater.T_ref))
    )

    return H_gas_out


# ======================================================
# STAGE GAS ENERGY BALANCE
#
# Moved from the gas-enthalpy block inside
# PreheaterStage.solve() (pyroprocess/preheater/stage.py).
# Logic is unchanged; this is now a free function taking
# the owning PreheaterStage instance's context explicitly
# (it does not mutate `stage` itself -- the caller,
# heat_transfer.solve_stage(), stores the returned values
# on `stage` in the same STORE RESULTS section as before).
#
# Moisture evaporated in the stage enters the gas as mass
# m_dot_vapor [kg/s] carrying H_vapor [W], its enthalpy as it
# leaves the solid (solid_phase / heat_transfer.solve_stage).
# The outlet temperature is therefore recovered on the outlet
# gas flow m_dot_g + m_dot_vapor. Both default to zero, which
# is the previous closed-gas stage exactly.
# ======================================================
def apply_stage_gas_energy_balance(
    model,
    state,
    Tg_in,
    m_dot_g,
    reaction_power,
    Q_gs,
    Q_gw,
    T_ref,
    m_dot_vapor=0.0,
    H_vapor=0.0,
):

    H_gas_in = m_dot_g * h_gas(
        Tg_in,
        T_ref,
    )

    H_gas_out = (
        H_gas_in
        + H_vapor
        + reaction_power
        - Q_gs
        - Q_gw
    )

    Tg_out = model.gas_temperature_from_enthalpy(
        H_gas_out,
        state,
        m_dot_g + m_dot_vapor,
    )

    return H_gas_in, H_gas_out, Tg_out
