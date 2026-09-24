"""Transparent mathematical constructions; none are hardware measurements."""
from __future__ import annotations
from copy import deepcopy
from itertools import combinations, product
from random import Random
from model import validate

SOURCE = "https://people.csail.mit.edu/mengjia/data/2026.SP.fractal.pdf"

def one_shot(name, table, labels=None, metadata=None):
    """table[h][a] is the sole informative response in each reset epoch."""
    n=len(table); ac=len(table[0])
    f={"name":name,"actions":labels or [f"test:{a}" for a in range(ac)],
       "observations":sorted({0}|{o for row in table for o in row}),
       "machines":[{"initial":0,"table":[[[o,1] for o in row],[[0,1] for _ in row]]} for row in table],
       "metadata":metadata or {"kind":"generated_one_shot"}}
    validate(f); return f

def graph_family(vertices, edges, name="graph"):
    if not edges:
        raise ValueError("the graph reduction requires at least one edge")
    # Marker forces anchors 0 and 1. Each edge has two disjoint collision pairs.
    table=[[0 if h in (0,1) else h] +
           [0 if h in (0,u+2) else 1 if h in (1,v+2) else h for u,v in edges]
           for h in range(vertices+2)]
    return one_shot(name,table,["marker"]+[f"edge:{u}-{v}" for u,v in edges],
                    {"kind":"graph_reduction","vertices":vertices,"edges":[list(e) for e in edges]})

def binary_encode(f, name=None):
    """Serialize a one-shot partition table. Reset count, not symbol depth, is preserved."""
    ac=len(f["actions"]); symbols=f["observations"]
    ell=max(1,(ac-1).bit_length()); width=max(1,(len(symbols)-1).bit_length())
    encoding={o:tuple((i>>k)&1 for k in range(width)) for i,o in enumerate(symbols)}
    prefixes=[tuple(bits) for d in range(ell) for bits in product((0,1),repeat=d)]
    machines=[]
    for m in f["machines"]:
        assert m["initial"]==0 and len(m["table"])==2
        assert all(edge==[0,1] for edge in m["table"][1])
        codes=[encoding[edge[0]] for edge in m["table"][0]]
        suffixes=sorted({c[k:] for c in codes for k in range(width)},key=lambda x:(len(x),x))
        ids={('select',p):i for i,p in enumerate(prefixes)}
        ids.update({('read',c):len(prefixes)+i for i,c in enumerate(suffixes)})
        sink=len(ids); rows=[]
        for p in prefixes:
            row=[]
            for bit in (0,1):
                extended=p+(bit,)
                if len(extended)<ell:
                    dest=ids['select',extended]
                else:
                    a=0
                    for b in extended: a=2*a+b
                    dest=ids['read',codes[a]] if a<ac else sink
                row.append([0,dest])
            rows.append(row)
        for c in suffixes:
            rows.append([[c[0],ids['read',c[1:]] if len(c)>1 else sink],[0,sink]])
        rows.append([[0,sink],[0,sink]])
        machines.append({"initial":0,"table":rows})
    result={"name":name or f["name"]+"-binary","actions":["bit:0","bit:1"],"observations":[0,1],
            "machines":machines,"metadata":{"kind":"binary_serialization","source_family":f["name"],
            "selection_bits":ell,"response_bits":width,"response_order":"least-significant first",
            "read_input":0,"abort_input":1,"invalid_selection":"all-zero spent state"}}
    validate(result); return result

def thresholds(n,name):
    return one_shot(name,[[int(h>cut) for cut in range(n-1)] for h in range(n)],
                    [f"cut:{cut}" for cut in range(n-1)],{"kind":"ordered_thresholds","hypotheses":n})

