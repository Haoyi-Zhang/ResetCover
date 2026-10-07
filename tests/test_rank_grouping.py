"""Portable rank/trap regression against a literal finite-game reference.

The reference scans each declared output separately. It does not import the
producer, its transition builder, or any historical/private implementation.
All tests concern authored finite transition tables, not external systems.
"""
import sys
import unittest
from copy import deepcopy
from itertools import combinations, product
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src")]
from checker import InvalidCertificate, check_rank


def literal_packet(family, budget, support):
    machines = family["machines"]
    n = len(machines)
    ac = len(family["actions"])
    initial = (tuple(m["initial"] if h in support else -1
                     for h, m in enumerate(machines)), -1 if budget is None else budget)
    positions = [initial]
    index = {initial: 0}
    transitions = []
    for belief, remaining in positions:
        branches = []
        if sum(s >= 0 for s in belief) > 1:
            for action in range(ac):
                destinations = []
                for output in sorted(family["observations"]):
                    # Independent declared-output filtering, not grouping.
                    after = tuple(
                        machines[h]["table"][state][action][1]
                        if state >= 0 and machines[h]["table"][state][action][0] == output
                        else -1 for h, state in enumerate(belief))
                    if any(state >= 0 for state in after):
                        destinations.append((after, remaining))
                branches.append(destinations)
            if remaining != 0:
                after = tuple(m["initial"] if belief[h] >= 0 else -1
                              for h, m in enumerate(machines))
                branches.append([(after, -1 if remaining == -1 else remaining - 1)])
            for destinations in branches:
                for destination in destinations:
                    if destination not in index:
                        index[destination] = len(positions)
                        positions.append(destination)
        transitions.append(branches)
    ranks = [0 if sum(s >= 0 for s in b) == 1 else None for b, _ in positions]
    choices = [None] * len(positions)
    while True:
        new_ranks = ranks[:]
        new_choices = choices[:]
        for i, branches in enumerate(transitions):
            if not branches:
                continue
            options = []
            for action, destinations in enumerate(branches):
                values = [ranks[index[d]] for d in destinations]
                if all(value is not None for value in values):
                    options.append((1 + max(values), action))
            if options:
                new_ranks[i], new_choices[i] = min(options)
        if new_ranks == ranks and new_choices == choices:
            break
        ranks, choices = new_ranks, new_choices
    packet = {"kind": "rank_trap", "resets": budget, "support": list(support),
              "root": 0, "rows": [
                  {"belief": list(b), "budget": r, "rank": ranks[i], "action": choices[i]}
                  for i, (b, r) in enumerate(positions)]}
    expected = {"depth": ranks[0], "status": "ambiguous" if ranks[0] is None else "identified",
                "obligations": sum(len(ds) for branches in transitions for ds in branches)}
    return packet, expected


def finite_cases():
    templates = list(product((0, 1), repeat=2))
    for n in range(1, 4):
        for rows in product(templates, repeat=n):
            f = {"actions": ["a", "b"], "observations": [1, 0], "machines": [
                {"initial": 0, "table": [[[o, 0] for o in row]]} for row in rows]}
            for size in range(1, n + 1):
                for support in combinations(range(n), size):
                    for budget in (0, 1, 2, None):
                        yield f, budget, support
    unary = [
        {"initial": 0, "table": [[[o0, s0]], [[o1, s1]]]}
        for o0, s0, o1, s1 in product((0, 1), repeat=4)]
    for i, j in combinations(range(16), 2):
        f = {"actions": ["tick"], "observations": [0, 1], "machines": [unary[i], unary[j]]}
        for budget in (0, 1, None):
            yield f, budget, (0, 1)
    # Max admitted dimensions, negative labels, nonzero initial coordinates,
    # absent identities and unused declared outputs.
    for n, ac, states in ((3, 2, 3), (8, 8, 2), (24, 8, 16)):
        f = {"actions": [str(a) for a in range(ac)], "observations": list(range(-4, 4)),
             "machines": [{"initial": states - 1, "table": [
                 [[(h + a) % 8 - 4, (s + 1) % states] for a in range(ac)]
                 for s in range(states)]} for h in range(n)]}
        for support in (tuple(range(n)), tuple(range(0, n, 2)), (n - 1,)):
            for budget in (0, 1, 12, None):
                yield f, budget, support


def observe(family, budget, support):
    packet, expected = literal_packet(family, budget, support)
    actual = check_rank(family, packet)
    if actual != expected:
        raise AssertionError((family, budget, support, actual, expected))
    reordered = deepcopy(packet)
    reordered["rows"].reverse()
    reordered["root"] = len(packet["rows"]) - 1
    reordered["support"].reverse()
    if check_rank(family, reordered) != expected:
        raise AssertionError("row/support reordering changed semantics")
    return packet, actual, reordered


