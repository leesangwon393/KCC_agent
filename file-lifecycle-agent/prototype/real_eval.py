"""Evaluate on the owner's real files. The label file stays local (personal data); this script only reads it.
Label file: {"catalog": {pid: {name, desc}}, "items": [{"path", "label": pid | "none" | "?", "confirmed"}]}
'none' = not project material: correct iff the agent does not assign. '?' and unconfirmed items are skipped.
Files are copied into a temp sandbox; originals are never touched.
usage: python real_eval.py LABELS.json rule|hybrid [ADAPTER] [--guards=a,b]"""
import json, sys, shutil, tempfile, collections
from pathlib import Path
from lifecycle_v3 import Lifecycle
from agent_v5 import ToolHostV5, run, run_hybrid, rule_controller, DEFAULT_GUARDS


def score(label, rec, assigned):
    planned = rec['status'] == 'planned'
    return {'correct': (planned and assigned == label) if label != 'none' else not planned,
            'wrong_assign': int(assigned is not None and assigned != label)}


def main(labels, mode, adapter=None, guards=None):
    d = json.loads(Path(labels).read_text()); cat = d['catalog']
    items = [x for x in d['items'] if x['confirmed'] and x['label'] != '?']
    ctl = rule_controller
    if mode == 'hybrid':
        from qwen_tool_controller import QwenToolController
        from agent_v5 import SPECS, SYSTEM
        M = next((Path.home() / '.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots').iterdir())
        ctl = QwenToolController(str(M), specs=SPECS, system=SYSTEM, adapter=adapter)
    rows = []
    for x in items:
        src = Path(x['path']); tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / 'downloads').mkdir(); shutil.copy2(src, tmp / 'downloads' / src.name)
        except OSError as e:  # e.g. iCloud placeholder not downloaded
            rows.append({'file': src.name, 'label': x['label'], 'skipped': str(e)[:60]}); shutil.rmtree(tmp); continue
        e = Lifecycle(tmp); e.data['projects'].update({k: 'active' for k in cat}); e.save(); aid = e.ingest('downloads/' + src.name)
        mk = lambda g: ToolHostV5(e, aid, cat, guards=g)
        if mode == 'hybrid': rec, h = run_hybrid(mk, ctl, guards or {*DEFAULT_GUARDS, 'dense'})
        else: h = mk(guards or DEFAULT_GUARDS); rec = run(h, ctl)
        ask = next((t['arguments'] for t in rec['trace'] if t['tool'] == 'ask_user' and 'error' not in t['result']), {})
        rows.append({'file': src.name, 'label': x['label'], 'status': rec['status'], 'assigned': h.assigned, 'decider': rec.get('decider', mode),
                     'candidates': ask.get('candidate_ids'), 'errors': rec['invalid_calls'], **score(x['label'], rec, h.assigned)})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True); shutil.rmtree(tmp)
    done = [r for r in rows if 'skipped' not in r]; proj = [r for r in done if r['label'] != 'none']; none = [r for r in done if r['label'] == 'none']
    summary = {'mode': mode, 'n': len(done), 'skipped': len(rows) - len(done), 'correct': sum(r['correct'] for r in done),
               'project_files_correct': f"{sum(r['correct'] for r in proj)}/{len(proj)}", 'not_project_correct': f"{sum(r['correct'] for r in none)}/{len(none)}",
               'wrong_assign': sum(r['wrong_assign'] for r in done), 'budget_exceeded': sum(r['status'] == 'budget_exceeded' for r in done),
               'asked_with_candidates_on_not_project': sum(bool(r['candidates']) for r in none)}
    print(json.dumps(summary, ensure_ascii=False))
    out = Path(labels).with_name(f'result_{mode}.json'); out.write_text(json.dumps({'summary': summary, 'rows': rows}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    g = next((set(x.split('=', 1)[1].split(',')) for x in sys.argv[1:] if x.startswith('--guards=')), None)
    main(a[0], a[1], a[2] if len(a) > 2 else None, g)
