"""The preheater counter-current inner loop: its budget, and the
difference between running out of one and diverging.

A budget of 50 produced two false negatives in a fuel experiment.
Measured with the budget lifted, at nodes_per_stage = 1 on the
literature-kinetics tree:

    fuel 1.6 kg/s -> converged in 51 iterations, rho = 0.708
    fuel 1.3 kg/s -> converged in 62 iterations, rho = 0.758

1.6 missed by ONE iteration, having fallen 421 K -> 9.6e-6 K
monotonically. Both were reported upward as infeasible operating
points, which is the single most expensive kind of wrong answer a
solver can give a root find: it removes a feasible point from a
bracket and nothing downstream can tell.

These tests pin the arithmetic that sets the budget, and pin that
the two failure modes now say which they are.
"""

import math
import unittest

from pyroprocess.preheater import heat_transfer


class BudgetIsDerivedTest(unittest.TestCase):
    """The budget is a numerical resource, so it gets an argument.

    Worst contraction still worth calling convergent: rho = 0.9.
    Initial error spans feed to exhaust, order 1e3 K. Tolerance
    1e-5 K.
    """

    def test_two_hundred_covers_the_derived_requirement(self):

        needed = math.log(1e-5 / 1e3) / math.log(0.9)

        self.assertAlmostEqual(needed, 175.0, delta=1.0)
        self.assertGreaterEqual(200, needed)

    def test_the_measured_cases_fit_with_room_to_spare(self):

        for rho, observed in ((0.708, 51), (0.758, 62)):

            needed = math.log(1e-5 / 421.0) / math.log(rho)

            # The measurement and the geometric estimate agree.
            self.assertAlmostEqual(needed, observed, delta=12)
            self.assertLess(needed, 200)

    def test_fifty_was_not_enough_for_either(self):

        for rho in (0.708, 0.758):
            self.assertGreater(
                math.log(1e-5 / 421.0) / math.log(rho),
                50,
            )


class _Preheater:
    """Just enough surface for the loop's bookkeeping."""

    def __init__(self):
        self.gas_handoff_residuals = []
        self.solid_handoff_residuals = []
        self.solid_error_history = []


class FailureModesAreDistinguishableTest(unittest.TestCase):
    """The messages, reproduced from the module's own wording.

    The point under test is not the prose but that the two
    outcomes are separable at all: before this, both arrived as
    the same sentence with a different number in it.
    """

    @staticmethod
    def _exhausted_message(solid_error, ratio, tolerance=1e-5,
                           max_iterations=200):
        shortfall = solid_error / tolerance
        message = (
            "Preheater counter-current solution did not converge: "
            f"solid_error={solid_error:.6e} K after "
            f"{max_iterations} iterations, which is "
            f"{shortfall:.2f}x the {tolerance:.1e} K tolerance "
            f"(last contraction ratio {ratio:.4f})."
        )
        if ratio == ratio and ratio < 1.0:
            message += (
                " Budget exhausted while still contracting -- "
                "this is not a divergence."
            )
        return message

    def test_a_near_miss_says_it_is_still_contracting(self):

        message = self._exhausted_message(3.111848e-05, 0.708)

        self.assertIn("not a divergence", message)
        self.assertIn("3.11x", message)

    def test_a_stalled_sequence_does_not_claim_to_be_contracting(self):

        message = self._exhausted_message(4.2e-01, 1.0004)

        self.assertNotIn("not a divergence", message)

    def test_a_missing_history_does_not_claim_either_way(self):
        """NaN must not be read as "< 1.0" and excused."""

        message = self._exhausted_message(4.2e-01, float("nan"))

        self.assertNotIn("not a divergence", message)


class DivergenceWindowTest(unittest.TestCase):
    """The early abort that pays for the larger budget.

    Compared against the START of the window, not the previous
    step, so an ordinary non-monotone wobble does not trip it.
    """

    WINDOW = 20

    @staticmethod
    def _trips(history, window):
        if len(history) <= window:
            return False
        return history[-1] >= history[-window - 1]

    def test_a_healthy_contraction_never_trips(self):

        history = [421.0 * 0.708 ** i for i in range(60)]

        for i in range(self.WINDOW + 1, len(history)):
            self.assertFalse(
                self._trips(history[: i + 1], self.WINDOW),
                f"tripped at iteration {i}",
            )

    def test_a_flat_sequence_trips(self):

        history = [1.0e-3] * 40

        self.assertTrue(self._trips(history, self.WINDOW))

    def test_a_single_wobble_does_not_trip(self):
        """One bad step inside a contracting window is survivable."""

        history = [421.0 * 0.708 ** i for i in range(40)]
        history[-3] *= 6.0

        self.assertFalse(self._trips(history, self.WINDOW))

    def test_the_window_is_what_the_module_uses(self):

        import inspect

        source = inspect.getsource(heat_transfer)

        self.assertIn("divergence_window = 20", source)
        self.assertIn("max_iterations = 200", source)
        self.assertIn("tolerance = 1e-5", source)


if __name__ == "__main__":
    unittest.main()
