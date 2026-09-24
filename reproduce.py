#!/usr/bin/env python3
"""Reproduce the retained finite evidence using only Python's standard library.

The run checks every main certificate with a separately implemented verifier,
compares the solver with structurally independent tiny oracles, validates the
cover/transversal constructions and binary serialization, rejects directed
certificate/model corruptions, and exercises conservative resource failures.
No network, external solver, hardware observation, or model service is used.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from copy import deepcopy
from itertools import combinations
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from checker import check_pair, check_rank, replay
from generators import binary_encode, graph_family, one_shot, private_pairs, thresholds
from model import load
from mutations import run_input_rejections, run_mutations
from obstructions import antichains, cover_transform, minimal
from oracles import (
    all_graphs,
    collision_failure,
    covers,
    deterministic_random_family,
    explicit_game_depth,
    pair_collision_table,
    perfect_matchings,
    selected_supports,
    subsets,
    table_depth,
    transversal_edges,
    transversal_failure,
    unary_depth,
    unary_machines,
)
from solver import pair_witness, solve

MAX_NODES = 100_000
MAX_OBLIGATIONS = 750_000
SCIENTIFIC_ROOT_FILES = (
    "summary.json",
    "main_results.json",
    "main_results.csv",
    "unary_oracle.json",
    "differential_oracle.json",
    "graph_oracle.json",
    "hypergraph_oracle.json",
    "binary_oracle.json",
    "antichain_oracle.json",
    "mutation_results.json",
    "input_validation.json",
)


class Meter:
    def __init__(self):
        self.nodes = 0
        self.obligations = 0
        self.solves = 0
        self.actual_producer_nodes = 0
        self.actual_producer_solves = 0

    def game(self, family, resets, subset=None, **kwargs):
        if self.nodes >= MAX_NODES or self.obligations >= MAX_OBLIGATIONS:
            raise RuntimeError("global run cap before game")
        result = solve(
            family,
            resets,
            subset,
            node_cap=min(20_000, MAX_NODES - self.nodes),
            obligation_cap=min(150_000, MAX_OBLIGATIONS - self.obligations),
            **kwargs,
        )
        self.nodes += result["nodes"]
        self.actual_producer_nodes += result["nodes"]
        self.obligations += result["transition_obligations"]
        self.solves += 1
        self.actual_producer_solves += 1
        if result["status"] == "unknown":
            raise RuntimeError("unexpected game cap: " + str(result))
        checked = check_rank(family, result["certificate"])
        self.obligations += checked["obligations"]
        if checked["status"] != result["status"] or checked["depth"] != result["depth"]:
            raise AssertionError("producer/checker disagreement")
        if result["strategy"] is not None:
            self.obligations += replay(family, result["certificate"], result["strategy"])["obligations"]
        if self.obligations > MAX_OBLIGATIONS:
            raise RuntimeError("global run obligation cap")
        return result


def dump(path, obj):
    data = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if len(data.encode()) > 32 * 1024 * 1024:
        raise RuntimeError("bounded JSON output exceeded")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def scientific_files(directory):
    result = [directory / name for name in SCIENTIFIC_ROOT_FILES]
    result.extend(sorted((directory / "certificates").glob("*.json")))
    return result


def run(out, *, verify_retained_main=False):
    started = time.monotonic()
    cpu = time.process_time()
    meter = Meter()

    # Retained main suite and independently checked certificate packets.
    main = []
    witnesses = {}
    pairs = {}
    main_obligations0 = meter.obligations
    manifest = json.loads((ROOT / "inputs/catalog.json").read_text())
    if len(manifest) != 48:
        raise AssertionError("48 retained families required")
    for item in manifest:
        name = item["name"]
        family = load(ROOT / "inputs" / item["file"])
        resets = item["resets"]
        if verify_retained_main:
            packet = json.loads((ROOT / "results" / "certificates" / f"{name}.json").read_text())
            checked = check_rank(family, packet["game"])
            strategy_obligations = 0
            if packet["strategy"] is not None:
                strategy_obligations = replay(family, packet["game"], packet["strategy"])["obligations"]
            result = {
                "status": checked["status"],
                "depth": checked["depth"],
                "nodes": len(packet["game"]["rows"]),
                "transition_obligations": checked["obligations"],
                "certificate": packet["game"],
                "strategy": packet["strategy"],
            }
            # Preserve the same conservative logical workload counters as a
            # producer run while avoiding a second enumeration of these 48
            # already-retained position graphs during clean-extraction checking.
            meter.nodes += result["nodes"]
            meter.obligations += result["transition_obligations"] + checked["obligations"] + strategy_obligations
            meter.solves += 1
        else:
            result = meter.game(family, resets)
        stats = {}
        pair_certificate = pair_witness(family, stats)
        meter.obligations += stats["pair_obligations"]
        retained_pair = packet["unlimited_pair"] if verify_retained_main else pair_certificate
        if (retained_pair is None) != (pair_certificate is None):
            raise AssertionError("retained rooted-pair presence differs from fresh search")
        if retained_pair is not None:
            meter.obligations += check_pair(family, retained_pair)["obligations"]
            if retained_pair != pair_certificate:
                raise AssertionError("retained rooted-pair witness differs from deterministic search")
            pairs[name] = retained_pair
        pair_certificate = retained_pair
        if resets is None and ((pair_certificate is not None) != (result["status"] == "ambiguous")):
            raise AssertionError("unlimited-reset equivalence criterion")
        row = {
            "name": name,
            "group": item["group"],
            "reset_budget": resets,
            "status": result["status"],
            "depth": result["depth"],
            "hypotheses": len(family["machines"]),
            "max_states": max(len(machine["table"]) for machine in family["machines"]),
            "actions": len(family["actions"]),
            "observations": len(family["observations"]),
            "belief_nodes": result["nodes"],
            "transition_obligations": result["transition_obligations"],
            "rooted_pair": pair_certificate is not None,
        }
        main.append(row)
        witnesses[name] = (family, result)
        dump(
            out / "certificates" / f"{name}.json",
            {
                "game": result["certificate"],
                "strategy": result["strategy"],
                "unlimited_pair": pair_certificate,
            },
        )
    main_counts = {
        "instances": len(main),
        "identified": sum(row["status"] == "identified" for row in main),
        "ambiguous": sum(row["status"] == "ambiguous" for row in main),
        "nodes": meter.nodes,
        "obligations": meter.obligations - main_obligations0,
    }

    # All unordered pairs and triples of all rooted two-state unary machines.
    tiny = []
    machines = unary_machines()
    n0, o0 = meter.nodes, meter.obligations
    for size in (2, 3):
        for ids in combinations(range(16), size):
            family = {
                "name": "unary",
                "machines": [deepcopy(machines[index]) for index in ids],
                "actions": ["tick"],
                "observations": [0, 1],
            }
            expected = unary_depth(family["machines"])
            for resets in (0, None):
                result = meter.game(family, resets)
                if result["depth"] != expected:
                    raise AssertionError(("unary oracle", ids, resets, expected, result))
            tiny.append({"machines": list(ids), "minimum_depth": expected, "both_budgets_match": True})
    tiny_counts = {
        "families": len(tiny),
        "game_comparisons": 2 * len(tiny),
        "identified": sum(row["minimum_depth"] is not None for row in tiny),
        "ambiguous": sum(row["minimum_depth"] is None for row in tiny),
        "nodes": meter.nodes - n0,
        "obligations": meter.obligations - o0,
    }

    # A small fixed-seed differential suite compares complete Bellman values,
    # not only status, against a separately implemented explicit position graph.
    differential = []
    n0, o0 = meter.nodes, meter.obligations
    oracle_positions = oracle_transitions = 0
    seeds = list(range(2026091700, 2026091712))
    for seed in seeds:
        family = deterministic_random_family(seed)
        for support in selected_supports(len(family["machines"])):
            for resets in (0, 1, None):
                expected = explicit_game_depth(family, resets, support)
                oracle_positions += expected["positions"]
                oracle_transitions += expected["transitions"]
                result = meter.game(family, resets, support)
                if result["depth"] != expected["depth"]:
                    raise AssertionError(("differential oracle", seed, support, resets, expected, result))
                differential.append({
                    "seed": seed,
                    "support": list(support),
                    "reset_budget": resets,
                    "expected_depth": expected["depth"],
                    "solver_depth": result["depth"],
                    "oracle_positions": expected["positions"],
                    "oracle_transitions": expected["transitions"],
                })
    differential_counts = {
        "families": len(seeds),
        "support_budget_comparisons": len(differential),
        "oracle_positions": oracle_positions,
        "oracle_transitions": oracle_transitions,
        "solver_nodes": meter.nodes - n0,
        "solver_obligations": meter.obligations - o0,
        "mismatches": 0,
    }

    # Exhaust every nonempty labeled graph on two through four vertices and
    # every nonempty hypothesis subset of its matching-collision construction.
    graphs = []
    n0, o0 = meter.nodes, meter.obligations
    graph_subsets = 0
    for vertex_count, edges in all_graphs():
        family = graph_family(vertex_count, edges)
        table = [[edge[0] for edge in machine["table"][0]] for machine in family["machines"]]
        forced, residual = cover_transform(table)
        if forced != [0, 1] or residual != sorted((left + 2, right + 2) for left, right in edges):
            raise AssertionError("cover graph not recovered")
        actual_minimum = None
        losing = 0
        action_count = len(table[0])
        for support in subsets(vertex_count + 2):
            graph_subsets += 1
            expected = 0 in support and 1 in support and all(
                left + 2 in support or right + 2 in support for left, right in edges
            )
            direct_table_failure = all(
                len({table[hypothesis][action] for hypothesis in support}) < len(support)
                for action in range(action_count)
            )
            if direct_table_failure != expected:
                raise AssertionError("cover/direct-table equivalence")
            if expected:
                losing += 1
                actual_minimum = len(support) if actual_minimum is None else min(actual_minimum, len(support))
        minimum_covers = covers(vertex_count, edges)
        if actual_minimum != 2 + len(minimum_covers[0]):
            raise AssertionError("minimum cardinality equality")
        minimum_support = tuple([0, 1] + [vertex + 2 for vertex in minimum_covers[0]])
        exact_checks = [
            (tuple(range(vertex_count + 2)), 0, "ambiguous", None),
            (tuple(range(vertex_count + 2)), 1, "identified", 3),
            ((0, 1), 0, "identified", 1),
            (minimum_support, 0, "ambiguous", None),
        ]
        for support, resets, status, depth in exact_checks:
            result = meter.game(family, resets, support)
            if result["status"] != status or (depth is not None and result["depth"] != depth):
                raise AssertionError("graph exact-game spot check")
        graphs.append({
            "vertices": vertex_count,
            "edges": [list(edge) for edge in edges],
            "minimum_vertex_cover": len(minimum_covers[0]),
            "minimum_ambiguity_support": actual_minimum,
            "losing_subsets": losing,
            "direct_table_supports_checked": (1 << (vertex_count + 2)) - 1,
            "exact_game_checks": len(exact_checks),
            "one_reset_depth": 3,
        })
    graph_counts = {
        "graphs": len(graphs),
        "all_subset_comparisons": graph_subsets,
        "exact_game_spot_checks": 4 * len(graphs),
        "nodes": meter.nodes - n0,
        "obligations": meter.obligations - o0,
    }

    # Rank-three hypergraph boundary: four six-hypothesis matching systems,
    # every nonempty support, three independent predicates (collision DNF,
    # distributed transversal CNF, and the exact game).
    hypergraph = []
    n0, o0 = meter.nodes, meter.obligations
    matchings = perfect_matchings(range(6))
    specifications = [
        [matchings[0]],
        [matchings[0], matchings[1]],
        [matchings[2], matchings[5], matchings[7]],
        [matchings[3], matchings[8], matchings[14]],
    ]
    hypergraph_supports = 0
    for case, tests in enumerate(specifications):
        table = pair_collision_table(6, tests)
        family = one_shot(
            f"rank-three-{case}",
            table,
            metadata={"kind": "rank_three_hypergraph_oracle", "tests": [[list(pair) for pair in test] for test in tests]},
        )
        losing = 0
        edges = transversal_edges(tests)
        first_losing = first_winning = None
        for support in subsets(6):
            direct = collision_failure(tests, support)
            transversal = transversal_failure(tests, support)
            if direct != transversal:
                raise AssertionError(("hypergraph/transversal mismatch", case, support))
            if direct and first_losing is None:
                first_losing = support
            if not direct and len(support) >= 2 and first_winning is None:
                first_winning = support
            losing += int(direct)
            hypergraph_supports += 1
        exact_supports = {tuple(range(6)), tuple(first_losing), tuple(first_winning)}
        for support in sorted(exact_supports, key=lambda item: (len(item), item)):
            result = meter.game(family, 0, support)
            expected_status = "ambiguous" if collision_failure(tests, support) else "identified"
            if result["status"] != expected_status:
                raise AssertionError(("hypergraph exact-game spot check", case, support))
        hypergraph.append({
            "case": case,
            "tests": [[list(pair) for pair in test] for test in tests],
            "hyperedges": [sorted(edge) for edge in edges],
            "all_nonempty_supports": 63,
            "losing_supports": losing,
            "exact_game_checks": len(exact_supports),
            "predicates_agree": True,
        })
    hypergraph_counts = {
        "families": len(hypergraph),
        "all_support_comparisons": hypergraph_supports,
        "exact_game_spot_checks": sum(row["exact_game_checks"] for row in hypergraph),
        "maximum_pairs_per_test": 3,
        "maximum_hypergraph_rank": 3,
        "nodes": meter.nodes - n0,
        "obligations": meter.obligations - o0,
    }

    # Binary serialization: all zero-reset supports of four graph shapes are
    # compared to their source tables, then representative supports are checked
    # at one, two, and unlimited reset budgets as an explicit regression.
    binary = []
    n0, o0 = meter.nodes, meter.obligations
    selected = [
        (3, [(0, 1), (1, 2)]),
        (3, [(0, 1), (0, 2), (1, 2)]),
        (4, [(0, 1), (1, 2), (2, 3)]),
        (4, list(combinations(range(4), 2))),
    ]
    zero_reset_supports = 0
    cross_budget = 0
    for shape, (vertex_count, edges) in enumerate(selected):
        family = graph_family(vertex_count, edges)
        encoded = binary_encode(family)
        for support in subsets(vertex_count + 2):
            source_failure = 0 in support and 1 in support and all(
                left + 2 in support or right + 2 in support for left, right in edges
            )
            encoded_result = meter.game(encoded, 0, support)
            source_status = "ambiguous" if source_failure else "identified"
            if source_status != encoded_result["status"]:
                raise AssertionError("binary zero-reset support preservation")
            binary.append({
                "shape": shape,
                "vertices": vertex_count,
                "edges": [list(edge) for edge in edges],
                "support": list(support),
                "reset_budget": 0,
                "source_status": source_status,
                "encoded_status": encoded_result["status"],
                "source_depth": None,
                "encoded_depth": encoded_result["depth"],
            })
            zero_reset_supports += 1
        if shape < 2:  # bounded-depth cross-budget checks on the two 5-hypothesis shapes.
            representatives = [
                tuple(range(vertex_count + 2)),
                (0, 1),
                (0, 1, 2),
            ]
            for support in representatives:
                for resets in (1, 2, None):
                    source_result = meter.game(family, resets, support)
                    encoded_result = meter.game(encoded, resets, support)
                    if source_result["status"] != encoded_result["status"]:
                        raise AssertionError("binary cross-budget support preservation")
                    binary.append({
                        "shape": shape,
                        "vertices": vertex_count,
                        "edges": [list(edge) for edge in edges],
                        "support": list(support),
                        "reset_budget": resets,
                        "source_status": source_result["status"],
                        "encoded_status": encoded_result["status"],
                        "source_depth": source_result["depth"],
                        "encoded_depth": encoded_result["depth"],
                    })
                    cross_budget += 1
    binary_counts = {
        "families": 4,
        "zero_reset_support_comparisons": zero_reset_supports,
        "cross_budget_support_comparisons": cross_budget,
        "budgets_in_cross_check": [1, 2, "unlimited"],
        "nodes": meter.nodes - n0,
        "obligations": meter.obligations - o0,
    }

    # Antichain recurrence versus strict-subset decision trees, including empty
    # obstruction antichains after enough queries and the sharp 3,5,9 bounds.
    anti = []
    joins = 0
    decisions = 0
    antichain_families = [
        thresholds(3, "threshold3"),
        thresholds(5, "threshold5"),
        thresholds(9, "threshold9"),
        private_pairs(2, "pairs2"),
        private_pairs(3, "pairs3"),
    ]
    antichain_families += [
        graph_family(vertex_count, edges, "graph" + str(index))
        for index, (vertex_count, edges) in enumerate(selected)
    ]
    for family in antichain_families:
        table = [[edge[0] for edge in machine["table"][0]] for machine in family["machines"]]
        depths = {support: table_depth(table, support) for support in subsets(len(table))}
        decisions += len(depths)
        for query_budget in range(4):
            got, formed = antichains(table, query_budget)
            joins += formed
            wanted = minimal([
                frozenset(support)
                for support, depth in depths.items()
                if depth is None or depth > query_budget
            ])
            if set(got) != set(wanted):
                raise AssertionError("antichain recurrence")
            anti.append({
                "family": family["name"],
                "query_budget": query_budget,
                "minimal_supports": [sorted(support) for support in got],
                "join_products": formed,
            })
    anti_counts = {
        "families": len(antichain_families),
        "antichain_comparisons": len(anti),
        "independent_tree_supports": decisions,
        "join_products": joins,
    }

    # Directed certificate corruptions, malformed input rejection, and caps.
    winning_name = "graph-triangle-budget-1"
    ambiguous_name = "graph-triangle-budget-0"
    pair_name = "stateful-104729-duplicate"
    winning_family, winning_result = witnesses[winning_name]
    ambiguous_family, ambiguous_result = witnesses[ambiguous_name]
    pair_family, _ = witnesses[pair_name]
    mutations = run_mutations(
        winning_family,
        winning_result,
        ambiguous_family,
        ambiguous_result,
        pair_family,
        pairs[pair_name],
    )
    input_rejections = run_input_rejections(winning_family, winning_result["certificate"])

    caprows = []
    for reason, kwargs in (
        ("node", {"node_cap": 1}),
        ("obligation", {"obligation_cap": 1}),
        ("depth", {"depth_cap": 0}),
    ):
        result = solve(winning_family, 1, **kwargs)
        meter.nodes += result["nodes"]
        meter.actual_producer_nodes += result["nodes"]
        meter.obligations += result["transition_obligations"]
        meter.actual_producer_solves += 1
        if (
            result["status"] != "unknown"
            or result["reason"] != reason
            or result["depth"] is not None
            or "certificate" in result
        ):
            raise AssertionError("cap falsely produced scientific conclusion")
        caprows.append({
            "bound": reason,
            "status": result["status"],
            "reason": result["reason"],
            "nodes": result["nodes"],
            "transition_obligations": result["transition_obligations"],
        })

    # Conservatively charge each rejected mutation the larger complete packet;
    # actual rejection normally stops earlier.  Input-validation checks are
    # charged one full raw-model scan apiece.
    mutation_charge = len(mutations) * (
        max(winning_result["transition_obligations"], ambiguous_result["transition_obligations"])
        + max(
            len(winning_family["machines"]) * winning_result["depth"],
            len(pairs[pair_name]["pairs"]) * (len(pair_family["actions"]) + 1),
        )
    )
    validation_charge = len(input_rejections) * sum(
        len(machine["table"]) * len(winning_family["actions"])
        for machine in winning_family["machines"]
    )
    meter.obligations += mutation_charge + validation_charge
    if meter.nodes > MAX_NODES or meter.obligations > MAX_OBLIGATIONS:
        raise RuntimeError("final run cap")

    semantic = {
        "main": main_counts,
        "unary": tiny_counts,
        "differential": differential_counts,
        "graphs": graph_counts,
        "hypergraphs": hypergraph_counts,
        "binary": binary_counts,
        "antichains": anti_counts,
        "mutations": {
            "tested": len(mutations),
            "rejected": len(mutations),
            "conservative_obligation_charge": mutation_charge,
        },
        "input_validation": {
            "malformed_cases": len(input_rejections),
            "rejected_by_producer": len(input_rejections),
            "rejected_by_checker": len(input_rejections),
            "conservative_obligation_charge": validation_charge,
        },
        "cap_controls": caprows,
        "total_solver_belief_nodes": meter.nodes,
        "independent_oracle_positions": oracle_positions,
        "transition_and_certificate_obligations_charged": meter.obligations,
        "independent_oracle_transitions": oracle_transitions,
        "exact_game_solves": meter.solves,
        "failures": 0,
        "worker_count": 1,
    }

    dump(out / "summary.json", semantic)
    dump(out / "main_results.json", main)
    dump(out / "unary_oracle.json", tiny)
    dump(out / "differential_oracle.json", differential)
    dump(out / "graph_oracle.json", graphs)
    dump(out / "hypergraph_oracle.json", hypergraph)
    dump(out / "binary_oracle.json", binary)
    dump(out / "antichain_oracle.json", anti)
    dump(out / "mutation_results.json", mutations)
    dump(out / "input_validation.json", input_rejections)
    with (out / "main_results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(main[0]))
        writer.writeheader()
        writer.writerows(main)

    metrics = {
        "wall_seconds": time.monotonic() - started,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "address_space_limit_bytes": 2 * 1024**3,
        "wall_limit_seconds": 180,
        "total_output_bytes_before_metrics": sum(
            path.stat().st_size for path in out.rglob("*") if path.is_file()
        ),
        "producer_nodes_enumerated_this_run": meter.actual_producer_nodes,
        "producer_games_enumerated_this_run": meter.actual_producer_solves,
        "retained_main_packets_verified_without_reenumeration": bool(verify_retained_main),
    }
    dump(out / "resources.json", metrics)
    return semantic, metrics


def compare_retained(out):
    generated = scientific_files(out)
    retained = scientific_files(ROOT / "results")
    generated_relative = [path.relative_to(out) for path in generated]
    retained_relative = [path.relative_to(ROOT / "results") for path in retained]
    if generated_relative != retained_relative:
        raise AssertionError("retained scientific file inventory differs")
    for relative in generated_relative:
        if (out / relative).read_bytes() != (ROOT / "results" / relative).read_bytes():
            raise AssertionError("retained scientific file differs byte-for-byte: " + str(relative))
    return len(generated_relative)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reproduced", help="new output directory (must not exist)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare every deterministic scientific output byte-for-byte with retained results",
    )
    args = parser.parse_args()
    out = Path(args.output).resolve()
    if out.exists():
        parser.error("output directory already exists; choose a new directory")
    if not hasattr(signal, "SIGALRM"):
        parser.error("this bounded runner requires POSIX signal/resource support")
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))

    def expired(_signum, _frame):
        raise TimeoutError("whole-run wall bound exceeded")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 180)
    out.mkdir(parents=True)
    try:
        scientific, metrics = run(out, verify_retained_main=args.check)
        compared = compare_retained(out) if args.check else 0
        dump(
            out / "run_status.json",
            {
                "status": "passed",
                "retained_byte_comparison": args.check,
                "scientific_files_compared": compared,
            },
        )
        print(json.dumps({"status": "passed", "scientific": scientific, "measured": metrics}, indent=2))
    except Exception as exc:
        dump(
            out / "run_status.json",
            {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)[:1000]},
        )
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
