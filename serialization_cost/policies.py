"""Exact whole-result and ordinary per-query prefix baselines.

Both consume the same known source table, retained support, reset budget and
fixed binary codes as the bit-level game. No producer/transition import. These
are standard decision-tree policies, not a new algorithm or CAMUS execution.
"""
from functools import lru_cache
from model import validate


def dimensions(family):
    validate(family)
    for m in family['machines']:
        if m['initial']!=0 or len(m['table'])!=2 or any(e[1]!=1 for e in m['table'][0]) or any(e!=[0,1] for e in m['table'][1]):
            raise ValueError('canonical one-shot source required')
    m=len(family['actions']); q=len(family['observations'])
    return max(1,(m-1).bit_length()),max(1,(q-1).bit_length())


def macro_plan(family,support,resets,mode):
    if mode not in ('whole','prefix'):
        raise ValueError('whole or prefix mode required')
    ell,width=dimensions(family)
    ms=family['machines']; n=len(ms)
    support=tuple(sorted(support))
    if not support or any(type(h) is not int or not 0<=h<n for h in support) or len(set(support))!=len(support):
        raise ValueError('nonempty distinct support required')
    if resets is not None and (type(resets) is not int or not 0<=resets<=12):
        raise ValueError('reset budget outside local domain')
    code={o:i for i,o in enumerate(family['observations'])}
    rows={}; obligations=0

    @lru_cache(None)
    def visit(keep,budget):
        nonlocal obligations
        if len(keep)==1:
            rows[keep,budget]=dict(support=list(keep),budget=budget,value=0,action=None,branches=[])
            return 0
        options=[]
        for action in range(len(family['actions'])):
            cells={}
            for h in keep:
                cells.setdefault(ms[h]['table'][0][action][0],[]).append(h)
            if len(cells)==1:
                continue
            branches=[]; worst=0; feasible=True
            for output,after in sorted(cells.items()):
                obligations+=1
                bits=width
                if mode=='prefix':
                    bits=next(d for d in range(1,width+1)
                              if all(o==output or (code[o]&((1<<d)-1))!=(code[output]&((1<<d)-1)) for o in cells))
                after=tuple(after)
                child=0
                if len(after)>1:
                    if budget==0:
                        feasible=False; break
                    child=visit(after,None if budget is None else budget-1)
                    if child is None:
                        feasible=False; break
                total=ell+bits+(1+child if len(after)>1 else 0)
                worst=max(worst,total)
                branches.append(dict(output=output,support=list(after),read_bits=bits,total_depth=total))
            if feasible:
                options.append((worst,action,branches))
        if not options:
            row=dict(support=list(keep),budget=budget,value=None,action=None,branches=[])
        else:
            value,action,branches=min(options,key=lambda x:(x[0],x[1]))
            row=dict(support=list(keep),budget=budget,value=value,action=action,branches=branches)
        rows[keep,budget]=row
        return row['value']

    value=visit(support,resets)
    return dict(mode=mode,depth=value,selection_bits=ell,response_bits=width,
                support=list(support),resets=resets,branch_obligations=obligations,
                rows=sorted(rows.values(),key=lambda r:(len(r['support']),r['support'],-1 if r['budget'] is None else r['budget'])))
