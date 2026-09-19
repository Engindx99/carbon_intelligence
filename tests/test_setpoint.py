"""The setpoint solver's wiring, without paying for a plant solve.

One real residual evaluation costs 27-900 s, so everything that
can be checked against a stub is checked against a stub. What
is deliberately NOT tested here is whether the solved fuel rate
is physically right -- that is a review judgement against
D2/D11/D12, not an assertion.
"""

import unittest

from physics.physics import gas_mass_balance
from solver import setpoint
from solver.rootfind import INFEASIBLE


class _StubBurning:
    kiln_fuel_fraction = 0.40
    primary_air_fraction = 0.10


class _StubCooler:
    cooling_air_rate = 2.2


class _StubMassFlow:
    def __init__(self, clinker):
        self.m_dot_clinker = clinker


class StubTwin:
    """Carries only what the setpoint module reads."""

    def __init__(self, clinker=19.184, fuel=2.5, o2=3.5):
        self.burning = _StubBurning()
        self.cooler = _StubCooler()
        self.mass_flow = _StubMassFlow(clinker)
        self.eps = 1.0e-12
        self.cfg = {"simulation": {"max_iterations": 100}}
        self._last_inputs = {"Fuel_rate_total": fuel, "O2": o2}
        self.converged = False

    # A plant whose "spec" is a known analytic function of fuel,
    # so the wiring can be exercised end to end in microseconds.
    def run(self, *, report=True, raise_on_nonconvergence=True):
        self.converged = True
        return self


class AirPerKgFuelTest(unittest.TestCase):

    def test_air_is_exactly_linear_in_the_fuel_rate(self):
        """The whole analytic bound rests on this.

        gas_mass_balance solves the excess-air ratio against the
        dry stack O2 target, which is a ratio and carries no
        fuel rate, so doubling fuel must exactly double air.
        """

        per_kg = setpoint.air_per_kg_fuel(3.5)

        for fuel in (0.5, 1.7, 2.5, 4.0):

            air = gas_mass_balance(
                fuel_rate_total=fuel, O2=3.5, eps=1.0e-12
            ) - fuel

            self.assertAlmostEqual(air, fuel * per_kg, places=9)

    def test_is_a_plausible_air_fuel_ratio(self):
        # Petcoke at ~3.5% dry stack O2: order 12-16 kg air/kg fuel.
        self.assertGreater(setpoint.air_per_kg_fuel(3.5), 10.0)
        self.assertLess(setpoint.air_per_kg_fuel(3.5), 20.0)


class FuelUpperBoundTest(unittest.TestCase):

    def test_bound_is_exactly_where_vent_air_reaches_zero(self):
        """At the bound, secondary + tertiary == total cooler air."""

        twin = StubTwin(clinker=19.184)

        cap = setpoint.fuel_upper_bound(twin)

        air = gas_mass_balance(
            fuel_rate_total=cap, O2=3.5, eps=1.0e-12
        ) - cap

        demanded = air * (
            1.0
            - _StubBurning.primary_air_fraction
            * _StubBurning.kiln_fuel_fraction
        )

        supplied = _StubCooler.cooling_air_rate * 19.184

        self.assertAlmostEqual(demanded, supplied, places=6)

    def test_more_clinker_allows_more_fuel(self):

        low = setpoint.fuel_upper_bound(StubTwin(clinker=15.0))
        high = setpoint.fuel_upper_bound(StubTwin(clinker=25.0))

        self.assertGreater(high, low)

    def test_infinite_when_there_is_no_clinker(self):

        self.assertEqual(
            setpoint.fuel_upper_bound(StubTwin(clinker=0.0)),
            float("inf"),
        )


class SpecTest(unittest.TestCase):

    def test_free_lime_default_matches_the_reported_band(self):

        import reporter.diagnostics as diagnostics

        spec = setpoint.free_lime_spec()
        lo, hi = diagnostics.FREE_LIME_BAND

        self.assertEqual(spec.unit, "%")
        self.assertGreaterEqual(spec.target, lo)
        self.assertLessEqual(spec.target, hi)

    def test_targets_are_overridable(self):

        spec = setpoint.free_lime_spec(target=1.0, tolerance=0.01)

        self.assertAlmostEqual(spec.target, 1.0)
        self.assertAlmostEqual(spec.tolerance, 0.01)


