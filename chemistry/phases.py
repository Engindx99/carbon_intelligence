from dataclasses import dataclass, fields
import numpy as np

from chemistry.composition import RAW_MEAL_COMPOSITION


@dataclass
class SolidPhases:

    # ================= MOISTURE =================
    H2O: np.ndarray

    # ================= BOUND WATER =================
    Bound_H2O: np.ndarray

    # ================= CARBONATES =================
    CaCO3: np.ndarray

    # ================= OXIDES =================
    CaO: np.ndarray
    SiO2: np.ndarray
    Al2O3: np.ndarray
    Fe2O3: np.ndarray

    # ================= CLINKER PHASES =================
    C2S: np.ndarray
    C3S: np.ndarray
    C3A: np.ndarray
    C4AF: np.ndarray


@dataclass
class GasPhases:

    CO2: np.ndarray
    H2O: np.ndarray


def copy_solid_phases(
    source: SolidPhases,
    target: SolidPhases,
):
    """
    Copy solid-phase mass arrays from one zone to another.

    Arrays are copied by value, not by reference.
    Therefore source and target remain independent.
    """

    for field in fields(SolidPhases):

        source_array = getattr(source, field.name)
        target_array = getattr(target, field.name)

        if source_array.shape != target_array.shape:
            raise ValueError(
                f"Solid phase shape mismatch for {field.name}: "
                f"{source_array.shape} != {target_array.shape}"
            )

        target_array[:] = source_array


def resample_solid_phases(
    source: SolidPhases,
    target: SolidPhases,
):
    """
    Transfer solid-phase composition from a source zone to a
    target zone with a different cell count. The source array
    is treated as a profile sampled at its own cell centers
    and linearly interpolated onto the target's cell centers,
    then rescaled so the target's total mass per species
    exactly matches the source's total mass per species.

    Reduces to copy_solid_phases when source and target share
    the same cell count.
    """

    for field in fields(SolidPhases):

        source_array = getattr(source, field.name)
        target_array = getattr(target, field.name)

        n_src = source_array.shape[0]
        n_tgt = target_array.shape[0]

        x_src = (np.arange(n_src) + 0.5) / n_src
        x_tgt = (np.arange(n_tgt) + 0.5) / n_tgt

        resampled = np.interp(x_tgt, x_src, source_array)

        total_source = np.sum(source_array)
        total_resampled = np.sum(resampled)

        if total_resampled > 0.0:
            resampled *= total_source / total_resampled

        target_array[:] = resampled


# ======================================================
# STEADY-STATE SPECIES FLOW HELPERS [kg/s]
#
# A single cell's solid flow is handled as a plain dict
# {phase name: kg/s} so the reaction models can march it
# cell by cell; these move it in and out of the per-cell
# SolidPhases arrays held in state.material_flows.
# ======================================================
def raw_meal_solid_flow(m_dot_raw_meal):
    """
    Species mass flows [kg/s] of a raw-meal stream of total
    mass flow m_dot_raw_meal [kg/s], split by
    chemistry.composition.RAW_MEAL_COMPOSITION (a 100 000 kg
    mass basis). The species sum equals m_dot_raw_meal.
    """

    basis = sum(RAW_MEAL_COMPOSITION.values())

    return {
        f.name: (
            float(m_dot_raw_meal)
            * RAW_MEAL_COMPOSITION[f.name]
            / basis
        )
        for f in fields(SolidPhases)
    }


def get_cell_solid_flow(solids: SolidPhases, i):

    return {
        f.name: float(getattr(solids, f.name)[i])
        for f in fields(SolidPhases)
    }


def set_cell_solid_flow(solids: SolidPhases, i, flow):

    for f in fields(SolidPhases):
        getattr(solids, f.name)[i] = flow[f.name]


def total_solid_flow(flow):

    return float(sum(flow.values()))
