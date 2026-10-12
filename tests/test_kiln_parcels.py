"""chemistry.parcels: the kiln's solid hold-up as a parcel train.

Checked against the steady flow march it must reduce to, for both
kiln zones, and for what makes it dynamic: mass conserved step by
step with a changing hold-up, and a feed change reaching the
outlet after the transit time, not before.

Synthetic but plant-like inputs (5000 t/d kiln at dt = 10 s), so no
twin solve is needed.
"""

import math
import unittest

import numpy as np

from chemistry import parcels as P
from chemistry.calcination import CalcinationModel
from chemistry.phases import raw_meal_solid_flow
from chemistry.reactions import ChemistryModel


DT = 10.0
U_S = 0.043  # m/s

DZ_TRANSITION = 1.54  # m, tau_cell ~36 s
DZ_BURNING = 2.16  # m, tau_cell ~50 s

T_TRANSITION = np.linspace(1380.0, 1590.0, 20)
T_BURNING = np.concatenate(
    [np.linspace(1600.0, 1640.0, 14), np.linspace(1630.0, 1505.0, 6)]
)


def _calcined_meal(m_dot, fraction):
    """Raw meal flow [kg/s] with `fraction` of its CaCO3 calcined."""

    calcination = CalcinationModel()
    flow = raw_meal_solid_flow(m_dot)
    reacted = fraction * flow["CaCO3"]
    flow["CaCO3"] -= reacted
    flow["CaO"] += reacted * calcination.CaO_ratio
    return flow


def _as_parcel(flow, dt=DT):
    return [({k: v * dt for k, v in flow.items()}, dt)]


def _total(species_list):
    return sum(sum(sp.values()) for sp in species_list)


def _holdup(train):
    return _total(p.species for p in train)


def _rel(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.max(np.abs(a - b)) / max(np.max(np.abs(b)), 1e-30))


class TransitionTrainTest(unittest.TestCase):

    def setUp(self):
        self.calcination = CalcinationModel()
        self.feed = _calcined_meal(85.0, 0.25)
        self.v = U_S / DZ_TRANSITION

        def reactor(T):
            return P.CalcinationReactor(self.calcination, T)

        self.reactor = reactor

    def _march(self):
        """The transition's steady march: CaCO3_out = in exp(-k tau)."""

        tau = DZ_TRANSITION / U_S
        CaCO3 = self.feed["CaCO3"]
        Q = []
        CO2 = []

        for T in T_TRANSITION:
            k = float(self.calcination.reaction_rate(T))
            out = CaCO3 * math.exp(-k * tau)
            Q.append((CaCO3 - out) * self.calcination.deltaH)
            CO2.append((CaCO3 - out) * self.calcination.CO2_ratio)
            CaCO3 = out

        return np.array(Q), np.array(CO2), CaCO3

    def test_steady_state_is_the_march(self):
        entering = _as_parcel(self.feed)
        train = P.steady_train(
            entering, T_TRANSITION, self.v, DT, self.reactor
        )
        step = P.advance_train(
            train, entering, T_TRANSITION, self.v, DT, self.reactor
        )

        Q, CO2, CaCO3_out = self._march()

        # Calcination composes exactly: exp(-k h1) exp(-k h2) =
        # exp(-k tau). Round-off only.
        self.assertLess(_rel(step.Q_cells, Q), 1e-12)
        self.assertLess(_rel(step.dm_CO2_cells, CO2), 1e-12)

        leaving_CaCO3 = sum(sp["CaCO3"] for sp, _ in step.leaving) / DT
        self.assertAlmostEqual(leaving_CaCO3, CaCO3_out, delta=1e-12 * CaCO3_out)

    def test_mass_is_conserved_each_step(self):
        entering = _as_parcel(self.feed)
        train = P.steady_train(
            entering, T_TRANSITION, self.v, DT, self.reactor
        )

        # A feed change: the hold-up is no longer steady.
        new_feed = _as_parcel(_calcined_meal(100.0, 0.10))

        for _ in range(40):
            step = P.advance_train(
                train, new_feed, T_TRANSITION, self.v, DT, self.reactor
            )

            inflow = _total(sp for sp, _ in new_feed)
            outflow = _total(sp for sp, _ in step.leaving)
            released = float(np.sum(step.dm_CO2_cells)) * DT
            stored = _holdup(step.parcels) - _holdup(train)

            self.assertAlmostEqual(
                inflow - outflow - released - stored,
                0.0,
                delta=1e-12 * inflow,
            )

            train = step.parcels

    def test_feed_change_arrives_after_the_transit_time(self):
        entering = _as_parcel(self.feed)
        train = P.steady_train(
            entering, T_TRANSITION, self.v, DT, self.reactor
        )

        steady_out = _total(
            sp
            for sp, _ in P.advance_train(
                train, entering, T_TRANSITION, self.v, DT, self.reactor
            ).leaving
        )

        transit_steps = len(T_TRANSITION) / self.v / DT  # ~71.6

        bigger = _as_parcel(_calcined_meal(100.0, 0.25))

        outflows = []

        for _ in range(int(transit_steps) + 3):
            step = P.advance_train(
                train, bigger, T_TRANSITION, self.v, DT, self.reactor
            )
            outflows.append(_total(sp for sp, _ in step.leaving))
            train = step.parcels

        # Unchanged until the first new parcel reaches the outlet...
        for k in range(int(transit_steps) - 1):
            self.assertAlmostEqual(
                outflows[k], steady_out, delta=1e-12 * steady_out
            )

        # ...and the bigger stream after it.
        self.assertGreater(outflows[-1], 1.1 * steady_out)

    def test_start_of_step_train_is_not_modified(self):
        entering = _as_parcel(self.feed)
        train = P.steady_train(
            entering, T_TRANSITION, self.v, DT, self.reactor
        )
        before = [(p.x, dict(p.species)) for p in train]

        P.advance_train(
            train, entering, T_TRANSITION + 20.0, self.v, DT, self.reactor
        )

        self.assertEqual(before, [(p.x, p.species) for p in train])


