from physics.physics import outlet_face_value
from physics.physics import T_gas_from_h
from physics.gas_thermo import GasMixture

# The variable-flow gas row moved to physics.variable_flow_rows when
# the calciner adopted it too (Faz 1c). Re-exported here so this
# module stays the transition zone's gas-side entry point.
from physics.variable_flow_rows import apply_gas_energy_balance  # noqa: F401


# ======================================================
# GAS INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Transition.gas_inlet_temperature_from_enthalpy()
# (pyroprocess/transition.py). Logic is unchanged; `self`
# was renamed to `transition` since this is now a free
# function taking the owning Transition instance explicitly.
# ======================================================
def inlet_gas_flow(state):
    """The gas Burning discharged [kg/s]: its burner gas plus
    the CO2 of its own residual calcination, the flow its outlet
    face published with Hgas_burning_out. Before Burning has run
    once there is no such face yet, and the burner gas is all
    there is."""

    return float(getattr(state, "m_dot_g_burning_out", state.m_dot_g))


def inlet_species(state):
    """The species the kiln gas brings in: what the burning zone
    published for its outlet face (physics.gas_thermo). Before
    Burning has run once there is no such face, and the burner
    gas is all there is."""

    species = getattr(state, "Burning_gas_species_out", None)

    if species is None:
        from pyroprocess.burning.gas_phase import kiln_inlet_species
        species = kiln_inlet_species(state)

    return species


def gas_inlet_temperature_from_enthalpy(transition, H, state):

    # The INLET flow, not state.m_dot_g_transition -- that
    # scalar already carries every kg of CO2 this zone will
    # release, so dividing the incoming enthalpy by it invented
    # a colder inlet than Burning actually discharged. Nor
    # state.m_dot_g, the burner gas alone: H was built by
    # Burning on its OUTLET face flow, which carries the kiln's
    # calcination CO2 too, and dividing by the smaller flow
    # read the inlet ~56 K hot at 2300 K (13 Oct 2026). The
    # inversion has to use the flow H was built on, or the
    # handoff conserves J/s while rescaling K.
    m_dot_g = inlet_gas_flow(state)

    if m_dot_g <= transition.eps:
        return transition.T_ref

    h_target = H / m_dot_g

    # Inverted with the mixture H was built on, the burning zone's
    # outlet gas, so the handoff keeps its temperature.
    return GasMixture(inlet_species(state)).T_from_h(
        h_target,
        transition.T_ref,
        transition.T_ref,
        4000.0,
    )


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Transition.gas_enthalpy_out()
# (pyroprocess/transition.py).
#
# This used to return Hg[0], the last CELL CENTRE. The gas
# leaves through the outlet FACE half a cell further
# downstream, so that was a systematic O(dz) bias in the
# handoff to the precalciner. It is the reconstructed
# outlet face value that the second-order flux in
# apply_gas_energy_balance() transports out of cell 0, so
# returning anything else would leak that difference out of
# the zone energy balance. Hg is m_dot_g * h_gas(Tg)
# elementwise, i.e. affine in h, so the extrapolation may be
# taken on Hg directly. Same construction as
# pyroprocess/burning/gas_phase.py.
# ======================================================
def gas_enthalpy_out(Hg):

    return outlet_face_value(Hg, reverse=True)
