import numpy as np


# ======================================================
# PER-CELL CALCINATION KINETICS
#
# Moved from the per-cell loop inside Transition.thermal_step()
# (pyroprocess/transition.py), where this exact formula was
# duplicated once inside the Picard loop (using the current
# iterate's solid temperature) and again after convergence
# (using the converged solid temperature). Logic is unchanged;
# `self` was renamed to `transition`. Extracting it into one
# function removes the duplicated *code*; both call sites still
# invoke it the same number of times, with the same inputs, so
# the numeric result at each call site is unchanged.
# ======================================================
def compute_cell_calcination(transition, Ts_cell, m_CaCO3_in_cell, dz, u_s):

    T_reaction = max(float(Ts_cell), 1.0)

    k_reaction = float(
        transition.chemistry.reaction_rate(T_reaction)
    )

    spatial_exponent = (
        k_reaction
        * dz
        / max(u_s, transition.eps)
    )

    m_CaCO3_out_cell = (
        m_CaCO3_in_cell
        * np.exp(-spatial_exponent)
    )

    m_CaCO3_out_cell = np.clip(
        m_CaCO3_out_cell,
        0.0,
        m_CaCO3_in_cell,
    )

    m_CaCO3_reacted_cell = (
        m_CaCO3_in_cell
        - m_CaCO3_out_cell
    )

    Q_calcination_cell = (
        m_CaCO3_reacted_cell
        * transition.chemistry.deltaH
    )

    return (
        k_reaction,
        m_CaCO3_out_cell,
        m_CaCO3_reacted_cell,
        Q_calcination_cell,
    )


# ======================================================
# TRANSITION CALCINATION (CONVERGED PROFILE)
#
# Moved from Transition.thermal_step() (pyroprocess/transition.py),
# the post-convergence calcination pass. Logic is unchanged;
# `self` was renamed to `transition`.
# ======================================================
def resolve_transition_calcination(transition, state, Ts, u_s):

    N = len(Ts)
    dz = transition.dz
    eps = transition.eps

    m_dot_CaCO3_transition_in = getattr(
        state,
        "m_dot_CaCO3_out_calciner",
        0.0,
    )

    m_dot_CaCO3_in_cells = np.zeros(N)
    m_dot_CaCO3_reacted_cells = np.zeros(N)
    m_dot_CaCO3_out_cells = np.zeros(N)
    reaction_heat_cells = np.zeros(N)
    reaction_rate_cells = np.zeros(N)

    if m_dot_CaCO3_transition_in > eps:
        m_dot_CaCO3_in_cells[0] = (
            m_dot_CaCO3_transition_in
        )

        for i in range(N):

            m_in = max(
                float(m_dot_CaCO3_in_cells[i]),
                0.0,
            )

            (
                k_reaction,
                m_out,
                m_reacted,
                Q_cell,
            ) = compute_cell_calcination(
                transition,
                Ts[i],
                m_in,
                dz,
                u_s,
            )

            reaction_rate_cells[i] = k_reaction

            m_dot_CaCO3_out_cells[i] = m_out
            m_dot_CaCO3_reacted_cells[i] = m_reacted

            reaction_heat_cells[i] = Q_cell

            if i + 1 < N:
                m_dot_CaCO3_in_cells[i + 1] = m_out

    Q_calcination_transition = np.sum(
        reaction_heat_cells
    )

    m_dot_CaCO3_out_transition = (
        m_dot_CaCO3_out_cells[-1]
    )

    X_calcination_transition = (
        1.0
        - (
            m_dot_CaCO3_out_transition
            / max(
                m_dot_CaCO3_transition_in,
                eps,
            )
        )
    )

    cell_conversion = (
        1.0
        - m_dot_CaCO3_out_cells
        / np.maximum(
            m_dot_CaCO3_in_cells,
            eps
        )
    )

    return (
        m_dot_CaCO3_transition_in,
        m_dot_CaCO3_in_cells,
        m_dot_CaCO3_reacted_cells,
        m_dot_CaCO3_out_cells,
        reaction_heat_cells,
        reaction_rate_cells,
        Q_calcination_transition,
        m_dot_CaCO3_out_transition,
        X_calcination_transition,
        cell_conversion,
    )


# ======================================================
# SOLID PHASE STATE UPDATE
# CaCO3 -> CaO
#
# Moved from Transition.thermal_step() (pyroprocess/transition.py).
# Logic is unchanged; `self` was renamed to `transition`.
# ======================================================
def update_solid_phase_composition(transition, state, cell_conversion):

    transition_solids = state.materials["transition"].solids

    CaCO3_before = (
        transition_solids.CaCO3.copy()
    )

    CaO_before = (
        transition_solids.CaO.copy()
    )

    # ------------------------------------------------------
    # Cell-wise conversion from transition kinetics
    # ------------------------------------------------------

    CaCO3_reacted_fraction = np.clip(
        cell_conversion.copy(),
        0.0,
        1.0,
    )

    CaCO3_reacted_inventory = (
        CaCO3_before
        * CaCO3_reacted_fraction
    )

    CaCO3_reacted_inventory = np.minimum(
        CaCO3_reacted_inventory,
        CaCO3_before,
    )

    # ------------------------------------------------------
    # CaCO3 consumption
    # ------------------------------------------------------

    transition_solids.CaCO3[:] = (
        CaCO3_before
        - CaCO3_reacted_inventory
    )

    # ------------------------------------------------------
    # CaO generation
    # ------------------------------------------------------

    CaO_generated_inventory = (
        CaCO3_reacted_inventory
        * transition.chemistry.CaO_ratio
    )

    transition_solids.CaO[:] = (
        CaO_before
        + CaO_generated_inventory
    )

    # ------------------------------------------------------
    # CO2 generation (gas phase)
    #
    # Zone-local inventory only: this array holds the CO2
    # generated by this zone's own reaction. It is not
    # transferred to/from neighboring zones.
    # ------------------------------------------------------

    transition_gases = state.materials["transition"].gases

    transition_gases.CO2[:] = (
        CaCO3_reacted_inventory
        * transition.chemistry.CO2_ratio
    )
