"""The cyclone solid is the cyclone the spec describes.

tests/test_preheater_cyclone_spec.py checks the arithmetic. This module checks
the SOLID: it builds the B-rep and then measures it, so what is
asserted is the geometry that exists rather than the code that was
meant to produce it. Dimensions come back out of the analytic surfaces
OCCT keeps behind each face, not out of the bounding box.

WHY THE CONE IS BUILT WITH makeCone
-----------------------------------
The cone half-angle is the one INDEPENDENT dimension of the cone --
cone height is derived from it -- so it is the one that most needs
checking in the finished solid. A lofted frustum is a B-spline and its
angle cannot be read back at all. makeCone leaves an analytic conical
surface and `BRepAdaptor_Surface(...).Cone().SemiAngle()` returns 22.0
degrees exactly. That is why the builder does not loft it.

WHAT THE FACETING TEST IS FOR
-----------------------------
The volute is a ruled loft through `sections` radial rectangles, so its
outer wall is a chordal polygon and the solid UNDERSTATES the smooth
scroll. That is only acceptable if `sections` is a resolution and not a
dimension, which means the error has to go to zero as it is refined.
MEASURED against the closed-form volume:

    sections   volume [m3]     error        signed
       18        283.6233     0.39038 %    -1.11153
       36        284.4568     0.09763 %    -0.27800
       72        284.6660     0.02417 %    -0.06881
      144        284.7177     0.00602 %    -0.01715
      288        284.7305     0.00153 %    -0.00435

The error quarters every time `sections` doubles -- O(d_theta^2), as a
chordal approximation must be -- and it is one-sided, always below.
Both facts are asserted below.

THAT ONE-SIDEDNESS IS NOT COSMETIC: IT IS HOW A REAL BUG WAS FOUND.
The closed form first subtracted the WHOLE dip tube wall, including
the length standing above the roof. Above the roof the envelope is the
outlet bore and the wall lies outside it, so nothing is cut there, and
the closed form was 0.146 m3 too small. The CAD volume then crossed it
between 36 and 72 sections instead of rising to meet it. A two-sided
tolerance would have passed; the crossing is what showed the error.

WHAT THIS MODULE DOES NOT CHECK
-------------------------------
Anything about the process. There is no pressure drop here, no
separation efficiency, no residence time and no coupling to the twin.
The twin's preheater still runs on its placeholder 4.2 m x 25 m rotary
cylinder (pyroprocess/preheater/preheater.py:89) and nothing in this
package touches it.
"""

import math
import unittest
from dataclasses import replace

from tests.twin_harness import REPO_ROOT  # noqa: F401  (puts repo on sys.path)

from geometry.preheater.cyclone_spec import CycloneSpec

try:
    import cadquery as cq  # noqa: F401

    from geometry import measure
    from geometry.preheater import measure as cyclone_measure
    from geometry.preheater.cyclone_build import build_cyclone, roof_height

    HAS_CADQUERY = True

except ImportError:
    HAS_CADQUERY = False


SKIP_REASON = (
    "cadquery is not importable; install it with "
    "requirements-cad.txt and put it on PYTHONPATH"
)

# The volute's chordal faceting at the default 72 sections.
FACET_TOLERANCE = 5.0e-4        # relative


