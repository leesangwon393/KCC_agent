"""Project profiles from the owner's real folders: name + description + keywords mined from file names and Markdown headings.
Input  local/projects.json: {pid: {"name", "folder", "desc"}}   (git-ignored; paths are personal)
Output the same file with "keywords" filled; agent catalogs use desc + keywords.
usage: python build_profiles.py [local/projects.json]"""
import json, re, sys, collections, unicodedata
from pathlib import Path

SKIP = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'data', 'dataset', 'datasets', 'runs', 'checkpoints', 'outputs', 'output', 'logs', 'wandb'}
STOP = set('''the and for with from this that are was of to in on a an is it be as by or at md py txt pdf zip json yaml yml png jpg jpeg csv ipynb docx pptx hwp hwpx xlsx sh toml lock
readme final copy new old test tests src lib config configs docs doc tmp temp file files v1 v2 v3 v4 v5 code main run utils init setup requirements data
및 의 을 를 이 가 은 는 에 와 과 으로 로 한 하는 최종 수정 자료 파일 버전
photo image img kakaotalk screenshot snapshot 스크린샷 오후 오전 사진 이미지 캡처 복사본'''.split())
tok = lambda s: [t for t in re.findall(r'[a-z][a-z0-9]{2,}|[가-힣]{2,}', unicodedata.normalize('NFC', s).lower()) if t not in STOP and not t.isdigit()]


def keywords(folder, k=25, max_files=400):
    root = Path(folder).expanduser(); c = collections.Counter(); seen = 0
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).parts
        if len(rel) > 3 or any(x.startswith('.') or x.lower() in SKIP for x in rel): continue
        seen += 1
        if seen > max_files: break
        c.update(set(tok(p.stem.replace('_', ' ').replace('-', ' '))))
        if p.suffix.lower() == '.md' and p.is_file() and p.stat().st_size < 500_000:
            heads = [l.lstrip('#').strip() for l in p.read_text(errors='replace').splitlines()[:200] if l.startswith('#')][:20]
            c.update(t for h in heads for t in set(tok(h)))
    return [t for t, _ in c.most_common(k)]


if __name__ == '__main__':
    f = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'local/projects.json')
    P = json.loads(f.read_text())
    for pid, p in P.items():
        p['keywords'] = keywords(p['folder'], k=40) if Path(p['folder']).expanduser().is_dir() else []
    # Words mined for 3+ projects (agent, api, ...) do not tell projects apart.
    shared = {t for t, n in collections.Counter(t for p in P.values() for t in p['keywords']).items() if n >= 3}
    for pid, p in P.items():
        p['keywords'] = [t for t in p['keywords'] if t not in shared][:25]
        print(pid, p['name'], '|', ', '.join(p['keywords']))
    f.write_text(json.dumps(P, ensure_ascii=False, indent=1))