def private_pairs(m,name):
    return one_shot(name,[[0 if h//2==a else h+1 for a in range(m)] for h in range(2*m)],
                    metadata={"kind":"private_pair_collisions","pairs":m})

def register_models(labels):
    machines=[]
    # Shared bit; two private bits; a bit cleared on domain change; destructive reads.
    for mode in range(4):
        ns=[2,4,5,2][mode]; rows=[]
        for s in range(ns):
            row=[]
            for a in range(4):
                domain=a//2; read=a%2
                if mode==0:
                    o=s if read else 0; t=s if read else 1
                elif mode==1:
                    o=(s>>domain)&1 if read else 0; t=s if read else s|(1<<domain)
                elif mode==2:
                    old_domain=-1 if s==0 else (s-1)//2
                    val=0 if s==0 else (s-1)%2
                    if old_domain!=domain: val=0
                    o=val if read else 0; t=1+2*domain+(val if read else 1)
                else:
                    o=s if read else 0; t=0 if read else 1
                row.append([o,t])
            rows.append(row)
        machines.append({"initial":0,"table":rows})
    return {"name":"register-schema","actions":labels,"observations":[0,1],"machines":machines}

def campaign():
    result=[]
    schemas=[("privilege",["prepare:user","observe:user","prepare:kernel","observe:kernel"],"Sections 4.1-4.4: privilege labels"),
             ("address-space",["prepare:asid0","observe:asid0","prepare:asid1","observe:asid1"],"Section 4.4.1: ASID labels"),
             ("mapping",["prepare:alias0","observe:alias0","prepare:alias1","observe:alias1"],"Sections 5.2 and 5.4.3: mapping labels"),
             ("schedule",["step:task0","observe:task0","step:task1","observe:task1"],"Sections 4.3 and 5.4.1: task-order labels")]
    for schema,labels,passage in schemas:
        for variant in range(4):
            name=f"schema-{schema}-{variant+1}"
            meta={"kind":"public_schema_toy","schema":schema,"variant":variant+1,"source":SOURCE,"passage":passage,
                  "provenance":"Only the vocabulary is source-derived. All states, outputs and transitions are authored mathematical fixtures; no traces.",
                  "semantic_archetype":["four bit-storage hypotheses","single-domain restriction","destructive threshold, zero reset","destructive threshold, one reset"][variant]}
            if variant<2:
                f=register_models(labels); f["name"]=name; f["metadata"]=meta
                if variant==1:
                    f["actions"]=labels[:2]
                    for m in f["machines"]:
                        m["table"]=[row[:2] for row in m["table"]]
                r=None
            else:
                f=thresholds(3,name); f["actions"]=[labels[1],labels[3]]; f["metadata"]=meta
                r=variant-2
            result.append((f,r,"schema"))
    graphs=[(3,[(0,1),(1,2)],"path-three"),(3,[(0,1),(0,2),(1,2)],"triangle"),
            (4,[(0,1),(1,2),(2,3)],"path-four"),(4,list(combinations(range(4),2)),"complete-four")]
    for n,edges,label in graphs:
        f=graph_family(n,edges,f"graph-{label}")
        for encode in (False,True):
            g=binary_encode(f) if encode else f
            for r in (0,1):
                h=deepcopy(g); h["name"]+=f"-budget-{r}"
                result.append((h,r,"generated"))
    for n,r in ((3,0),(5,1),(9,2)):
        for rr in (r,r+1):
            f=thresholds(n,f"threshold-{n}-budget-{rr}"); result.append((f,rr,"generated"))
    for m in (2,3):
        for r in (0,1):
            f=private_pairs(m,f"private-pairs-{m}-budget-{r}"); result.append((f,r,"generated"))
    for seed in (104729,130363,155921):
        rng=Random(seed)
        ms=[{"initial":0,"table":[[[rng.randrange(2),rng.randrange(3)] for _ in range(2)] for _ in range(3)]} for _ in range(4)]
        for duplicate in (False,True):
            mm=deepcopy(ms)
            if duplicate: mm[-1]=deepcopy(mm[0])
            f={"name":f"stateful-{seed}-"+("duplicate" if duplicate else "distinct-table"),"actions":["a","b"],"observations":[0,1],"machines":mm,
               "metadata":{"kind":"seeded_stateful","seed":seed,"duplicate_control":duplicate,"distribution":"independent uniform output and next-state cells"}}
            result.append((f,None,"generated"))
    assert len(result)==48
    for f,_,_ in result: validate(f)
    return result
