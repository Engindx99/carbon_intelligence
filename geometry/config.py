"""The twin configuration values the geometry reads.

configs/twin_cfg.yaml is the only twin data this package sees. It is
read, never written, and no twin module is imported.

Missing keys raise. Geometry built on a silently defaulted plant
property is geometry of a different plant.
"""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
TWIN_CFG_PATH = REPO_ROOT / "configs" / "twin_cfg.yaml"


def twin_cfg(path=None):
    """The parsed twin config."""

    path = Path(path) if path is not None else TWIN_CFG_PATH

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def config_value(section, key, path=None):
    """One value, or a ValueError naming the missing key."""

    block = twin_cfg(path).get(section)

    if not isinstance(block, dict) or key not in block:
        raise ValueError(
            f"{path or TWIN_CFG_PATH}: {section}.{key} is missing"
        )

    return block[key]


def reference_line_key(path=None):
    """Which catalogue line the geometry is built from."""

    return str(config_value("geometry", "reference_line", path))


def repose_angle_deg(path=None):
    """Dynamic angle of repose of the raw meal [deg].

    The same material property the kiln bed model reads. Cone walls
    and meal chutes must be steeper than it.
    """

    return float(config_value("motion", "repose_angle_deg", path))
