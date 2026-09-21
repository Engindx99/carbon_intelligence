"""CFD fluid volumes of the pyroprocess, built from published plant sizes.

    catalog.py    reference lines: every dimension with its provenance
    config.py     the twin config values this package reads
    SOURCES.md    where each catalogue value comes from

Dimensions are taken from published equipment tables. None is solved
for, and none is scaled from capacity, flow or velocity (SOURCES.md).

Nothing under pyroprocess/, physics/, chemistry/ or solver/ imports
this package, and it imports no twin module.
"""
