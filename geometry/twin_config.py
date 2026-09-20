"""Values the CAD reads out of the twin's own configuration.

Shared by every unit, because the plant properties they need are plant
properties, not unit properties. The meal's angle of repose constrains
the preheater's cone AND its meal lines AND, when it is built, the
calciner's own solids handling -- one number, one place.

This is the only twin DATA `geometry/` reads. It parses
configs/twin_cfg.yaml; it never imports a twin module and never writes
anything back.
"""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
TWIN_CFG_PATH = REPO_ROOT / "configs" / "twin_cfg.yaml"


_CACHE = {}


def twin_cfg(path=None):
    """The parsed twin config, read once per path."""

    path = Path(path) if path is not None else TWIN_CFG_PATH
    key = str(path)

    if key not in _CACHE:

        with open(path, "r", encoding="utf-8") as f:
            _CACHE[key] = yaml.safe_load(f) or {}

    return _CACHE[key]


def config_value(section, key, path=None):
    """One value, or a ValueError naming what was missing.

    Never returns a default. A CAD model built on a silently defaulted
    plant property is a CAD model of a different plant.
    """

    cfg = twin_cfg(path)
    block = cfg.get(section)

    if not isinstance(block, dict) or key not in block:
        raise ValueError(
            f"{TWIN_CFG_PATH if path is None else path}: "
            f"{section}.{key} is missing, and the geometry is "
            "validated against it"
        )

    return block[key]


def repose_angle_deg(path=None):
    """Angle of repose of the raw meal [deg].

    Read from `motion.repose_angle_deg`, which the twin already carries
    for the kiln bed. It is the same meal in the same plant, and a
    second copy is how two numbers that must agree stop agreeing.
    """

    return float(config_value("motion", "repose_angle_deg", path))
