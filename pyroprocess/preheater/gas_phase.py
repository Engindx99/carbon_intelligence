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
# ======================================================
def gas_temperature_from_enthalpy(preheater, H, state):

    target_h = H / (state.m_dot_g + preheater.eps)

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
# (pyroprocess/preheater/preheater.py). Logic is unchanged.
# ======================================================
def gas_enthalpy_out(preheater, Tg, state):

    H_gas_out = (
        state.m_dot_g
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
):

    H_gas_in = m_dot_g * h_gas(
        Tg_in,
        T_ref,
    )

    H_gas_out = (
        H_gas_in
        + reaction_power
        - Q_gs
        - Q_gw
    )

    Tg_out = model.gas_temperature_from_enthalpy(
        H_gas_out,
        state,
    )

    return H_gas_in, H_gas_out, Tg_out
