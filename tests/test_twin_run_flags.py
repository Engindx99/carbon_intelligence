"""Twin.run()'s opt-in flags for callers that drive it in a loop.

A setpoint solver evaluates one operating point per run() call.
Two things about the old signature made that impossible to do
cleanly: run() wrote a row per balance to reporter/logs on every
call, and it RAISED when the sweep budget ran out, so an outer
loop lost the bracket it had already paid for.

These tests pin both flags AND, more importantly, pin that the
defaults changed nothing. The bit-exact twin_state_reference
fixture covers the converged numbers; this covers the control
flow around them.
"""

import contextlib
import io
import os
import unittest
from unittest import mock

import main
from pyroprocess.globalstate import GlobalState
from tests.twin_harness import REPO_ROOT


def _build(max_iterations=None, nodes_per_stage=1):
    """A Twin on the repo config.

    `max_iterations=None` keeps the config's own budget. The two
    solving tests below used to hardcode 100, which was a second
    copy of a number that lives in configs/twin_cfg.yaml -- and it
    broke the moment the plant needed 101 sweeps, reporting a
    RuntimeError that said nothing about the flags under test.
    A budget belongs in one place.
    """

    cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
    cfg["preheater"]["nodes_per_stage"] = nodes_per_stage

    if max_iterations is not None:
        cfg.setdefault("simulation", {})["max_iterations"] = (
            max_iterations
        )

    return main.Twin(
        state=GlobalState(N=cfg["plant"]["N"]),
        cfg=cfg,
    )


class RunFlagsTest(unittest.TestCase):

    def setUp(self):
        # Zone models read configs/twin_cfg.yaml relative to cwd.
        self._cwd = os.getcwd()
        os.chdir(REPO_ROOT)
        self.addCleanup(os.chdir, self._cwd)

    # ------------------------------------------------------
    # One sweep cannot converge, so this exercises the
    # budget-exhausted path without paying for a full solve.
    # ------------------------------------------------------
    def test_default_still_raises_when_the_budget_runs_out(self):

        twin = _build(max_iterations=1)

        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError) as caught:
                twin.run()

        self.assertIn("did not converge", str(caught.exception))
        self.assertFalse(twin.converged)

    def test_flag_returns_the_state_instead_of_raising(self):

        twin = _build(max_iterations=1)

        with contextlib.redirect_stdout(io.StringIO()):
            state = twin.run(raise_on_nonconvergence=False)

        self.assertIs(state, twin.state)
        self.assertFalse(twin.converged)

    def test_converged_is_false_before_any_run(self):

        self.assertFalse(_build(max_iterations=1).converged)

    # ------------------------------------------------------
    # The expensive pair: one real solve each. They are the
    # only way to reach the post-convergence block, which is
    # the thing report= exists to skip.
    # ------------------------------------------------------
    def test_report_false_writes_no_validation_rows(self):

        twin = _build()

        calls = []

        def collect(result, equipment, balance_type="energy"):
            calls.append(equipment)
            return result

        with mock.patch.object(main, "report_validation", collect):
            with contextlib.redirect_stdout(io.StringIO()):
                state = twin.run(report=False)

        self.assertIs(state, twin.state)
        self.assertTrue(twin.converged)
        self.assertEqual(calls, [])

    def test_default_reports_and_validates(self):

        twin = _build()

        calls = []

        def collect(result, equipment, balance_type="energy"):
            calls.append(equipment)
            return result

        buffer = io.StringIO()

        with mock.patch.object(main, "report_validation", collect):
            with contextlib.redirect_stdout(buffer):
                twin.run()

        self.assertTrue(twin.converged)

        # The 13 balances the plant validates on convergence (one
        # per preheater stage: C1-C4, C5 being the calciner's).
        self.assertEqual(len(calls), 13)

        # And the printed report is the other half of report=True.
        self.assertIn("D14", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
