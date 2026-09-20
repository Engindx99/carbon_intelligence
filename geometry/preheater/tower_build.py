"""
Faz 4 and Faz 5 -- the five-cyclone tower, as solids.

FAZ 4 IS ONE LINE, AND THAT IS THE POINT
----------------------------------------
`build_cyclone` is called ONCE. The five stages are that one shape
turned and moved to five places:

    base = build_cyclone(spec)[0]
    [base.rotate(Z, p.azimuth_deg).translate(p) for p in tower.placements()]

ROTATE FIRST, THEN TRANSLATE. The builder leaves the cyclone's axis on
the global Z through the origin, so a rotation about Z-through-origin
is a rotation about the cyclone's OWN axis -- which is what
`Placement.to_world` means by an azimuth. Translating first and then
rotating would swing each cyclone around the TOWER axis instead, and
the tower would still fuse into one solid, so nothing downstream would
notice. This paragraph is the check.

So the cyclones cannot differ. There is no second construction that
could take a different parameter, no loop that could pick up a stage
index, and nothing to keep in step. "Five identical cyclones" is a
property of the code's shape rather than a claim the tests have to go
and check -- though tests/test_preheater_tower.py checks it anyway.

FAZ 5 IS PIPES ALONG CENTRE-LINES
---------------------------------
Every duct is a circular pipe along a polyline that tower_spec computed
without a CAD kernel. The pipe builder itself is geometry/pipes.py,
shared with every other unit, because a duct between two vessels is not
a preheater idea.

The two bores are derived, not chosen: the gas duct carries the
cyclone's own inlet area so it runs at the design inlet velocity, and
the meal lines are the cyclone's own dipleg bore.

WHAT THE FUSED TOWER PROVES
---------------------------
`build_tower_solid` fuses all sixteen bodies. If the result is ONE
solid then every cyclone is genuinely reachable from every other
through the ducts -- gas path and meal path both continuous, nothing
left floating. That single number is the Faz 5 acceptance test, and it
is why the ducts are allowed to overlap the vessels they enter rather
than merely touching them.

The fuse is slow (five 83-face cyclones and eleven pipes), so it is a
separate call; `build_preheater` hands back the parts unfused for
anything that does not need it.
"""

from cadquery import Vector

from ..pipes import pipe
from .cyclone_build import build_cyclone
from .tower_spec import TowerSpec


def build_cyclones(tower=None, sections=72):
    """The five stages: ONE shape, five placements. Stage 1 first."""

    tower = tower or TowerSpec()

    base, _ = build_cyclone(tower.cyclone, sections=sections)

    return [
        base
        .rotate(Vector(0, 0, 0), Vector(0, 0, 1), placement.azimuth_deg)
        .translate(Vector(placement.x, placement.y, placement.z))
        for placement in tower.placements()
    ], base


def build_ducts(tower=None):
    """Every gas and solids connection, by name."""

    tower = tower or TowerSpec()

    return {
        name: pipe(path, diameter)
        for name, _kind, path, diameter in tower.connections()
    }


def build_preheater(tower=None, sections=72):
    """The whole tower, unfused.

    Returns (cyclones, ducts, base) -- the five placed stages, the
    named ducts, and the single shape every stage was made from.
    """

    tower = tower or TowerSpec()

    cyclones, base = build_cyclones(tower, sections=sections)
    ducts = build_ducts(tower)

    return cyclones, ducts, base


def build_tower_solid(tower=None, sections=72):
    """Everything fused into one body, if the tower really connects.

    THE FUSE IS NOT CLEANED, and that is deliberate. `clean()` unifies
    faces the boolean left split, which is cosmetic -- and here it
    does damage: it returns an INVALID solid 1.0 m3 light.

    The joint it chokes on is a real one. A meal line has the dipleg's
    own bore and, since the stages were offset, now leaves it straight
    down, so the two are one cylinder in two pieces meeting across a
    zero-width annulus. Before the offset the line turned sideways
    within 0.30 m and there was nothing to unify. Worse, the unifier
    works through the shared underlying shape, so merely CALLING
    `clean()` and discarding the result leaves the original reporting
    invalid afterwards -- which is how this was found, and why there
    is no "clean it and check" fallback here.
    """

    cyclones, ducts, _ = build_preheater(tower, sections=sections)

    solid = cyclones[0]

    for other in cyclones[1:]:
        solid = solid.fuse(other)

    for duct in ducts.values():
        solid = solid.fuse(duct)

    return solid


if __name__ == "__main__":

    from .. import export
    from .tower_spec import layout_report

    tower = TowerSpec()

    print(layout_report(tower))

    cyclones, ducts, base = build_preheater(tower)

    print(f"base cyclone volume  {base.Volume():.3f} m3")
    print(f"stages               {len(cyclones)}")

    volumes = [c.Volume() for c in cyclones]
    print(f"stage volume spread  {max(volumes) - min(volumes):.3e} m3")
    print(f"ducts                {len(ducts)}")

    solid = build_tower_solid(tower)
    bb = solid.BoundingBox()

    print(f"tower solids         {len(solid.Solids())}")
    print(f"tower valid          {solid.isValid()}")
    print(f"tower volume         {solid.Volume():.1f} m3")
    print(f"tower z              {bb.zmin:.2f} .. {bb.zmax:.2f} m")

    for path in export.export_solid(solid, "preheater", "tower"):
        print(f"wrote                {path}")
