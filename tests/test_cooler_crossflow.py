"""The cooler's air is cross-flow, not one counter-current duct.

A grate cooler is not a duct. Each segment has its own undergrate
fan box and blows its own fresh ambient air UP through the clinker
bed; that air leaves through the hood at that segment's temperature
and is taken off as secondary, tertiary or vent depending on where
along the grate it sits.

Source: Svensen, Leal da Silva, Pigazo Merino, Sampath & Jorgensen,
"A Dynamic Cooler Model for Cement Clinker Production",
arXiv:2409.09076 (2024) -- 10 segments, each with its own air
inflow, secondary being segment 1's air and tertiary segment 2's.

WHAT THE LUMPED MODEL COST. One stream meant one outlet
temperature for all 2.2 kg air/kg clinker, so C_air/C_solid = 2.91
and the air rise was capped at 266 K. Secondary air measured
586.06 K against BOUNDS["secondary_air"] = (1050, 1350). The cooler
was at ~100% counter-current effectiveness -- it was not broken.
Air cannot get hot when its heat-capacity rate is 2.9x the
clinker's.

MEASURED after this change, at nodes_per_stage=1:

    secondary air     586.06 -> 717.81 K
    tertiary  air     586.06 -> 515.35 K   (colder -- see below)
    vent      air     586.06 -> 415.10 K
    clinker discharge 338.16 -> 462.06 K   (into its band)
    kiln discharge   1175.06 -> 1213.81 K  (the loop, working)

Tertiary gets COLDER and that is expected, not a regression: ours
is the larger stream (20.88 vs 12.53 kg/s, because
fuel.kiln_fraction = 0.40 sends 60% of the fuel to the calciner) so
drawn hot-end-first after secondary it takes the cooler half of the
grate. The source's plant has the opposite ratio.
"""

import unittest

import numpy as np

from physics.physics import h_gas
from pyroprocess.cooler import gas_phase


T_REF = 298.15
T_AMB = 300.0


class _StubCooler:
    T_ref = T_REF
    eps = 1.0e-12

    def __init__(self, N=20):
        self.N = N


class _StubState:
    def __init__(self, total, secondary, tertiary):
        self.m_dot_air_cooler = total
        self.m_dot_secondary_air = secondary
        self.m_dot_tertiary_air = tertiary
        self.m_dot_vent_air = total - secondary - tertiary


# The committed operating point.
TOTAL = 42.20480705060488
SECONDARY = 12.528395784350385
TERTIARY = 20.880659640583975


def _profile(N, hot=811.5, cold=400.1):
    """A monotone-decreasing hood profile, hot end at cell 0."""
    return np.linspace(hot, cold, N)


class GasBlockIsDiagonalTest(unittest.TestCase):
    """The topology change itself.

    With no axial gas transport there is no upstream cell, so the
    gas-to-gas block carries no off-diagonal term. A reintroduced
    advection term would show up here and nowhere else -- the
    energy balance would still close, because it closes on
    whatever the rows say.
    """

    @staticmethod
    def _assemble(N=6):
        cooler = _StubCooler(N)
        state = _StubState(TOTAL, SECONDARY, TERTIARY)

        A = np.zeros((3 * N, 3 * N))
        b = np.zeros(3 * N)

        Tg = _profile(N)
        Ts = _profile(N, 1174.9, 469.5)
        Tw = _profile(N, 700.0, 380.0)

        gas_phase.apply_gas_energy_balance(
            A, b, 0, N, T_AMB, Tg, Ts, Tw, T_REF,
            gas_phase.cooler_air_cells(cooler, state),
            13.854, 180.0, 70.0,
            np.full(N, 1.0e4), np.full(N, 1.0e3),
        )
        return A, N

    def test_no_gas_to_gas_off_diagonal_survives(self):

        A, N = self._assemble()

        gas_block = A[:N, :N]

        self.assertTrue(
            np.array_equal(gas_block, np.diag(np.diag(gas_block))),
            "an off-diagonal gas coupling means axial advection "
            "came back",
        )

    def test_the_diagonal_is_positive_and_the_couplings_are_not(self):
        """Still an M-matrix, and now anchored cell by cell to the
        fan box instead of through a chain of N."""

        A, N = self._assemble()

        for i in range(N):
            self.assertGreater(A[i, i], 0.0)
            self.assertLess(A[i, N + i], 0.0)
            self.assertLess(A[i, 2 * N + i], 0.0)


