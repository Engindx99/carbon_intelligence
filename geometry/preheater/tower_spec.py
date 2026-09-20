"""
Faz 4 and Faz 5 -- where the five cyclones sit, and what joins them.

This module is PURE PYTHON. It computes every placement and every duct
centre-line without importing a CAD kernel, so the layout arithmetic --
which is where a tower actually goes wrong -- is checkable in the
twin's own environment. geometry/preheater/tower_build.py turns these points
into solids and does nothing else.

IT ADDS NO CYCLONE DIMENSION. Every length here is either a ratio to
the cyclone's own D_body or read straight off `CycloneSpec`. The five
cyclones are one shape object placed five times (see
geometry.preheater.tower_build.build_preheater), so "identical" is structural
rather than something to be measured afterwards.

STAGE NUMBERING
---------------
Stage 1 is the TOP cyclone and stage 5 the BOTTOM one, which is the
industrial convention. Gas enters at the bottom and leaves at the top;
meal enters at the top and leaves at the bottom. They are
counter-current, which is the whole point of the tower.

    NOTE, because the twin numbers them the other way: in
    pyroprocess/preheater the gas inlet enthalpy goes to index 0, so
    index 0 is the HOT BOTTOM stage. `preheater.py:67-80 gas_T_bounds_K`
    is written top-first and is inconsistent with that, which is why it
    is marked "reference bounds only". Nothing here is wired to the
    twin, so the two numberings cannot collide -- but anyone who later
    connects them must reverse the index.

WHERE THE MEAL GOES, AND WHY IT IS NOT THE OBVIOUS PLACE
--------------------------------------------------------
Meal caught by cyclone n is NOT dropped into cyclone n+1. It is
injected into the gas duct FEEDING cyclone n+1, so the gas picks it up,
heats it on the way, and cyclone n+1 separates it again. That is what
makes a preheater a heat exchanger instead of a stack of hoppers: the
exchange happens in the ducts, and the cyclones only do the separating.

So, with riser n being the duct that feeds cyclone n:

    raw meal      ->  riser 1
    cyclone n     ->  riser n+1        (n = 1..4)
    cyclone 5     ->  out, to the calciner
    gas           ->  riser 5, from the calciner, upward

TWO DIAMETERS THAT ARE DERIVED, NOT INVENTED
--------------------------------------------
  * the riser duct carries the same gas at the same velocity the
    cyclone was sized for, so its area IS the cyclone's inlet area and
    its diameter follows. Giving it a ratio of its own would have let
    the duct and the inlet disagree about the design velocity.
  * the meal lines are the cyclone's own dipleg bore.

THE ONE ANGLE THAT IS A REAL CONSTRAINT
---------------------------------------
`dipleg_entry_angle_deg` must clear the meal's angle of repose, for the
same reason the cone must: a meal line laid shallower than the heap the
meal makes does not run, it plugs. The repose angle is read from the
twin's `motion.repose_angle_deg`, not restated.

That constraint is what forces the geometry, and it is tight. The entry
point must still land on the riser's vertical run, and `_validate`
rejects the layout when it does not -- so the angle, the drop, the
approach distance and the stage pitch are checked against each other
rather than chosen independently.

WHERE THE STAGES STAND, AND WHY IT IS DERIVED
---------------------------------------------
The five cyclones DO NOT share an axis. They stand on a circle of
`column_radius` about the tower axis, which is reserved for the
in-line calciner, each one turned so that the stage above it lies at
`meal_side_azimuth_deg` in its own frame.

They used to share one axis, and that was the defect. Every dipleg
then discharged directly above the next cyclone's gas outlet, and the
meal duct leaving the first and the gas duct leaving the second both
began ON that axis, so they cleared each other only if

    stage_gap > riser_radius + meal_line_radius = 1.831 m

With `stage_gap_ratio = 0.25` it was 1.391 m and there was 3.69 m3 of
solid overlap per stage, which nothing caught, because the tests
asserted that the intended joints EXIST and never that the unintended
ones do not. Widening the gap and bending the meal line sideways
patched it, but the meal line then had to leave its dipleg, step
sideways and only then run down -- a three-legged dodge around a
cyclone that should never have been underneath it.

The offset removes the cause rather than the symptom. It lets the meal
line be what a dipleg actually is: a long VERTICAL pipe down past the
cyclone below, then one inclined chute into the riser.

WHAT THIS PACKAGE IS FOR, AND WHAT IT THEREFORE CHECKS
------------------------------------------------------
The solid this builds is the FLUID VOLUME -- the wetted envelope,
whose volume is the gas volume -- for CFD. It is not a fabrication
model. Erection clearance, flanges, bolts, access for a man with a
pipe, steel and supports are all out of scope, and so is any number
derived from them.

That decides what a clearance means here. A CFD mesh is indifferent
to a gap OUTSIDE the domain, because that gap is never meshed. What
the domain cannot survive is INTERFERENCE: the tower is assembled as
a union, and a union merges whatever overlaps, so a duct touching a
vessel it does not enter opens a short circuit between two flow
paths -- and the fuse still returns one valid solid, so nothing
downstream notices. Every check below is therefore against
`mesh_clearance_m`, which is zero plus enough to keep the boolean and
the surface mesh off a tangency. It is a discretisation number, like
ENVELOPE_SECTIONS.

SIX INEQUALITIES, AND ONE RULE
------------------------------
`_validate_plan` walks `CLEARANCES`. Each is a duct against a VESSEL,
or a vessel against the calciner, and each is measured in plan,
because a vessel is a body of revolution and plan is where its
envelope lives:

    1. the vertical dipleg leg drops past the cyclone below
    2. the inclined chute clears that cyclone too
    3. the riser's vertical run climbs past its own cyclone
    4. the cyclone stands clear of the reserved calciner
    5. so does the riser's vertical run
    6. the chute starts below the across leg of its own riser

Then ONE rule covers every duct against every other duct, in 3-D and
exactly, on every pair of legs: no passage may come within its bores
of a passage it does not JOIN, and a junction is read per LEG -- an
end of one path landing on the leg being excused.

That rule replaced two hand-written plan checks, and it had to. They
measured the dipleg against the elbow at the bottom of its own riser
and nobody had written the mirror case, the elbow at the TOP of the
next one, so the meal line ran through the very duct it was aiming
at, 1.657 m of interference in all four stages, and then joined it
properly nine metres lower. It crossed its riser TWICE. Every plan
check passed, because in plan the two really are close and are
SUPPOSED to be; the fusion passed too, because a duct that runs
through the duct it joins still fuses into one solid. A rule that
does not enumerate cases cannot miss one.

THE LAYOUT, AND WHY IT IS THESE NUMBERS
---------------------------------------
    column radius   8.511 m    1.530 D
    azimuth step    45 deg     -> a 6.514 m chord between neighbours
    meal side       330 deg    the flank where the scroll has closed
    mesh clearance  0.050 m

The step is the smallest opening of the zigzag at which nothing
touches what it does not join, rounded up: at 43 deg the meal line
runs into the mouth leg of the riser below, at 44 deg the narrowest
gap is 0.131 m, and 45 deg leaves 0.250 m. Past 50 deg the binding
pair changes and opening further buys nothing, so there is no reason
to spread the tower -- and good reason not to, since every extra
metre of radius is another metre of duct, and duct is pressure drop
and shell loss.

It is NOT chosen by maximising clearance. That was tried and it is
the wrong shape of question: check 3 is measured in the cyclone's own
frame, so no plan knob moves it, and it caps the narrowest margin at
2.248 m for every layout that reaches it -- 23 % of everything valid.
The maximum was known in closed form before any search started, and
what a search could still have decided, it decided by grid order.

TWO PATTERNS, AND WHY THE DEFAULT IS THE ZIGZAG
-----------------------------------------------
`layout_pattern` is "zigzag" -- two places, alternating, so stages n
and n+2 share one -- or "fan", every stage one step further round, so
all five stand in different places. Both satisfy every check
and both are the same height.

The zigzag is the default because of a property neither the plan
checks nor the fusion could see: it puts every riser column on ONE
line, so a single elevation shows all five standing clear of their
own cyclones. The fan turns each stage 45 deg further round a circle,
so the columns face 108 deg apart, and NO view separates them -- swept
over 360 deg, the best still draws some duct 0.556 m over a cyclone it
does not enter, while the zigzag's best leaves 0.426 m of daylight
(`tower_draw.elevation_clearance`).

That is not a drawing preference. A tower whose ducts cannot be seen
clear of its vessels in any one view cannot be checked by looking at
one, and the sheets are here to be checked by looking. The fan is
kept, tested and drawable; it is simply not what this tower is.

The tower is 112.36852420346332 m tall either way, and not one level
moved: this is a purely horizontal rearrangement.
"""

