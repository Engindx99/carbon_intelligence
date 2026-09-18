from physics.physics import fuel_heat_release
from physics.physics import combustion_axial_distribution
from physics.physics import ZONE_ENERGY_WEIGHTS
from physics.physics import resample_axial_weights


# ======================================================
# FUEL HEAT RELEASE
#
# Moved from inside Burning.thermal_step()
# (pyroprocess/burning.py). Logic is unchanged; `self`
# was renamed to `burning` since this is now a free
# function taking the owning Burning instance explicitly.
# ======================================================
def fuel_heat_release_for(burning, inputs):

    # Only the kiln burner's share. The rest fires in the
    # precalciner (pyroprocess/precalciner), so passing the
    # plant total here would release the whole plant's fuel
    # energy twice over once the calciner is fired too.
    fuel_rate_total = (
        burning.kiln_fuel_fraction
        * inputs.get("Fuel_rate_total", 1.0)
    )

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

    # Must match state.Burning_Q_sink_cells, which is what the
    # solid row actually absorbs. Once calcination started running
    # in the kiln (Faz 4b) the four clinkering terms stopped being
    # the whole story, and summing only them left the zone energy
    # balance short by exactly the kiln's calcination heat --
    # 19.07 MW, a 31% residual.
    return (
        state.Belite_Q_sink
        + state.Alite_Q_sink
        + state.C3A_Q_sink
        + state.C4AF_Q_sink
        + float(getattr(state, "Calcination_Q_burning", 0.0))
    )


# ======================================================
# AXIAL COMBUSTION HEAT DISTRIBUTION
#
# Moved from inside Burning.thermal_step()
# (pyroprocess/burning.py).
#
# These weights are a flame shape: they describe where the
# fuel releases its heat into the gas. They used to be
# reused to spread the clinkering reaction sink as well,
# which tied the location of the reactions to the location
# of the flame. The reaction sink now comes from the
# kinetics instead (state.Burning_Q_sink_cells, built cell
# by cell in ChemistryModel.apply_burning from the local
# bed temperature), so this function only distributes
# combustion heat.
# ======================================================
def axial_heat_distribution(N, Q_burning):

    weights = resample_axial_weights(
        ZONE_ENERGY_WEIGHTS["burning"]["axial"],
        N,
    )

    q_cell = combustion_axial_distribution(
        Q_total=Q_burning,
        weights=weights,
    )

    return q_cell
