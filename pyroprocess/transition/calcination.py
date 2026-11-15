import numpy as np

from chemistry import parcels
from chemistry.phases import get_cell_solid_flow
from pyroprocess.precalciner import c5_cyclone


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

    tau_cell = dz / max(u_s, transition.eps)

    spatial_exponent = (
        k_reaction
        * tau_cell
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

    # dQ/dTs for this cell, returned from the same place as the
    # heat itself so the slope and the value cannot drift apart
    # -- the same reason the march computes mass transfer and
    # heat sink from one conversion. The solid row puts it on
    # its diagonal; see physics.variable_flow_rows.
    dQ_dTs_cell = transition.chemistry.reaction_heat_slope(
        float(m_CaCO3_in_cell),
        T_reaction,
        float(tau_cell),
    )

    return (
        k_reaction,
        m_CaCO3_out_cell,
        m_CaCO3_reacted_cell,
        Q_calcination_cell,
        dQ_dTs_cell,
    )


# ======================================================
# THE TRANSITION'S REACTION MARCH (STEADY)
#
# The whole species dict from C5's underflow, cell by cell,
# through the burning zone's own step (ChemistryModel.
# react_burning): calcination plus the four clinkering
# reactions, at the cell's bed temperature for its residence
# dz/u_s. Calcination still runs through this zone's
# CalcinationModel (Transition.clinker_chemistry shares it), so
# the CaCO3 profile is what compute_cell_calcination gives,
# exactly; what is new is that belite, C3A and C4AF form where
# the bed reaches them (chemistry/belite.py).
#
# Returned per cell: the total reaction heat [W] (the solid
# row's sink), the calcination part and its slope dQ/dTs (the
# only part linearised, as in the burning zone), the CO2
# released [kg/s], the CaCO3 entering/leaving, the species
# leaving, and each clinkering reaction's zone total.
# ======================================================
def transition_inlet_species(state):
    """C5's underflow: the solid entering the transition [kg/s]."""

    solids = state.material_flows["calciner"].solids

    return dict(
        c5_cyclone.underflow(
            get_cell_solid_flow(solids, solids.CaCO3.size - 1),
            state,
        )
    )


def march_transition(transition, state, Ts, u_s):

    chem = transition.clinker_chemistry

    N = len(Ts)

    tau = transition.dz / max(float(u_s), transition.eps)

    flow = transition_inlet_species(state)

    heat = {
        chem.belite: 0.0,
        chem.alite: 0.0,
        chem.c3a: 0.0,
        chem.c4af: 0.0,
    }

    Q_cells = np.zeros(N)
    Q_calc_cells = np.zeros(N)
    slope_cells = np.zeros(N)
    dm_CO2_cells = np.zeros(N)
    CaCO3_in_cells = np.zeros(N)
    CaCO3_out_cells = np.zeros(N)
    faces = []

    CaCO3_inlet = float(flow.get("CaCO3", 0.0))

    for i in range(N):

        T_i = max(float(Ts[i]), 1.0)

        CaCO3_in_cells[i] = float(flow["CaCO3"])

        rate, rate_calcination = chem.burning_rates(T_i)

        Q, Q_calc, dm_CO2 = chem.react_burning(
            flow, T_i, tau, rate, rate_calcination, heat
        )

        Q_cells[i] = Q
        Q_calc_cells[i] = Q_calc
        dm_CO2_cells[i] = dm_CO2

        slope_cells[i] = chem.calcination.reaction_heat_slope(
            CaCO3_in_cells[i], T_i, tau
        )

        CaCO3_out_cells[i] = float(flow["CaCO3"])

        faces.append(dict(flow))

    return {
        "CaCO3_in": CaCO3_inlet,
        "Q_cells": Q_cells,
        "Q_calcination_cells": Q_calc_cells,
        "Q_calcination_slope_cells": slope_cells,
        "dm_CO2_cells": dm_CO2_cells,
        "CaCO3_in_cells": CaCO3_in_cells,
        "CaCO3_out_cells": CaCO3_out_cells,
        "face_species": faces,
        "clinkering_heat": {
            "belite": heat[chem.belite],
            "alite": heat[chem.alite],
            "c3a": heat[chem.c3a],
            "c4af": heat[chem.c4af],
        },
    }


# ======================================================
# TRANSITION CALCINATION (CONVERGED PROFILE)
#
# The post-convergence pass: re-marches the converged bed
# temperatures through march_transition (calcination plus the
# clinkering reactions since 15 Nov 2026).
# ======================================================
def resolve_transition_calcination(transition, state, Ts, u_s):
    """The converged profile, from the same march the Picard loop
    ran (march_transition). Returns the calcination arrays as
    before plus `reactions`: the march itself, whose Q_cells is
    the zone's WHOLE reaction heat."""

    eps = transition.eps

    march = march_transition(transition, state, Ts, u_s)

    m_dot_CaCO3_transition_in = march["CaCO3_in"]
    m_dot_CaCO3_in_cells = march["CaCO3_in_cells"]
    m_dot_CaCO3_out_cells = march["CaCO3_out_cells"]
    m_dot_CaCO3_reacted_cells = m_dot_CaCO3_in_cells - m_dot_CaCO3_out_cells
    reaction_heat_cells = march["Q_calcination_cells"].copy()

    reaction_rate_cells = np.array(
        [float(transition.chemistry.reaction_rate(max(float(T), 1.0))) for T in Ts]
    )

    Q_calcination_transition = float(np.sum(reaction_heat_cells))

    m_dot_CaCO3_out_transition = float(m_dot_CaCO3_out_cells[-1])

    X_calcination_transition = 1.0 - (
        m_dot_CaCO3_out_transition / max(m_dot_CaCO3_transition_in, eps)
    )

    cell_conversion = 1.0 - m_dot_CaCO3_out_cells / np.maximum(
        m_dot_CaCO3_in_cells, eps
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
        march,
    )


# ======================================================
# SOLID PHASE STATE UPDATE
# CaCO3 -> CaO
#
# The held-up INVENTORY (state.materials) only: calcination,
# not the clinkering reactions that the flow march now runs in
# this zone. Nothing in the steady or dynamic solve reads this
# inventory (the burning zone takes its inlet from
# material_flows, which carries the full species); it is kept
# for the inventory interface only.
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


# ======================================================
# DYNAMIC STEP: THE PARCEL TRAIN (chemistry/parcels.py)
#
# In a dynamic step the transition's bed is the parcel train
# that was inside the zone at the start of the step, plus the
# solid the calciner discharged during it. Each call steps that
# same start-of-step train at the given bed temperatures, so it
# can stand in for the steady march at every Picard iterate. The
# latest step is left on state: the burning zone takes its
# inflow from it and Twin.advance commits it.
# ======================================================
def kiln_dynamic(state):
    return (
        getattr(state, "transient_dt", None) is not None
        and getattr(state, "kiln_train_transition", None) is not None
    )


def calciner_discharge(state, dt):
    """What the calciner discharged over the step, as the one
    parcel that enters the transition at x = 0 [kg]."""

    solids = state.material_flows["calciner"].solids

    # C5's underflow: the share it does not let up into C4.
    flow = c5_cyclone.underflow(
        get_cell_solid_flow(solids, solids.CaCO3.size - 1),
        state,
    )

    return [({name: value * dt for name, value in flow.items()}, dt)]


def transition_train_step(transition, state, Ts, u_s):

    dt = float(state.transient_dt)

    step = parcels.advance_train(
        state.kiln_train_transition,
        calciner_discharge(state, dt),
        np.asarray(Ts, dtype=float),
        u_s / transition.dz,
        dt,
        lambda T: parcels.BurningReactor(transition.clinker_chemistry, T),
    )

    state.kiln_step_transition = step

    return step


def resolve_transition_calcination_dynamic(transition, state, Ts, u_s):
    """resolve_transition_calcination's outputs, from the train.

    The bed's CaCO3 no longer leaves each cell as what entered
    less what reacted: the cell's hold-up changes over the step.
    So 'in' and 'out' are the CaCO3 crossing the cell's faces and
    'reacted' is what calcined inside it, which the CO2 is booked
    from."""

    step = transition_train_step(transition, state, Ts, u_s)

    eps = transition.eps

    CaCO3_face = np.array(
        [face.get("CaCO3", 0.0) for face in step.face_species]
    )

    m_dot_CaCO3_in_cells = CaCO3_face[:-1].copy()
    m_dot_CaCO3_out_cells = CaCO3_face[1:].copy()

    m_dot_CaCO3_reacted_cells = (
        step.dm_CO2_cells / transition.chemistry.CO2_ratio
    )

    reaction_heat_cells = step.Q_calcination_cells.copy()

    reaction_rate_cells = np.array(
        [float(transition.chemistry.reaction_rate(max(float(T), 1.0))) for T in Ts]
    )

    m_dot_CaCO3_transition_in = float(CaCO3_face[0])
    m_dot_CaCO3_out_transition = float(CaCO3_face[-1])

    X_calcination_transition = 1.0 - (
        m_dot_CaCO3_out_transition / max(m_dot_CaCO3_transition_in, eps)
    )

    cell_conversion = m_dot_CaCO3_reacted_cells / np.maximum(
        m_dot_CaCO3_in_cells, eps
    )

    return (
        m_dot_CaCO3_transition_in,
        m_dot_CaCO3_in_cells,
        m_dot_CaCO3_reacted_cells,
        m_dot_CaCO3_out_cells,
        reaction_heat_cells,
        reaction_rate_cells,
        float(np.sum(reaction_heat_cells)),
        m_dot_CaCO3_out_transition,
        X_calcination_transition,
        cell_conversion,
        {
            "Q_cells": step.Q_cells.copy(),
            "dm_CO2_cells": step.dm_CO2_cells.copy(),
            "face_species": [dict(f) for f in step.face_species[1:]],
            "clinkering_heat": {
                name: float(sum(
                    v for m, v in step.clinkering_heat.items()
                    if m is getattr(transition.clinker_chemistry, name)
                ))
                for name in ("belite", "alite", "c3a", "c4af")
            },
        },
    )
