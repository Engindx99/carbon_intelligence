"""The preheater's dimension table and tower layout.

    python3 -m geometry.preheater

Builds nothing and imports no CAD kernel, so it runs in the twin's own
environment. For the solids:

    python3 -m geometry.preheater.cyclone_build
    python3 -m geometry.preheater.tower_build
"""

from .cyclone_spec import dimension_report
from .tower_spec import layout_report


if __name__ == "__main__":
    print(dimension_report())
    print(layout_report())
