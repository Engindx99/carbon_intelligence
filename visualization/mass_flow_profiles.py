import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from visualization.zone_profiles import OUTPUT_DIR, preheater_stage_axis


# ======================================================
# SOLID MASS FLOW CHAIN
# Raw Meal -> Preheater -> Precalciner -> Transition ->
# Burning -> Cooler
#
# Values are the steady-state solid stream mass flow
# leaving each stage (physics.steady_state_mass.SteadyStateMassFlow),
# already computed by Twin.step() and held on twin.mass_flow.
# ======================================================

def plot_solid_mass_flow_chain(twin, output_dir=None):

    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    mf = twin.mass_flow

    stages = [
        ("Raw Meal", mf.m_dot_raw_meal),
        ("Preheater", mf.m_dot_s_calciner_in),
        ("Precalciner", mf.m_dot_s_calciner_out),
        ("Transition", mf.m_dot_s_transition),
        ("Burning", mf.m_dot_s_burning),
        ("Cooler", mf.m_dot_s_cooler),
    ]

    labels = [s[0] for s in stages]
    values = [s[1] for s in stages]
    x = np.arange(len(stages))

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(x, values)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Solid Mass Flow: Raw Meal → Clinker")
    ax.set_ylabel("Solid mass flow [kg/s]")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out_path = output_dir / "solid_mass_flow_chain.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return out_path


# ======================================================
# CLINKER MINERAL PHASES
# C2S, C3S, C3A, C4AF are only formed in the Burning zone
# (chemistry.reactions.ChemistryModel.apply_burning), so
# the axial profile is plotted for that zone only.
# ======================================================

def plot_clinker_phase_profile(twin, output_dir=None):

    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    state = twin.state
    zone = twin.burning
    dz = zone.L / zone.N
    x = (np.arange(zone.N) + 0.5) * dz

    solids = state.material_flows["burning"].solids

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(x, solids.C2S, label="C2S (Belite)")
    ax.plot(x, solids.C3S, label="C3S (Alite)")
    ax.plot(x, solids.C3A, label="C3A")
    ax.plot(x, solids.C4AF, label="C4AF")

    ax.set_title("Burning Zone – Clinker Mineral Phase Formation")
    ax.set_xlabel("Axial position [m]")
    ax.set_ylabel("Solid phase flow [kg/s]")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out_path = output_dir / "clinker_phase_profile.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return out_path


# ======================================================
# CO2 / H2O GENERATION PROFILES
#
# Gas-phase generation is only nonzero where a reaction
# model releases it into state.material_flows[zone].gases:
#   Preheater   -> H2O (drying)
#   Precalciner -> CO2 (calcination), H2O (dehydroxylation)
#   Transition  -> CO2 (residual in-flight calcination)
# ======================================================

GAS_GENERATION_ZONES = [
    ("preheater", "Preheater"),
    ("calciner", "Precalciner"),
    ("transition", "Transition"),
]


def plot_gas_generation_profile(twin, output_dir=None):

    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    state = twin.state

    fig, axes = plt.subplots(
        len(GAS_GENERATION_ZONES),
        1,
        figsize=(8, 3 * len(GAS_GENERATION_ZONES)),
    )

    for ax, (key, label) in zip(axes, GAS_GENERATION_ZONES):

        zone = getattr(twin, key)

        if key == "preheater":
            x = preheater_stage_axis(ax, zone)
        else:
            dz = zone.L / zone.N
            x = (np.arange(zone.N) + 0.5) * dz
            ax.set_xlabel("Axial position [m]")

        gases = state.material_flows[key].gases

        ax.plot(x, gases.CO2, label="CO2")
        ax.plot(x, gases.H2O, label="H2O")

        ax.set_title(label)
        ax.set_ylabel("Gas generation rate [kg/s]")
        ax.legend()
        ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out_path = output_dir / "gas_generation_profile.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return out_path


def plot_mass_flow_profiles(twin, output_dir=None):

    return [
        plot_solid_mass_flow_chain(twin, output_dir),
        plot_clinker_phase_profile(twin, output_dir),
        plot_gas_generation_profile(twin, output_dir),
    ]
