"""CAD geometry of the preheater: five identical cyclones in a tower.

    cyclone_spec.py   ONE cyclone's dimensions -- the single source
    cyclone_build.py  that cyclone, as a solid
    tower_spec.py     where the five sit and what joins them
    tower_build.py    the tower, as solids
    tower_draw.py     the 2-D drawing set (section, elevation, plan, detail)
    measure.py        the cyclone's dimension table, read from the B-rep

The two `_spec` modules import no CAD kernel, so the whole parameter
model, both reports and the drawings run in the twin's own environment:

    python3 -m geometry.preheater
    python3 -m geometry.preheater.tower_draw

Building the solids needs CadQuery (requirements-cad.txt):

    python3 -m geometry.preheater.cyclone_build
    python3 -m geometry.preheater.tower_build
"""

from .cyclone_spec import CycloneSpec
from .tower_spec import TowerSpec

__all__ = ["CycloneSpec", "TowerSpec"]
