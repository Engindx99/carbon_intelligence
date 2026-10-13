"""The calciner gas inlet divisor, and the sweep of lag that used
to sit in it.

`Hgas_calciner_in` is assembled from two streams -- the transition
gas and the cooler's tertiary air -- so inverting it to a
temperature requires the flow those two carry. That flow used to
be read back from `state.m_dot_g_calciner_in`, which thermal_step
publishes as (zone outlet - everything the bed releases). The
identity holds at the fixed point, and
test_diagnostics.test_calciner_stream_flows asserts it there. On
the PATH to the fixed point it does not: the outlet flow it was
built from is recomputed by _update_steady_state_mass_flow before
the value is ever read.

These tests pin the live assembly, and pin the measured case that
exposed the lag.
"""

import unittest

from physics.physics import T_gas_from_h, h_gas
from physics.gas_thermo import GasMixture
from pyroprocess.precalciner.raw_meal_inlet import (
    calciner_inlet_species,
    gas_temperature_from_enthalpy,
)


T_REF = 298.15


class _StubCalciner:
    T_ref = T_REF
    eps = 1.0e-12


class _StubState:
    """Only what the inversion reads."""

    def __init__(
        self,
        m_dot_g_transition,
        m_dot_tertiary_air,
        m_dot_fuel_calciner,
        m_dot_g_calciner,
        stale_inlet=None,
    ):
        self.m_dot_g_transition = m_dot_g_transition
        self.m_dot_tertiary_air = m_dot_tertiary_air
        self.m_dot_fuel_calciner = m_dot_fuel_calciner
        self.m_dot_g_calciner = m_dot_g_calciner
        # Kiln gas as the transition discharges it (mass fractions
        # of a converged run), for the inlet mixture's composition.
        self.Transition_gas_species_out = {
            s: w * m_dot_g_transition
            for s, w in (
                ("N2", 0.68), ("O2", 0.03), ("Ar", 0.012),
                ("CO2", 0.25), ("H2O", 0.028),
            )
        }
        if stale_inlet is not None:
            self.m_dot_g_calciner_in = stale_inlet


def _h_in(state, T):
    """Specific enthalpy of the calciner's inlet mixture, the one
    gas_temperature_from_enthalpy inverts with."""
    return GasMixture(calciner_inlet_species(state)).h(T, T_REF)


class InletFlowIsAssembledLiveTest(unittest.TestCase):

    def test_divides_by_the_streams_the_enthalpy_carries(self):

        state = _StubState(
            m_dot_g_transition=14.9204,
            m_dot_tertiary_air=20.8807,
            m_dot_fuel_calciner=1.5,
            m_dot_g_calciner=46.7736,
        )

        expected_flow = 14.9204 + 20.8807 + 1.5
        H = expected_flow * _h_in(state, 1200.0)

        T = gas_temperature_from_enthalpy(_StubCalciner(), H, state)

        self.assertAlmostEqual(T, 1200.0, places=6)

    def test_a_stale_published_inlet_flow_is_ignored(self):
        """The regression itself.

        A value left over from a sweep whose flows were a fifth of
        today's must not be picked up. Before the fix this same
        call returned the stale-divisor answer.
        """

        live = _StubState(
            m_dot_g_transition=14.9204,
            m_dot_tertiary_air=20.8807,
            m_dot_fuel_calciner=1.5,
            m_dot_g_calciner=46.7736,
        )

        stale = _StubState(
            m_dot_g_transition=14.9204,
            m_dot_tertiary_air=20.8807,
            m_dot_fuel_calciner=1.5,
            m_dot_g_calciner=46.7736,
            # 16.4204 - 9.4725, published a sweep earlier.
            stale_inlet=6.9479,
        )

        H = 4.090602e7

        self.assertAlmostEqual(
            gas_temperature_from_enthalpy(_StubCalciner(), H, stale),
            gas_temperature_from_enthalpy(_StubCalciner(), H, live),
            places=9,
        )

    def test_the_fuel_mass_is_counted_with_the_scalar_chain(self):
        """physics.steady_state_mass puts the calciner fuel in the
        zone outlet, so the subtraction this replaced carried it
        too. Dropping it here would silently re-scale the handoff.
        """

        with_fuel = _StubState(10.0, 20.0, 1.5, 40.0)
        without = _StubState(10.0, 20.0, 0.0, 40.0)

        H = 31.5 * _h_in(with_fuel, 1100.0)

        self.assertAlmostEqual(
            gas_temperature_from_enthalpy(_StubCalciner(), H, with_fuel),
            1100.0,
            places=6,
        )
        self.assertNotAlmostEqual(
            gas_temperature_from_enthalpy(_StubCalciner(), H, without),
            1100.0,
            places=3,
        )


class TheMeasuredCaseTest(unittest.TestCase):
    """Literature calcination kinetics, sweep 2, fuel 2.5 kg/s.

    Every figure below was read off the running plant. The zone
    outlet flow moves 16.42 -> 46.77 kg/s as calcination lights
    off, while the divisor published in sweep 1 stays at 6.95.
    """

    H_TRANSITION = 3.324943e7
    H_TERTIARY = 7.656583e6
    M_TRANSITION = 14.9204
    M_TERTIARY = 20.8807
    M_FUEL = 1.5
    M_ZONE_OUT = 46.7736
    STALE_DIVISOR = 6.9479

    def test_the_stale_divisor_put_the_gas_outside_the_window(self):

        H = self.H_TRANSITION + self.H_TERTIARY

        h_stale = H / self.STALE_DIVISOR

        self.assertAlmostEqual(h_stale, 5.887536e6, delta=1.0e2)
        self.assertGreater(h_stale, h_gas(4000.0, T_REF))

        with self.assertRaises(ValueError):
            T_gas_from_h(h_stale, T_REF, 200.0, 4000.0)

    def test_the_live_divisor_gives_a_real_calciner_inlet(self):

        state = _StubState(
            self.M_TRANSITION,
            self.M_TERTIARY,
            self.M_FUEL,
            self.M_ZONE_OUT,
            stale_inlet=self.STALE_DIVISOR,
        )

        T = gas_temperature_from_enthalpy(
            _StubCalciner(),
            self.H_TRANSITION + self.H_TERTIARY,
            state,
        )

        # Riser gas mixed with tertiary air. A real ILC calciner
        # inlet sits in this region; 4000 K does not.
        self.assertGreater(T, 1100.0)
        self.assertLess(T, 1450.0)

    def test_the_two_mass_accountings_did_not_drift(self):
        """Worth pinning: the lag was NOT a conservation error.

        Per-cell release and the scalar chain both booked 9.4725
        kg/s. Only the sweep they were paired with differed.
        """

        scalar_release = self.M_ZONE_OUT - (
            self.M_TRANSITION + self.M_TERTIARY + self.M_FUEL
        )

        sweep_one_outlet = 16.4204

        self.assertAlmostEqual(scalar_release, 9.4725, places=3)
        self.assertAlmostEqual(
            sweep_one_outlet - 9.4725,
            self.STALE_DIVISOR,
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