class BurningTrainTest(unittest.TestCase):

    def setUp(self):
        self.chemistry = ChemistryModel()
        self.feed = _calcined_meal(85.0, 0.35)
        self.v = U_S / DZ_BURNING

        def reactor(T):
            return P.BurningReactor(self.chemistry, T)

        self.reactor = reactor

    def _march(self):
        """apply_burning's per-cell step, on a plain flow dict."""

        tau = DZ_BURNING / U_S
        flow = dict(self.feed)
        heat = {
            self.chemistry.belite: 0.0,
            self.chemistry.alite: 0.0,
            self.chemistry.c3a: 0.0,
            self.chemistry.c4af: 0.0,
        }
        Q = []
        Q_calc = []

        for T in T_BURNING:
            rate, rate_calcination = self.chemistry.burning_rates(T)
            q, q_calc, _ = self.chemistry.react_burning(
                flow, T, tau, rate, rate_calcination, heat
            )
            Q.append(q)
            Q_calc.append(q_calc)

        return np.array(Q), np.array(Q_calc), flow

    def test_steady_state_is_the_march(self):
        entering = _as_parcel(self.feed)
        train = P.steady_train(entering, T_BURNING, self.v, DT, self.reactor)
        step = P.advance_train(
            train, entering, T_BURNING, self.v, DT, self.reactor
        )

        Q, Q_calc, clinker = self._march()

        # Calcination exactly; the clinkering reactions to the
        # difference of two Strang splits of the same ODE (each
        # within ~5e-4 of its converged solution).
        self.assertLess(_rel(step.Q_calcination_cells, Q_calc), 1e-12)
        self.assertLess(_rel(step.Q_cells, Q), 1e-4)

        for name, value in clinker.items():
            if value > 1e-6:
                leaving = sum(sp[name] for sp, _ in step.leaving) / DT
                self.assertLess(abs(leaving - value) / value, 2e-3, name)


if __name__ == "__main__":
    unittest.main()
