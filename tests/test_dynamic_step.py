"""Twin.advance: the implicit dynamic step.

One steady solve, then two steps with the inputs unchanged (the
step must return the steady state) and three after a 5 % fuel step
(stored energy must appear, and every step must conserve energy
with it booked as an outflow).
"""

import contextlib
import io
import os
import unittest
from unittest import mock

import numpy as np

from tests.twin_harness import REPO_ROOT, main, run_twin


ZONES = ("burning", "transition", "calciner", "preheater", "cooler")

STORED = tuple(
    f"{zone.capitalize()}_stored_energy_change" for zone in ZONES
)


def _temperatures(twin):
    return {
        f"{prefix}_{zone}": np.array(getattr(twin.state, f"{prefix}_{zone}"))
        for zone in ZONES
        for prefix in ("Tg", "Ts", "Tw")
    }


def _global_energy(twin):
    results = []

    def collect(result, equipment, balance_type="energy"):
        results.append(result)
        return result

    with mock.patch.object(main, "report_validation", collect):
        with contextlib.redirect_stdout(io.StringIO()):
            twin._validate_global_energy_balance()

    return results[0]


class DynamicStepTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.twin, _ = run_twin()
        twin = cls.twin

        steady = _temperatures(twin)

        cwd = os.getcwd()
        os.chdir(REPO_ROOT)

        try:
            with contextlib.redirect_stdout(io.StringIO()):

                for _ in range(2):
                    twin.advance(10.0)

                cls.hold_drift = max(
                    float(np.max(np.abs(value - steady[key])))
                    for key, value in _temperatures(twin).items()
                )
                cls.hold_time = twin.state.t

                twin._last_inputs["Fuel_rate_total"] *= 1.05

                cls.steps = []

                for _ in range(3):
                    twin.advance(10.0)
                    cls.steps.append(
                        {
                            "global": _global_energy(twin),
                            "stored": sum(
                                getattr(twin.state, name) for name in STORED
                            ),
                            "zones": [
                                main.validate_energy(
                                    energy_in=getattr(twin, zone).energy_in,
                                    energy_out=getattr(twin, zone).energy_out,
                                    relative_tolerance=1e-6,
                                )
                                for zone in (
                                    "burning",
                                    "transition",
                                    "calciner",
                                    "cooler",
                                )
                            ],
                        }
                    )

        finally:
            os.chdir(cwd)

    def test_unchanged_inputs_hold_the_steady_state(self):
        # The steady solve stops at 1e-3 K, so a step from it may
        # finish converging, but not drift.
        self.assertLess(self.hold_drift, 1e-5)
        self.assertEqual(self.hold_time, 20.0)

    def test_fuel_step_stores_energy(self):
        # More fuel heats the linings and the kiln bed: storage is
        # an outflow of ~2 MW on a ~13 MW step.
        for step in self.steps:
            self.assertGreater(step["stored"], 1e5)

    def test_every_step_conserves_energy(self):
        for step in self.steps:
            self.assertLess(step["global"]["relative_residual"], 1e-6)

            for zone in step["zones"]:
                self.assertTrue(zone["converged"], zone)

    def test_steady_mode_restored_after_a_step(self):
        self.assertIsNone(self.twin.state.transient_dt)

    def test_rejects_non_positive_dt(self):
        for dt in (0.0, -10.0, float("nan")):
            with self.assertRaises(ValueError):
                self.twin.advance(dt)


if __name__ == "__main__":
    unittest.main()
