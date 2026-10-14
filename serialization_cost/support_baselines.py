"""Owned exhaustive same-information minimum zero-reset support baselines.

Direct oracle, maximal-identifiable-set duality and the existing cover transform
all consume the same table and return minimum cardinality, not just minimality.
This is neither CAMUS execution nor a new transversal algorithm.
"""
import argparse
import json
import sys
import time
from itertools import combinations
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'src'),str(HERE)]
from generators import graph_family, one_shot, private_pairs
from obstructions import cover_transform
from policies import dimensions


def need(ok,text):
    if not ok: raise RuntimeError(text)


def ordered(n):
    for size in range(n+1):
        yield from combinations(range(n),size)


def minimum(source,method):
    dimensions(source)  # shared complete-input admission; included in costs
    table=[[edge[0] for edge in m['table'][0]] for m in source['machines']]
    n=len(table); counts=dict(predicate_calls=0,table_cells_examined=0,selection_tests=0,duality_subset_comparisons=0)
    def failing(keep):
        counts['predicate_calls']+=1
        if len(keep)<2: return False
        for a in range(len(table[0])):
            seen=set(); collision=False
            for h in keep:
                counts['table_cells_examined']+=1
                o=table[h][a]
                if o in seen: collision=True; break
                seen.add(o)
            if not collision: return False
        return True
    answer=None; maximal=[]; clauses=[]
    if method=='direct':
        for keep in ordered(n):
            counts['selection_tests']+=1
            if failing(keep): answer=list(keep); break
    elif method=='mss_dual':
        identifiable=[frozenset(keep) for keep in ordered(n) if not failing(keep)]
        for keep in identifiable:
            is_maximal=True
            for other in identifiable:
                counts['duality_subset_comparisons']+=1
                if keep<other: is_maximal=False; break
            if is_maximal: maximal.append(keep)
        clauses=[set(range(n))-set(keep) for keep in maximal]
        for keep in ordered(n):
            counts['selection_tests']+=1
            if all(set(keep)&clause for clause in clauses): answer=list(keep); break
    elif method=='cover':
        transformed=cover_transform(table)
        if transformed is not None:
            forced,edges=transformed; residual=[h for h in range(n) if h not in forced]
            for indices in ordered(len(residual)):
                cover={residual[i] for i in indices}; counts['selection_tests']+=1
                if all(u in cover or v in cover for u,v in edges):
                    answer=sorted(set(forced)|cover); break
    else: raise ValueError('method')
    need(failing(answer) if answer is not None else not failing(tuple(range(n))),'returned witness correctness')
    return dict(support=answer,cardinality=None if answer is None else len(answer),counts=counts,
                maximal_identifiable=[sorted(k) for k in maximal],dual_clauses=[sorted(k) for k in clauses])


def cases():
    for n in (2,3,4):
        edges=list(combinations(range(n),2))
        for mask in range(1,1<<len(edges)):
            yield graph_family(n,[e for i,e in enumerate(edges) if mask>>i&1],'graph-'+str(n)+'-'+str(mask))
    for m in (1,2,3): yield private_pairs(m,'private-'+str(m))
    yield one_shot('injective-negative',[[h] for h in range(5)])


def run(out,repetitions):
    need(not out.exists(),'new output required'); out.mkdir(parents=True)
    records=[]
    for index,source in enumerate(cases()):
        methods={}
        for method in ('direct','mss_dual','cover'):
            samples=[]; first=None
            for _ in range(repetitions):
                start=time.perf_counter(); cpu=time.process_time(); result=minimum(source,method)
                samples.append(dict(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu))
                if first is None: first=result
                need(result==first,'repeat semantic agreement')
            methods[method]=dict(result=first,samples=samples)
        need(len({m['result']['cardinality'] for m in methods.values()})==1,'equal minimum-cardinality guarantee')
        records.append(dict(id=index,source=source,methods=methods))
    need(len(records)==75,'complete declared cohort')
    report=dict(cases=len(records),repetitions=repetitions,method_invocations=len(records)*3*repetitions,
                mismatches=0,optimized=not __debug__,python=sys.version,
                scope='71 complete labeled nonempty graphs on 2-4 vertices, 3 private-pair controls and one injective control. Owned exhaustive baselines, not native CAMUS, general adaptive-game or scalability evaluation.',
                totals={method:dict(wall_seconds=sum(s['wall_seconds'] for r in records for s in r['methods'][method]['samples']),
                                   cpu_seconds=sum(s['cpu_seconds'] for r in records for s in r['methods'][method]['samples']),
                                   single_pass_predicate_calls=sum(r['methods'][method]['result']['counts']['predicate_calls'] for r in records),
                                   single_pass_selection_tests=sum(r['methods'][method]['result']['counts']['selection_tests'] for r in records))
                        for method in ('direct','mss_dual','cover')})
    for name,value in (('records.json',records),('summary.json',report)):
        (out/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--repetitions',type=int,default=100)
    args=ap.parse_args(); need(1<=args.repetitions<=100,'repetition bound'); run(args.out.resolve(),args.repetitions)
