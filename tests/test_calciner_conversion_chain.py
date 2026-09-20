"""Why the calciner calcines 1 % once its transit is correct.

Fixing the calciner from a rotary cylinder to a vertical riser took
its solids transit from 574.38 s to 3.48 s -- into the 2-5 s an ILC
calciner runs -- and calcination collapsed with it. This file
isolates that collapse link by link, because "the residence time
went down so the conversion went down" is a restatement, not a
diagnosis, and three of the four links turn out to be innocent.

    particle temperature history
        -> gas/solid heat transfer
            -> CO2 release
                -> conversion

LINK 1, the particle's temperature history: NOT fragile, OVER-coupled.
`u_s` never appears in the solid energy row at all
(physics/variable_flow_rows.py:303-343) -- it advects on
`m_dot_s * Cp_s`, not on `rho*u_s*A`. The transit reaches this zone
ONLY through the chemistry march. The solid is driven onto the gas
whatever the transit: NTU = V_total*K_gs/(m_dot_s*Cp_s) = 5.02. In
the riser state the solid runs HOTTER than the gas in half the
cells, because the wall feeds it. A 25 um particle's thermal time
constant at the Nu = 2 conduction limit is 1.4 ms against a 3483 ms
transit.

LINK 2, the gas/solid area: genuinely wrong, and still not the cause.
The calciner calls `interfacial_areas` without `d_particle`
(pyroprocess/precalciner/precalciner.py:64-72), so the 4.2 m VESSEL
diameter is substituted for the particle diameter -- the same
dimensional substitution bbc1045 fixed for the cooler and Faz 5
fixed for the kiln. It is 14.78x too small. It changes nothing,
because 5.02 and 70.5 both drive the solid onto the gas. RECORDED
HERE, DELIBERATELY NOT FIXED: fixing it belongs in its own commit
and would move the plant for a reason that has nothing to do with
this collapse.

LINK 3, the chemistry: applied exactly as stated. The march is
analytic, not an Euler step, and re-integrating it by hand over the
model's OWN converged Ts profile reproduces the model's outlet to
MACHINE PRECISION in both states. There is no second gate: the only
factor on the Arrhenius term is a linear temperature window that
saturates at 1.0 above 1300 K, and the calciner is far above that.

LINK 4, the cause: the rate constant. `self.prefactor = 42.5 1/s`
paired with `Ea = 150 kJ/mol` needs 648 HOURS to reach 90 %
conversion at 1123 K. A real ILC precalciner does it in about 3.4
seconds. To meet that at the same activation energy the prefactor
would have to be 6.4e6 -- short by a factor of 1.5e5.

    The model reaches even 1 % only because the calciner SELF-HEATS
    until Arrhenius catches up: Ts_calciner runs 1519 K mean /
    1735 K max in the rotary state and 1797 K / 2103 K in the riser
    state, against a real calciner's 1150-1200 K.

So the 574 s hold-up and that self-heating were a compensating pair
masking a rate five orders of magnitude too slow. Correcting the
transit did not break the calciner; it removed the mask.

TWO THINGS THIS FILE ALSO PINS, because both cost time to find:

  * The per-cell arrays store each cell's OUTLET, so the zone inlet
    is NOT `flow_calciner_solid_CaCO3[0]` -- that value already has
    one cell of reaction in it. The inlet is recovered from the CO2
    released. Reading the array end-to-end understates the rotary
    conversion as 21.10 % when it is 23.98 %.
  * The transit that reproduces the fixture is 574.3811 s, which is
    exactly `residence_time(...)` at rpm = 3.5 -- THE KILN'S SPEED,
    read off `state.rpm`. Turning the kiln faster moved the meal
    through the calciner faster. That is the coupling the riser
    change removes.

Nothing here changes any physics. It is a diagnosis, made
reproducible so it does not have to be re-derived.
"""

import json
import math
import unittest

import numpy as np

import main
from chemistry.calcination import CalcinationModel
from physics.physics import residence_time
from tests.twin_harness import REPO_ROOT


FIXTURE = REPO_ROOT / "tests" / "data" / "twin_state_reference.json"


def _snapshot():
    with open(FIXTURE) as handle:
        return json.load(handle)["snapshot"]


def _calciner():
    cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
    return main.Calciner(
        N=cfg["plant"]["N"],
        L=cfg["calciner"]["length"],
        cfg=cfg,
    )


def _zone_inlet_CaCO3(snapshot, model):
    """The flow ENTERING the zone.

    `flow_calciner_solid_CaCO3[0]` is cell 0's OUTLET and already
    carries one cell of reaction, so it cannot be used. Mass
    conservation on the released CO2 gives the inlet exactly.
    """

    outlet = float(np.asarray(snapshot["flow_calciner_solid_CaCO3"])[-1])
    consumed = (
        float(snapshot["state_m_dot_CO2_generated_calciner"])
        / model.CO2_ratio
    )

    return outlet + consumed


