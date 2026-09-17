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
