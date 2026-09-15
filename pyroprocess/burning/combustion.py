import numpy as np

from physics.physics import fuel_heat_release
from physics.physics import combustion_axial_distribution
from physics.physics import ZONE_ENERGY_WEIGHTS


# ======================================================
# FUEL HEAT RELEASE
#
# Moved from inside Burning.thermal_step()
# (pyroprocess/burning.py). Logic is unchanged; `self`
# was renamed to `burning` since this is now a free
# function taking the owning Burning instance explicitly.
# ======================================================
def fuel_heat_release_for(burning, inputs):

    fuel_rate_total = inputs.get("Fuel_rate_total", 1.0)
    O2 = inputs.get("O2", 3.5)

    return fuel_heat_release(
        fuel_rate_total=fuel_rate_total,
        O2=O2,
        O2_opt=burning.O2_opt,
        O2_sigma2=burning.O2_sigma2,
        LHV={
            "petcoke": 32.0e6,
        },
        inputs=inputs,
        eps=burning.eps,
    )


# ======================================================
# CLINKERING REACTION HEAT SINK
#
# Moved from inside Burning.thermal_step() and
# Burning.apply() (pyroprocess/burning.py), where the same
# sum was computed twice. Logic is unchanged.
# ======================================================
def reaction_heat_sink(state):

    return (
        state.Belite_Q_sink
        + state.Alite_Q_sink
        + state.C3A_Q_sink
        + state.C4AF_Q_sink
    )


# ======================================================
# AXIAL ENERGY DISTRIBUTION
#
# Moved from inside Burning.thermal_step()
# (pyroprocess/burning.py). Logic is unchanged.
# ======================================================
def axial_heat_distribution(N, Q_burning, Burning_Q_sink):

    weights = ZONE_ENERGY_WEIGHTS["burning"]["axial"]

    if len(weights) != N:
        raise ValueError(
            f"Burning axial weights length ({len(weights)}) "
            f"must match N ({N})."
        )

    q_cell = combustion_axial_distribution(
        Q_total=Q_burning,
        weights=weights,
    )

    reaction_q_cell = (
        Burning_Q_sink
        * np.asarray(weights, dtype=float)
    )

    return q_cell, reaction_q_cell