# ======================================================
# Measured on the riser tree, which is NOT committed, so these are
# recorded constants rather than something this file can rebuild.
# ======================================================
RISER = {
    "transit_s": 3.4833,
    "Ts_mean": 1797.1740,
    "Ts_max": 2103.2882,
    "conversion": 0.011602,
}

# What a real in-line calciner runs at, and what it achieves.
REAL_CALCINER_T = (1150.0, 1200.0)
REAL_CALCINER_T90_S = 3.4


class Link1TheTransitDoesNotSetTheSolidTemperatureTest(unittest.TestCase):
    """The particle's temperature history is not where the
    conversion went."""

    def setUp(self):
        self.snapshot = _snapshot()
        self.calciner = _calciner()
        self.m_dot_s = float(
            self.snapshot["mass_flow_m_dot_s_calciner_in"]
        )

    def test_the_solid_is_driven_onto_the_gas(self):
        """NTU over the zone. Well above 1 means the bed reaches the
        gas temperature regardless of how fast it passes."""

        c = self.calciner

        ntu = (
            c.V_total
            * c.hv_gs
            * c.a_gs
            / (self.m_dot_s * c.Cp_s)
        )

        self.assertAlmostEqual(ntu, 5.018, delta=0.002)
        self.assertGreater(ntu, 3.0)

    def test_the_solid_is_hotter_than_the_gas_in_half_the_cells(self):
        """Which settles it: a bed that OVERSHOOTS the gas is not a
        bed starved of heat. The wall is feeding it."""

        Tg = np.asarray(self.snapshot["Tg_calciner"], dtype=float)
        Ts = np.asarray(self.snapshot["Ts_calciner"], dtype=float)

        hotter = int(np.sum(Ts > Tg))

        self.assertEqual(hotter, 10)
        self.assertEqual(Ts.size, 20)

        # And the approach is close everywhere, in both directions.
        self.assertLess(float(np.max(Tg - Ts)), 101.0)
        self.assertGreater(float(np.min(Tg - Ts)), -255.0)

    def test_the_particle_cannot_lag_the_gas(self):
        """A 25 um particle at the Nu = 2 conduction limit. Its
        thermal time constant is milliseconds against a transit of
        seconds, so no plausible meal size introduces a lag."""

        d_p, rho_p, cp_p, k_gas = 25.0e-6, 2700.0, 900.0, 0.09

        h = 2.0 * k_gas / d_p
        tau_thermal = rho_p * cp_p * d_p / (6.0 * h)

        self.assertAlmostEqual(h, 7200.0, places=6)
        self.assertAlmostEqual(tau_thermal, 1.40625e-3, places=9)

        # Three orders of magnitude of margin at the SHORT transit.
        self.assertGreater(RISER["transit_s"] / tau_thermal, 2000.0)


class Link2TheContactAreaIsWrongAndItDoesNotMatterTest(unittest.TestCase):
    """Recorded, not fixed. Fixing it belongs in its own commit and
    would move the plant for reasons unrelated to this collapse."""

    # Measured on the converged calciner stream.
    SOLIDS_VOLUME_FRACTION = 5.72e-5
    PARTICLE_DIAMETER = 25.0e-6

    def setUp(self):
        self.calciner = _calciner()
        self.m_dot_s = float(
            _snapshot()["mass_flow_m_dot_s_calciner_in"]
        )

    def test_a_gs_is_the_vessel_diameter_substitution(self):
        """`interfacial_areas` is called without `d_particle`, so
        the packed-bed specific surface 6(1-eps)/d_p gets the 4.2 m
        BORE where a particle diameter belongs."""

        c = self.calciner

        self.assertAlmostEqual(
            c.a_gs,
            6.0 * (1.0 - c.epsilon_bed) / c.D,
            places=12,
        )
        self.assertAlmostEqual(c.a_gs, 0.9285714286, places=9)

    def test_the_true_suspension_area_is_fifteen_times_larger(self):

        suspension = (
            6.0
            * self.SOLIDS_VOLUME_FRACTION
            / self.PARTICLE_DIAMETER
        )

        self.assertAlmostEqual(suspension, 13.728, places=3)
        self.assertAlmostEqual(
            suspension / self.calciner.a_gs, 14.784, delta=0.002
        )

    def test_both_areas_drive_the_solid_onto_the_gas(self):
        """The reason this defect is not the cause. NTU is already
        past the point where more area changes the outcome."""

        c = self.calciner
        suspension = (
            6.0 * self.SOLIDS_VOLUME_FRACTION / self.PARTICLE_DIAMETER
        )

        def ntu(a_gs):
            return c.V_total * c.hv_gs * a_gs / (self.m_dot_s * c.Cp_s)

        self.assertAlmostEqual(ntu(c.a_gs), 5.018, delta=0.002)
        self.assertAlmostEqual(ntu(suspension), 74.19, delta=0.02)

        self.assertGreater(ntu(c.a_gs), 3.0)
        self.assertGreater(ntu(suspension), 3.0)

    def test_the_wall_areas_still_double_count(self):
        """A second defect on the same line, also recorded and not
        fixed: the covered and exposed wall must SPLIT the
        perimeter, so a_ws + a_gw cannot exceed 4/D. The burning
        zone fixed this; the calciner did not."""

        c = self.calciner

        self.assertGreater(c.a_ws + c.a_gw, 4.0 / c.D)
        self.assertAlmostEqual(c.a_ws + c.a_gw, 1.5095, delta=0.001)
        self.assertAlmostEqual(4.0 / c.D, 0.95238, places=5)


