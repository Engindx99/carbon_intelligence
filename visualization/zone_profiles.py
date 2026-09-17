import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

ZONES = [
    ("preheater", "Preheater"),
    ("calciner", "Precalciner"),
    ("transition", "Transition"),
    ("burning", "Burning"),
    ("cooler", "Cooler"),
]


PREHEATER_STAGE_XLABEL = "Cyclone stage (gas: 1 → 5, solid feed: 5 → 1)"


AXIAL_XLABEL = "Axial position along solid path z [m]"


def preheater_stage_axis(ax, preheater, x=None):
    # Preheater cells are cyclone stages, not an axial mesh.
    stage_labels = [f"Stage {s.stage_id}" for s in preheater.stages]

    if x is None:
        x = np.arange(preheater.N)
        ax.set_xticks(x)
        ax.set_xticklabels(stage_labels)
        ax.set_xlabel(PREHEATER_STAGE_XLABEL)
        return x

    # Stages placed on the global axis: metres below, stage names on top.
    top = ax.secondary_xaxis("top")
    top.set_xticks(x)
    top.set_xticklabels(stage_labels)
    top.set_xlabel(PREHEATER_STAGE_XLABEL)
    return x


def plot_zone_temperature_profiles(twin, output_dir=None):

    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    state = twin.state

    fig, axes = plt.subplots(
        len(ZONES),
        1,
        figsize=(8, 3 * len(ZONES)),
    )

    for ax, (key, label) in zip(axes, ZONES):

        zone = getattr(twin, key)

        segment = twin.axial_layout[key]
        x = segment.z_at_index

        if key == "preheater":
            preheater_stage_axis(ax, zone, x=x)

        ax.set_xlim(segment.z_start, segment.z_end)
        ax.set_xlabel(AXIAL_XLABEL)

        Tg = getattr(state, f"Tg_{key}")
        Ts = getattr(state, f"Ts_{key}")
        Tw = getattr(state, f"Tw_{key}")

        ax.plot(x, Tg, label="Gas")
        ax.plot(x, Ts, label="Solid")
        ax.plot(x, Tw, label="Wall")

        ax.set_title(label)
        ax.set_ylabel("Temperature [K]")
        ax.legend()
        ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out_path = output_dir / "zone_temperature_profiles.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return out_path


def plot_global_temperature_profile(twin, output_dir=None):

    output_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    state = twin.state
    layout = twin.axial_layout

    series = (
        ("Tg", "Gas", "C0"),
        ("Ts", "Solid", "C1"),
        ("Tw", "Wall", "C2"),
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    for i, (key, label) in enumerate(ZONES):

        segment = layout[key]
        x = segment.z_at_index

        # Each zone is drawn separately: handoffs between zones are
        # face values, so joining the last and first cell centres of
        # neighbouring zones would invent an interpolated profile.
        for prefix, series_label, color in series:
            ax.plot(
                x,
                getattr(state, f"{prefix}_{key}"),
                color=color,
                label=series_label if i == 0 else None,
            )

        if i > 0:
            ax.axvline(segment.z_start, color="0.5", linestyle="--", linewidth=0.8)

        ax.text(
            0.5 * (segment.z_start + segment.z_end),
            1.01,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
        )

    first = layout[ZONES[0][0]]
    last = layout[ZONES[-1][0]]
    ax.set_xlim(first.z_start, last.z_end)

    ax.set_xlabel(AXIAL_XLABEL + "  (gas flows in -z)")
    ax.set_ylabel("Temperature [K]")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()

    out_path = output_dir / "global_temperature_profile.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    return out_path
