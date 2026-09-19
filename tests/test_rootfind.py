"""The root finder, against analytic residuals only.

No twin, no solve: every test here runs in microseconds. That
is the point. The expensive thing in a setpoint solve is the
residual, so the control flow around it has to be pinned
somewhere that costs nothing, or it never gets exercised for
the awkward cases -- an evaluation that fails, a bracket with
no root, a non-monotone residual.
"""

import math
import unittest

from solver.rootfind import INFEASIBLE, find_root


TOL = {"residual_tolerance": 1e-9, "x_tolerance": 1e-9}


class CountedResidual:
    """Wraps a residual and counts the calls the finder makes."""

    def __init__(self, fn):
        self.fn = fn
        self.calls = 0
        self.xs = []

    def __call__(self, x):
        self.calls += 1
        self.xs.append(x)
        return self.fn(x)


class FindRootTest(unittest.TestCase):

    def test_linear(self):

        f = CountedResidual(lambda x: 2.0 * x - 7.0)
        r = find_root(f, 0.0, 10.0, **TOL)

        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.x, 3.5, places=8)
        self.assertLessEqual(f.calls, 12)

    def test_stiff_exponential(self):
        """Arrhenius-shaped: flat, then a wall.

        This is the shape that makes plain secant overshoot.
        """

        def residual(x):
            return math.exp(12.0 * (x - 4.0)) - 1.0

        f = CountedResidual(residual)

        # x_tolerance has to be small enough for the slope:
        # |f'| = 12 at the root, so reaching a 1e-8 residual
        # needs steps below ~1e-9 and the stagnation check
        # would otherwise fire first -- correctly.
        r = find_root(f, 0.0, 10.0, residual_tolerance=1e-8,
                      x_tolerance=1e-12, max_evaluations=40)

        self.assertTrue(r.converged, r.reason)
        self.assertAlmostEqual(r.x, 4.0, places=6)

    def test_non_monotone_with_one_root_in_the_bracket(self):
        """The residual dips and recovers before crossing.

        The bracket must survive that; a secant step that left
        it would converge to the wrong place or diverge.
        """

        def residual(x):
            # Negative at 0, negative dip near 2, crosses at 5.
            return (x - 5.0) * (1.0 + 0.5 * math.sin(3.0 * x))

        r = find_root(residual, 0.0, 8.0, residual_tolerance=1e-8,
                      x_tolerance=1e-9, max_evaluations=60)

        self.assertTrue(r.converged, r.reason)
        self.assertAlmostEqual(r.x, 5.0, places=5)

    def test_root_exactly_at_a_bracket_end(self):

        r = find_root(lambda x: x - 3.0, 3.0, 9.0, **TOL)

        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.x, 3.0, places=12)
        self.assertEqual(r.reason, "root at a bracket end")

    # ------------------------------------------------------
    # The cases that matter for a plant residual.
    # ------------------------------------------------------
    def test_no_sign_change_is_reported_not_looped(self):
        """This is the HEAD case: the handle has no authority.

        Measured: dT_discharge/dfuel = -6.50 K per kg/s, wrong
        sign, so no fuel rate reaches the spec. The finder must
        say so rather than grind or return a plausible-looking
        number.
        """

        f = CountedResidual(lambda x: 100.0 + x)
        r = find_root(f, 0.0, 5.0, **TOL)

        self.assertFalse(r.converged)
        self.assertIn("no sign change", r.reason)
        self.assertLessEqual(f.calls, 12)

    def test_expansion_finds_a_root_outside_the_initial_bracket(self):

        r = find_root(lambda x: x - 9.0, 0.0, 4.0,
                      residual_tolerance=1e-8, x_tolerance=1e-9,
                      max_evaluations=40)

        self.assertTrue(r.converged, r.reason)
        self.assertAlmostEqual(r.x, 9.0, places=6)

    def test_infeasible_endpoint_is_retreated_from(self):
        """Low fuel makes the preheater solve fail.

        The finder should walk the endpoint inward until the
        model can be evaluated, not abandon the solve.
        """

        def residual(x):
            if x < 1.0:
                return INFEASIBLE
            return x - 3.0

        f = CountedResidual(residual)
        r = find_root(f, 0.0, 10.0, residual_tolerance=1e-8,
                      x_tolerance=1e-9, max_evaluations=40)

        self.assertTrue(r.converged, r.reason)
        self.assertAlmostEqual(r.x, 3.0, places=6)
        self.assertTrue(any(x < 1.0 for x in f.xs))

    def test_infeasible_interior_patch_is_stepped_around(self):

        def residual(x):
            if 6.0 < x < 7.0:
                return INFEASIBLE
            return x - 3.0

        r = find_root(residual, 0.0, 10.0, residual_tolerance=1e-8,
                      x_tolerance=1e-9, max_evaluations=40)

        self.assertTrue(r.converged, r.reason)
        self.assertAlmostEqual(r.x, 3.0, places=6)

    def test_everything_infeasible_is_reported(self):

        r = find_root(lambda x: INFEASIBLE, 0.0, 10.0, **TOL)

        self.assertFalse(r.converged)
        self.assertIn("infeasible", r.reason)

    def test_budget_is_honoured(self):

        # A tolerance below double precision, so the only way
        # out is the budget.
        f = CountedResidual(lambda x: math.sin(x) - 0.5)
        r = find_root(f, 0.0, 1.0, residual_tolerance=1e-30,
                      x_tolerance=1e-30, max_evaluations=7)

        self.assertLessEqual(f.calls, 7)
        self.assertEqual(r.evaluations, f.calls)

    def test_small_step_alone_does_not_claim_convergence(self):
        """A bracket collapsing on a wall is not a root.

        Both tolerances are required precisely so this cannot
        be reported as converged.
        """

        # Never crosses zero; tiny steps, large residual.
        r = find_root(lambda x: 5.0 + x * x, -1.0, 1.0,
                      residual_tolerance=1e-9, x_tolerance=1e30,
                      max_evaluations=30)

        self.assertFalse(r.converged)

    def test_history_records_every_evaluation(self):

        f = CountedResidual(lambda x: x - 2.0)
        r = find_root(f, 0.0, 10.0, **TOL)

        self.assertEqual(len(r.history), f.calls)
        self.assertEqual([x for x, _ in r.history], f.xs)

    def test_rejects_a_backwards_bracket(self):

        with self.assertRaises(ValueError):
            find_root(lambda x: x, 5.0, 1.0, **TOL)

    def test_rejects_non_positive_tolerances(self):

        with self.assertRaises(ValueError):
            find_root(lambda x: x, 0.0, 1.0,
                      residual_tolerance=0.0, x_tolerance=1e-9)


if __name__ == "__main__":
    unittest.main()