class Link3TheChemistryIsAppliedExactlyAsStatedTest(unittest.TestCase):
    """The march reproduces the model to machine precision, so the
    conversion is not being lost in the chemistry."""

    # The transit that reproduces the committed fixture, to four
    # decimals. The march below uses the EXACT value instead --
    # rounding it here costs eight significant figures, which is
    # exactly the difference between "reproduces it" and
    # "reproduces it to machine precision".
    ROTARY_TRANSIT_S = 574.3811

    def setUp(self):
        self.snapshot = _snapshot()
        self.calciner = _calciner()
        self.model = CalcinationModel()
        self.Ts = np.asarray(
            self.snapshot["Ts_calciner"], dtype=float
        )
        self.inlet = _zone_inlet_CaCO3(self.snapshot, self.model)
        self.cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
        self.transit = self._rotary_transit()

    def _rotary_transit(self):
        """The calciner's own hard-coded rotary parameters, driven
        by the KILN's speed off `state.rpm`. Quoted as literals
        because they are the thing being documented as wrong."""

        return residence_time(
            L=25.0,
            D=4.2,
            slope_deg=3.0,        # the calciner's hard-coded slope
            fill_fraction=0.10,   # and its hard-coded fill
            rpm=self.cfg["motion"]["rpm_default"],
            eps=1.0e-9,
        )

    def _march(self, transit_s, inlet):
        """chemistry/calcination.py:324-437, restated:

            m_{i+1} = m_i * exp(-k(Ts_i) * dz / u_s)
        """

        dz_over_u_s = transit_s / self.calciner.N

        mass = inlet
        for T in self.Ts:
            mass *= math.exp(
                float(self.model.reaction_rate(T)) * -dz_over_u_s
            )

        return mass

    def test_the_cell_array_stores_outlets_not_inlets(self):
        """So the zone inlet is not array[0]. Reading it that way
        understates the conversion -- and did, at 21.10 % against
        the true 23.98 %."""

        stored = np.asarray(
            self.snapshot["flow_calciner_solid_CaCO3"], dtype=float
        )

        self.assertAlmostEqual(self.inlet, 20.279400, places=5)
        self.assertGreater(self.inlet, stored[0])

        naive = 1.0 - stored[-1] / stored[0]
        true = 1.0 - stored[-1] / self.inlet

        self.assertAlmostEqual(naive, 0.211005, places=5)
        self.assertAlmostEqual(true, 0.239774, places=5)

    def test_the_march_reproduces_the_model_to_machine_precision(self):
        """The decisive one. Same formula, same Ts profile, same
        transit -- and the same outlet to the last bit. Nothing is
        being lost or added in the chemistry."""

        outlet = float(
            np.asarray(
                self.snapshot["flow_calciner_solid_CaCO3"], dtype=float
            )[-1]
        )

        rebuilt = self._march(self.transit, self.inlet)

        self.assertAlmostEqual(rebuilt / outlet, 1.0, places=12)

    def test_the_transit_was_the_kilns_rpm(self):
        """574.3811 s is `residence_time` at rpm = 3.5, and 3.5 is
        `motion.rpm_default` -- the KILN's speed, read off
        `state.rpm`. The calciner does not rotate, so this coupling
        should not exist at all; it is what the riser change
        removes."""

        self.assertAlmostEqual(self.cfg["motion"]["rpm_default"], 3.5)

        self.assertAlmostEqual(
            self.transit, self.ROTARY_TRANSIT_S, places=3
        )

        # And it really does track the kiln: a different kiln speed
        # is a different calciner residence.
        self.cfg["motion"]["rpm_default"] = 3.0
        self.assertAlmostEqual(
            self._rotary_transit(), 670.1113, places=3
        )

    def test_the_temperature_window_is_the_only_gate_and_it_is_open(self):
        """The one factor multiplying Arrhenius. It saturates above
        1300 K and the calciner sits far above that, so it is not
        suppressing anything here."""

        model = self.model

        self.assertAlmostEqual(model.T_start, 1073.0)
        self.assertAlmostEqual(model.T_end, 1300.0)

        window = np.clip(
            (self.Ts - model.T_start) / (model.T_end - model.T_start),
            0.0,
            1.0,
        )

        # Fully open in 17 of 20 cells; only the coldest tail, where
        # almost no CaCO3 is left to react anyway, is gated at all.
        self.assertEqual(int(np.sum(window >= 1.0)), 17)
        self.assertGreater(float(self.Ts.mean()), model.T_end)

    def test_the_configured_target_is_not_enforced(self):
        """`operational.calcination_degree_target: 0.92` is dead
        config -- no .py file reads it. Conversion is purely
        kinetic, and lands nowhere near it."""

        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")
        target = cfg["operational"]["calcination_degree_target"]

        stored = np.asarray(
            self.snapshot["flow_calciner_solid_CaCO3"], dtype=float
        )
        achieved = 1.0 - stored[-1] / self.inlet

        self.assertAlmostEqual(target, 0.92)
        self.assertLess(achieved, 0.25)


