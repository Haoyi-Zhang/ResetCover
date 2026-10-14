"""Owned compiled-process study; no third-party target or native prior software.

All controllers know exactly the same complete table and support. The chosen
identity is supplied only to the process and to the final ground-truth check.
No action is chosen from that identity. Outputs, costs and refusals are retained.
"""
import argparse
import hashlib
import json
import platform
import queue
import subprocess
import sys
import threading
import time
from itertools import product
from pathlib import Path
from random import Random

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'src'),str(HERE)]
from checker import check_rank, replay
from generators import binary_encode, graph_family, one_shot, thresholds
from policies import macro_plan
from solver import solve


def require(ok,text):
    if not ok:
        raise RuntimeError(text)


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timed(call):
    start=time.perf_counter(); cpu=time.process_time()
    result=call()
    return result,dict(wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)


def assess(source,support,budget):
    encoded=binary_encode(source)
    plans={}; costs={}
    for method in ('whole','prefix'):
        plans[method],costs[method]=timed(lambda:macro_plan(source,support,budget,method))
    bit,costs['bit']=timed(lambda:solve(encoded,budget,subset=support,seconds=5))
    plans['bit']=bit
    if bit['status']!='unknown':
        _,costs['checking']=timed(lambda:check_rank(encoded,bit['certificate']))
        if bit['status']=='identified':
            replay(encoded,bit['certificate'],bit['strategy'])
            require(bit['depth']<=plans['prefix']['depth']<=plans['whole']['depth'],'policy inclusion')
            source_game=solve(source,budget,subset=support,seconds=5)
            require(source_game['status']=='identified','source preservation')
            tau=(source_game['depth']+1)//2
            ell=plans['whole']['selection_bits']; width=plans['whole']['response_bits']
            require(plans['whole']['depth']==tau*(ell+width+1)-1 if len(support)>1 else plans['whole']['depth']==0,'whole exact cost')
            require(bit['depth']>=tau*(ell+2)-1 if len(support)>1 else bit['depth']==0,'lower symbol cost')
            if width==1:
                require(bit['depth']==plans['whole']['depth'],'binary-response equality')
        else:
            require(plans['whole']['depth'] is None and plans['prefix']['depth'] is None,'failure preservation')
    return encoded,plans,costs


def cases():
    # Complete tiny cohorts, followed by fixed seeds; no improvement filter.
    for values in product(range(2),repeat=6):
        source=one_shot('exhaustive-3x2-binary',[list(values[i:i+2]) for i in (0,2,4)])
        for budget in (0,1,None):
            yield source,list(range(3)),budget
    for values in product(range(3),repeat=3):
        source=one_shot('exhaustive-3x1-ternary',[[v] for v in values])
        for budget in (0,1):
            yield source,list(range(3)),budget
    for seed in range(12):
        rng=Random(seed)
        source=one_shot('seeded-5x3-four-'+str(seed),[[rng.randrange(4) for _ in range(3)] for _ in range(5)])
        yield source,list(range(5)),2


def native_catalog():
    sources=[thresholds(3,'threshold3'),thresholds(5,'threshold5'),
             graph_family(3,[(0,1),(1,2)],'path3'),
             graph_family(3,[(0,1),(0,2),(1,2)],'triangle'),
             one_shot('single-test-five',[[h] for h in range(5)]),
             one_shot('duplicate-control',[[0,1],[0,1],[1,0]])]
    for source in sources:
        n=len(source['machines'])
        for support in (list(range(n)),list(range(n-1))):
            for budget in (0,1,2):
                yield source,support,budget
    # Retain the local depth-cap refusal instead of silently dropping it.
    yield thresholds(9,'threshold9-cap'),list(range(9)),3


def table_text(encoded):
    fields=[len(encoded['machines']),len(encoded['actions'])]
    for m in encoded['machines']:
        fields.extend((len(m['table']),m['initial']))
        for row in m['table']:
            for edge in row:
                fields.extend(edge)
    return ' '.join(map(str,fields))+'\n'


def execute(exe,table,encoded,source,support,budget,method,plan):
    command=[str(exe),str(table),str(support[0]),str(-1 if budget is None else budget)]
    # Caller replaces argv identity; it is never supplied to the controller.
    return command


