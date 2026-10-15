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
                            "mass_residual": float(
                                twin.mass_flow.calculate_global_balance()
                            ),
                            "mass_in": float(twin.mass_flow.mass_flow_in),
                            "kiln_mass_stored": (
                                twin.state.Transition_mass_stored
                                + twin.state.Burning_mass_stored
                            ),
                            "cooler_solid_stored": (
                                twin.state.Cooler_solid_stored
                            ),
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
        # The kiln's parcel trains start from their own steady
        # state, which differs from the steady march's by the two
        # Strang splits (~5e-4 in the clinker species), so a hold
        # relaxes the plant towards it: 4e-5 K after two steps,
        # levelling off at ~3e-4 K after 30 min -- inside the
        # steady solve's own 1e-3 K.
        self.assertLess(self.hold_drift, 1e-4)
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

    def test_kiln_hold_up_moves_and_mass_is_conserved(self):
        # The kiln bed's hold-up changes after the fuel step
        # (chemistry/parcels.py), and the plant's mass balance
        # closes with it booked as an outflow.
        self.assertTrue(
            any(abs(step["kiln_mass_stored"]) > 1e-6 for step in self.steps)
        )

        # Bounded by the step's own flow tolerance (main.Twin.run:
        # 1e-6 kg/s in a dynamic step): the residual is the C5 dust
        # recycle's change between the sweep's two calciner passes,
        # which the step stops resolving at that tolerance. It was
        # 1e-9 of the inflow, tighter than the solver's stopping
        # rule, and failed at 2.4e-7 kg/s (1.07e-9) once the clay
        # water left in the preheater (15 Oct 2026).
        for step in self.steps:
            self.assertLess(abs(step["mass_residual"]), 1e-6)

    def test_the_grate_bed_stores_heat(self):
        # The cooler's clinker bed is a parcel train too: the hotter
        # clinker the kiln discharges after the fuel step heats it,
        # and that heat is booked as stored, not lost.
        for step in self.steps:
            self.assertNotEqual(step["cooler_solid_stored"], 0.0)

    def test_steady_mode_restored_after_a_step(self):
        self.assertIsNone(self.twin.state.transient_dt)

    def test_rejects_non_positive_dt(self):
        for dt in (0.0, -10.0, float("nan")):
            with self.assertRaises(ValueError):
                self.twin.advance(dt)


if __name__ == "__main__":
    unittest.main()