class Link4TheRateConstantIsTheCauseTest(unittest.TestCase):
    """`self.prefactor = 42.5  # 1/s`."""

    def setUp(self):
        self.model = CalcinationModel()
        self.snapshot = _snapshot()

    def test_the_committed_pair_needs_hours_where_a_plant_needs_seconds(self):

        model = self.model

        self.assertAlmostEqual(model.prefactor, 42.5)
        self.assertAlmostEqual(model.activation_energy, 1.5e5)

        k = float(model.reaction_rate(1123.0))
        t90_hours = math.log(10.0) / k / 3600.0

        self.assertAlmostEqual(t90_hours, 648.4, delta=0.5)
        self.assertGreater(t90_hours, 100.0)

        # Against what the vessel actually has.
        self.assertLess(RISER["transit_s"], 5.0)

    def test_how_far_the_prefactor_is_from_the_physical_requirement(self):
        """An ILC calciner finishes ~90 % in about 3.4 s at 1123 K.
        That fixes k -- not the pair -- so it is a constraint any
        (k0, Ea) has to satisfy, not a number to tune to."""

        model = self.model

        k_required = math.log(10.0) / REAL_CALCINER_T90_S
        arrhenius = math.exp(
            -model.activation_energy / (8.314 * 1123.0)
        )

        k0_required = k_required / arrhenius

        self.assertAlmostEqual(k_required, 0.67723, places=4)
        self.assertAlmostEqual(k0_required / 1.0e6, 6.427, delta=0.01)

        shortfall = k0_required / model.prefactor
        self.assertGreater(shortfall, 1.0e5)

    def test_the_calciner_self_heats_to_make_up_for_it(self):
        """Which is why the model gets any conversion at all, and
        why correcting the transit exposed the rate rather than
        breaking anything."""

        Ts = np.asarray(self.snapshot["Ts_calciner"], dtype=float)

        self.assertAlmostEqual(float(Ts.mean()), 1519.33, delta=0.02)
        self.assertAlmostEqual(float(Ts.max()), 1734.79, delta=0.02)

        # More than 300 K above the top of a real calciner's band.
        self.assertGreater(float(Ts.mean()) - REAL_CALCINER_T[1], 300.0)

        # And the riser state, with less calcination to absorb the
        # calciner's fuel, runs hotter still.
        self.assertGreater(RISER["Ts_mean"], float(Ts.mean()))
        self.assertGreater(RISER["Ts_max"], 2000.0)

    def test_the_collapse_is_the_rate_not_the_transit(self):
        """The whole argument in one assertion. At a REAL calciner
        temperature the committed kinetics convert essentially
        nothing in a real calciner's transit -- so the 1 % the model
        does reach is bought entirely with 600 K of excess
        temperature, not with residence time."""

        model = self.model

        for T in REAL_CALCINER_T:
            k = float(model.reaction_rate(T))
            conversion = 1.0 - math.exp(-k * RISER["transit_s"])
            self.assertLess(conversion, 1.0e-4)

        # What it actually managed, at 1797 K mean.
        self.assertAlmostEqual(RISER["conversion"], 0.0116, places=4)


if __name__ == "__main__":
    unittest.main()
