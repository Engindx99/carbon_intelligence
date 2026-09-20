"""
Faz 1 -- the central geometry specification for ONE preheater cyclone.

Every dimension of the cyclone is stated here exactly once. Nothing
downstream (cyclone_build, preheater_build, the tests) carries a length
of its own: they read this object. Copying a dimension into a second
file is what lets five "identical" cyclones drift apart, so there is
nowhere to copy it to.

WHAT SIZES THE CYCLONE
----------------------
The body diameter is NOT a chosen number. It is what the gas duty
demands at a design inlet velocity:

    rho_g  = P M / (R T)                ideal gas
    Q_v    = m_dot_g / rho_g            volumetric flow      [m3/s]
    A_in   = Q_v / u_in                 inlet cross-section  [m2]
    A_in   = (Ka D)(Kb D)               inlet is Ka D by Kb D
    ->  D  = sqrt(A_in / (Ka Kb))

Every other dimension is a ratio to D, so the whole cyclone follows the
gas through one square root.

THE DESIGN BASIS IS NOT THE TWIN'S CURRENT OPERATING POINT, AND THAT IS
DELIBERATE. Running the derivation on what the twin actually carries
gives a cyclone nobody can build. MEASURED on the converged twin
(tests.twin_harness.run_twin, 2026-09-20), against the same derivation
with only the gas duty moving:

    design basis                       rho_g    Q_v    D_body   tower
    twin as it runs  42.4 kg/s 1986 K  0.184   230.1   8.80 m   ~156 m
    flow corrected   28.0 kg/s 1986 K  0.184   152.1   7.16 m   ~127 m
    THIS MODULE      28.0 kg/s 1200 K  0.305    91.9   5.56 m    ~98 m

    real cement preheater cyclone: body 4-6 m, whole tower 60-120 m

The twin's measured preheater gas profile, bottom stage first, is
1986.1 / 1906.8 / 1787.6 / 1608.0 / 1273.4 K at 42.36 kg/s.

Both of the twin's inputs are inflated, and neither is a new claim:

  * GAS FLOW. The plant feeds 27.78 kg/s of raw meal
    (configs/twin_cfg.yaml feed.Feed_rate_kg_s), so ~17.5 kg/s of
    clinker. Preheater exhaust runs ~1.6 kg gas per kg clinker, i.e.
    ~28 kg/s. The twin carries 42.4 kg/s -- 1.51x -- which is the
    1.53x over-firing already on record.
  * TEMPERATURE. The twin reads 1986 K into the bottom stage. A real
    ILC preheater sees 1150-1200 K there.

    (Do NOT read `state.Feed_rate` for the feed: it is 40.0 kg/s, the
    dataclass default at pyroprocess/globalstate.py:37, and nothing
    ever assigns it. The feed the solver uses goes through
    mass_flow.set_external_inputs at main.py:174.)

D scales as sqrt(Q_v) and Q_v as m_dot*T, so the two compound:
(42.36/28)(1986/1200) = 2.50x the volumetric flow, 1.58x the diameter.
That is the whole of the 8.80 -> 5.56 m gap.

THIS MODULE DOES NOT FIX EITHER DEFECT -- it is geometry, not a solver
change. It only refuses to inherit them, and writes down the size of
what it refused.

WHICH STAGE SETS THE ONE DIAMETER
---------------------------------
The five cyclones are identical, but gas expands up the tower, so their
volumetric flows differ by ~1.5x. The diameter is sized on the HOTTEST
stage -- the largest Q_v -- so that no stage exceeds the design inlet
velocity. The upper stages then run below it, which costs separation
efficiency rather than pressure drop and erosion.

WHAT IS INDEPENDENT AND WHAT IS NOT
-----------------------------------
Four of the listed dimensions are locked to each other by the cone:

    tan(half_angle) = (D_body - D_dipleg) / (2 H_cone)

so only three of them are free. Here the CONE ANGLE is the independent
one and the cone HEIGHT is derived, because the angle is the quantity
physics constrains: the cone wall must be steeper than the meal's angle
of repose or the meal sits in the cone instead of leaving it. That
repose angle is not invented here -- it is read out of the twin's own
`motion.repose_angle_deg`.

Total height is likewise the sum of its parts, never an input.

Both derived quantities are properties on a frozen dataclass, so they
cannot be set by hand and cannot disagree with the parts they come from.
"""

