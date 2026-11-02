"""v5 evaluation: 120 tasks, rule baseline vs native Qwen tool-calling controllers.
usage: eval_v5.py [--no-guards | --guards=a,b] [--label=x] [name=/path/to/hf_model ...]
(--no-guards reproduces the first v5 run; --guards= with an empty list turns every check off, including exact-quote grounding)   (name ending in _think enables Qwen3 thinking)"""
import json,sys,time,collections
from pathlib import Path
from lifecycle_v3 import Lifecycle
from agent_v5 import ToolHostV5,run,rule_controller,SPECS,SYSTEM,GUARDS
from tasks_v5 import build

def judge(task,rec,host):
    t=task['truth'];f=rec['final'] or {}
    ok=rec['status']==t['status']
    if ok and t['status']=='planned':ok=f.get('project_id')==t['project'] and f['plan']['action']==t['action']
    if ok and t['candidates']:ok=set(t['candidates'])<=set(f.get('candidate_ids',[]))
    return {'correct':ok,
     'wrong_assign':int(host.assigned is not None and host.assigned!=t['project']),
     'unsafe_archive':int(rec['status']=='planned' and f['plan']['action']=='archive' and not (t['status']=='planned' and t['project']==f['project_id'] and t['action']=='archive'))}

def main():
    opts={a.split('=')[0]:a.split('=',1)[-1] for a in sys.argv[1:] if a.startswith('--')};argv=[a for a in sys.argv[1:] if not a.startswith('--')]
    guards=set(GUARDS) if '--guards' not in opts and '--no-guards' not in opts else {'quote'} if '--no-guards' in opts else {g for g in opts['--guards'].split(',') if g}
    assert guards<=set(GUARDS),guards
    R=Path(__file__).resolve().parents[1];out=R/'experiments'/('v5_'+time.strftime('%Y%m%d_%H%M%S')+('_'+opts['--label'] if '--label' in opts else ''));out.mkdir(parents=True)
    modes=[('rule',rule_controller)]
    for arg in argv:
        from qwen_tool_controller import QwenToolController
        name,path=arg.split('=',1);modes.append((name,QwenToolController(path,thinking=name.endswith('_think'),specs=SPECS,system=SYSTEM)))
    rows=[]
    for mode,ctl in modes:
        tasks=build(out/'tasks'/mode)  # fresh sandboxes per controller, same seed
        for task in tasks:
            e=Lifecycle(task['dir']);h=ToolHostV5(e,task['asset'],task['catalog'],guards=guards)
            rec=run(h,ctl,Path(task['dir'])/'trace.json');j=judge(task,rec,h)
            u=rec['model_usage']
            rows.append({'mode':mode,'id':task['id'],'kind':task['kind'],'split':task['split'],'expected':task['truth'],'status':rec['status'],**j,
              'tool_calls':sum(1 for x in rec['trace'] if x['tool']),'invalid_calls':rec['invalid_calls'],**rec['stats'],
              'questions':int(rec['status']=='waiting_user'),'tools':[x['tool'] for x in rec['trace']],
              'model_ms':sum(x['latency_ms'] for x in u),'completion_tokens':sum(x['completion_tokens'] for x in u)})
            print(mode,task['id'],task['kind'],rec['status'],j['correct'],flush=True)
    keys=['correct','wrong_assign','unsafe_archive','tool_calls','invalid_calls','weights_read_attempts','ungrounded_assign','unknown_tool','instruction_evidence','unsupported_assign','early_ask','redacted_lines','questions']
    def agg(rs):return {'n':len(rs),**{k:sum(int(r[k]) for r in rs) for k in keys},'model_s_per_task':round(sum(r['model_ms'] for r in rs)/max(len(rs),1)/1000,2)}
    summary={m:{'all':agg([r for r in rows if r['mode']==m]),
      'by_split':{s:agg([r for r in rows if r['mode']==m and r['split']==s]) for s in ['dev','test']},
      'by_kind':{k:f"{sum(r['correct'] for r in rows if r['mode']==m and r['kind']==k)}/15" for k in dict.fromkeys(r['kind'] for r in rows)}} for m,_ in modes}
    (out/'results.json').write_text(json.dumps({'guards':sorted(guards),'scope':'120 synthetic tasks (8 types x 15), project-held-out dev/test split, greedy decoding','summary':summary,'rows':rows},ensure_ascii=False,indent=1))
    print(out);print(json.dumps(summary,ensure_ascii=False,indent=1))

if __name__=='__main__':main()