class SplitIdentityTest(unittest.TestCase):
    """H_sec + H_ter + H_vent == Hgas_cooler_out, to the last bit.

    Four places depend on this, none of them the cooler's own
    energy validator: main.py:315-323 recovers primary air by
    SUBTRACTING secondary from Hgas_burning_in; main.py:347 and
    reporter/diagnostics.py:1117 put vent on the OUT side; and
    diagnostics.py:1136-1140 repeats the subtraction in D12. It is
    exact because vent is computed as the residual m - w_sec -
    w_ter rather than independently, so the three weights sum to
    the cell's mass in floating point for every cell.

    assertEqual, not assertAlmostEqual. That is the claim.
    """

    def _check(self, N, total, secondary, tertiary, Tg=None):
        cooler = _StubCooler(N)
        state = _StubState(total, secondary, tertiary)
        Tg = _profile(N) if Tg is None else Tg

        parts = gas_phase.gas_enthalpy_split(cooler, Tg, state)
        whole = gas_phase.gas_enthalpy_out(cooler, Tg, state)

        self.assertEqual(sum(parts), whole)

    def test_at_the_committed_operating_point(self):
        self._check(20, TOTAL, SECONDARY, TERTIARY)

    def test_on_a_random_profile(self):
        rng = np.random.default_rng(20260920)
        for _ in range(25):
            Tg = np.sort(rng.uniform(320.0, 1200.0, 20))[::-1]
            self._check(20, TOTAL, SECONDARY, TERTIARY, Tg=Tg)

    def test_with_a_boundary_exactly_on_a_cell_edge(self):
        # Secondary is exactly 5 of 20 cells.
        self._check(20, 40.0, 10.0, 20.0)

    def test_with_no_vent_air(self):
        """Reachable: vent is the slack and main.py:1099 raises
        only once it goes NEGATIVE, so zero is a valid state."""
        self._check(20, 40.0, 15.0, 25.0)

    def test_with_no_tertiary_air(self):
        self._check(20, 40.0, 15.0, 0.0)


class StreamMassesTest(unittest.TestCase):

    def test_the_masses_match_the_scalar_chain(self):
        """This is main.py's Cooler/air_split validator restated on
        the enthalpy side: what the cooler allocates along the
        grate must be what the mass model handed it."""

        cooler = _StubCooler(20)
        state = _StubState(TOTAL, SECONDARY, TERTIARY)

        w_sec, w_ter, w_vent = gas_phase.stream_masses(cooler, state)

        self.assertAlmostEqual(w_sec.sum(), SECONDARY, places=9)
        self.assertAlmostEqual(w_ter.sum(), TERTIARY, places=9)
        self.assertAlmostEqual(
            w_vent.sum(), TOTAL - SECONDARY - TERTIARY, places=9
        )

    def test_every_cell_gives_up_exactly_its_own_air(self):

        cooler = _StubCooler(20)
        state = _StubState(TOTAL, SECONDARY, TERTIARY)

        m_air = gas_phase.cooler_air_cells(cooler, state)
        w_sec, w_ter, w_vent = gas_phase.stream_masses(cooler, state)

        for i in range(20):
            self.assertEqual(
                w_sec[i] + w_ter[i] + w_vent[i], m_air[i]
            )

    def test_no_stream_is_ever_negative(self):
        """The boundaries are clipped, so an infeasible split
        cannot produce negative mass here even though
        main.py:1099 would have raised first."""

        cooler = _StubCooler(20)
        state = _StubState(40.0, 30.0, 30.0)

        for w in gas_phase.stream_masses(cooler, state):
            self.assertTrue(np.all(w >= 0.0))


class HotEndFirstTest(unittest.TestCase):

    def test_secondary_is_hotter_than_tertiary_than_vent(self):
        """The plumbing order: the kiln hood sits over the
        clinker-inlet end and takes the hottest grate, the tertiary
        duct taps immediately downstream, the rest vents. A
        reversed allocation would still conserve energy, which is
        why it needs its own test."""

        cooler = _StubCooler(20)
        state = _StubState(TOTAL, SECONDARY, TERTIARY)
        Tg = _profile(20)

        H = gas_phase.gas_enthalpy_split(cooler, Tg, state)
        T = gas_phase.stream_temperatures(cooler, *H, state)

        self.assertGreater(T[0], T[1])
        self.assertGreater(T[1], T[2])

    def test_the_streams_no_longer_share_one_temperature(self):
        """The lumped model gave all three the same value. That
        equality is what capped secondary air at 586 K."""

        cooler = _StubCooler(20)
        state = _StubState(TOTAL, SECONDARY, TERTIARY)

        H = gas_phase.gas_enthalpy_split(cooler, _profile(20), state)
        T = gas_phase.stream_temperatures(cooler, *H, state)

        self.assertGreater(T[0] - T[2], 100.0)


class NotADiscretisationArtifactTest(unittest.TestCase):
    """Why the boundaries are fractional.

    Secondary air is 5.94 cells wide at the committed point.
    Rounding to whole cells would make the reported temperature
    jump by a whole cell's worth whenever the fuel rate moved --
    an artifact of the mesh, not of the plant.
    """

    def test_the_split_converges_under_refinement(self):

        results = []

        for N in (10, 20, 40, 80):
            cooler = _StubCooler(N)
            state = _StubState(TOTAL, SECONDARY, TERTIARY)

            H = gas_phase.gas_enthalpy_split(
                cooler, _profile(N), state
            )
            T = gas_phase.stream_temperatures(cooler, *H, state)
            results.append(T[0])

        # Successive refinements must close on each other, not
        # jump around by a cell's worth of temperature.
        gaps = [
            abs(b - a) for a, b in zip(results, results[1:])
        ]

        self.assertEqual(gaps, sorted(gaps, reverse=True))
        self.assertLess(gaps[-1], 2.0)

    def test_a_whole_cell_rounding_would_have_been_visible(self):
        """How big the artifact this avoids actually is: one cell
        of the committed profile spans ~22 K at N=20."""

        Tg = _profile(20)

        self.assertGreater(abs(Tg[0] - Tg[1]), 15.0)


if __name__ == "__main__":
    unittest.main()