class SolveFuelRateTest(unittest.TestCase):
    """End-to-end wiring against an analytic 'plant'."""

    @staticmethod
    def _spec(fn, target, tolerance=1.0e-6):
        return setpoint.Spec(
            name="stub",
            read=lambda twin: fn(twin._last_inputs["Fuel_rate_total"]),
            target=target,
            tolerance=tolerance,
            unit="",
        )

    def test_finds_the_fuel_rate_that_meets_the_spec(self):

        twin = StubTwin()

        # Free lime falling with fuel, the patched-tree sign.
        spec = self._spec(lambda fuel: 10.0 - 3.0 * fuel, target=1.5)

        result = setpoint.solve_fuel_rate(
            twin, spec, bracket=(1.0, 4.0)
        )

        self.assertTrue(result.converged, result.reason)
        self.assertAlmostEqual(result.fuel, 8.5 / 3.0, places=5)
        self.assertAlmostEqual(result.achieved, 1.5, places=5)

    def test_the_handle_is_actually_moved_on_the_twin(self):

        twin = StubTwin()
        spec = self._spec(lambda fuel: 10.0 - 3.0 * fuel, target=1.5)

        result = setpoint.solve_fuel_rate(
            twin, spec, bracket=(1.0, 4.0)
        )

        self.assertAlmostEqual(
            twin._last_inputs["Fuel_rate_total"],
            result.fuel,
            places=9,
        )

    def test_no_root_is_reported_not_invented(self):
        """The HEAD case: the handle has no authority."""

        twin = StubTwin()

        # Never reaches 1.5 anywhere in the bracket.
        spec = self._spec(lambda fuel: 30.0 + fuel, target=1.5)

        result = setpoint.solve_fuel_rate(
            twin, spec, bracket=(1.0, 4.0), max_evaluations=8
        )

        self.assertFalse(result.converged)
        self.assertIn("no sign change", result.reason)
        self.assertLessEqual(result.evaluations, 8)

    def test_a_raising_plant_becomes_an_infeasible_point(self):

        class Raising(StubTwin):
            def run(self, *, report=True, raise_on_nonconvergence=True):
                fuel = self._last_inputs["Fuel_rate_total"]
                if fuel < 1.5:
                    raise ValueError(
                        "Cooler air split infeasible"
                    )
                self.converged = True
                return self

        twin = Raising()
        spec = self._spec(lambda fuel: 10.0 - 3.0 * fuel, target=1.5)

        result = setpoint.solve_fuel_rate(
            twin, spec, bracket=(0.5, 4.0), max_evaluations=20
        )

        self.assertTrue(result.converged, result.reason)
        self.assertAlmostEqual(result.fuel, 8.5 / 3.0, places=5)

    def test_an_unconverged_plant_is_infeasible_not_a_reading(self):
        """A plant that ran out of sweeps has no spec value.

        This is the trap the 1.8 kg/s hand experiment fell into:
        budget exhaustion looks exactly like divergence from
        outside, and reading a spec off an unconverged state
        would feed the root find a number that means nothing.
        """

        class NeverConverges(StubTwin):
            def run(self, *, report=True, raise_on_nonconvergence=True):
                self.converged = False
                return self

        twin = NeverConverges()
        spec = self._spec(lambda fuel: 10.0 - 3.0 * fuel, target=1.5)

        result = setpoint.solve_fuel_rate(
            twin, spec, bracket=(1.0, 4.0), max_evaluations=8
        )

        self.assertFalse(result.converged)

    def test_evaluate_returns_the_sentinel_on_failure(self):

        class Raising(StubTwin):
            def run(self, *, report=True, raise_on_nonconvergence=True):
                raise RuntimeError("boom")

        value = setpoint._evaluate(
            Raising(),
            2.0,
            self._spec(lambda fuel: fuel, target=0.0),
        )

        self.assertIs(value, INFEASIBLE)

    def test_run_is_called_without_reporting(self):
        """Intermediate iterates must not write validation rows."""

        seen = {}

        class Watching(StubTwin):
            def run(self, *, report=True, raise_on_nonconvergence=True):
                seen["report"] = report
                seen["raise"] = raise_on_nonconvergence
                self.converged = True
                return self

        setpoint._evaluate(
            Watching(),
            2.0,
            self._spec(lambda fuel: fuel, target=2.0),
        )

        self.assertFalse(seen["report"])
        self.assertFalse(seen["raise"])


if __name__ == "__main__":
    unittest.main()
