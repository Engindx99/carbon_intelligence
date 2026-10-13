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


class DefaultNodeCountTest(unittest.TestCase):

    def test_default_is_1_node_per_stage(self):
        """1 since the node exchange is exact; see the config."""

        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        self.assertEqual(cfg["preheater"]["nodes_per_stage"], 1)


class NodalPreheaterBalanceTest(unittest.TestCase):
    """20 co-current nodes per cyclone stage: the multi-node march,
    and the claim that one exact node already gives its answer."""

    NODES = 20

    @classmethod
    def setUpClass(cls):
        cls.twin, cls.validations = run_twin(nodes_per_stage=cls.NODES)
        cls.one_node, _ = run_twin(nodes_per_stage=1)

    def test_one_exact_node_matches_twenty(self):
        """The reference is a 1-node plant on the SAME physics, run
        here (the stored twin_state_reference.json predates solid
        Cp(T) and the composition-aware gas). With each stream's
        heat capacity a secant over the node, 20 nodes move the
        stage outlets by at most 1.98 K (stage 3 solid; gas
        0.35-1.16 K) and the calciner's solid inlet enthalpy by
        0.09 % (measured 13 Oct 2026). With Cp at the node mean
        instead, the solid's Cp(T) put one node 4-15 K off twenty
        and that enthalpy 0.9 %; under the old forward-Euler node,
        stage 1's gas outlet alone was 38 K off and that enthalpy
        12 %. What is left is radiation linearised at the node
        means, Tw held over the node, and the plant loop
        reconverging around both."""

        one = {s.stage_id: s for s in self.one_node.preheater.stages}

        for stage in self.twin.preheater.stages:
            with self.subTest(stage=stage.stage_id):
                for side in ("gas", "solid"):
                    attr = f"{side}_outlet_temperature"
                    self.assertLess(
                        abs(getattr(stage, attr)
                            - getattr(one[stage.stage_id], attr)),
                        2.5,
                    )

        H20 = self.twin.state.Hsolid_calciner_in
        H1 = self.one_node.state.Hsolid_calciner_in
        self.assertLess(abs(H20 - H1) / H1, 2e-3)

    def test_runs_20_nodes_per_stage(self):

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