import math
from dataclasses import dataclass, replace

from physics.kiln_closures import R_UNIVERSAL

from ..twin_config import repose_angle_deg


# ======================================================
# ACCEPTED RANGES
#
# Out-of-range is REJECTED, never clamped (CLAUDE.md). The
# message names the field and the value it received, so a bad
# sweep says which knob it turned.
#
# The ratios are the cement-preheater family: low pressure
# drop, wide inlet, high throughput. They are NOT Stairmand's
# high-efficiency dust-collector ratios, which belong to a
# different machine doing a different job.
# ======================================================
RATIO_RANGES = {
    "inlet_height_ratio":             (0.45, 0.70),
    "inlet_width_ratio":              (0.20, 0.40),
    "vortex_finder_diameter_ratio":   (0.40, 0.60),
    "vortex_finder_length_ratio":     (0.45, 0.80),
    "vortex_finder_protrusion_ratio": (0.15, 0.40),
    "cylinder_height_ratio":          (1.00, 1.60),
    "dipleg_diameter_ratio":          (0.15, 0.28),
    "dipleg_length_ratio":            (0.50, 2.00),
    "volute_overlap_ratio":           (0.005, 0.050),
}

SCALAR_RANGES = {
    "design_gas_mass_flow_kg_s":      (1.0, 500.0),
    "design_gas_temperature_K":       (300.0, 2000.0),
    "design_gas_molar_mass_kg_mol":   (0.028, 0.032),
    "design_pressure_Pa":             (95000.0, 102000.0),
    "design_inlet_velocity_m_s":      (15.0, 22.0),
    "cone_half_angle_deg":            (12.0, 30.0),
    "volute_wrap_angle_deg":          (180.0, 360.0),
    "vortex_finder_wall_thickness_m": (0.008, 0.020),
}


