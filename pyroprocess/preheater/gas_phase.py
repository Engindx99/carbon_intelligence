import numpy as np

from physics.gas_thermo import SPECIES
from physics.gas_thermo import mixture_cached


# ======================================================
# THE PREHEATER'S GAS (physics.gas_thermo)
#
# Calciner exhaust, plus the free moisture the stages have
# evaporated into it so far. A stream's mass says how much of
# that water it holds: everything above the calciner exhaust
# flow (state.m_dot_g_preheater) is vapour picked up on the
# way. So the mixture follows from the flow alone, and every
# caller that already passes its own flow gets its own gas.
# ======================================================
def gas_mixture(state, m_dot_g):

    base = getattr(state, "Calciner_gas_species_out", None)

    if base is None:
        from pyroprocess.precalciner.raw_meal_inlet import (
            calciner_inlet_species,
        )
        base = calciner_inlet_species(state)

    m_base = float(state.m_dot_g_preheater)
    total = sum(float(base.get(s, 0.0)) for s in SPECIES)

    flows = {s: float(base.get(s, 0.0)) / total * m_base for s in SPECIES}
    flows["H2O"] += max(float(m_dot_g) - m_base, 0.0)

    return mixture_cached(flows)


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

    gas = gas_mixture(state, m_dot_g)

    # Clipped to [250, 4000] K rather than raising, as this
    # inversion always was: a stage mid-sweep may hand it an
    # enthalpy outside the window.
    T_lo, T_hi = 250.0, 4000.0

    if target_h <= gas.h(T_lo, preheater.T_ref):
        return T_lo

    if target_h >= gas.h(T_hi, preheater.T_ref):
        return T_hi

    return float(gas.T_from_h(target_h, preheater.T_ref, T_lo, T_hi))


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

    m_dot_g_out = getattr(preheater, "m_dot_g_out", state.m_dot_g_preheater)

    H_gas_out = (
        m_dot_g_out
        * float(gas_mixture(state, m_dot_g_out).h(float(Tg[-1]), preheater.T_ref))
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
    H_gas_in=None,
):

    # A node inside a stage receives the previous node's exact
    # outlet enthalpy; re-deriving it from Tg_in would add the
    # enthalpy -> temperature inversion error at every node.
    if H_gas_in is None:
        H_gas_in = m_dot_g * gas_mixture(state, m_dot_g).h(
            float(Tg_in),
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
