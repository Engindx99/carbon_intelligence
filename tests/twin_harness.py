import contextlib
import dataclasses
import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

import main
from pyroprocess.globalstate import GlobalState


ZONES = ("preheater", "calciner", "transition", "burning", "cooler")

STAGE_FIELDS = (
    "gas_inlet_temperature",
    "gas_outlet_temperature",
    "solid_inlet_temperature",
    "solid_outlet_temperature",
    "gas_inlet_enthalpy",
    "gas_outlet_enthalpy",
    "solid_inlet_enthalpy",
    "solid_outlet_enthalpy",
    "wall_temperature",
    "Q_gs",
    "Q_gw",
    "Q_ws",
    "Q_wall_loss",
    "Q_reaction",
    "energy_in",
    "energy_out",
    "energy_residual",
)

STATE_SCALARS = (
    "Hgas_preheater_in",
    "Hgas_preheater_out",
    "Hsolid_preheater_out",
    "Hsolid_calciner_in",
    "Hsolid_calciner_out",
    "Wall_loss_preheater",
    "m_dot_H2O_evaporated_preheater",
    "m_dot_H2O_generated_dehydroxylation",
    "m_dot_CO2_generated_calciner",
    "m_dot_CO2_generated_transition",
)


def run_twin(nodes_per_stage=None):
    """
    Run the steady-state twin from the repository config and return
    (twin, validations). validations holds every report_validation()
    call as {"equipment", "balance_type", "result"}; nothing is written
    to reporter/logs. nodes_per_stage=None leaves the config value.
    """

    validations = []

    def collect(result, equipment, balance_type="energy"):
        validations.append(
            {
                "equipment": equipment,
                "balance_type": balance_type,
                "result": result,
            }
        )
        return result

    # Zone models read configs/twin_cfg.yaml relative to the cwd.
    cwd = os.getcwd()
    os.chdir(REPO_ROOT)

    try:
        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        if nodes_per_stage is not None:
            cfg["preheater"]["nodes_per_stage"] = nodes_per_stage

        twin = main.Twin(
            state=GlobalState(N=cfg["plant"]["N"]),
            cfg=cfg,
        )

        with mock.patch.object(main, "report_validation", collect):
            with contextlib.redirect_stdout(io.StringIO()):
                twin.run()

    finally:
        os.chdir(cwd)

    return twin, validations


def capture_state(twin, validations):
    """Plain-float snapshot of the converged twin (JSON round-trip exact)."""

    state = twin.state
    snapshot = {}

    for zone in ZONES:

        for prefix in ("Tg", "Ts", "Tw"):
            snapshot[f"{prefix}_{zone}"] = _floats(
                getattr(state, f"{prefix}_{zone}")
            )

        flows = state.material_flows[zone]

        for f in dataclasses.fields(flows.solids):
            snapshot[f"flow_{zone}_solid_{f.name}"] = _floats(
                getattr(flows.solids, f.name)
            )

        for f in dataclasses.fields(flows.gases):
            snapshot[f"flow_{zone}_gas_{f.name}"] = _floats(
                getattr(flows.gases, f.name)
            )

    for name, value in dataclasses.asdict(twin.mass_flow).items():
        snapshot[f"mass_flow_{name}"] = float(value)

    for name in STATE_SCALARS:
        snapshot[f"state_{name}"] = float(getattr(state, name))

    preheater = twin.preheater

    for name in ("energy_in", "energy_out", "energy_residual", "Q_reaction_total"):
        snapshot[f"preheater_{name}"] = float(getattr(preheater, name))

    for stage in preheater.stages:
        for name in STAGE_FIELDS:
            snapshot[f"stage{stage.stage_id}_{name}"] = float(
                getattr(stage, name)
            )

    for i, v in enumerate(validations):
        key = f"validation_{i}_{v['equipment']}_{v['balance_type']}"
        snapshot[f"{key}_residual"] = float(v["result"]["residual"])
        snapshot[f"{key}_converged"] = bool(v["result"]["converged"])

    return snapshot


def _floats(values):
    return [float(x) for x in np.asarray(values, dtype=float)]


if __name__ == "__main__":

    # python -m tests.twin_harness OUT.json SOURCE_LABEL [NODES_PER_STAGE]
    out_path = Path(sys.argv[1])
    source = sys.argv[2]
    nodes = int(sys.argv[3]) if len(sys.argv) > 3 else None

    twin, validations = run_twin(nodes)

    reference = {
        "source": source,
        "snapshot": capture_state(twin, validations),
    }

    out_path.write_text(json.dumps(reference, indent=1))
    print(f"wrote {out_path} ({len(reference['snapshot'])} entries)")
