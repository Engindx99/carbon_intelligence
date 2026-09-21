"""CFD fluid volumes of the pyroprocess, built from published plant sizes.

    catalog.py     reference lines: every dimension with its provenance
    config.py      the twin config values this package reads
    SOURCES.md     where each catalogue value comes from
    properties.py  closed-form volumes, areas, hydraulic diameters
    modelling.py   CFD boundary parameters (not plant dimensions)
    components.py  one cyclone or the calciner as a fluid volume
    solids.py      B-rep primitives (CadQuery)
    export.py      STEP / STL under output/<line>/ (CadQuery)
    report.py      the provenance report; `python -m geometry`
    tower.py       what a tower needs, and why no line has it yet

Volumes: properties.py gives EQUIPMENT volumes, for residence time and
hold-up. A solid from components.py is the CFD domain, which adds
inlet and outlet extensions set by CFD modelling parameters.

Dimensions are taken from published equipment tables. None is solved
for, and none is scaled from capacity, flow or velocity (SOURCES.md).

Nothing under pyroprocess/, physics/, chemistry/ or solver/ imports
this package, and it imports no twin module.
"""
