"""
Precalciner firing.

Until now the calciner had no combustion model at all: every kilogram
of the plant's fuel burned at the kiln burner, so the calciner ran on
recuperated heat alone, sat at 1245 K and calcined 1.3% of the CaCO3
instead of the 90-95% an ILC calciner is built for. The meal then
arrived at the kiln still carbonated, starved the clinkering reactions
of CaO, and the kiln had to finish the calcination it was never sized
for.

This mirrors pyroprocess/burning/combustion.py deliberately -- same
fuel model, same efficiency curve, same axial-distribution helper --
so the two firings stay comparable and there is one fuel model in the
plant rather than two that can drift apart.

What is NOT modelled here, and matters for later work: char burnout
kinetics, the calciner's own gas-solid slip, CO, and any dependence of
the heat-release profile on injector placement. The axial shape is the
same fixed, calibrated weight vector the other zones use.
"""

from physics.physics import combustion_axial_distribution
from physics.physics import fuel_heat_release
from physics.physics import resample_axial_weights
from physics.physics import ZONE_ENERGY_WEIGHTS


# ======================================================
# FUEL HEAT RELEASE
#
# The calciner burns the complement of the kiln's share.
# Both read the same fuel.kiln_fraction, so the two can
# never sum to more (or less) than the plant's fuel.
# ======================================================
def fuel_heat_release_for(calciner, state):

    # main._update_steady_state_mass_flow already partitioned the
    # fuel and published this zone's share, so reading it back
    # keeps the mass that enters the gas stream and the energy
    # released here derived from one and the same number.
    fuel_rate_calciner = float(
        getattr(state, "m_dot_fuel_calciner", 0.0)
    )

    return fuel_heat_release(
        fuel_rate_total=fuel_rate_calciner,
        O2=calciner.O2,
        O2_opt=calciner.O2_opt,
        O2_sigma2=calciner.O2_sigma2,
        LHV={
            "petcoke": 32.0e6,
        },
        inputs=None,
        eps=calciner.eps,
    )


# ======================================================
# AXIAL COMBUSTION HEAT DISTRIBUTION
#
# ZONE_ENERGY_WEIGHTS["calciner"]["axial"] has been defined
# since the zone tables were written but nothing ever read
# it, because nothing ever burned here. It rises towards the
# gas inlet, i.e. the fuel releases its heat low in the
# vessel where the tertiary air enters.
# ======================================================
def axial_heat_distribution(N, Q_calciner):

    weights = resample_axial_weights(
        ZONE_ENERGY_WEIGHTS["calciner"]["axial"],
        N,
    )

    return combustion_axial_distribution(
        Q_total=Q_calciner,
        weights=weights,
    )
