"""Harder held-out variant: each test case's catalog padded to N projects with distractors from the training batches.
Distractors whose bge-m3 cosine to any original project exceeds MAX_SIM are skipped (near-duplicates could make the gold label wrong).
usage: python expand_catalog.py [N=15]   -> data_collect/batch_tx.json, sft/test_split_x.json (ids prefixed 'X')"""
import json, glob, random, sys
from pathlib import Path
from agent_v5 import dense_scores

R = Path(__file__).resolve().parents[1]; N = int(sys.argv[1]) if len(sys.argv) > 1 else 15; MAX_SIM = 0.8
doc = lambda p: p['name'] + ' ' + p['desc']
pool = {k: v for f in sorted(glob.glob(str(R / 'data_collect/batch_[0-9]*.json'))) for c in json.loads(Path(f).read_text()) for k, v in c['catalog'].items()}
tests = [c for f in sorted(glob.glob(str(R / 'data_collect/batch_t[0-9]*.json'))) for c in json.loads(Path(f).read_text())]
out, skipped = [], 0
for c in tests:
    rng = random.Random(c['id']); names = {v['name'] for v in c['catalog'].values()}
    cand = [k for k in pool if k not in c['catalog'] and pool[k]['name'] not in names]; rng.shuffle(cand)
    cat = dict(c['catalog']); orig = [doc(v) for v in c['catalog'].values()]
    for k in cand:
        if len(cat) >= N: break
        if max(dense_scores(doc(pool[k]), orig)) > MAX_SIM: skipped += 1; continue
        cat[k] = pool[k]
    items = list(cat.items()); rng.shuffle(items)  # original projects must not always come first
    out.append(dict(c, id='X' + c['id'], catalog=dict(items)))
assert all(len(c['catalog']) == N for c in out) and all(set(t['catalog']) <= set(x['catalog']) for t, x in zip(tests, out))
(R / 'data_collect/batch_tx.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
sp = json.loads((R / 'sft/test_split.json').read_text())
(R / 'sft/test_split_x.json').write_text(json.dumps({k: ['X' + i for i in v] for k, v in sp.items()}, indent=1))
print(len(out), 'cases,', N, 'projects each; near-duplicate distractors skipped:', skipped, '; pool', len(pool))
