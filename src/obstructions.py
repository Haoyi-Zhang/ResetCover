"""One-shot obstruction antichains and the two-pair/vertex-cover equivalence."""
from itertools import combinations, product

def minimal(sets):
    result=[]
    for s in sorted(set(sets),key=lambda x:(len(x),tuple(sorted(x)))):
        if not any(t<=s for t in result):
            result.append(s)
    return result

def partitions(table):
    n=len(table)
    return [[frozenset(h for h in range(n) if table[h][a]==o)
             for o in sorted({table[h][a] for h in range(n)})]
            for a in range(len(table[0]))]

def antichains(table, tests):
    """All inclusion-minimal supports not identifiable in at most `tests` queries.

    Exponential construction, only used for tiny finite checks. No efficiency claim.
    """
    if type(tests) is not int or not 0<=tests<=4 or len(table)>9:
        raise ValueError("bounded antichain check: <=9 hypotheses, <=4 tests")
    current=[frozenset(p) for p in combinations(range(len(table)),2)]
    parts=partitions(table); joins=0
    for _ in range(tests):
        combined=[frozenset()]
        for blocks in parts:
            options=[u for u in current if any(u<=b for b in blocks)]
            joins+=len(combined)*len(options)
            if joins>250000:
                raise ValueError("antichain join cap")
            combined=minimal([s|u for s in combined for u in options])
            if not combined:
                break
        current=combined
    return current, joins

def cover_transform(table):
    """Return forced vertices and an induced vertex-cover graph.

    None means that an injective test identifies every subset immediately.
    Every non-singleton observation block must have size two; at most two per test.
    """
    forced=set(); edges=set()
    for blocks in partitions(table):
        ambiguous=[b for b in blocks if len(b)>1]
        if not ambiguous:
            return None
        if len(ambiguous)>2 or any(len(b)!=2 for b in ambiguous):
            raise ValueError("outside two-pair collision class")
        if len(ambiguous)==1:
            forced.update(ambiguous[0])
        else:
            p,q=ambiguous
            edges.update(tuple(sorted((u,v))) for u in p for v in q)
    remaining=sorted(e for e in edges if not (set(e)&forced))
    return sorted(forced),remaining

def minimum_cover(vertices, edges):
    """Tiny exact cardinality oracle: exhaustive subsets, not the game algorithm."""
    vv=list(vertices)
    for k in range(len(vv)+1):
        for xs in combinations(vv,k):
            ss=set(xs)
            if all(u in ss or v in ss for u,v in edges):
                return list(xs)
    raise AssertionError("a finite graph always has a vertex cover")