import math
from dataclasses import dataclass

from .. import plan, space
from ..calciner.ilc_spec import ILCSpec
from ..twin_config import repose_angle_deg
from .cyclone_spec import CycloneSpec


@dataclass(frozen=True)
class Placement:
    """Where one stage stands, and which way it faces.

    `azimuth_deg` is the cyclone's rotation about ITS OWN vertical
    axis, normalised to [0, 360). The local frame is the cyclone
    builder's datum exactly -- z = 0 at the dipleg discharge, the
    volute mouth on +x -- so `to_world` IS the transform
    `tower_build` applies to the solid. The layout arithmetic and the
    CAD placement cannot disagree, because there is only one of them.
    """

    stage: int
    x: float
    y: float
    z: float
    azimuth_deg: float

    @property
    def azimuth_rad(self):
        return math.radians(self.azimuth_deg)

    def to_world(self, local):
        """A point in the cyclone's own frame -> tower coordinates."""

        c = math.cos(self.azimuth_rad)
        s = math.sin(self.azimuth_rad)
        lx, ly, lz = local

        return (
            self.x + c * lx - s * ly,
            self.y + s * lx + c * ly,
            self.z + lz,
        )

    def to_world_xy(self, local_xy):
        """Plan only, for envelope and clearance work."""

        return self.to_world((local_xy[0], local_xy[1], 0.0))[:2]

    def bearing_to_local_deg(self, world_deg):
        """A compass bearing, as this cyclone sees it."""

        return (world_deg - self.azimuth_deg) % 360.0


TOWER_RATIO_RANGES = {
    "stage_gap_ratio":          (0.10, 1.00),
    "riser_rise_ratio":         (0.02, 1.00),
    "riser_approach_ratio":     (0.75, 2.00),
    "exit_stack_height_ratio":  (0.50, 3.00),
    "gas_inlet_height_ratio":   (0.50, 3.00),
    "meal_inlet_length_ratio":  (0.50, 2.00),
    "meal_inlet_height_ratio":  (0.10, 0.90),
    "meal_reach_ratio":         (0.00, 3.00),
    "meal_entry_height_ratio":  (0.05, 0.95),
    "column_radius_ratio":      (0.50, 4.00),
}

# Angles get their own table. A degree is not a ratio, and a dict that
# holds both cannot state what its values are multiples of. Both are
# swept by their own test, and a third test asserts that every tunable
# field is in one table or the other -- which is what would have caught
# `meal_azimuth_offset_deg` shipping with no range at all.
#
# `dipleg_entry_angle_deg` is deliberately ABSENT. Its lower bound is
# the meal's angle of repose, read from the twin's config, so it is
# derived rather than tabulated and `_validate` owns that rejection.
TOWER_ANGLE_RANGES = {
    "stage_azimuth_step_deg":   (-180.0, 180.0),
    "meal_side_azimuth_deg":    (0.0, 360.0),
}

# And absolute lengths get a third, for the same reason angles got a
# second: a metre is not a multiple of anything. There is exactly one
# so far, and it is absolute on purpose -- see `mesh_clearance_m`.
TOWER_LENGTH_RANGES = {
    "mesh_clearance_m":         (0.01, 0.50),
}

LAYOUT_PATTERNS = ("fan", "zigzag")

# How finely a cyclone's plan envelope is polygonised before anything
# measures a distance to it.
#
# THE DISCRETISATION HAS A DIRECTION and it is the dangerous one: the
# inscribed polygon lies INSIDE the true envelope, so a coarse one
# reports more clearance than there is. At 72 sections the sagitta on
# the barrel is 2.781 * (1 - cos 2.5 deg) = 0.0026 m, three orders
# below the clearances being measured, and it runs 2.5x faster than
# the 180 this used to default to -- which matters because
# `neighbour_plan_clearance` is now on the validation path and every
# TowerSpec construction pays for it.
#
# One constant, so the validator and the drawing measure the same
# polygon. Nothing may quietly pass a coarser one to get an answer it
# likes better.
ENVELOPE_SECTIONS = 72


