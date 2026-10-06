"""Benign one-shot serializer contract regressions; standard library only."""
import sys
import unittest
from copy import deepcopy
from itertools import combinations
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src")]
from checker import check_rank, replay
from generators import binary_encode, graph_family, one_shot
from model import validate
from solver import solve


class SerializationContract(unittest.TestCase):
    def setUp(self):
        self.family = one_shot("threshold-three", [[0, 0], [1, 0], [1, 1]])

    def test_reusable_tests_are_rejected(self):
        # Without the fresh-to-spent requirement, the source can identify in
        # two zero-reset queries while its destructive encoding cannot.
        reusable = deepcopy(self.family)
        for machine in reusable["machines"]:
            for edge in machine["table"][0]:
                edge[1] = 0
        validate(reusable)
        result = solve(reusable, 0, seconds=5)
        self.assertEqual(result["status"], "identified")
        self.assertEqual(result["depth"], 2)
        check_rank(reusable, result["certificate"])
        replay(reusable, result["certificate"], result["strategy"])
        with self.assertRaisesRegex(ValueError, "fresh action"):
            binary_encode(reusable)

    def test_one_non_destructive_cell_is_rejected(self):
        changed = deepcopy(self.family)
        changed["machines"][1]["table"][0][1][1] = 0
        with self.assertRaisesRegex(ValueError, "fresh action"):
            binary_encode(changed)

    def test_other_one_shot_preconditions_are_explicit(self):
        edits = (
            lambda f: f["machines"][0].__setitem__("initial", 1),
            lambda f: f["machines"][0]["table"].append([[0, 1], [0, 1]]),
            lambda f: f["machines"][0]["table"][1][0].__setitem__(0, 1),
            lambda f: f["machines"][0]["table"][1][0].__setitem__(1, 0),
            lambda f: f["machines"][0]["table"][0].pop(),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                changed = deepcopy(self.family)
                edit(changed)
                with self.assertRaises(ValueError):
                    binary_encode(changed)

    def test_all_small_supports_preserve_reset_feasibility(self):
        families = [self.family, graph_family(2, [(0, 1)], "single-edge")]
        comparisons = 0
        for family in families:
            encoded = binary_encode(family)
            n = len(family["machines"])
            for size in range(1, n + 1):
                for support in combinations(range(n), size):
                    for budget in (0, 1, 2, None):
                        with self.subTest(family=family["name"], support=support, budget=budget):
                            source = solve(family, budget, support, seconds=5)
                            target = solve(encoded, budget, support, seconds=5)
                            for model, result in ((family, source), (encoded, target)):
                                self.assertNotEqual(result["status"], "unknown")
                                check_rank(model, result["certificate"])
                                if result["strategy"] is not None:
                                    replay(model, result["certificate"], result["strategy"])
                            self.assertEqual(source["status"], target["status"])
                            comparisons += 1
        self.assertEqual(comparisons, 88)


if __name__ == "__main__":
    unittest.main()