@dataclass(frozen=True)
class CycloneSpec:
    """One preheater cyclone, in SI units.

    Frozen on purpose: a spec that can be edited after construction is
    a spec that can be edited past its own validation. Build a changed
    one with `dataclasses.replace(spec, ...)` and it revalidates.
    """

    # ================= DESIGN DUTY =================
    # What the gas asks the cyclone to be. See the module
    # docstring for why these are design values and not the
    # twin's current operating point.
    design_gas_mass_flow_kg_s:    float = 28.0       # kg/s
    design_gas_temperature_K:     float = 1200.0     # K, hottest stage
    design_gas_molar_mass_kg_mol: float = 0.030      # kg/mol, CO2-rich
    design_pressure_Pa:           float = 101325.0   # Pa
    design_inlet_velocity_m_s:    float = 18.0       # m/s

    # ================= SHAPE RATIOS (x D_body) =================
    inlet_height_ratio:             float = 0.55     # a/D
    inlet_width_ratio:              float = 0.30     # b/D
    vortex_finder_diameter_ratio:   float = 0.50     # De/D
    vortex_finder_length_ratio:     float = 0.60     # S/D, below roof
    vortex_finder_protrusion_ratio: float = 0.25     # above roof
    cylinder_height_ratio:          float = 1.30     # h/D
    dipleg_diameter_ratio:          float = 0.20     # B/D
    dipleg_length_ratio:            float = 1.00     # tower-layout figure

    # ================= ANGLES AND THICKNESSES =================
    # The cone is specified by its ANGLE; its height follows.
    cone_half_angle_deg:            float = 22.0     # deg from the axis
    volute_wrap_angle_deg:          float = 270.0    # deg of wrap

    # How far the volute's spiral runs INSIDE the body radius, so
    # the union is a clean overlap and not a tangency that leaves a
    # non-manifold edge. Geometry-construction robustness, not a
    # physical dimension.
    volute_overlap_ratio:           float = 0.020    # x D_body

    # A zero-thickness internal baffle is not a valid B-rep solid, so
    # the dip tube needs a wall for the envelope to close around it.
    vortex_finder_wall_thickness_m: float = 0.012    # m

    def __post_init__(self):
        self._validate()

    # ======================================================
    # DESIGN DUTY -> BODY DIAMETER
    # ======================================================
    @property
    def gas_density(self):
        """Ideal-gas density at the design condition [kg/m3]."""

        return (
            self.design_pressure_Pa
            * self.design_gas_molar_mass_kg_mol
            / (R_UNIVERSAL * self.design_gas_temperature_K)
        )

    @property
    def volumetric_flow(self):
        """Design volumetric gas flow [m3/s]."""

        return self.design_gas_mass_flow_kg_s / self.gas_density

    @property
    def inlet_area(self):
        """Inlet duct cross-section the design velocity implies [m2]."""

        return self.volumetric_flow / self.design_inlet_velocity_m_s

    @property
    def D_body(self):
        """Cyclone body diameter [m] -- DERIVED from the gas duty."""

        return math.sqrt(
            self.inlet_area
            / (self.inlet_height_ratio * self.inlet_width_ratio)
        )

    # ======================================================
    # LINEAR DIMENSIONS (all x D_body)
    # ======================================================
    @property
    def inlet_height(self):
        return self.inlet_height_ratio * self.D_body

    @property
    def inlet_width(self):
        return self.inlet_width_ratio * self.D_body

    @property
    def cylinder_height(self):
        return self.cylinder_height_ratio * self.D_body

    @property
    def vortex_finder_diameter(self):
        return self.vortex_finder_diameter_ratio * self.D_body

    @property
    def vortex_finder_length(self):
        """Immersion of the dip tube below the roof [m]."""

        return self.vortex_finder_length_ratio * self.D_body

    @property
    def vortex_finder_protrusion(self):
        """Outlet duct standing above the roof [m]."""

        return self.vortex_finder_protrusion_ratio * self.D_body

    @property
    def dipleg_diameter(self):
        return self.dipleg_diameter_ratio * self.D_body

    @property
    def dipleg_length(self):
        return self.dipleg_length_ratio * self.D_body

    # ======================================================
    # DERIVED, AND UNSETTABLE
    #
    # cone_height closes tan(half_angle) = (D - B)/(2 H).
    # total_height is the sum of the parts. Neither is a
    # field, so neither can be given a value that disagrees
    # with what it is made of.
    # ======================================================
    @property
    def cone_half_angle_rad(self):
        return math.radians(self.cone_half_angle_deg)

    @property
    def cone_height(self):
        """Height of the conical section [m] -- DERIVED."""

        return (
            (self.D_body - self.dipleg_diameter)
            / (2.0 * math.tan(self.cone_half_angle_rad))
        )

    @property
    def cone_wall_inclination_deg(self):
        """Cone wall angle from HORIZONTAL [deg]; must beat repose."""

        return 90.0 - self.cone_half_angle_deg

    @property
    def total_height(self):
        """Outlet duct top to dipleg bottom [m] -- DERIVED."""

        return (
            self.vortex_finder_protrusion
            + self.cylinder_height
            + self.cone_height
            + self.dipleg_length
        )

    # ======================================================
    # VOLUTE
    # ======================================================
    @property
    def volute_outer_radius(self):
        """Spiral radius at the inlet mouth [m]."""

        return 0.5 * self.D_body + self.inlet_width

    @property
    def volute_inner_radius(self):
        """Spiral radius where it meets the body, slightly inside [m]."""

        return 0.5 * self.D_body - self.volute_overlap_ratio * self.D_body

    @property
    def volute_wrap_angle_rad(self):
        return math.radians(self.volute_wrap_angle_deg)

    @property
    def volute_path_length(self):
        """Arc length of the spiral centre-line [m].

        r(t) = r0 - (r0 - r1) t / tw is linear in t, so dr/dt is the
        constant (r1 - r0)/tw and the length is the closed integral of
        sqrt(r^2 + (dr/dt)^2) dt. Evaluated by Simpson's rule, which is
        exact to well past the tolerance the CAD sweep is built to.
        """

        r0 = self.volute_outer_radius
        r1 = self.volute_inner_radius
        tw = self.volute_wrap_angle_rad
        drdt = (r1 - r0) / tw

        n = 400  # even
        h = tw / n

        def f(t):
            r = r0 + drdt * t
            return math.sqrt(r * r + drdt * drdt)

        total = f(0.0) + f(tw)

        for i in range(1, n):
            total += (4.0 if i % 2 else 2.0) * f(i * h)

        return total * h / 3.0

    # ======================================================
    # THE PLAN ENVELOPE
    #
    # How far the cyclone reaches from its own axis, as a
    # function of which way you look. It is NOT a circle,
    # because the scroll stands proud of the barrel over its
    # wrap and closes flush at the end of it.
    #
    # Everything that has to keep out of a cyclone's way asks
    # this question: the tower layout deciding how far apart
    # two stages must stand, and the drawings deciding where
    # to put the ink. So the law lives here, once. It used to
    # be written twice -- inline in cyclone_build.build_volute
    # and again in the drawing module -- which is two places
    # for one shape to be defined and one of them to go stale.
    # ======================================================
    def plan_envelope_radius(self, azimuth_deg):
        """Reach from the axis at one LOCAL azimuth [m].

        Azimuth 0 is the mouth, where the scroll is widest, and it
        grows the way the gas turns. Past the wrap there is no scroll
        left and the answer is the barrel.

        This is the same r_out(t) = R + b (1 - t) that
        `cyclone_build.build_volute` lofts the scroll through, with
        theta = wrap * t. At t = 1 both branches return exactly R, so
        the envelope has no step in it.
        """

        theta = azimuth_deg % 360.0
        R = 0.5 * self.D_body

        if theta > self.volute_wrap_angle_deg:
            return R

        return R + self.inlet_width * (
            1.0 - theta / self.volute_wrap_angle_deg
        )

    def plan_envelope(self, sections=180):
        """The envelope as a closed polygon, (x, y) in the local frame.

        `sections` is NUMERICAL, not physical -- how finely the curve
        is sampled. The polygon is inscribed, so it UNDERSTATES the
        reach by O(dtheta^2); anything using it for a clearance check
        must know that its answer is the conservative one only when it
        is the OTHER body that is polygonised. Where it matters, use
        `plan_envelope_radius` at the exact azimuth instead.
        """

        if int(sections) != sections or sections < 12:
            raise ValueError(
                f"plan envelope sections must be an integer >= 12, "
                f"got {sections}"
            )

        sections = int(sections)

        return [
            (
                self.plan_envelope_radius(360.0 * i / sections)
                * math.cos(2.0 * math.pi * i / sections),
                self.plan_envelope_radius(360.0 * i / sections)
                * math.sin(2.0 * math.pi * i / sections),
            )
            for i in range(sections + 1)
        ]

    # ======================================================
    # VOLUMES
    #
    # Analytic, and the Faz 3 test checks the CAD solid
    # against them. The envelope is the INNER (wetted) shape,
    # so these are gas volumes.
    # ======================================================
    @property
    def cylinder_volume(self):
        return math.pi * self.D_body ** 2 / 4.0 * self.cylinder_height

    @property
    def cone_volume(self):
        R = 0.5 * self.D_body
        r = 0.5 * self.dipleg_diameter

        return math.pi * self.cone_height / 3.0 * (R * R + R * r + r * r)

    @property
    def dipleg_volume(self):
        return math.pi * self.dipleg_diameter ** 2 / 4.0 * self.dipleg_length

    @property
    def outlet_volume(self):
        return (
            math.pi * self.vortex_finder_diameter ** 2 / 4.0
            * self.vortex_finder_protrusion
        )

    @property
    def volute_volume(self):
        """Volume of the scroll solid on its own [m3], before the fuse.

        The scroll is NOT a constant section swept along a path -- it
        narrows from `b` at the mouth to nothing where it meets the
        barrel, which is what lets all of the gas turn into the body.
        So it is an integral, not area x length:

            r_out(t) = R + b (1 - t),   r_in = R - ov,   t = theta/theta_w

            V = (a/2) theta_w [ integral r_out^2 dt  -  r_in^2 ]
              = (a/2) theta_w [ ((R+b)^3 - R^3)/(3b)  -  (R-ov)^2 ]

        exactly, since (a/2)(r_out^2 - r_in^2) d(theta) is the volume
        of the radial slab between the two radii.
        """

        R = 0.5 * self.D_body
        b = self.inlet_width
        a = self.inlet_height
        r_in = self.volute_inner_radius

        mean_square_r_out = ((R + b) ** 3 - R ** 3) / (3.0 * b)

        return (
            0.5 * a * self.volute_wrap_angle_rad
            * (mean_square_r_out - r_in * r_in)
        )

    @property
    def volute_overlap_volume(self):
        """The part of the scroll that lies inside the barrel [m3].

        Swallowed whole by the fuse, so it is the difference between
        the scroll solid and what the scroll adds to the envelope.
        Existing only to make the tangent joint manifold, it must not
        change the answer -- the Faz 3 test halves `volute_overlap_ratio`
        and asserts the fused volume does not move.
        """

        R = 0.5 * self.D_body
        r_in = self.volute_inner_radius

        return (
            0.5 * self.inlet_height * self.volute_wrap_angle_rad
            * (R * R - r_in * r_in)
        )

    @property
    def volute_envelope_volume(self):
        """What the scroll actually contributes to the envelope [m3]."""

        return self.volute_volume - self.volute_overlap_volume

    @property
    def vortex_finder_wall_volume(self):
        """Dip tube wall actually removed from the envelope [m3].

        ONLY THE IMMERSED LENGTH COUNTS. The builder runs the annulus
        from the dip tube's mouth up past the roof so the boolean cuts
        cleanly through the roof plane, but above the roof the envelope
        IS the outlet bore -- radius r_in -- and the wall sits outside
        it, so there is nothing there to remove.

        Counting the protruding length too overstated this by
        pi (r_out^2 - r_in^2) E = 0.146 m3 at the committed point, and
        the CAD volume crossed the analytic value between 36 and 72
        sections instead of converging up to it. That crossing is how
        the error was found; tests/test_cyclone_geometry.py now asserts
        the convergence is one-sided so it cannot come back.
        """

        r_in = 0.5 * self.vortex_finder_diameter
        r_out = r_in + self.vortex_finder_wall_thickness_m

        return math.pi * (r_out ** 2 - r_in ** 2) * self.vortex_finder_length

    @property
    def envelope_volume(self):
        """Closed-form gas volume of the whole cyclone [m3].

        The statement the CAD solid is held to in Faz 3. Written out
        here by hand so the test compares the geometry against the
        arithmetic rather than against the builder that made it.
        """

        return (
            self.cylinder_volume
            + self.cone_volume
            + self.dipleg_volume
            + self.volute_envelope_volume
            + self.outlet_volume
            - self.vortex_finder_wall_volume
        )

    @property
    def separator_volume(self):
        """Cylinder plus cone [m3] -- the separation space proper."""

        return self.cylinder_volume + self.cone_volume

    # ======================================================
    # VALIDATION
    #
    # Everything raises. Nothing clamps.
    # ======================================================
    def _validate(self):

        for name, (lo, hi) in SCALAR_RANGES.items():
            value = float(getattr(self, name))

            if not (lo <= value <= hi):
                raise ValueError(
                    f"CycloneSpec.{name} must be within [{lo}, {hi}], "
                    f"got {value}"
                )

        for name, (lo, hi) in RATIO_RANGES.items():
            value = float(getattr(self, name))

            if not (lo <= value <= hi):
                raise ValueError(
                    f"CycloneSpec.{name} must be within [{lo}, {hi}], "
                    f"got {value}"
                )

        # ---- the cone must shed the meal ----
        #
        # UNREACHABLE AS THE RANGES STAND, AND KEPT ANYWAY. A half
        # angle inside [12, 30] deg leaves the wall at 60-78 deg from
        # horizontal, always clear of the meal's 40 deg repose, so
        # SCALAR_RANGES rejects a bad angle first. This check is what
        # stops WIDENING that range from silently producing a cone the
        # meal sits in: the constraint is physical and belongs next to
        # the geometry, not in the range table's provenance comment.
        repose = repose_angle_deg()

        if self.cone_wall_inclination_deg <= repose:
            raise ValueError(
                "CycloneSpec.cone_half_angle_deg leaves a cone wall at "
                f"{self.cone_wall_inclination_deg} deg from horizontal, "
                f"which does not clear the meal's angle of repose "
                f"({repose} deg, motion.repose_angle_deg): the meal "
                "would sit in the cone instead of leaving it"
            )

        # ---- the dip tube must reach below the inlet ----
        # Otherwise gas entering the volute finds the outlet directly
        # and short-circuits the swirl the cyclone exists to make.
        if self.vortex_finder_length <= self.inlet_height:
            raise ValueError(
                "CycloneSpec: the vortex finder must reach below the "
                f"inlet mouth -- immersion {self.vortex_finder_length} m "
                f"against an inlet height of {self.inlet_height} m; "
                "raise vortex_finder_length_ratio "
                f"({self.vortex_finder_length_ratio}) above "
                f"inlet_height_ratio ({self.inlet_height_ratio})"
            )

        # ---- the dip tube must stay in the cylinder ----
        # Also unreachable as the ranges stand (S tops out at 0.80 D,
        # the cylinder starts at 1.00 D), and kept for the same reason
        # as the repose check above.
        if self.vortex_finder_length >= self.cylinder_height:
            raise ValueError(
                "CycloneSpec: the vortex finder would reach into the "
                f"cone -- immersion {self.vortex_finder_length} m "
                f"against a cylinder height of {self.cylinder_height} m"
            )

        # ---- openings must fit in the body ----
        if self.vortex_finder_diameter >= self.D_body:
            raise ValueError(
                "CycloneSpec: vortex finder diameter "
                f"{self.vortex_finder_diameter} m does not fit the body "
                f"bore {self.D_body} m"
            )

        if self.dipleg_diameter >= self.D_body:
            raise ValueError(
                f"CycloneSpec: dipleg diameter {self.dipleg_diameter} m "
                f"does not fit the body bore {self.D_body} m"
            )

        # ---- the dip tube wall must fit inside the dip tube ----
        if 2.0 * self.vortex_finder_wall_thickness_m >= self.vortex_finder_diameter:
            raise ValueError(
                "CycloneSpec: vortex_finder_wall_thickness_m "
                f"{self.vortex_finder_wall_thickness_m} m closes a dip "
                f"tube of {self.vortex_finder_diameter} m bore"
            )

        # ---- the scroll must not wrap into itself ----
        # Unreachable too: inlet_width_ratio tops out at 0.40 < 0.50.
        # tests/test_cyclone_spec.py asserts each of these three bands
        # really does exclude its violation, so "unreachable" is a
        # checked claim and not a comment.
        if self.inlet_width >= 0.5 * self.D_body:
            raise ValueError(
                "CycloneSpec: inlet width "
                f"{self.inlet_width} m is at or past the body radius "
                f"{0.5 * self.D_body} m, so the volute sweep would "
                "self-intersect"
            )