# ==========================================================
# THE CLEARANCES, AS A TABLE
# ==========================================================
# Every inequality the plan layout has to satisfy, in one place.
#
# IT USED TO BE SIX PLACES. `_validate_plan` raised them one by one,
# `layout_report` printed its own list, and the drawing had three more
# -- all of them written out by hand and all of them saying SEVEN.
# That is how check 8 came to be missing for as long as it was: the
# dipleg drop was measured against the elbow at the bottom of its own
# riser and nobody had written the mirror case, the elbow at the TOP of
# the next one, so four collisions of 1.657 m passed every check and
# the fusion as well. A list that is written out cannot be counted
# against anything. A list that is walked can.
#
# `pairs` means the check is about a stage and the one below it, so it
# runs 1..n-1; `each` means it is about one stage on its own.
def _stage_of(*names):
    """Which stage a refusal is about, read off the duct names.

    The duct rule is generic -- it knows legs, not stages -- but every
    duct in this tower carries its stage in its name, and a message
    that cannot say which stage sends the reader through all five.
    """

    for name in names:
        head, _sep, tail = name.rpartition("_")

        if head and tail.isdigit():
            return f"stage {tail}"

    return "no stage"


def _pairs(stage_count):
    return range(1, stage_count)


def _each(stage_count):
    return range(1, stage_count + 1)


def _explain_dipleg_drop(tower, stage, have, need):
    r_meal = 0.5 * tower.meal_line_diameter
    reach = tower.meal_side_envelope_radius

    return (
        f"the dipleg drop from stage {stage} passes "
        f"{have + reach + r_meal:.3f} m from the axis of stage "
        f"{stage + 1}, leaving {have:.3f} m over that cyclone's "
        f"{reach:.3f} m reach and the line's own {r_meal:.3f} m -- "
        f"less than the {need:.3f} m mesh clearance. Raise "
        f"column_radius_ratio ({tower.column_radius_ratio}) or "
        f"stage_azimuth_step_deg ({tower.stage_azimuth_step_deg}), or "
        f"turn meal_side_azimuth_deg ({tower.meal_side_azimuth_deg}) "
        "onto a narrower flank of the scroll"
    )


def _explain_chute(tower, stage, have, need):
    return (
        f"the meal chute from stage {stage} comes within {have:.3f} m "
        f"of the body of stage {stage + 1} in plan, against a "
        f"{need:.3f} m mesh clearance; widen "
        f"stage_azimuth_step_deg ({tower.stage_azimuth_step_deg}) or "
        f"shorten riser_approach_ratio ({tower.riser_approach_ratio})"
    )


def _explain_riser_column(tower, stage, have, need):
    return (
        f"the vertical run of riser {stage} stands "
        f"{tower.riser_reach:.3f} m from that cyclone's axis, which "
        f"leaves {have:.3f} m over the "
        f"{tower.riser_local_envelope_radius:.3f} m the body reaches "
        f"on that flank plus the duct's own "
        f"{0.5 * tower.riser_diameter:.3f} m -- less than the "
        f"{need:.3f} m mesh clearance; raise riser_approach_ratio "
        f"({tower.riser_approach_ratio})"
    )


def _explain_cyclone_calciner(tower, stage, have, need):
    return (
        f"cyclone {stage} comes within {have:.3f} m of the calciner "
        f"envelope reserved on the tower axis "
        f"({tower.calciner.reserved_radius:.3f} m radius, derived from "
        f"{tower.calciner.design_volumetric_flow_m3_s:.2f} m3/s at "
        f"{tower.calciner.gas_velocity_m_s:.1f} m/s), against a "
        f"{need:.3f} m mesh clearance; raise column_radius_ratio "
        f"({tower.column_radius_ratio})"
    )


def _explain_riser_calciner(tower, stage, have, need):
    return (
        f"the vertical run of riser {stage} comes within {have:.3f} m "
        f"of the reserved calciner envelope, against a {need:.3f} m "
        "mesh clearance. The column swings inward as "
        f"stage_azimuth_step_deg ({tower.stage_azimuth_step_deg}) "
        f"grows; reduce it, or raise column_radius_ratio "
        f"({tower.column_radius_ratio})"
    )


@dataclass(frozen=True)
class Clearance:
    """One inequality: what is measured, and where."""

    number: int
    key: str          # the TowerSpec member that measures it
    label: str        # short name, for the report and the sheets
    stages: object    # _pairs or _each
    explain: object   # (tower, stage, have, need) -> str

    @property
    def about_pairs(self):
        """Is this about a stage and the one below it, or one alone?

        What the stage-detail sheet filters on: that panel shows one
        pair of stages, so it can only carry the checks that are
        themselves about a pair.
        """

        return self.stages is _pairs


CLEARANCES = (
    Clearance(1, "dipleg_drop_clearance",
              "dipleg drop vs cyclone below",
              _pairs, _explain_dipleg_drop),
    Clearance(2, "chute_clearance",
              "meal chute vs cyclone below",
              _pairs, _explain_chute),
    Clearance(3, "riser_column_clearance",
              "riser column vs own cyclone",
              _each, _explain_riser_column),
    Clearance(4, "cyclone_calciner_clearance",
              "cyclone vs calciner",
              _each, _explain_cyclone_calciner),
    Clearance(5, "riser_calciner_clearance",
              "riser column vs calciner",
              _each, _explain_riser_calciner),
)


