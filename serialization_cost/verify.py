"""Receipt verifier and descriptive statistics; reads raw inputs and outputs.

No solver imports for trace reconstruction. Exact optimality is additionally
checked through the separate raw-input rank checker, not inferred from counts.
"""
import argparse
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'src'))
from checker import check_rank, replay


def need(ok,text):
    if not ok: raise RuntimeError(text)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    configs=read(root/'configs.json'); summaries=read(root/'summary.json')
    traces=[read(p) for p in sorted((root/'traces').glob('*.json'),key=lambda p:int(p.stem))]
    need(len(configs)==37 and len(traces)==528,'cohort cardinality')
    seen=set(); events=0
    for c in configs:
        folder=root/'inputs'/str(c['id']); f=read(folder/'encoded.json'); plans=read(folder/'plans.json')
        table=[int(x) for x in (folder/'table.txt').read_text(encoding='ascii').split()]
        expected=[len(f['machines']),len(f['actions'])]
        for m in f['machines']:
            expected.extend((len(m['table']),m['initial']))
            for row in m['table']:
                for edge in row: expected.extend(edge)
        need(expected==table and digest(folder/'table.txt')==c['table_sha256'],'table binding')
        bit=plans['bit']
        if bit['status']!='unknown':
            checked=check_rank(f,bit['certificate'])
            need(checked['status']==c['status'] and checked['depth']==c['depths']['bit'],'rank receipt binding')
            if bit['status']=='identified': replay(f,bit['certificate'],bit['strategy'])
        own=[r for r in traces if r['config']==c['id']]
        if c['status']!='identified':
            need(not own,'negative/unknown execution must not be admitted'); continue
        for method in ('whole','prefix','bit'):
            arm=[r for r in own if r['method']==method]
            need({(r['repeat'],r['identity']) for r in arm}=={(rep,h) for rep in (0,1) for h in c['support']},'same-info common identity cohort')
            need(len(arm)==2*len(c['support']),'no duplicate/missing runs')
            need(max(len(r['events']) for r in arm)==c['depths'][method],'worst-depth attainment')
        for r in own:
            key=(r['config'],r['method'],r['repeat'],r['identity']); need(key not in seen,'duplicate receipt'); seen.add(key)
            identity=r['identity']; state=f['machines'][identity]['initial']; budget=c['budget']
            belief={h:f['machines'][h]['initial'] for h in c['support']}
            need(r['exit_code']==0 and r['stderr']=='','process exit')
            need(int(r['command'][2])==identity and int(r['command'][3])==(-1 if budget is None else budget),'argv identity/budget')
            need(len(r['stdout'])==len(r['events'])+2,'stdout line count')
            for i,e in enumerate(r['events']):
                need({int(h):s for h,s in e['before'].items()}==belief,'before belief')
                a=e['action']; need(type(a) is int and 0<=a<=2,'action domain')
                if a==2:
                    need(budget!=0,'reset budget'); state=f['machines'][identity]['initial']; out=0
                    if budget is not None: budget-=1
                    belief={h:f['machines'][h]['initial'] for h in belief}
                else:
                    out,state=f['machines'][identity]['table'][state][a]
                    belief={h:f['machines'][h]['table'][s][a][1] for h,s in belief.items() if f['machines'][h]['table'][s][a][0]==out}
                need(out==e['output'] and r['stdout'][i+1]=='OBS '+str(out),'literal native transition')
                need(e['remaining']==budget and {int(h):s for h,s in e['after'].items()}==belief,'after belief/budget')
                events+=1
            need(set(belief)=={identity} and r['answer']==identity,'terminal identity')
            need(r['process_metrics']['steps']==len(r['events']),'self step counter')
            need(r['process_metrics']['resets']==sum(e['action']==2 for e in r['events']),'self reset counter')
            receipt_metrics={k:int(v) for k,v in (field.split('=',1) for field in r['stdout'][-1].split()[1:])}
            need(receipt_metrics==r['process_metrics'],'raw END binding')
    need(events==2894 and summaries['events']==events and summaries['process_runs']==len(traces),'total counters')
    exhaustive=read(root/'exhaustive.json'); need(len(exhaustive)==258,'exhaustive cohort')
    data={}
    for method in ('whole','prefix','bit'):
        arm=[r for r in traces if r['method']==method]
        data[method]=dict(process_runs=len(arm),events=sum(len(r['events']) for r in arm),
                         harness_wall_total_seconds=sum(r['harness_wall_seconds'] for r in arm),
                         harness_wall_median_seconds=statistics.median(r['harness_wall_seconds'] for r in arm),
                         startup_wall_total_seconds=sum(r['startup_wall_seconds'] for r in arm),
                         harness_cpu_total_seconds=sum(r['harness_cpu_seconds'] for r in arm),
                         worker_cpu_sample_total_seconds=sum(r['process_metrics']['cpu_ticks'] for r in arm)/1e7,
                         worker_peak_working_set_median_bytes=statistics.median(r['process_metrics']['peak_working_set_bytes'] for r in arm),
                         worker_peak_working_set_max_bytes=max(r['process_metrics']['peak_working_set_bytes'] for r in arm),
                         worker_zero_cpu_samples=sum(r['process_metrics']['cpu_ticks']==0 for r in arm),
                         planning_wall_seconds=sum(c['costs'][method]['wall_seconds'] for c in configs),
                         planning_cpu_seconds=sum(c['costs'][method]['cpu_seconds'] for c in configs))
    identified=[c for c in configs if c['status']=='identified']
    descriptor=dict(configs=len(configs),process_runs=len(traces),events=events,mismatches=0,
                    whole_to_prefix_strict=sum(c['depths']['prefix']<c['depths']['whole'] for c in identified),
                    prefix_to_bit_strict=sum(c['depths']['bit']<c['depths']['prefix'] for c in identified),
                    exhaustive_whole_to_prefix_strict=sum(c['status']=='identified' and c['depths']['prefix']<c['depths']['whole'] for c in exhaustive),
                    exhaustive_prefix_to_bit_strict=sum(c['status']=='identified' and c['depths']['bit']<c['depths']['prefix'] for c in exhaustive),
                    rank_check_wall_seconds=sum(c['costs'].get('checking',{}).get('wall_seconds',0) for c in configs),
                    logical_output_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
                    logical_output_files=sum(p.is_file() for p in root.rglob('*')),arms=data)
    return configs,exhaustive,traces,descriptor


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--normal',type=Path,required=True); ap.add_argument('--optimized',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    args.normal=args.normal.resolve(); args.optimized=args.optimized.resolve(); args.out=args.out.resolve()
    normal=verify(args.normal); optimized=verify(args.optimized)
    for index in (0,1):
        keys=('id','status','reason','depths','support','budget')+(('name',) if index==0 else ('source',))
        projection=lambda rows:[{k:r[k] for k in keys} for r in rows]
        need(projection(normal[index])==projection(optimized[index]),'normal/O semantic agreement')
    need(not args.out.exists(),'new verification output required'); args.out.mkdir(parents=True)
    report=dict(normal=normal[3],optimized=optimized[3],semantic_agreement=True,
                methodology='All raw transitions/identities/budgets; same common cohort; descriptive costs only, no significance/generalization/physical-deployment claim.')
    (args.out/'verified.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    with (args.out/'depths.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['id','name','support_size','budget','status','whole','prefix','bit'])
        writer.writeheader()
        for c in normal[0]:
            writer.writerow(dict(id=c['id'],name=c['name'],support_size=len(c['support']),budget=c['budget'],status=c['status'],**c['depths']))
    bindings=[dict(path=p.relative_to(HERE.parent.parent).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for root in (args.normal,args.optimized) for p in sorted(root.rglob('*')) if p.is_file()]
    (args.out/'raw-bindings.json').write_text(json.dumps(bindings,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__': main()
