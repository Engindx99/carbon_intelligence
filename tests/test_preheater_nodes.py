import json
import unittest
from pathlib import Path

from tests.twin_harness import REPO_ROOT, capture_state, run_twin
import main


REFERENCE_PATH = Path(__file__).resolve().parent / "data" / "twin_state_reference.json"

EXPECTED_VALIDATIONS = {
    ("Burning", "energy"),
    ("Transition", "energy"),
    ("Calciner", "energy"),
    ("Cooler", "energy"),
    ("Preheater", "energy"),
    ("Preheater Stage 1", "energy"),
    ("Preheater Stage 2", "energy"),
    ("Preheater Stage 3", "energy"),
    ("Preheater Stage 4", "energy"),
    ("Preheater Stage 5", "energy"),
    ("Pyroprocess", "global_energy"),
    ("Pyroprocess", "global_mass"),
    ("Cooler", "air_split"),
    ("Pyroprocess", "global_co2_species"),
}


def assert_balances_pass(test, validations):

    reported = {(v["equipment"], v["balance_type"]) for v in validations}

    test.assertEqual(
        reported,
        EXPECTED_VALIDATIONS,
        "the set of balance checks run by Twin.run() changed",
    )

    for v in validations:
        with test.subTest(equipment=v["equipment"], balance=v["balance_type"]):
            result = v["result"]
            test.assertTrue(
                result["converged"],
                f"residual={result['residual']:.6e}, "
                f"relative={result['relative_residual']:.6e}, "
                f"abs_tol={result['absolute_tolerance']:.1e}, "
                f"rel_tol={result['relative_tolerance']:.1e}",
            )


class TwinStateRegressionTest(unittest.TestCase):
    """
    Bit-exact change detector for the converged twin at
    nodes_per_stage=1: every one of the 235 captured fields must match
    tests/data/twin_state_reference.json exactly.

    What this guarantees: no change anywhere in the plant alters the
    converged state without someone noticing. The snapshot spans all
    five zones, so a failure here is a signal to check that the
    difference was intended -- not necessarily a defect. When it was
    intended, regenerate the reference in the same commit as the change
    that caused it, via

        python -m tests.twin_harness tests/data/twin_state_reference.json "<why>" 1

    so the "source" field always records which change set the baseline.

    What this no longer guarantees: this file previously held
    tests/data/preheater_lumped_reference.json, generated from commit
    2991185, and proved that the nodal preheater with nodes_per_stage=1
    reproduces the older lumped-stage model bit for bit. That reference
    is kept as tests/data/preheater_lumped_reference_2991185.json, but
    it is no longer compared against: it snapshots the whole plant, and
    the preheater is coupled to the kiln through the counter-current gas
    chain, so an intentional physics change in any zone invalidates it.
    The first such change was moving the clinkering reaction enthalpy
    from the gas phase to the solid phase in the burning zone. The
    lumped model no longer exists in the code, so that equivalence
    cannot be re-derived -- the 2991185 file is its only record.
    """

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin(nodes_per_stage=1)
        cls.snapshot = capture_state(cls.twin, cls.validations)
        cls.reference = json.loads(REFERENCE_PATH.read_text())["snapshot"]

    def test_snapshot_matches_reference_exactly(self):

        self.assertEqual(set(self.snapshot), set(self.reference))

        for key, expected in self.reference.items():
            with self.subTest(key=key):
                self.assertEqual(self.snapshot[key], expected)

    def test_balances_pass(self):
        assert_balances_pass(self, self.validations)


class NodalPreheaterBalanceTest(unittest.TestCase):
    """Default configuration: 20 co-current nodes per cyclone stage."""

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin()

    def test_default_is_20_nodes_per_stage(self):

        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        self.assertEqual(cfg["preheater"]["nodes_per_stage"], 20)
        self.assertEqual(self.twin.preheater.nodes_per_stage, 20)

        for stage in self.twin.preheater.stages:
            with self.subTest(stage=stage.stage_id):
                self.assertEqual(stage.node_gas_temperatures.size, 20)
                self.assertEqual(stage.node_solid_temperatures.size, 20)
                self.assertEqual(stage.node_wall_temperatures.size, 20)

    def test_balances_pass(self):
        assert_balances_pass(self, self.validations)

    def test_stage_node_profiles_end_at_stage_outlets(self):

        for stage in self.twin.preheater.stages:
            with self.subTest(stage=stage.stage_id):
                self.assertEqual(
                    stage.node_gas_temperatures[-1],
                    stage.gas_outlet_temperature,
                )
                self.assertEqual(
                    stage.node_solid_temperatures[-1],
                    stage.solid_outlet_temperature,
                )


if __name__ == "__main__":
    unittest.main()