@dataclass(frozen=True)
class TowerSpec:
    """The arrangement of five identical cyclones, in SI units."""

    cyclone: CycloneSpec = None

    # The calciner is not modelled -- this is the envelope the tower
    # has to stand around, and it is what sets the column radius. Its
    # bore comes from the cyclone's own gas duty (see ILCSpec), so
    # there is one gas in this model and not two.
    calciner: ILCSpec = None

    stage_count: int = 5

    # ================= WHERE THE STAGES STAND =================
    # The five cyclones stand on a circle about the tower axis, which
    # is reserved for the calciner. Each is turned so that the stage
    # ABOVE it lies at `meal_side_azimuth_deg` in its own frame, which
    # is what decides which flank of the scroll the meal comes down
    # past -- and the scroll is 1.669 m wider at its mouth than at the
    # end of its wrap, so that choice is worth 1.669 m of tower.
    #
    # NONE OF THESE IS A FREE NUMBER. They are the smallest opening of
    # the zigzag at which no flow passage touches a passage it does not
    # join: at 44 deg the narrowest gap is 0.131 m and at 43 deg the
    # meal line runs into the mouth leg of the riser below. 45 deg is
    # that threshold rounded up, and it leaves 0.250 m. Past 50 deg the
    # binding pair changes and opening further buys nothing, so there
    # is nothing to be gained by spreading the tower.
    column_radius_ratio:      float = 1.530   # x D_body -> 8.511 m
    stage_azimuth_step_deg:   float = 45.0    # -> a 6.514 m chord
    meal_side_azimuth_deg:    float = 330.0   # where the stage above sits
    layout_pattern:           str = "zigzag"  # or "fan"

    # The ONE clearance in this model, and it is numerical, not
    # mechanical. Flanges, bolts, erection room and the width of a man
    # are manufacturing concerns and this package does not model them:
    # it models the fluid volume, and a CFD mesh is indifferent to a
    # gap OUTSIDE the domain because that gap is never meshed.
    #
    # What the fluid volume cannot survive is interference. The tower
    # is built as a union, and a union merges whatever overlaps, so a
    # duct that touches a vessel it does not enter opens a short
    # circuit in the domain. The bar is therefore zero plus enough to
    # keep the boolean and the surface mesh off a tangency, which is a
    # discretisation number like ENVELOPE_SECTIONS, not a physical one.
    #
    # The committed layout clears it by 0.250 m, five times over, so
    # the layout does not turn on its exact value.
    mesh_clearance_m: float = 0.05

    # Clear height between one cyclone's top and the next one's base.
    #
    # It is no longer the thing that keeps the two ducts apart -- the
    # plan offset does that now -- but a stage still has to be lifted
    # clear of the one below it for the gas elbow to turn, and the
    # tower's total height is frozen through it: raising this raises
    # the pitch, and the exhaust stub is what pays.
    stage_gap_ratio: float = 0.45          # x D_body -> 2.503 m

    # Short vertical rise off a gas outlet before the duct turns.
    #
    # Kept SMALL and deliberately different from stage_gap_ratio. When
    # the two were both 0.25 the riser's lift ended exactly at the
    # dipleg discharge of the cyclone above and its elbow sat on the
    # meal outlet -- two defaults that happened to be the same number.
    riser_rise_ratio: float = 0.03         # x D_body -> 0.167 m

    # How far out in -y the riser's vertical run stands. It has to
    # clear the cyclone it climbs past, whose volute reaches the barrel
    # radius on that side.
    riser_approach_ratio: float = 1.00     # x D_body

    exit_stack_height_ratio: float = 0.70  # x D_body, above cyclone 1
    gas_inlet_height_ratio:  float = 1.00  # x D_body, below cyclone 5
    meal_inlet_length_ratio: float = 1.00  # x D_body
    meal_inlet_height_ratio: float = 0.50  # fraction along riser 1

    # WHERE on the riser's vertical run the meal lands, as a fraction
    # of that run, and how far it swings OUT on the way.
    #
    # THE OUTWARD SWING IS WHAT MAKES THE ENTRY TANGENTIAL. A dipleg
    # stands only 3.106 m from the riser column it feeds, against a
    # 21.7 m descent, so a line that goes straight there has nowhere to
    # be but nearly vertical -- it hangs, and meets the riser along its
    # own axis instead of running into it. Taking it wide first turns
    # 3.106 m of lateral room into 11.8 m, and the same descent then
    # lies at 58 deg: a slope you can see, and a duct the gas meets at
    # 32 deg rather than head-on. Both ends are fixed, so that slope is
    # derived; the repose angle is what refuses it when it goes flat.
    #
    # It also keeps the line clear of the mouth leg of the riser below,
    # which starts at the TOP of the very column the meal is aiming
    # for. A line that cuts straight across is refused by the duct
    # rule, which is how this was measured.
    meal_reach_ratio:        float = 1.00   # x D_body, out to the side
    meal_entry_height_ratio: float = 0.30   # a third up the riser's run

    # Meal lines. The angle is the binding constraint; see the docstring.
    dipleg_entry_angle_deg: float = 55.0   # from horizontal

    def __post_init__(self):

        if self.cyclone is None:
            object.__setattr__(self, "cyclone", CycloneSpec())

        if self.calciner is None:
            # The calciner's bore comes from the cyclone's OWN gas
            # duty, so there is one gas in this model and not two.
            object.__setattr__(
                self,
                "calciner",
                ILCSpec(
                    design_volumetric_flow_m3_s=self.cyclone.volumetric_flow
                ),
            )

        self._validate()

    @property
    def D(self):
        return self.cyclone.D_body

    def _check_stage(self, stage):

        if int(stage) != stage or not (1 <= stage <= self.stage_count):
            raise ValueError(
                f"TowerSpec: stage must be 1..{self.stage_count} "
                f"(1 = top, {self.stage_count} = bottom), got {stage}"
            )

    # ======================================================
    # VERTICAL ARRANGEMENT
    # ======================================================

    @property
    def pitch(self):
        """Floor-to-floor spacing of one stage [m]."""

        return self.cyclone.total_height + self.stage_gap

    @property
    def stage_gap(self):
        return self.stage_gap_ratio * self.D

    @property
    def tower_height(self):
        """Dipleg of stage 5 to the top of the exit stack [m].

        PURELY VERTICAL, and that is why the plan rearrangement could
        not move it: nothing here reads the azimuth step, the column
        radius or the flank.
        """

        return (
            (self.stage_count - 1) * self.pitch
            + self.cyclone.total_height
            + self.exit_stack_height_ratio * self.D
        )

    def stage_base_z(self, stage):
        """z of a stage's dipleg discharge [m]. Stage 1 is the top."""

        self._check_stage(stage)

        return (self.stage_count - stage) * self.pitch

    # ======================================================
    # WHERE THE STAGES STAND, IN PLAN
    # ======================================================

    @property
    def column_radius(self):
        """Radius of the circle the cyclones stand on [m]."""

        return self.column_radius_ratio * self.D

    @property
    def chord_between_stages(self):
        """Plan distance between two NEIGHBOURING stages [m].

        The same in both patterns: neighbours are always one
        `stage_azimuth_step_deg` apart round the circle, whether the
        pattern walks on round it (fan) or steps back and forth
        between two places (zigzag).
        """

        return 2.0 * self.column_radius * math.sin(
            0.5 * math.radians(self.stage_azimuth_step_deg)
        )

    def stage_compass_deg(self, stage):
        """The placement law, defined for stage 0 as well.

        Stage 0 does not exist, and it is still needed: stage 1 is
        turned to face the stage ABOVE it like every other stage, and
        without a position to face it would be the one cyclone placed
        by a different rule. In the zigzag the virtual stage 0 lands
        where stage 2 is, which is the same flank stage 1 would have
        been given anyway.
        """

        if self.layout_pattern == "zigzag":
            return ((stage - 1) % 2) * self.stage_azimuth_step_deg

        return (stage - 1) * self.stage_azimuth_step_deg

    def _stage_xy(self, stage):
        """Plan position of a stage, stage 0 included."""

        angle = math.radians(self.stage_compass_deg(stage))

        return (
            self.column_radius * math.cos(angle),
            self.column_radius * math.sin(angle),
        )

    def stage_azimuth_deg(self, stage):
        """How far the cyclone is turned about its OWN axis [deg].

        Set by one rule: the stage ABOVE must lie at
        `meal_side_azimuth_deg` in this cyclone's frame, because that
        is the flank the meal comes down past and the scroll is 1.669 m
        narrower on the closed one.
        """

        here = self._stage_xy(stage)
        above = self._stage_xy(stage - 1)

        bearing = math.degrees(
            math.atan2(above[1] - here[1], above[0] - here[0])
        )

        return (bearing - self.meal_side_azimuth_deg) % 360.0

    def placements(self):
        """Where each stage stands and which way it faces, stage 1 first.

        The cyclones DO NOT share an axis. They stand on a circle of
        `column_radius` about the tower axis, which belongs to the
        calciner, and each is turned by `stage_azimuth_deg`.
        """

        return [
            Placement(
                stage,
                *self._stage_xy(stage),
                self.stage_base_z(stage),
                self.stage_azimuth_deg(stage),
            )
            for stage in range(1, self.stage_count + 1)
        ]

    def placement(self, stage):
        """One stage's placement."""

        self._check_stage(stage)

        return self.placements()[stage - 1]

    def stage_envelope(self, stage, sections=ENVELOPE_SECTIONS):
        """A stage's plan envelope, in tower coordinates."""

        placement = self.placement(stage)

        return [
            placement.to_world_xy(point)
            for point in self.cyclone.plan_envelope(sections=sections)
        ]

    # ======================================================
    # DUCT SIZES -- BOTH DERIVED
    # ======================================================

    @property
    def riser_diameter(self):
        """Gas duct bore [m], set by the cyclone's own inlet area.

        Same gas, same velocity, therefore the same area. Not a free
        ratio, because a free ratio could disagree with the inlet the
        cyclone was sized around.
        """

        return math.sqrt(4.0 * self.cyclone.inlet_area / math.pi)

    @property
    def meal_line_diameter(self):
        """Meal line bore [m] -- the cyclone's own dipleg."""

        return self.cyclone.dipleg_diameter

    # ======================================================
    # THE POINTS EVERY DUCT IS BUILT FROM
    # ======================================================

    @property
    def mouth_x(self):
        """x of the centre of a volute mouth, in the cyclone's frame.

        The scroll's section at theta = 0 lies in the y = 0 plane and
        spans r from the inner radius out to R + b, so the duct meets it
        face-on when it arrives along y.
        """

        cyc = self.cyclone

        return 0.5 * (
            cyc.volute_inner_radius + 0.5 * cyc.D_body + cyc.inlet_width
        )

    @property
    def riser_approach_y(self):
        """y of the riser's vertical run [m]; negative, i.e. behind."""

        return -self.riser_approach_ratio * self.D

    @property
    def riser_offset_local(self):
        """Where the riser column stands, in the cyclone's own frame."""

        return (self.mouth_x, self.riser_approach_y)

    @property
    def riser_reach(self):
        """How far the riser column stands off the cyclone's axis [m].

        TRUE ONLY IN THE LOCAL FRAME, which is why the drawing may
        only dimension it on a view that holds both axes: it is the
        hypotenuse of `mouth_x` and `riser_approach_y`, and a flat
        elevation of the tower shows neither at true length.
        """

        return math.hypot(self.mouth_x, self.riser_approach_y)

    @property
    def riser_bearing_rad(self):
        """Compass bearing of the riser column, from the tower axis."""

        return math.atan2(self.riser_approach_y, self.mouth_x)

    @property
    def riser_local_envelope_radius(self):
        """Cyclone reach on the flank the riser column stands off [m]."""

        return self.cyclone.plan_envelope_radius(
            math.degrees(self.riser_bearing_rad)
        )

    @property
    def meal_side_envelope_radius(self):
        """Cyclone reach on the flank the meal comes down past [m]."""

        return self.cyclone.plan_envelope_radius(self.meal_side_azimuth_deg)

    def riser_axis(self, stage):
        """Plan position of a riser's vertical run, in tower coords."""

        return self.placement(stage).to_world_xy(self.riser_offset_local)

    def dipleg_point(self, stage):
        """A stage's dipleg discharge, in tower coordinates.

        The cyclone builder's datum is z = 0 at the discharge, so this
        is simply where the stage stands.
        """

        placement = self.placement(stage)

        return (placement.x, placement.y, placement.z)

    def mouth_point(self, stage):
        """Centre of a stage's gas inlet mouth, in tower coordinates."""

        self._check_stage(stage)

        cyc = self.cyclone
        roof = cyc.total_height - cyc.vortex_finder_protrusion

        return self.placement(stage).to_world(
            (self.mouth_x, 0.0, roof - 0.5 * cyc.inlet_height)
        )

    def outlet_point(self, stage):
        """Top of a stage's gas outlet duct, in tower coordinates."""

        self._check_stage(stage)

        placement = self.placement(stage)

        return (
            placement.x,
            placement.y,
            placement.z + self.cyclone.total_height,
        )

    # ======================================================
    # THE DUCTS
    # ======================================================

    def riser_path(self, stage):
        """Centre-line of the gas duct FEEDING `stage`.

        Stages 1-4 are fed by the stage below. Stage 5 is fed from the
        calciner, so its duct starts below the tower instead of at
        another cyclone's outlet, and is one segment shorter.
        """

        self._check_stage(stage)

        mouth = self.mouth_point(stage)
        axis = self.riser_axis(stage)
        corner = (axis[0], axis[1], mouth[2])

        if stage == self.stage_count:

            foot = (
                axis[0],
                axis[1],
                self.stage_base_z(stage) - self.gas_inlet_height_ratio * self.D,
            )

            return [foot, corner, mouth]

        start = self.outlet_point(stage + 1)
        rise = (start[0], start[1], start[2] + self.riser_rise_ratio * self.D)
        across = (axis[0], axis[1], rise[2])

        return [start, rise, across, corner, mouth]

    def riser_vertical_span(self, stage):
        """(z_low, z_high) of the riser's vertical run [m].

        The meal line from the stage above has to land inside this.
        """

        path = self.riser_path(stage)

        return (path[-3][2], path[-2][2])

    def meal_line_path(self, stage):
        """Centre-line from a stage's dipleg into the riser below it.

        Meal from stage n joins riser n+1 -- the duct feeding the NEXT
        cyclone down, not that cyclone itself.

        ONE STRAIGHT INCLINED PIPE, and that is the tangential entry.
        A meal line that drops vertically and then kinks into the riser
        meets it at a wide angle -- 35 deg in the layout this replaced
        -- and a duct arriving across the flow is a duct the gas has to
        turn. Run straight from the discharge to the entry instead and
        the pipe arrives at 12 deg to the riser's own axis: it is
        already going the way the riser goes, so the meal is picked up
        rather than deflected. It is also the longer path of the two,
        which is what "come in from wider" means here.

        THE SLOPE IS DERIVED, NOT CHOSEN. Both ends are fixed -- the
        dipleg discharge above, the landing point on the riser's
        vertical run below -- so the angle is whatever those two give,
        and `_validate` is what insists it still clears the meal's
        angle of repose. That is the right way round: a meal line that
        will not run is refused, rather than an angle being set and
        the geometry bent to honour it.
        """

        self._check_stage(stage)

        if stage >= self.stage_count:
            raise ValueError(
                f"stage {stage} is the bottom cyclone; its meal leaves "
                "the tower for the calciner and has no riser to join"
            )

        start = self.dipleg_point(stage)

        low, high = self.riser_vertical_span(stage + 1)
        z = low + self.meal_entry_height_ratio * (high - low)

        axis = self.riser_axis(stage + 1)

        # Out to the SIDE first, and only then back in. Sideways, not
        # radially outward: the riser it is aiming at lies almost
        # straight in towards the tower axis, so a line that steps
        # radially out and comes back retraces its own path -- the
        # duct rule refuses it, which is how this was measured. Across
        # the approach, the two legs make a real V in plan and the
        # lateral room grows instead of cancelling.
        #
        # The side is the one AWAY from the tower axis, so the meal
        # runs outside the duct bundle where the picture puts it.
        #
        # Both legs at the SAME slope: a solids line wants one gradient
        # the whole way, since a flat spot is where meal stops. So the
        # bend is in PLAN alone -- in elevation the line is straight.
        span = math.hypot(axis[0] - start[0], axis[1] - start[1])
        toward = ((axis[0] - start[0]) / span, (axis[1] - start[1]) / span)

        side = (-toward[1], toward[0])

        if start[0] * side[0] + start[1] * side[1] < 0.0:
            side = (-side[0], -side[1])

        reach = self.meal_reach_ratio * self.D

        corner = (start[0] + reach * side[0], start[1] + reach * side[1])

        out = math.hypot(corner[0] - start[0], corner[1] - start[1])
        back = math.hypot(axis[0] - corner[0], axis[1] - corner[1])

        drop = start[2] - z
        share = out / (out + back) if out + back > 0.0 else 0.0

        return [
            start,
            (corner[0], corner[1], start[2] - drop * share),
            (axis[0], axis[1], z),
        ]

    def meal_entry_angle_deg(self, stage):
        """Slope of a meal line, from horizontal [deg]. DERIVED.

        It has to clear the meal's angle of repose, for the same reason
        the cone does: a line laid shallower than the heap the meal
        makes does not run, it plugs.
        """

        _start, end = self.meal_line_path(stage)[-2:]
        start = _start

        return math.degrees(
            math.atan2(
                start[2] - end[2],
                math.hypot(end[0] - start[0], end[1] - start[1]),
            )
        )

    def meal_riser_angle_deg(self, stage):
        """Angle between a meal line and the riser it enters [deg].

        The tangential-entry measure: 0 would be a pipe running
        alongside, 90 a pipe stabbed straight through the wall. The
        riser's run is vertical, so this is simply the complement of
        the slope.
        """

        return 90.0 - self.meal_entry_angle_deg(stage)

    def meal_chute_plan(self, stage):
        """The inclined leg's plan projection, as a segment."""

        path = self.meal_line_path(stage)

        return (path[1][:2], path[2][:2])

    def exit_stack_path(self):
        """The tower's gas outlet, above cyclone 1."""

        top = self.outlet_point(1)

        return [
            top,
            (top[0], top[1], top[2] + self.exit_stack_height_ratio * self.D),
        ]

    def meal_inlet_path(self):
        """Raw meal into riser 1, the duct feeding the top cyclone."""

        z_low, z_high = self.riser_vertical_span(1)
        z = z_low + self.meal_inlet_height_ratio * (z_high - z_low)

        placement = self.placement(1)
        length = self.meal_inlet_length_ratio * self.D
        angle = math.radians(self.dipleg_entry_angle_deg)

        end_local = (self.mouth_x, self.riser_approach_y)
        start_local = (end_local[0] - length * math.cos(angle), end_local[1])

        end = placement.to_world_xy(end_local)
        start = placement.to_world_xy(start_local)

        return [
            (start[0], start[1], z + length * math.sin(angle)),
            (end[0], end[1], z),
        ]

    def connections(self):
        """Every duct in the tower, as (name, kind, path, diameter)."""

        items = []

        for stage in range(1, self.stage_count + 1):
            items.append(
                (
                    f"riser_{stage}",
                    "gas",
                    self.riser_path(stage),
                    self.riser_diameter,
                )
            )

        for stage in range(1, self.stage_count):
            items.append(
                (
                    f"meal_line_{stage}",
                    "solids",
                    self.meal_line_path(stage),
                    self.meal_line_diameter,
                )
            )

        items.append(
            ("exit_stack", "gas", self.exit_stack_path(), self.riser_diameter)
        )
        items.append(
            (
                "raw_meal_inlet",
                "solids",
                self.meal_inlet_path(),
                self.meal_line_diameter,
            )
        )

        return items

    # ======================================================
    # CLEARANCES
    #
    # Every one of these is a GAP: the bodies' own radii are
    # already taken off, so the answer is what is left over.
    # ======================================================

    def dipleg_drop_clearance(self, stage):
        """Gap between a stage's vertical dipleg leg and the cyclone
        below it [m]."""

        return (
            self.chord_between_stages
            - self.meal_side_envelope_radius
            - 0.5 * self.meal_line_diameter
        )

    def chute_clearance(self, stage):
        """Gap between a meal chute and the cyclone it drops past [m]."""

        a, b = self.meal_chute_plan(stage)

        return plan.polygon_segment_distance(
            self.stage_envelope(stage + 1), a, b
        ) - 0.5 * self.meal_line_diameter

    def riser_column_clearance(self, stage=None):
        """Gap between a riser's vertical run and its own cyclone [m].

        Stage-independent: the column stands in the cyclone's own
        frame, so every stage sees the same picture. `stage` is
        accepted and ignored so that all the clearances share one
        signature and `CLEARANCES` can call them without a special
        case -- the table is what keeps the list from being
        hand-counted again.
        """

        return (
            self.riser_reach
            - self.riser_local_envelope_radius
            - 0.5 * self.riser_diameter
        )

    def cyclone_calciner_clearance(self, stage):
        """Gap between a cyclone and the reserved calciner [m]."""

        return plan.polygon_point_distance(
            self.stage_envelope(stage), (0.0, 0.0)
        ) - self.calciner.reserved_radius

    def riser_calciner_clearance(self, stage):
        """Gap between a riser's vertical run and the calciner [m]."""

        return (
            math.hypot(*self.riser_axis(stage))
            - 0.5 * self.riser_diameter
            - self.calciner.reserved_radius
        )

    def clearances(self):
        """Every check, its narrowest measurement, and the bar.

        Yields (Clearance, have, need). ONE call for every table that
        wants to show the clearances -- `layout_report` and the ones
        on the drawing sheets -- so none of them can count to seven
        while the validator counts to six.
        """

        return [
            (
                check,
                min(
                    getattr(self, check.key)(stage)
                    for stage in check.stages(self.stage_count)
                ),
                self.mesh_clearance_m,
            )
            for check in CLEARANCES
        ]

    def duct_interferences(self):
        """Flow passages that overlap one they do not join.

        The six checks in `CLEARANCES` are each a duct against a
        VESSEL, or a vessel against the calciner, and each is measured
        in plan because a vessel is a body of revolution and plan is
        where its envelope lives. A duct against another DUCT is not
        that question: two pipes can share a patch of plan and miss by
        twenty metres of height, so it is asked in 3-D, exactly, on
        every pair of legs -- the raw meal inlet and the exit stack
        included, because they are passages like any other.

        ONE RULE REPLACES TWO HAND-WRITTEN ONES. There used to be a
        check for the dipleg against its own gas elbow and another for
        the dipleg against the mouth leg below, both in plan, both
        enumerated by hand -- and the pair they missed is exactly the
        one that was wrong: the meal line crossed its riser twice, once
        by accident nine metres above the junction it was aiming for.
        A rule that says "no passage may touch a passage it does not
        join" cannot miss a case, because it does not enumerate any.
        """

        return space.interferences(
            [
                (name, path, diameter)
                for name, _kind, path, diameter in self.connections()
            ],
            self.mesh_clearance_m,
        )

    # ======================================================
    # VALIDATION
    # ======================================================

    def _validate(self):

        if int(self.stage_count) != self.stage_count or self.stage_count < 2:
            raise ValueError(
                f"TowerSpec.stage_count must be an integer >= 2, "
                f"got {self.stage_count}"
            )

        for table in (TOWER_RATIO_RANGES, TOWER_ANGLE_RANGES,
                      TOWER_LENGTH_RANGES):

            for name, (lo, hi) in table.items():
                value = float(getattr(self, name))

                if not (lo <= value <= hi):
                    raise ValueError(
                        f"TowerSpec.{name} must be within [{lo}, {hi}], "
                        f"got {value}"
                    )

        if self.layout_pattern not in LAYOUT_PATTERNS:
            raise ValueError(
                f"TowerSpec.layout_pattern must be one of "
                f"{LAYOUT_PATTERNS}, got {self.layout_pattern!r}"
            )

        # ---- meal lines have to run ----
        #
        # Checked on the DERIVED slope of every meal line, not on a
        # field. The path is fixed at both ends -- dipleg discharge
        # above, landing point on the riser below -- so the slope is a
        # consequence of the layout, and this is where the layout is
        # refused for producing one the meal would plug in.
        repose = repose_angle_deg()

        for stage in range(1, self.stage_count):

            slope = self.meal_entry_angle_deg(stage)

            if slope <= repose:
                raise ValueError(
                    f"TowerSpec: the meal line from stage {stage} falls "
                    f"at {slope:.1f} deg, which does not clear the "
                    f"meal's angle of repose ({repose} deg, from the "
                    "twin's motion.repose_angle_deg). A meal line laid "
                    "shallower than the heap the meal makes does not "
                    "run, it plugs. Lower meal_entry_height_ratio "
                    f"({self.meal_entry_height_ratio}) so it lands "
                    "further down the riser, or close "
                    f"stage_azimuth_step_deg ({self.stage_azimuth_step_deg})"
                )

        # The raw meal inlet is a chute of its own, set rather than
        # derived: it comes in from outside the tower, so nothing but
        # this fixes its slope.
        if self.dipleg_entry_angle_deg <= repose:
            raise ValueError(
                "TowerSpec.dipleg_entry_angle_deg is "
                f"{self.dipleg_entry_angle_deg} deg, which does not "
                f"clear the meal's angle of repose ({repose} deg)"
            )

        self._validate_plan()

    def _validate_plan(self):
        """Every inequality in `CLEARANCES`, in number order, and then
        the one rule that covers every pair of ducts.

        THE LIST IS WALKED, NOT WRITTEN OUT. It used to be written out
        here and in five other places, all of them saying seven, and
        that is how the crossing came to be missed: nobody was counting
        against anything. `layout_report` and the drawing's tables walk
        the same table, so a seventh check appears everywhere at once
        or nowhere at all.

        NOTHING IS CLAMPED. A layout that does not clear is refused.
        """

        for check in CLEARANCES:

            need = self.mesh_clearance_m
            measure = getattr(self, check.key)

            for stage in check.stages(self.stage_count):

                have = measure(stage)

                if have < need:
                    raise ValueError(
                        f"TowerSpec check {check.number} ({check.label}): "
                        + check.explain(self, stage, have, need)
                    )

        for name_a, i, name_b, j, gap in self.duct_interferences():
            raise ValueError(
                f"TowerSpec ducts ({_stage_of(name_a, name_b)}): leg {i} "
                f"of {name_a} and leg {j} of "
                f"{name_b} overlap by {-gap:.3f} m, and they do not "
                "join there. The tower is built as a union, so the two "
                "passages would merge and the fluid volume would carry "
                "a short circuit between them. Turn "
                f"meal_side_azimuth_deg ({self.meal_side_azimuth_deg}) "
                "off the leg, or widen stage_azimuth_step_deg "
                f"({self.stage_azimuth_step_deg})"
            )


