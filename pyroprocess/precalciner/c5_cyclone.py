# ======================================================
# C5: THE CALCINER'S OUTLET CYCLONE
#
# The calciner gas carries the calcined meal up the gooseneck
# into the two C5s (geometry/macros/plant_topology_2d.bas).
# C5 sends eta of the solid down into the kiln inlet chamber
# and lets the rest up with the gas into C4, the preheater's
# Stage 1; C4's underflow brings it back into the calciner.
# That is the plant's hot-meal loop: at steady state it adds
# flow through C4 and the calciner, not mass to the plant.
#
# C5 is a separation node on the calciner's outlet face: the
# solid there splits by MASS, so each species, the enthalpy
# and the flow split in the same ratio and both streams leave
# at the outlet temperature. It is adiabatic for now; its
# volume and wall belong to the calciner zone (next step).
#
# configs `calciner.c5_separation_efficiency`, read by the
# Calciner and published here as state.C5_separation_efficiency
# so every reader uses the value the calciner split with.
# ======================================================


def separation_efficiency(state):
    """C5's eta: the share of the calciner's solid outlet that
    goes down into the kiln. 1.0 before the calciner has run."""

    return float(getattr(state, "C5_separation_efficiency", 1.0))


def underflow(flow, state):
    """The kiln's share of a calciner-outlet species flow dict."""

    eta = separation_efficiency(state)

    return {name: value * eta for name, value in flow.items()}


def escaping_dust(flow, state):
    """The share of a calciner-outlet species flow dict that C5
    lets up into C4."""

    k = 1.0 - separation_efficiency(state)

    return {name: value * k for name, value in flow.items()}
