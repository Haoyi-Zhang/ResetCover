"""Standalone certificate checker; intentionally no imports from producer/model.

Trust boundary: Python integer/list semantics, this file, and the explicit input.
Not a proof-assistant formalization, secure parser, or independent human review.
"""
from __future__ import annotations

class InvalidCertificate(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise InvalidCertificate(message)

def raw_model(f):
    require(type(f) is dict, "model object")
    ms=f.get("machines"); aa=f.get("actions"); oo=f.get("observations")
    require(type(ms) is list and 1<=len(ms)<=24, "hypothesis bounds")
    require(type(aa) is list and 1<=len(aa)<=8, "action bounds")
    require(all(type(a) is str and 0<len(a)<=80 for a in aa) and len(set(aa))==len(aa), "action labels")
    require(type(oo) is list and 1<=len(oo)<=8 and all(type(o) is int for o in oo) and len(set(oo))==len(oo), "observation bounds")
    for m in ms:
        require(type(m) is dict, "machine object")
        t=m.get("table"); s=m.get("initial")
        require(type(t) is list and 1<=len(t)<=16 and type(s) is int and 0<=s<len(t), "machine bounds")
        for row in t:
            require(type(row) is list and len(row)==len(aa), "totality")
            for edge in row:
                require(type(edge) is list and len(edge)==2, "edge shape")
                require(type(edge[0]) is int and edge[0] in oo and type(edge[1]) is int and 0<=edge[1]<len(t), "edge bounds")
    return ms, len(aa)

def check_rank(f, c):
    ms, ac=raw_model(f); n=len(ms)
    require(type(c) is dict and c.get("kind")=="rank_trap", "certificate kind")
    rows=c.get("rows"); r=c.get("resets"); keep=c.get("support")
    require(r is None or type(r) is int and 0<=r<=12, "reset budget")
    require(type(keep) is list and keep and all(type(h) is int and 0<=h<n for h in keep) and len(set(keep))==len(keep), "support")
    require(type(rows) is list and 1<=len(rows)<=250000, "certificate size")
    require(type(c.get("root")) is int and 0<=c["root"]<len(rows), "root index")
    lookup={}
    for i, row in enumerate(rows):
        require(type(row) is dict, "row object")
        b=row.get("belief"); rr=row.get("budget"); k=row.get("rank"); a=row.get("action")
        require(type(b) is list and len(b)==n and all(type(s) is int and -1<=s<len(ms[h]["table"]) for h,s in enumerate(b)), "belief shape")
        require(any(s>=0 for s in b) and all(s<0 or h in keep for h,s in enumerate(b)), "belief support")
        require(type(rr) is int and (rr==-1 if r is None else 0<=rr<=r), "layer range")
        require(k is None or type(k) is int and 0<=k<len(rows), "rank range")
        require(a is None or type(a) is int and 0<=a<=ac, "action range")
        key=(tuple(b),rr); require(key not in lookup, "duplicate belief"); lookup[key]=i
        singleton=sum(s>=0 for s in b)==1
        require((k==0)==singleton, "terminal rank iff singleton")
        if singleton or k is None:
            require(a is None, "terminal/trap choice")
    initial=(tuple(m["initial"] if h in keep else -1 for h,m in enumerate(ms)), -1 if r is None else r)
    root=rows[c["root"]]
    require((tuple(root["belief"]),root["budget"])==initial, "root semantics")
    obligations=0; all_succ=[]
    for row in rows:
        b=row["belief"]; rr=row["budget"]; k=row["rank"]; successors={}
        if k!=0:
            for a in range(ac):
                by_output={}
                for h,s in enumerate(b):
                    if s>=0:
                        observation,target=ms[h]["table"][s][a]
                        if observation not in by_output:
                            by_output[observation]=[-1]*n
                        by_output[observation][h]=target
                dests=[]
                for o in sorted(by_output):
                    key=(tuple(by_output[o]),rr); require(key in lookup, "ordinary successor omitted")
                    dests.append(lookup[key]); obligations+=1
                successors[a]=dests
            if rr!=0:
                v=tuple(ms[h]["initial"] if s>=0 else -1 for h,s in enumerate(b))
                key=(v,rr if rr==-1 else rr-1); require(key in lookup,"reset successor omitted")
                successors[ac]=[lookup[key]]; obligations+=1
            require(obligations<=2000000, "checker obligation cap")
            if k is None:
                require(all(any(rows[j]["rank"] is None for j in js) for js in successors.values()), "trap not closed adversarially")
            else:
                require(row["action"] in successors, "unavailable chosen action")
                chosen=successors[row["action"]]
                require(all(rows[j]["rank"] is not None and rows[j]["rank"]<=k-1 for j in chosen), "upper rank")
                require(all(any(rows[j]["rank"] is None or rows[j]["rank"]>=k-1 for j in js) for js in successors.values()), "lower rank")
        all_succ.append(successors)
    # The packet is a reachable graph, not an arbitrary collection of distractions.
    reached={c["root"]}; todo=[c["root"]]
    for i in todo:
        for js in all_succ[i].values():
            for j in js:
                if j not in reached:
                    reached.add(j); todo.append(j)
    require(len(reached)==len(rows), "unreachable extra row")
    return {"depth": root["rank"], "status": "ambiguous" if root["rank"] is None else "identified", "obligations": obligations}

def check_pair(f,c):
    ms,ac=raw_model(f)
    require(type(c) is dict and c.get("kind")=="rooted_pair", "pair kind")
    hs=c.get("hypotheses"); pp=c.get("pairs")
    require(type(hs) is list and len(hs)==2 and all(type(h) is int and 0<=h<len(ms) for h in hs) and hs[0]!=hs[1], "distinct hypotheses")
    i,j=hs
    require(type(pp) is list and 1<=len(pp)<=256, "pair size")
    for p in pp:
        require(type(p) is list and len(p)==2 and all(type(s) is int for s in p) and 0<=p[0]<len(ms[i]["table"]) and 0<=p[1]<len(ms[j]["table"]), "pair coordinates")
    relation={tuple(p) for p in pp}; require(len(relation)==len(pp), "duplicate relation")
    require((ms[i]["initial"],ms[j]["initial"]) in relation, "initial/reset pair absent")
    obligations=0
    for x,y in relation:
        for a in range(ac):
            o,p=ms[i]["table"][x][a]; z,q=ms[j]["table"][y][a]
            require(o==z and (p,q) in relation, "pair output or closure"); obligations+=1
    return {"status":"ambiguous_unlimited", "obligations":obligations+len(relation)}

def replay(f,c,strategy):
    ms,ac=raw_model(f)
    require(type(strategy) is dict and type(strategy.get("nodes")) is list, "strategy object")
    nodes={}
    for row in strategy["nodes"]:
        require(type(row) is dict and type(row.get("node")) is int and row["node"] not in nodes, "DAG node")
        nodes[row["node"]]=row
    require(strategy.get("root")==c["root"] and strategy["root"] in nodes, "DAG root")
    worst=0; obligations=0; used=set()
    for h in c["support"]:
        s=ms[h]["initial"]; i=strategy["root"]; b=c["resets"]; seen=set(); steps=0
        while True:
            require(i in nodes and i not in seen,"strategy missing node or cycle")
            seen.add(i); used.add(i); row=nodes[i]
            if "hypothesis" in row:
                require(type(row["hypothesis"]) is int and row["hypothesis"]==h,"incorrect terminal identity"); break
            a=row.get("action")
            require(type(a) is int and 0<=a<=ac,"DAG action")
            if a==ac:
                require(b is None or b>0,"DAG reset budget")
                if b is not None: b-=1
                o=0; s=ms[h]["initial"]
            else:
                o,s=ms[h]["table"][s][a]
            edges=row.get("edges"); require(type(edges) is list,"DAG edges")
            require(all(type(e) is list and len(e)==2 and all(type(z) is int for z in e) for e in edges),"DAG edge shape")
            require(len({e[0] for e in edges})==len(edges),"DAG duplicate observation")
            matches=[j for z,j in edges if z==o]; require(len(matches)==1,"DAG branch missing")
            i=matches[0]; steps+=1; obligations+=1
            require(steps<=len(c["rows"]),"DAG length")
        worst=max(worst,steps)
    require(used==set(nodes),"unreachable DAG node")
    require(worst==c["rows"][c["root"]]["rank"],"strategy not matching certified optimum")
    return {"worst_depth":worst,"obligations":obligations}