def interact(command,encoded,source,support,budget,method,plan):
    wall=time.perf_counter(); cpu=time.process_time()
    p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    lines=queue.Queue()
    def reader():
        for line in p.stdout:
            lines.put(line.rstrip('\r\n'))
        lines.put(None)
    thread=threading.Thread(target=reader,daemon=True); thread.start()
    raw=[]; events=[]
    def receive():
        line=lines.get(timeout=5)
        require(line is not None,'premature EOF')
        raw.append(line); return line
    # Independent literal belief updates; not solver successor code.
    belief={h:encoded['machines'][h]['initial'] for h in support}; remaining=budget
    def send(action):
        nonlocal belief,remaining
        require(len(events)<64,'controller step cap')
        p.stdin.write(str(action)+'\n'); p.stdin.flush()
        line=receive(); require(line.startswith('OBS '),'observation format')
        observed=int(line[4:]); before=dict(belief)
        if action==2:
            require(remaining!=0 and observed==0,'reset contract')
            if remaining is not None: remaining-=1
            belief={h:encoded['machines'][h]['initial'] for h in belief}
        else:
            belief={h:encoded['machines'][h]['table'][s][action][1]
                    for h,s in belief.items() if encoded['machines'][h]['table'][s][action][0]==observed}
        require(bool(belief),'actual output outside support')
        events.append(dict(action=action,output=observed,before=before,after=dict(belief),remaining=remaining))
        return observed
    try:
        ready=receive(); require(ready.startswith('READY '),'startup format')
        ready_seconds=time.perf_counter()-wall
        if method=='bit':
            rows={r['node']:r for r in plan['strategy']['nodes']}; node=plan['strategy']['root']
            while 'hypothesis' not in rows[node]:
                row=rows[node]; observed=send(row['action'])
                node=dict(row['edges'])[observed]
            answer=rows[node]['hypothesis']
        else:
            rows={(tuple(r['support']),r['budget']):r for r in plan['rows']}
            code={o:i for i,o in enumerate(source['observations'])}
            while len(belief)>1:
                keep=tuple(sorted(belief)); row=rows[keep,remaining]; action=row['action']
                for k in reversed(range(plan['selection_bits'])):
                    require(send((action>>k)&1)==0,'constant selector')
                possibilities={source['machines'][h]['table'][0][action][0] for h in keep}
                prefix=0
                for k in range(plan['response_bits']):
                    prefix|=send(0)<<k
                    matches=[o for o in possibilities if code[o]&((1<<(k+1))-1)==prefix]
                    require(bool(matches),'response code')
                    if method=='prefix' and len(matches)==1: break
                require(len(matches)==1,'complete query decode')
                if len(belief)>1: send(2)
            answer=next(iter(belief))
        require(set(belief)=={answer},'terminal belief identity')
        require(len(events)<=plan['depth'],'planned worst depth')
        p.stdin.write('stop\n'); p.stdin.flush(); end=receive()
        require(end.startswith('END '),'cost receipt')
        exit_code=p.wait(timeout=5); stderr=p.stderr.read()
        require(exit_code==0 and not stderr,'owned process exit')
        metrics={k:int(v) for k,v in (field.split('=',1) for field in end.split()[1:])}
        require(metrics['steps']==len(events) and metrics['resets']==sum(e['action']==2 for e in events),'native counters')
        return dict(command=command,answer=answer,events=events,stdout=raw,stderr=stderr,exit_code=exit_code,
                    startup_wall_seconds=ready_seconds,harness_wall_seconds=time.perf_counter()-wall,
                    harness_cpu_seconds=time.process_time()-cpu,process_metrics=metrics)
    finally:
        if p.poll() is None: p.kill(); p.wait(timeout=5)
        thread.join(timeout=5)
        p.stdin.close(); p.stdout.close(); p.stderr.close()


def run(out,exe):
    require(not out.exists(),'new output required'); out.mkdir(parents=True)
    exhaustive=[]
    for i,(source,support,budget) in enumerate(cases()):
        encoded,plans,costs=assess(source,support,budget)
        record=dict(id=i,source=source,support=support,budget=budget,
                    status=plans['bit']['status'],reason=plans['bit'].get('reason'),
                    depths={m:plans[m]['depth'] for m in plans},costs=costs)
        exhaustive.append(record)
    dump(out/'exhaustive.json',exhaustive)
    configs=[]; receipts=[]
    for i,(source,support,budget) in enumerate(native_catalog()):
        encoded,plans,costs=assess(source,support,budget)
        folder=out/'inputs'/str(i)
        dump(folder/'source.json',source); dump(folder/'encoded.json',encoded); dump(folder/'plans.json',plans)
        table=folder/'table.txt'; table.write_text(table_text(encoded),encoding='ascii',newline='\n')
        config=dict(id=i,name=source['name'],support=support,budget=budget,status=plans['bit']['status'],
                    reason=plans['bit'].get('reason'),depths={m:plans[m]['depth'] for m in plans},costs=costs,
                    table_sha256=sha(table),exe_sha256=sha(exe))
        configs.append(config)
        if config['status']!='identified': continue
        # Common admitted cohort; same identities and repetitions for all arms.
        for rep in range(2):
            for h in support:
                for method in ('whole','prefix','bit')[rep:]+('whole','prefix','bit')[:rep]:
                    command=execute(exe,table,encoded,source,support,budget,method,plans[method]); command[2]=str(h)
                    result=interact(command,encoded,source,support,budget,method,plans[method])
                    require(result['answer']==h,'ground truth only after controller completion')
                    result.update(config=i,method=method,repeat=rep,identity=h)
                    receipts.append(result)
                    dump(out/'traces'/(str(len(receipts)-1)+'.json'),result)
        for method in ('whole','prefix','bit'):
            actual=max(len(r['events']) for r in receipts if r['config']==i and r['method']==method)
            require(actual==config['depths'][method],'all identities attain predicted worst depth')
    dump(out/'configs.json',configs)
    summary=dict(exhaustive_cases=len(exhaustive),configs=len(configs),
                 statuses={s:sum(c['status']==s for c in configs) for s in ('identified','ambiguous','unknown')},
                 process_runs=len(receipts),events=sum(len(r['events']) for r in receipts),
                 mismatch_count=0,optimized=not __debug__,python=sys.version,executable=sys.executable,
                 platform=platform.platform(),compiler_executable=str(exe),exe_sha256=sha(exe),
                 scope='Compiled owned .NET Framework managed Windows process, not AOT native, CAMUS, Fractal or third-party execution.',
                 exhaustive_statuses={s:sum(c['status']==s for c in exhaustive) for s in ('identified','ambiguous','unknown')},
                 clocks={k:vars(time.get_clock_info(k)) for k in ('perf_counter','process_time')})
    dump(out/'summary.json',summary); print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--exe',type=Path,required=True)
    args=ap.parse_args(); run(args.out.resolve(),args.exe.resolve())