def layout_report(tower=None):
    """The Faz 5 layout, as text. Makes no geometry."""

    tower = tower or TowerSpec()
    cyc = tower.cyclone
    out = []

    out.append("=" * 66)
    out.append("FAZ 4 + 5 -- preheater tower layout (no solid is built)")
    out.append("=" * 66)

    out.append("")
    out.append(f"  {tower.stage_count} IDENTICAL cyclones, D_body {cyc.D_body:.2f} m")
    out.append(f"  stage pitch          {tower.pitch:10.2f} m")
    out.append(f"  stage gap            {tower.stage_gap:10.2f} m")
    out.append(f"  tower height         {tower.tower_height:10.2f} m")
    out.append(f"  riser bore (derived) {tower.riser_diameter:10.2f} m")
    out.append(f"  meal line bore       {tower.meal_line_diameter:10.2f} m")

    out.append("")
    out.append("STAGES  (1 = top, gas leaves here; 5 = bottom, gas enters)")
    out.append(f"  {'stage':<8}{'dipleg z':>12}{'roof z':>12}{'mouth z':>12}")

    for stage in range(1, tower.stage_count + 1):
        roof_z = (
            tower.stage_base_z(stage)
            + cyc.total_height
            - cyc.vortex_finder_protrusion
        )
        out.append(
            f"  {stage:<8}{tower.stage_base_z(stage):>12.2f}"
            f"{roof_z:>12.2f}{tower.mouth_point(stage)[2]:>12.2f}"
        )

    out.append("")
    out.append(
        f"PLAN  ({tower.layout_pattern}, "
        f"{tower.stage_azimuth_step_deg:.0f} deg step on a "
        f"{tower.column_radius:.3f} m circle)"
    )
    out.append(
        f"  {'stage':<7}{'x':>9}{'y':>9}{'azimuth':>9}"
        f"{'dX':>9}{'dY':>9}{'offset':>9}{'riser x':>10}{'riser y':>9}"
    )

    previous = None

    for placement in tower.placements():

        if previous is None:
            step = " " * 27
        else:
            step = (
                f"{placement.x - previous.x:>9.3f}"
                f"{placement.y - previous.y:>9.3f}"
                f"{math.hypot(placement.x - previous.x, placement.y - previous.y):>9.3f}"
            )

        axis = tower.riser_axis(placement.stage)

        out.append(
            f"  {placement.stage:<7}{placement.x:>9.3f}{placement.y:>9.3f}"
            f"{placement.azimuth_deg:>9.1f}{step}{axis[0]:>10.3f}{axis[1]:>9.3f}"
        )

        previous = placement

    out.append("")
    out.append(
        f"  reserved calciner   radius {tower.calciner.reserved_radius:.3f} m "
        f"on the tower axis, derived from "
        f"{tower.calciner.design_volumetric_flow_m3_s:.2f} m3/s at "
        f"{tower.calciner.gas_velocity_m_s:.1f} m/s"
    )

    out.append("")
    out.append(
        f"CLEARANCES  ({len(CLEARANCES)} of them; each has to beat its "
        "own bar or the layout is refused)"
    )
    out.append(
        f"  {'':<38}{'narrowest':>11}{'needs':>9}{'margin':>9}"
    )

    for check, have, need in tower.clearances():
        out.append(
            f"  {check.number} {check.label:<36}"
            f"{have:>11.3f}{need:>9.3f}{have - need:>9.3f}"
        )

    out.append("")
    out.append(
        f"  mesh clearance {tower.mesh_clearance_m:.3f} m -- numerical, "
        "not mechanical: the fluid volume is a union, and what it "
        "cannot survive is interference"
    )

    out.append("")
    out.append("CONNECTIONS")

    for name, kind, path, diameter in tower.connections():
        length = sum(
            math.dist(a, b) for a, b in zip(path, path[1:])
        )
        out.append(
            f"  {name:<18}{kind:<8}{len(path) - 1} segments"
            f"{length:>10.2f} m  bore {diameter:.2f} m"
        )

    out.append("")
    out.append("MEAL LINES  (must land on the riser they join)")
    out.append(
        f"  {'from stage':<12}{'entry z':>10}{'riser run z':>22}{'  ok':>6}"
    )

    for stage in range(1, tower.stage_count):
        z_low, z_high = tower.riser_vertical_span(stage + 1)
        z_entry = tower.meal_line_path(stage)[-1][2]
        ok = "yes" if z_low <= z_entry <= z_high else "NO"
        out.append(
            f"  {stage:<12}{z_entry:>10.2f}"
            f"{z_low:>11.2f} ..{z_high:>8.2f}{ok:>6}"
        )

    out.append("")
    out.append(
        f"  meal lines at {tower.dipleg_entry_angle_deg:.1f} deg against a "
        f"{repose_angle_deg():.1f} deg repose angle"
    )
    out.append("")
    out.append("  NOT WIRED INTO THE TWIN. Geometry only -- no solver change.")
    out.append("")

    return "\n".join(out)
