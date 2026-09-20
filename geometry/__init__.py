"""Parametric CAD geometry for the pyroprocess, one sub-package per unit.

    geometry/
        twin_config.py    plant properties read from configs/twin_cfg.yaml
        measure.py        reading dimensions back out of a B-rep
        pipes.py          ducts along a centre-line
        export.py         STEP / STL, into output/<unit>/
        drafting.py       2-D sheets, dimensioned FROM the parameter model
        preheater/        the five-stage cyclone tower
        calciner/         the in-line calciner's reserved envelope

The layout mirrors the twin's own `pyroprocess/<zone>/`, so a unit's
CAD sits where its physics sits. Anything a second unit would need is
at this level; anything only one unit means is inside that unit.

`drafting` needs only matplotlib, which the twin already has, so the
2-D drawings come out in the twin's own environment -- next to the
layout arithmetic they document. Only the solid builders need CadQuery.

THIS PACKAGE IS GEOMETRY ONLY. It builds no physics, runs no solver,
and nothing under pyroprocess/, physics/, chemistry/ or solver/ imports
it -- the Digital Twin keeps running on numpy/pyyaml/matplotlib whether
or not CadQuery is installed (see requirements-cad.txt).

It reaches into the twin in exactly two places, both of them reads:

  * `twin_config` parses configs/twin_cfg.yaml for plant properties
    the geometry is validated against, such as the meal's angle of
    repose. This is the only twin DATA the CAD sees.
  * `preheater.cyclone_spec` imports R_UNIVERSAL from
    physics.kiln_closures. A constant of nature, reused rather than
    copied -- the repository already carried four separate 8.314s and
    this is not the fifth.

Nothing here writes to the twin, and no twin module is executed.

NOTE ON THE NAME. `geometry` here is CAD geometry, which is a different
thing from the lumped vessel geometry the twin solves on
(physics.physics.kiln_geometry, and the `self.D` / `self.V_cell` each
zone carries). Nothing here feeds those yet.
"""

UNITS = ("preheater", "calciner")

__all__ = ["UNITS"]
