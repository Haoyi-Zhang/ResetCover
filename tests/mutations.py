"""Rule-directed certificate and input corruptions; not a security fuzzer."""
from __future__ import annotations

from copy import deepcopy

from checker import InvalidCertificate, check_pair, check_rank, replay
from model import validate


def run_mutations(f, result, amb_f, amb_result, pair_f, pair_cert):
    rows = []

    def expect(label, function):
        rejected = False
        diagnostic = ""
        try:
            function()
        except InvalidCertificate as exc:
            rejected = True
            diagnostic = str(exc)
        if not rejected:
            raise AssertionError("mutation accepted: " + label)
        rows.append({"mutation": label, "rejected": True, "diagnostic": diagnostic})

    def rank_mut(label, edit, model=f, packet=None):
        certificate = deepcopy(packet or result["certificate"])
        edit(certificate)
        expect(label, lambda: check_rank(model, certificate))

    root = result["certificate"]["root"]
    rank_mut("rank too large", lambda c: c["rows"][root].__setitem__("rank", c["rows"][root]["rank"] + 1))
    rank_mut("rank too small", lambda c: c["rows"][root].__setitem__("rank", c["rows"][root]["rank"] - 1))
    rank_mut("false singleton root", lambda c: c["rows"][root].__setitem__("rank", 0))
    rank_mut("missing reachable successor", lambda c: c["rows"].pop())
    rank_mut("duplicate belief", lambda c: c["rows"].append(deepcopy(c["rows"][0])))
    rank_mut("root state changed", lambda c: c["rows"][root]["belief"].__setitem__(0, 1))
    rank_mut("reset layer changed", lambda c: c["rows"][root].__setitem__("budget", 0))
    rank_mut("boolean rank", lambda c: c["rows"][root].__setitem__("rank", True))
    rank_mut("boolean state", lambda c: c["rows"][root]["belief"].__setitem__(0, True))
    rank_mut("boolean budget", lambda c: c["rows"][root].__setitem__("budget", True))
    rank_mut("boolean action", lambda c: c["rows"][root].__setitem__("action", True))
    rank_mut("identity removed", lambda c: c["rows"][root]["belief"].__setitem__(0, -1))
    rank_mut(
        "reset chosen without budget",
        lambda c: next(
            row for row in c["rows"]
            if row["budget"] == 0 and row["rank"] not in (0, None)
        ).__setitem__("action", len(f["actions"])),
    )
    rank_mut(
        "fake finite root in losing trap",
        lambda c: (c["rows"][0].__setitem__("rank", 1), c["rows"][0].__setitem__("action", 0)),
        amb_f,
        amb_result["certificate"],
    )
    rank_mut(
        "winning root marked infinite",
        lambda c: (c["rows"][root].__setitem__("rank", None), c["rows"][root].__setitem__("action", None)),
    )
    rank_mut("support contains duplicate", lambda c: c["support"].append(c["support"][0]))
    rank_mut("support contains out-of-range identity", lambda c: c["support"].append(len(f["machines"])))
    rank_mut("root index out of range", lambda c: c.__setitem__("root", len(c["rows"])))
    rank_mut("chosen action out of range", lambda c: c["rows"][root].__setitem__("action", len(f["actions"]) + 1))

    # Independent fixed-identity replay detects terminal, edge, graph, and
    # reachability corruptions that a rank packet alone does not exercise.
    strategy = deepcopy(result["strategy"])
    leaf = next(row for row in strategy["nodes"] if "hypothesis" in row)
    leaf["hypothesis"] = (leaf["hypothesis"] + 1) % len(f["machines"])
    expect("wrong terminal identity", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    next(row for row in strategy["nodes"] if "edges" in row)["edges"].pop()
    expect("missing observed branch", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    next(row for row in strategy["nodes"] if "edges" in row)["edges"][0][1] = strategy["root"]
    expect("strategy cycle", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    strategy["nodes"].append(deepcopy(strategy["nodes"][0]))
    expect("duplicate strategy node", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    strategy["root"] = max(row["node"] for row in strategy["nodes"]) + 1
    expect("strategy root mismatch", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    branch = next(row for row in strategy["nodes"] if row.get("edges"))
    branch["edges"].append(deepcopy(branch["edges"][0]))
    expect("duplicate strategy observation", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    branch = next(row for row in strategy["nodes"] if row.get("edges"))
    branch["edges"][0][1] = max(row["node"] for row in strategy["nodes"]) + 100
    expect("strategy target absent", lambda: replay(f, result["certificate"], strategy))

    strategy = deepcopy(result["strategy"])
    strategy["nodes"].append({"node": max(row["node"] for row in strategy["nodes"]) + 1, "hypothesis": 0})
    expect("unreachable strategy node", lambda: replay(f, result["certificate"], strategy))

    certificate = deepcopy(pair_cert)
    certificate["hypotheses"][1] = certificate["hypotheses"][0]
    expect("pair uses one identity twice", lambda: check_pair(pair_f, certificate))

    certificate = deepcopy(pair_cert)
    certificate["pairs"] = []
    expect("pair relation empty", lambda: check_pair(pair_f, certificate))

    modified_model = deepcopy(pair_f)
    left = pair_cert["hypotheses"][0]
    initial = modified_model["machines"][left]["initial"]
    modified_model["machines"][left]["table"][initial][0][0] = 1 - modified_model["machines"][left]["table"][initial][0][0]
    expect("pair output equality broken", lambda: check_pair(modified_model, pair_cert))

    certificate = deepcopy(pair_cert)
    certificate["pairs"].append(deepcopy(certificate["pairs"][0]))
    expect("duplicate product pair", lambda: check_pair(pair_f, certificate))

    certificate = deepcopy(pair_cert)
    initial_pair = [pair_f["machines"][pair_cert["hypotheses"][0]]["initial"],
                    pair_f["machines"][pair_cert["hypotheses"][1]]["initial"]]
    certificate["pairs"].remove(initial_pair)
    expect("initial product pair omitted", lambda: check_pair(pair_f, certificate))

    certificate = deepcopy(pair_cert)
    certificate["pairs"][0][0] = len(pair_f["machines"][pair_cert["hypotheses"][0]]["table"])
    expect("product pair coordinate out of range", lambda: check_pair(pair_f, certificate))

    modified_model = deepcopy(f)
    modified_model["machines"][0]["table"][0][0][1] = 999
    expect("out of range transition", lambda: check_rank(modified_model, result["certificate"]))

    modified_model = deepcopy(f)
    modified_model["machines"][0]["table"][0].pop()
    expect("partial transition row", lambda: check_rank(modified_model, result["certificate"]))

    modified_model = deepcopy(f)
    modified_model["machines"][0]["table"][0][0][0] = 999
    expect("undeclared observation", lambda: check_rank(modified_model, result["certificate"]))

    return rows


def run_input_rejections(family, certificate):
    """Verify that producer and independent checker reject malformed models."""
    cases = []

    def add(label, edit):
        model = deepcopy(family)
        edit(model)
        producer_rejected = checker_rejected = False
        producer_diagnostic = checker_diagnostic = ""
        try:
            validate(model)
        except ValueError as exc:
            producer_rejected = True
            producer_diagnostic = str(exc)
        try:
            check_rank(model, certificate)
        except InvalidCertificate as exc:
            checker_rejected = True
            checker_diagnostic = str(exc)
        if not (producer_rejected and checker_rejected):
            raise AssertionError("malformed model not rejected by both paths: " + label)
        cases.append({
            "case": label,
            "producer_rejected": True,
            "checker_rejected": True,
            "producer_diagnostic": producer_diagnostic,
            "checker_diagnostic": checker_diagnostic,
        })

    add("empty actions", lambda f: f.__setitem__("actions", []))
    add("duplicate action labels", lambda f: f["actions"].__setitem__(1, f["actions"][0]))
    add("empty observations", lambda f: f.__setitem__("observations", []))
    add("boolean observation", lambda f: f["observations"].__setitem__(0, True))
    add("duplicate observations", lambda f: f["observations"].__setitem__(1, f["observations"][0]))
    add("empty machine family", lambda f: f.__setitem__("machines", []))
    add("boolean initial state", lambda f: f["machines"][0].__setitem__("initial", True))
    add("seventeen states", lambda f: f["machines"][0].__setitem__("table", f["machines"][0]["table"] + [deepcopy(f["machines"][0]["table"][0])] * 16))
    add("malformed transition edge", lambda f: f["machines"][0]["table"][0].__setitem__(0, [0]))
    add("noninteger next state", lambda f: f["machines"][0]["table"][0][0].__setitem__(1, 0.5))
    add("twenty-five hypotheses", lambda f: f.__setitem__("machines", [deepcopy(f["machines"][0]) for _ in range(25)]))
    add("action label is not text", lambda f: f["actions"].__setitem__(0, 7))
    return cases
