"""Bounded belief-game enumerator and certificate producer.

Each hypothesis has its own state coordinate; identity is never quotiented away.
The verifier in checker.py neither imports this module nor uses its successors.
"""
from __future__ import annotations
from collections import deque
from time import monotonic
from model import validate

class BoundExceeded(RuntimeError):
    pass

def solve(f: dict, resets: int | None, subset=None, *, node_cap=250000,
          obligation_cap=2000000, depth_cap=12, seconds=180.0) -> dict:
    validate(f)
    if type(depth_cap) is not int or not 0 <= depth_cap <= 12:
        raise ValueError("depth cap must be an integer in [0,12]")
    if resets is not None and (type(resets) is not int or not 0 <= resets <= 12):
        raise ValueError("resets must be null (unlimited) or an integer in [0,12]")
    if type(node_cap) is not int or not 1 <= node_cap <= 250000 or type(obligation_cap) is not int or not 1 <= obligation_cap <= 2000000:
        raise ValueError("node cap must be in [1,250000]; obligation cap in [1,2000000]")
    ms = f["machines"]; n = len(ms); a_count = len(f["actions"])
    keep = tuple(range(n)) if subset is None else tuple(subset)
    if not keep or len(set(keep)) != len(keep) or any(type(h) is not int or not 0 <= h < n for h in keep):
        raise ValueError("invalid nonempty hypothesis support")
    from math import isfinite
    if type(seconds) not in (int, float) or not isfinite(float(seconds)) or not 0 < float(seconds) <= 180:
        raise ValueError("positive finite time bound at most 180 seconds required")
    deadline = monotonic() + float(seconds)
    initial = tuple(m["initial"] if h in keep else -1 for h, m in enumerate(ms))
    root = (initial, -1 if resets is None else resets)
    nodes = [root]; index = {root: 0}; actions = []; obligations = 0
    try:
        for b, r in nodes:
            if monotonic() > deadline:
                raise BoundExceeded("time")
            local = []
            if sum(s >= 0 for s in b) > 1:
                candidates = []
                for a in range(a_count):
                    branches = {}
                    for h, s in enumerate(b):
                        if s >= 0:
                            o, t = ms[h]["table"][s][a]
                            branches.setdefault(o, [-1] * n)[h] = t
                    candidates.append((a, [(o, (tuple(v), r)) for o, v in sorted(branches.items())]))
                if r != 0:
                    dest = tuple(ms[h]["initial"] if s >= 0 else -1 for h, s in enumerate(b))
                    candidates.append((a_count, [(0, (dest, r if r == -1 else r - 1))]))
                for a, branches in candidates:
                    succ = []
                    for o, key in branches:
                        obligations += 1
                        if obligations > obligation_cap:
                            raise BoundExceeded("obligation")
                        if key not in index:
                            if len(nodes) >= node_cap:
                                raise BoundExceeded("node")
                            index[key] = len(nodes); nodes.append(key)
                        succ.append((o, index[key]))
                    local.append((a, succ))
            actions.append(local)
        # Synchronous attractor layers implement minimax symbol depth exactly.
        rank = [0 if sum(s >= 0 for s in b) == 1 else None for b, _ in nodes]
        choices = [None] * len(nodes)
        d = 0
        while True:
            if monotonic() > deadline:
                raise BoundExceeded("time")
            d += 1; fresh = []
            for i, local in enumerate(actions):
                if rank[i] is None:
                    for a, succ in local:
                        if all(rank[j] is not None and rank[j] < d for _, j in succ):
                            fresh.append((i, a)); break
            if not fresh:
                break
            for i, a in fresh:
                rank[i] = d; choices[i] = a
        if rank[0] is not None and rank[0] > depth_cap:
            return {"status": "unknown", "reason": "depth", "nodes": len(nodes),
                    "transition_obligations": obligations, "depth": None}
        cert = {"kind": "rank_trap", "root": 0, "resets": resets, "support": list(keep),
                "rows": [{"belief": list(b), "budget": r, "rank": rank[i], "action": choices[i]}
                         for i, (b, r) in enumerate(nodes)]}
        strategy = None
        if rank[0] is not None:
            seen = {0}; todo = deque([0]); dag = []
            while todo:
                i = todo.popleft()
                if rank[i] == 0:
                    h = next(h for h, s in enumerate(nodes[i][0]) if s >= 0)
                    dag.append({"node": i, "hypothesis": h})
                else:
                    edges = next(s for a, s in actions[i] if a == choices[i])
                    dag.append({"node": i, "action": choices[i], "edges": [[o,j] for o,j in edges]})
                    for _, j in edges:
                        if j not in seen:
                            seen.add(j); todo.append(j)
            strategy = {"root": 0, "nodes": sorted(dag, key=lambda x:x["node"])}
        return {"status": "identified" if rank[0] is not None else "ambiguous",
                "depth": rank[0], "nodes": len(nodes), "transition_obligations": obligations,
                "certificate": cert, "strategy": strategy}
    except BoundExceeded as exc:
        return {"status": "unknown", "reason": str(exc), "nodes": len(nodes),
                "transition_obligations": obligations, "depth": None}

def pair_witness(f: dict, stats=None):
    """Return one rooted bisimulation of distinct hypotheses, or None."""
    validate(f); ms = f["machines"]
    if stats is not None:
        stats["pair_obligations"] = 0
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            start = (ms[i]["initial"], ms[j]["initial"])
            pairs = [start]; seen = {start}; unequal = False
            for p, q in pairs:
                for a in range(len(f["actions"])):
                    if stats is not None:
                        stats["pair_obligations"] += 1
                    o, x = ms[i]["table"][p][a]; z, y = ms[j]["table"][q][a]
                    if o != z:
                        unequal = True; break
                    if (x,y) not in seen:
                        seen.add((x,y)); pairs.append((x,y))
                if unequal:
                    break
            if not unequal:
                return {"kind": "rooted_pair", "hypotheses": [i,j], "pairs": [list(p) for p in sorted(pairs)]}
    return None