# ======================================================
# FAZ 1 GATE
#
# Prints the full dimension table and BUILDS NOTHING. No
# solid is made until these numbers have been read by a
# human and agreed with.
# ======================================================
DIMENSION_TABLE = (
    # (label, attribute, unit, provenance)
    ("Total height",            "total_height",             "m",   "DERIVED (sum of parts)"),
    ("Body diameter  D",        "D_body",                   "m",   "DERIVED (from gas duty)"),
    ("Cylinder height  h",      "cylinder_height",          "m",   "independent (x D)"),
    ("Cone height  H",          "cone_height",              "m",   "DERIVED (angle, D, B)"),
    ("Cone half-angle",         "cone_half_angle_deg",      "deg", "INDEPENDENT"),
    ("Vortex finder dia.  De",  "vortex_finder_diameter",   "m",   "independent (x D)"),
    ("Vortex finder len.  S",   "vortex_finder_length",     "m",   "independent (x D)"),
    ("Dipleg diameter  B",      "dipleg_diameter",          "m",   "independent (x D)"),
    ("Dipleg length",           "dipleg_length",            "m",   "independent (x D)"),
    ("Inlet width  b",          "inlet_width",              "m",   "independent (x D)"),
    ("Inlet height  a",         "inlet_height",             "m",   "independent (x D)"),
    ("Volute wrap angle",       "volute_wrap_angle_deg",    "deg", "independent"),
    ("Outlet duct above roof",  "vortex_finder_protrusion", "m",   "independent (x D)"),
)


