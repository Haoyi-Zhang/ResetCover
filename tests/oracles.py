"""Independent tiny oracles for finite-state identification checks.

The functions in this module do not import the belief-game producer, its model
validator, transition code, or certificate checker.  They intentionally repeat
small semantics in structurally separate code so agreement is informative.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import combinations, product
from random import Random


def unary_machines():
    """All 16 rooted two-state, unary-input, binary-output Mealy tables."""
    return [
        {"initial": 0, "table": [[[o0, s0]], [[o1, s1]]]}
        for o0, s0, o1, s1 in product(range(2), repeat=4)
    ]


def unary_depth(machines):
    """Exact distinguishing-prefix depth for a unary deterministic family."""
    states = [m["initial"] for m in machines]
    words = [[] for _ in machines]
    # Two-state product pairs either separate within four steps or repeat.
    for depth in range(1, 5):
        for h, machine in enumerate(machines):
            output, target = machine["table"][states[h]][0]
            words[h].append(output)
            states[h] = target
        if len({tuple(word) for word in words}) == len(machines):
            return depth
    return None


def table_depth(table, subset):
    """Exact decision-tree depth; every useful branch strictly shrinks support."""
    action_count = len(table[0])

    @lru_cache(None)
    def visit(hypotheses):
        if len(hypotheses) <= 1:
            return 0
        best = None
        for action in range(action_count):
            cells = {}
            for hypothesis in hypotheses:
                cells.setdefault(table[hypothesis][action], []).append(hypothesis)
            if len(cells) == 1:
                continue
            children = [visit(tuple(cell)) for cell in cells.values()]
            if all(depth is not None for depth in children):
                value = 1 + max(children)
                best = value if best is None else min(best, value)
        return best

    return visit(tuple(sorted(subset)))


def explicit_game_depth(family, resets, subset):
    """Exact tiny-state Bellman oracle, independent of ``src/solver.py``.

    It first materializes the complete reachable position graph using immutable
    dictionaries of output successors, then computes the least fixed-point
    winning layers.  ``None`` denotes an unbounded reset supply and, separately,
    an ambiguous root depth in the returned result.
    """
    machines = family["machines"]
    action_count = len(family["actions"])
    keep = frozenset(subset)
    start_states = tuple(
        machine["initial"] if h in keep else -1
        for h, machine in enumerate(machines)
    )
    root = (start_states, None if resets is None else resets)
    positions = [root]
    index = {root: 0}
    moves = []
    transition_count = 0

    cursor = 0
    while cursor < len(positions):
        states, budget = positions[cursor]
        cursor += 1
        local = []
        if sum(state >= 0 for state in states) > 1:
            for action in range(action_count):
                by_output = {}
                for h, state in enumerate(states):
                    if state < 0:
                        continue
                    output, target = machines[h]["table"][state][action]
                    branch = by_output.setdefault(output, [-1] * len(machines))
                    branch[h] = target
                destinations = []
                for output in sorted(by_output):
                    destination = (tuple(by_output[output]), budget)
                    if destination not in index:
                        index[destination] = len(positions)
                        positions.append(destination)
                    destinations.append(index[destination])
                    transition_count += 1
                local.append(tuple(destinations))
            if budget is None or budget > 0:
                reset_states = tuple(
                    machines[h]["initial"] if state >= 0 else -1
                    for h, state in enumerate(states)
                )
                next_budget = None if budget is None else budget - 1
                destination = (reset_states, next_budget)
                if destination not in index:
                    index[destination] = len(positions)
                    positions.append(destination)
                local.append((index[destination],))
                transition_count += 1
        moves.append(tuple(local))

    ranks = [0 if sum(state >= 0 for state in position[0]) == 1 else None
             for position in positions]
    depth = 0
    while True:
        depth += 1
        newly_winning = []
        for node, local in enumerate(moves):
            if ranks[node] is not None:
                continue
            if any(all(ranks[target] is not None and ranks[target] < depth
                       for target in destinations)
                   for destinations in local):
                newly_winning.append(node)
        if not newly_winning:
            break
        for node in newly_winning:
            ranks[node] = depth

    return {
        "depth": ranks[0],
        "positions": len(positions),
        "transitions": transition_count,
    }


def deterministic_random_family(seed):
    """Small fixed-seed family for differential checking, never user data."""
    rng = Random(seed)
    hypothesis_count = 2 + seed % 3
    action_count = 1 + (seed // 3) % 2
    machines = []
    for _ in range(hypothesis_count):
        state_count = 1 + rng.randrange(3)
        table = []
        for _state in range(state_count):
            row = []
            for _action in range(action_count):
                row.append([rng.randrange(2), rng.randrange(state_count)])
            table.append(row)
        machines.append({"initial": rng.randrange(state_count), "table": table})
    # Force a genuine equivalent pair in one quarter of fixtures.  The other
    # fixtures remain unconstrained random finite machines.
    if seed % 4 == 0:
        machines[-1] = deepcopy(machines[0])
    return {
        "name": f"differential-{seed}",
        "actions": [f"a{action}" for action in range(action_count)],
        "observations": [0, 1],
        "machines": machines,
    }


def selected_supports(hypothesis_count):
    """Deterministic nontrivial supports for bounded differential tests."""
    supports = {tuple(range(hypothesis_count))}
    supports.update(combinations(range(hypothesis_count), 2))
    if hypothesis_count >= 3:
        supports.add(tuple(range(3)))
    return sorted(supports, key=lambda support: (len(support), support))


def perfect_matchings(vertices):
    """All perfect matchings of an even, sorted vertex tuple."""
    vertices = tuple(vertices)
    if not vertices:
        return [tuple()]
    first = vertices[0]
    result = []
    for index in range(1, len(vertices)):
        second = vertices[index]
        rest = vertices[1:index] + vertices[index + 1:]
        for suffix in perfect_matchings(rest):
            result.append(((first, second),) + suffix)
    return result


def pair_collision_table(hypothesis_count, tests):
    """Build an observation table from disjoint collision pairs per test."""
    table = [[None for _ in tests] for _ in range(hypothesis_count)]
    for action, pairs in enumerate(tests):
        used = set()
        next_output = 0
        for left, right in pairs:
            if left == right or left in used or right in used:
                raise ValueError("collision pairs must be disjoint")
            if not (0 <= left < hypothesis_count and 0 <= right < hypothesis_count):
                raise ValueError("collision endpoint outside the table")
            table[left][action] = next_output
            table[right][action] = next_output
            next_output += 1
            used.update((left, right))
        for hypothesis in range(hypothesis_count):
            if table[hypothesis][action] is None:
                table[hypothesis][action] = next_output
                next_output += 1
    return table


def transversal_edges(tests):
    """Distribute each test's pair-DNF into its chosen-endpoint clauses."""
    edges = []
    for pairs in tests:
        for choices in product(*pairs):
            edges.append(frozenset(choices))
    return tuple(edges)


def collision_failure(tests, support):
    selected = frozenset(support)
    return all(any(frozenset(pair) <= selected for pair in pairs) for pairs in tests)


def transversal_failure(tests, support):
    selected = frozenset(support)
    return all(bool(selected & edge) for edge in transversal_edges(tests))


def subsets(n):
    for size in range(1, n + 1):
        yield from combinations(range(n), size)


def all_graphs():
    for n in (2, 3, 4):
        pairs = list(combinations(range(n), 2))
        for bits in range(1, 1 << len(pairs)):
            yield n, [edge for k, edge in enumerate(pairs) if bits >> k & 1]


def covers(n, edges):
    # Enumerating all subsets makes this an exact, deliberately tiny baseline.
    for size in range(n + 1):
        good = [
            list(vertices)
            for vertices in combinations(range(n), size)
            if all(left in vertices or right in vertices for left, right in edges)
        ]
        if good:
            return good
    raise AssertionError("finite cover absent")