def rejection_cases():
    f = {"actions": ["a", "b"], "observations": [0, 1], "machines": [
        {"initial": 0, "table": [[[0, 0], [0, 0]]]},
        {"initial": 0, "table": [[[1, 0], [0, 0]]]}]}
    packet, _ = literal_packet(f, 1, (0, 1))
    model_edits = (
        (lambda x: x.__setitem__("machines", []), "hypothesis bounds"),
        (lambda x: x.__setitem__("machines", [{}] * 25), "hypothesis bounds"),
        (lambda x: x.__setitem__("actions", []), "action bounds"),
        (lambda x: x.__setitem__("actions", ["a", "a"]), "action labels"),
        (lambda x: x.__setitem__("observations", [True]), "observation bounds"),
        (lambda x: x["machines"].__setitem__(0, []), "machine object"),
        (lambda x: x["machines"][0].__setitem__("initial", True), "machine bounds"),
        (lambda x: x["machines"][0]["table"][0].pop(), "totality"),
        (lambda x: x["machines"][0]["table"][0].__setitem__(0, (0, 0)), "edge shape"),
        (lambda x: x["machines"][0]["table"][0][0].__setitem__(0, True), "edge bounds"),
        (lambda x: x["machines"][0]["table"][0][0].__setitem__(1, 1), "edge bounds"),
    )
    for edit, message in model_edits:
        changed = deepcopy(f)
        edit(changed)
        yield changed, deepcopy(packet), message
    packet_edits = (
        (lambda x: x.__setitem__("kind", "other"), "certificate kind"),
        (lambda x: x.__setitem__("resets", True), "reset budget"),
        (lambda x: x.__setitem__("resets", 13), "reset budget"),
        (lambda x: x.__setitem__("support", [0, 0]), "support"),
        (lambda x: x.__setitem__("support", [True]), "support"),
        (lambda x: x.__setitem__("rows", []), "certificate size"),
        (lambda x: x.__setitem__("rows", [None] * 250001), "certificate size"),
        (lambda x: x.__setitem__("root", True), "root index"),
        (lambda x: x["rows"].__setitem__(0, []), "row object"),
        (lambda x: x["rows"][0]["belief"].__setitem__(0, True), "belief shape"),
        (lambda x: x["rows"][0].__setitem__("belief", [-1, -1]), "belief support"),
        (lambda x: x["rows"][0].__setitem__("budget", -1), "layer range"),
        (lambda x: x["rows"][0].__setitem__("rank", len(x["rows"])), "rank range"),
        (lambda x: x["rows"][0].__setitem__("action", True), "action range"),
        (lambda x: x["rows"].append(deepcopy(x["rows"][0])), "duplicate belief"),
        (lambda x: x["rows"][0].__setitem__("rank", 0), "terminal rank iff singleton"),
        (lambda x: x["rows"][1].__setitem__("action", 0), "terminal/trap choice"),
        (lambda x: x.__setitem__("root", 1), "root semantics"),
        (lambda x: x["rows"].pop(1), "ordinary successor omitted"),
        (lambda x: x["rows"].pop(3), "reset successor omitted"),
        (lambda x: x["rows"][0].__setitem__("action", None), "unavailable chosen action"),
        (lambda x: x["rows"][0].__setitem__("action", 1), "upper rank"),
        (lambda x: x["rows"][0].__setitem__("rank", 2), "lower rank"),
    )
    for edit, message in packet_edits:
        changed = deepcopy(packet)
        edit(changed)
        yield deepcopy(f), changed, message
    # Multiple invalid fields establish the original admission order.
    bad = deepcopy(f)
    bad["actions"] = []
    bad["observations"] = [True]
    yield bad, {"kind": "other"}, "action bounds"
    false_trap = deepcopy(packet)
    false_trap["rows"][0]["rank"] = None
    false_trap["rows"][0]["action"] = None
    yield deepcopy(f), false_trap, "trap not closed adversarially"
    trap_f = deepcopy(f)
    trap_f["machines"][1] = deepcopy(trap_f["machines"][0])
    trap, _ = literal_packet(trap_f, 0, (0, 1))
    trap["rows"][0]["rank"] = 1
    trap["rows"][0]["action"] = 0
    yield trap_f, trap, "rank range"
    extra = deepcopy(packet)
    extra["rows"].append({"belief": [0, -1], "budget": 1, "rank": 0, "action": None})
    # This position already occurs; use an unreachable singleton state instead.
    extra_f = deepcopy(f)
    extra_f["machines"][0]["table"].append([[0, 1], [0, 1]])
    extra["rows"][-1]["belief"] = [1, -1]
    yield extra_f, extra, "unreachable extra row"


class RankGroupingRegression(unittest.TestCase):
    def test_literal_games(self):
        count = 0
        for f, budget, support in finite_cases():
            observe(f, budget, support)
            count += 1
        self.assertEqual(count, 2396)

    def test_rejections_and_order(self):
        count = 0
        for f, packet, message in rejection_cases():
            with self.assertRaises(InvalidCertificate) as caught:
                check_rank(f, packet)
            self.assertEqual(str(caught.exception), message)
            count += 1
        self.assertEqual(count, 38)

    def test_mutated_inputs_are_not_cached(self):
        f = {"actions": ["a"], "observations": [0, 1], "machines": [
            {"initial": 0, "table": [[[0, 0]]]},
            {"initial": 0, "table": [[[0, 0]]]}]}
        self.assertEqual(observe(f, 0, (0, 1))[1]["status"], "ambiguous")
        f["machines"][1]["table"][0][0][0] = 1
        self.assertEqual(observe(f, 0, (0, 1))[1]["depth"], 1)
        f["machines"][1]["table"][0][0][0] = 0
        self.assertEqual(observe(f, None, (0, 1))[1]["status"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
