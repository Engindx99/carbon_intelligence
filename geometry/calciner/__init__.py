"""CAD geometry of the in-line calciner.

    ilc_spec.py   the vessel's envelope -- what the tower must leave free

NOTHING OF THE VESSEL IS MODELLED YET. There is no body, no cone, no
burner and no tertiary air duct. What this sub-package states today is
the one number the preheater tower cannot be laid out without: how much
of the tower's axis the calciner is going to want.

That number is not a guess. It comes through the same square root every
other bore in `geometry/` comes through -- an area from a gas duty at a
stated velocity -- and it is handed the preheater's own volumetric
flow, so the calciner and the cyclones cannot come to disagree about
the gas they share.

    python3 -m geometry.calciner
"""

from .ilc_spec import ILCSpec

__all__ = ["ILCSpec"]