def dimension_report(spec=None, stage_count=5):
    """The Faz 1 gate, as text. Makes no geometry."""

    spec = spec or CycloneSpec()
    out = []

    out.append("=" * 66)
    out.append("FAZ 1 GATE -- cyclone dimension table (no solid is built)")
    out.append("=" * 66)

    out.append("")
    out.append("DESIGN DUTY")
    out.append(f"  gas mass flow           {spec.design_gas_mass_flow_kg_s:10.3f} kg/s")
    out.append(f"  gas temperature         {spec.design_gas_temperature_K:10.1f} K")
    out.append(f"  gas molar mass          {spec.design_gas_molar_mass_kg_mol:10.4f} kg/mol")
    out.append(f"  pressure                {spec.design_pressure_Pa:10.0f} Pa")
    out.append(f"  inlet velocity          {spec.design_inlet_velocity_m_s:10.2f} m/s")
    out.append(f"  -> gas density          {spec.gas_density:10.4f} kg/m3")
    out.append(f"  -> volumetric flow      {spec.volumetric_flow:10.2f} m3/s")
    out.append(f"  -> inlet area           {spec.inlet_area:10.3f} m2")

    out.append("")
    out.append("DIMENSIONS")
    out.append(f"  {'quantity':<26}{'value':>10}  {'unit':<5}provenance")
    out.append("  " + "-" * 62)

    for label, attr, unit, provenance in DIMENSION_TABLE:
        out.append(
            f"  {label:<26}{getattr(spec, attr):10.2f}  {unit:<5}{provenance}"
        )

    out.append("")
    out.append("CONSISTENCY")
    out.append(
        f"  dip tube clears the inlet   S {spec.vortex_finder_length:.2f} "
        f"> a {spec.inlet_height:.2f} m"
    )
    out.append(
        f"  dip tube stays in cylinder  S {spec.vortex_finder_length:.2f} "
        f"< h {spec.cylinder_height:.2f} m"
    )
    out.append(
        f"  volute does not self-cut    b {spec.inlet_width:.2f} "
        f"< D/2 {0.5 * spec.D_body:.2f} m"
    )
    out.append(
        f"  cone sheds the meal         {spec.cone_wall_inclination_deg:.1f} "
        f"> repose {repose_angle_deg():.1f} deg"
    )

    out.append("")
    out.append("VOLUMES (inner/wetted envelope)")
    out.append(f"  cylinder                {spec.cylinder_volume:10.2f} m3")
    out.append(f"  cone                    {spec.cone_volume:10.2f} m3")
    out.append(f"  dipleg                  {spec.dipleg_volume:10.2f} m3")
    out.append(f"  volute (adds to envelope){spec.volute_envelope_volume:9.2f} m3")
    out.append(f"  separator (cyl + cone)  {spec.separator_volume:10.2f} m3")
    out.append(f"  WHOLE ENVELOPE          {spec.envelope_volume:10.2f} m3")

    out.append("")
    out.append("TOWER")
    out.append(
        f"  {stage_count} identical cyclones, bodies only: "
        f"{stage_count * spec.total_height:.1f} m of stacked height"
    )

    out.append("")
    out.append("INLET VELOCITY SENSITIVITY  (D ~ 1/sqrt(u))")
    out.append(f"  {'u_in [m/s]':<14}{'D_body [m]':>12}")

    for u in (15.0, 18.0, 22.0):
        swept = replace(spec, design_inlet_velocity_m_s=u)
        out.append(f"  {u:<14.1f}{swept.D_body:>12.2f}")

    out.append("")
    out.append("FOR REFERENCE -- the placeholder geometry this replaces")
    out.append("  pyroprocess/preheater/preheater.py models a stage as a")
    out.append("  slice of a 4.2 m x 25 m rotary cylinder: V_cell = 69.27 m3.")
    out.append(
        f"  This cyclone's separation space is "
        f"{spec.separator_volume:.1f} m3 "
        f"({spec.separator_volume / 69.27:.1f}x)."
    )
    out.append("")
    out.append("  NOT WIRED INTO THE TWIN. Geometry only -- no solver change.")
    out.append("")

    return "\n".join(out)


if __name__ == "__main__":
    print(dimension_report())