def _intersection_volume(a, b):
    """Volume shared by two solids [m3]; 0.0 when they only touch."""

    try:
        common = a.intersect(b)
    except Exception:
        return 0.0

    if not common.Solids():
        return 0.0

    return float(common.Volume())


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class CycloneSolidTest(unittest.TestCase):
    """One closed solid, and no stray bodies in it."""

    @classmethod
    def setUpClass(cls):
        # OCCT is slow and the solid does not change between tests.
        cls.spec = CycloneSpec()
        cls.envelope, cls.parts = build_cyclone(cls.spec)

    def test_the_cyclone_is_a_single_body(self):
        """Faz 3's 'no accidental parts' condition, as a number."""

        self.assertEqual(len(self.envelope.Solids()), 1)

    def test_the_cyclone_is_watertight(self):
        """One closed shell, and OCCT's own validity check passes."""

        self.assertEqual(len(self.envelope.Shells()), 1)
        self.assertTrue(self.envelope.isValid())

    def test_every_component_is_itself_a_valid_single_solid(self):
        """A stray body in a part would survive the fuse unnoticed."""

        for name, part in self.parts.items():

            with self.subTest(component=name):
                self.assertEqual(len(part.Solids()), 1)
                self.assertTrue(part.isValid())
                self.assertGreater(part.Volume(), 0.0)


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class CycloneDimensionTest(unittest.TestCase):
    """The dimension table, read back out of the B-rep."""

    @classmethod
    def setUpClass(cls):
        cls.spec = CycloneSpec()
        cls.envelope, cls.parts = build_cyclone(cls.spec)

    def test_the_datum_is_the_dipleg_discharge(self):
        """z = 0 at the bottom, so Faz 5 stacking is pure addition."""

        self.assertAlmostEqual(
            self.envelope.BoundingBox().zmin, 0.0, delta=1.0e-9
        )

    def test_the_solid_is_as_tall_as_the_spec_says(self):
        self.assertAlmostEqual(
            self.envelope.BoundingBox().zlen,
            self.spec.total_height,
            delta=1.0e-9,
        )

    def test_the_volute_mouth_sits_at_the_outer_spiral_radius(self):
        """The scroll starts on +x at R + b; nothing reaches past it.

        Held to a micrometre rather than to machine precision: OCCT
        computes a bounding box to its own linear tolerance, ~1e-7 m,
        and on a 4.45 m radius that is 2e-8 relative. A micrometre on a
        5.6 m vessel is still far finer than any dimension here means.
        """

        expected = 0.5 * self.spec.D_body + self.spec.inlet_width

        self.assertAlmostEqual(
            self.envelope.BoundingBox().xmax, expected, delta=1.0e-6
        )

    def test_every_radius_in_the_solid_is_a_radius_the_spec_names(self):
        """Catches a stray cylinder as well as a wrong one."""

        spec = self.spec
        r_vf_in = 0.5 * spec.vortex_finder_diameter

        expected = (
            0.5 * spec.D_body,
            0.5 * spec.dipleg_diameter,
            r_vf_in,
            r_vf_in + spec.vortex_finder_wall_thickness_m,
            spec.volute_inner_radius,
        )

        found = measure.cylinder_radii(self.envelope)

        for radius in found:

            with self.subTest(radius=radius):
                self.assertTrue(
                    any(abs(radius - e) < 1.0e-7 for e in expected),
                    f"solid carries a cylinder of radius {radius} m "
                    f"that the spec does not name",
                )

    def test_the_body_and_dipleg_radii_are_present(self):
        found = measure.cylinder_radii(self.envelope)

        for label, expected in (
            ("body", 0.5 * self.spec.D_body),
            ("dipleg", 0.5 * self.spec.dipleg_diameter),
            ("vortex finder", 0.5 * self.spec.vortex_finder_diameter),
        ):

            with self.subTest(surface=label):
                self.assertTrue(
                    any(abs(r - expected) < 1.0e-7 for r in found),
                    f"no {label} cylinder of radius {expected} m in the solid",
                )

    def test_the_cone_angle_survives_into_the_solid(self):
        """The cone's one independent dimension, read from the B-rep."""

        angles = measure.cone_half_angles_deg(self.envelope)

        self.assertEqual(len(angles), 1)
        self.assertAlmostEqual(
            angles[0], self.spec.cone_half_angle_deg, places=9
        )

    def test_the_roof_and_the_volute_floor_are_where_they_should_be(self):
        """Heights come from planar-face z, not from the box."""

        spec = self.spec
        decks = measure.planar_face_heights(self.envelope)

        roof = roof_height(spec)

        for label, z in (
            ("dipleg discharge", 0.0),
            ("volute floor", roof - spec.inlet_height),
            ("roof", roof),
            ("gas outlet", roof + spec.vortex_finder_protrusion),
        ):

            with self.subTest(deck=label):
                self.assertTrue(
                    any(abs(z - d) < 1.0e-7 for d in decks),
                    f"no horizontal face at the {label}, z = {z} m",
                )

    def test_the_measurement_table_agrees_with_the_spec(self):
        """The deliverable itself: two columns that must match."""

        rows = cyclone_measure.measure_cyclone(self.envelope, self.spec)

        self.assertTrue(rows)

        for name, from_cad, from_spec, unit in rows:

            with self.subTest(quantity=name):
                self.assertAlmostEqual(from_cad, from_spec, delta=1.0e-7)


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class CycloneVolumeTest(unittest.TestCase):
    """The solid holds the gas volume the arithmetic says it does."""

    @classmethod
    def setUpClass(cls):
        cls.spec = CycloneSpec()
        cls.envelope, cls.parts = build_cyclone(cls.spec)

    def test_the_primitive_components_are_exact(self):
        """No faceting in a cylinder or an analytic cone."""

        spec = self.spec

        for name, expected in (
            ("dipleg", spec.dipleg_volume),
            ("cone", spec.cone_volume),
            ("barrel", spec.cylinder_volume),
            ("outlet", spec.outlet_volume),
        ):

            with self.subTest(component=name):
                self.assertAlmostEqual(
                    self.parts[name].Volume() / expected, 1.0, places=9
                )

    def test_the_envelope_volume_matches_the_closed_form(self):
        self.assertAlmostEqual(
            self.envelope.Volume() / self.spec.envelope_volume,
            1.0,
            delta=FACET_TOLERANCE,
        )

    def test_the_faceting_error_falls_as_the_spiral_is_refined(self):
        """Proves `sections` is a resolution and not a dimension."""

        exact = self.spec.envelope_volume
        errors = []

        for sections in (18, 36, 72, 144):
            envelope, _ = build_cyclone(self.spec, sections=sections)
            errors.append(abs(envelope.Volume() - exact) / exact)

        for coarse, fine in zip(errors, errors[1:]):

            with self.subTest(coarse=coarse, fine=fine):
                self.assertLess(fine, coarse)

        self.assertLess(errors[-1], 1.0e-4)

    def test_the_faceted_solid_never_overshoots_the_smooth_one(self):
        """A chordal polygon is inscribed, so it can only lose volume.

        The one-sidedness is the assertion that caught the dip-tube
        wall error described in the module docstring. Do not relax it
        to a two-sided tolerance.
        """

        exact = self.spec.envelope_volume

        for sections in (18, 36, 72, 144):

            with self.subTest(sections=sections):
                envelope, _ = build_cyclone(self.spec, sections=sections)

                self.assertLess(envelope.Volume(), exact)

    def test_the_overlap_that_makes_the_joint_manifold_is_inert(self):
        """It exists for the boolean, so it must not move the answer."""

        volumes = []

        for overlap in (0.005, 0.010, 0.020, 0.040):
            spec = replace(self.spec, volute_overlap_ratio=overlap)
            envelope, _ = build_cyclone(spec)
            volumes.append(envelope.Volume())

        self.assertAlmostEqual(
            max(volumes) / min(volumes), 1.0, delta=1.0e-4
        )


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class CycloneConnectionTest(unittest.TestCase):
    """The components are joined, and joined where they should be."""

    @classmethod
    def setUpClass(cls):
        cls.spec = CycloneSpec()
        cls.envelope, cls.parts = build_cyclone(cls.spec)

    def test_the_butt_joints_do_not_overlap(self):
        """Dipleg on cone and cone on barrel meet face to face.

        Zero shared volume, yet the fused result is still one solid --
        which is exactly what a correct butt joint looks like, and what
        a floating, unconnected part does not.
        """

        for a, b in (("dipleg", "cone"), ("cone", "barrel"), ("barrel", "outlet")):

            with self.subTest(joint=f"{a}-{b}"):
                self.assertAlmostEqual(
                    _intersection_volume(self.parts[a], self.parts[b]),
                    0.0,
                    delta=1.0e-9,
                )

    def test_the_volute_really_overlaps_the_barrel(self):
        """The one tangential joint, and the one that needs volume.

        Zero here would mean a tangency, which fuses into a
        zero-thickness sliver and a non-manifold solid.
        """

        shared = _intersection_volume(self.parts["volute"], self.parts["barrel"])

        self.assertGreater(shared, 0.0)

        # The closed form is the SMOOTH overlap. The scroll's inner
        # boundary is a chordal polygon inscribed in that radius, so it
        # dips inside the smooth wall and the measured overlap runs a
        # faceting-sized amount high -- 0.8 % at 72 sections. The claim
        # under test is that the joint is a real overlap of about the
        # right size, not a tangency, and 2 % says that without
        # pretending the loft is smooth.
        self.assertAlmostEqual(
            shared / self.spec.volute_overlap_volume,
            1.0,
            delta=2.0e-2,
        )

    def test_the_fusion_actually_fused(self):
        """Between the largest part and the sum: overlap is real.

        One assertion covering volume, connectivity and the absence of
        a duplicated body all at once.
        """

        parts_total = sum(
            self.parts[name].Volume()
            for name in ("dipleg", "cone", "barrel", "volute", "outlet")
        )
        largest = max(
            self.parts[name].Volume()
            for name in ("dipleg", "cone", "barrel", "volute", "outlet")
        )

        self.assertGreater(self.envelope.Volume(), largest)
        self.assertLess(self.envelope.Volume(), parts_total)

    def test_the_vortex_finder_is_a_void_and_not_material(self):
        """After the cut, no part of the wall is inside the envelope."""

        self.assertAlmostEqual(
            _intersection_volume(self.envelope, self.parts["vortex_finder_wall"]),
            0.0,
            delta=1.0e-6,
        )

    def test_cutting_the_dip_tube_removes_only_its_immersed_length(self):
        """Above the roof the wall is outside the bore, so nothing goes.

        This is the arithmetic the closed form originally got wrong.
        """

        spec = self.spec
        r_in = 0.5 * spec.vortex_finder_diameter
        r_out = r_in + spec.vortex_finder_wall_thickness_m

        immersed = math.pi * (r_out ** 2 - r_in ** 2) * spec.vortex_finder_length
        whole_tube = math.pi * (r_out ** 2 - r_in ** 2) * (
            spec.vortex_finder_length + spec.vortex_finder_protrusion
        )

        self.assertAlmostEqual(
            spec.vortex_finder_wall_volume, immersed, places=12
        )
        self.assertLess(spec.vortex_finder_wall_volume, whole_tube)

        uncut = (
            self.parts["dipleg"]
            .fuse(self.parts["cone"])
            .fuse(self.parts["barrel"])
            .fuse(self.parts["volute"])
            .fuse(self.parts["outlet"])
        )

        # 1 % on the CUT, because the dip tube wall is 12 mm thick on a
        # 1.4 m radius and OCCT resolves a feature that thin to about
        # that. It is still a wide enough gap to tell the two candidate
        # formulas apart: counting the protruding length too would put
        # this ratio at 0.70, not 0.997.
        self.assertAlmostEqual(
            (uncut.Volume() - self.envelope.Volume()) / immersed,
            1.0,
            delta=1.0e-2,
        )


@unittest.skipUnless(HAS_CADQUERY, SKIP_REASON)
class CycloneReplicationTest(unittest.TestCase):
    """Faz 4 rests on this: the same spec gives the same solid."""

    def test_building_twice_gives_the_same_geometry(self):
        spec = CycloneSpec()

        first, _ = build_cyclone(spec)
        second, _ = build_cyclone(spec)

        self.assertAlmostEqual(first.Volume(), second.Volume(), places=9)
        self.assertAlmostEqual(
            first.BoundingBox().zlen, second.BoundingBox().zlen, places=9
        )


if __name__ == "__main__":
    unittest.main()
