"""D2's secondary-air band, and the quantity it was aimed at.

`BOUNDS["secondary_air"] = (1050, 1350) K` is a band on the air
the cooler recuperates and hands the kiln burner. D2 was checking
it against `state.Tg_burning_in`, which is the BURNER MIXTURE:
secondary air, plus primary air at ambient, plus the fuel's mass.
That mixture is always colder, so the check could not be satisfied
at the floor of its own band however well the cooler ran.

The arithmetic, at the committed operating point (primary 1.3920
kg/s at 300 K, secondary 12.5284 kg/s, divisor
`m_dot_g_burning` = 14.9204 kg/s):

    true secondary     D2 read      verdict
       586.06 K        540.81 K      fail
      1050.00 K        933.92 K      fail   <- the band's own floor
      1150.00 K       1018.90 K      fail
      1350.00 K       1189.05 K      pass

These tests pin that dilution, and pin that the band now reads a
stream inverted on the mass that stream carries.
"""

import unittest

from physics.physics import T_gas_from_h, h_gas
from pyroprocess.cooler import gas_phase
from reporter.diagnostics import BOUNDS


T_REF = 298.15

M_PRIMARY = 1.3920
M_SECONDARY = 12.5284
M_G_BURNING = 14.9204


class _StubCooler:
    T_ref = T_REF
    eps = 1.0e-12


class _StubState:
    def __init__(self, secondary, tertiary, vent):
        self.m_dot_secondary_air = secondary
        self.m_dot_tertiary_air = tertiary
        self.m_dot_vent_air = vent


class TheBandWasUnsatisfiableTest(unittest.TestCase):
    """Why this commit exists, as arithmetic rather than opinion."""

    @staticmethod
    def _burner_mixture(T_secondary):
        """What Tg_burning_in reads for a given secondary air."""

        H = (
            M_SECONDARY * float(h_gas(T_secondary, T_REF))
            + M_PRIMARY * float(h_gas(300.0, T_REF))
        )

        return T_gas_from_h(H / M_G_BURNING, T_REF, T_REF, 4000.0)

    def test_the_floor_of_the_band_reported_as_a_failure(self):

        lo, hi, _ = BOUNDS["secondary_air"]

        reported = self._burner_mixture(lo)

        self.assertAlmostEqual(reported, 933.92, delta=0.05)
        self.assertLess(reported, lo)

    def test_a_good_cooler_would_still_have_failed(self):

        lo, _, _ = BOUNDS["secondary_air"]

        self.assertAlmostEqual(
            self._burner_mixture(1150.0), 1018.90, delta=0.05
        )
        self.assertLess(self._burner_mixture(1150.0), lo)

    def test_the_dilution_grows_with_temperature(self):
        """It is not a constant offset, so no fixed allowance
        could have been subtracted to repair the old check."""

        gaps = [
            T - self._burner_mixture(T)
            for T in (586.06, 1050.0, 1150.0, 1350.0)
        ]

        self.assertAlmostEqual(gaps[0], 45.25, delta=0.05)
        self.assertAlmostEqual(gaps[-1], 160.95, delta=0.05)
        self.assertEqual(gaps, sorted(gaps))


class StreamTemperaturesTest(unittest.TestCase):

    def test_each_stream_is_inverted_on_its_own_mass(self):

        state = _StubState(12.5284, 20.8807, 8.7958)

        H_sec = state.m_dot_secondary_air * float(h_gas(1200.0, T_REF))
        H_ter = state.m_dot_tertiary_air * float(h_gas(800.0, T_REF))
        H_vent = state.m_dot_vent_air * float(h_gas(400.0, T_REF))

        T_sec, T_ter, T_vent = gas_phase.stream_temperatures(
            _StubCooler(), H_sec, H_ter, H_vent, state
        )

        self.assertAlmostEqual(T_sec, 1200.0, places=6)
        self.assertAlmostEqual(T_ter, 800.0, places=6)
        self.assertAlmostEqual(T_vent, 400.0, places=6)

    def test_a_zero_mass_stream_is_not_a_division(self):
        """Vent air goes to zero exactly at the cooler air split's
        feasibility limit (main.py:1099), so this is reachable."""

        state = _StubState(12.5284, 20.8807, 0.0)

        _, _, T_vent = gas_phase.stream_temperatures(
            _StubCooler(), 1.0, 1.0, 0.0, state
        )

        self.assertEqual(T_vent, T_REF)

    def test_the_lumped_model_gives_all_three_the_same_value(self):
        """Today's split shares one hot-end enthalpy, so the three
        temperatures must come back equal. When the cooler becomes
        cross-flow this stops being true, and that is the point --
        this test is the BEFORE half of that change.
        """

        state = _StubState(12.5284, 20.8807, 8.7958)
        h_hot = float(h_gas(586.06, T_REF))

        temps = gas_phase.stream_temperatures(
            _StubCooler(),
            state.m_dot_secondary_air * h_hot,
            state.m_dot_tertiary_air * h_hot,
            state.m_dot_vent_air * h_hot,
            state,
        )

        self.assertAlmostEqual(temps[0], temps[1], places=9)
        self.assertAlmostEqual(temps[1], temps[2], places=9)


if __name__ == "__main__":
    unittest.main()
