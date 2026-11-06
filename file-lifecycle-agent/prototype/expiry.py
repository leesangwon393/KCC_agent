"""Installer cleanup: .dmg/.pkg (and setup/installer .zip/.exe) left in the watched inboxes go to the Trash N days after the
agent first saw them. Age is measured on the Mac clock, so moving the clock forward demos it. Not the model: a fixed rule
decides, the files are moved to ~/.Trash (never deleted), and every move can be restored from the page."""
from pathlib import Path
import json, re, shutil, time

INSTALLER = {'.dmg', '.pkg', '.mpkg'}
INSTALL_NAME = re.compile(r'(?i)setup|install')  # .zip/.exe only when the name says it is an installer
TRASH = Path.home() / '.Trash'


def installer(p):
    s = p.suffix.lower()
    return s in INSTALLER or (s in {'.zip', '.exe'} and bool(INSTALL_NAME.search(p.stem)))


class Expiry:
    def __init__(self, path, inboxes, days, trash=TRASH):
        self.path = Path(path); self.inboxes = [Path(x).expanduser() for x in inboxes]; self.days = days; self.trash = Path(trash)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {'seen': {}, 'trashed': []}

    def save(self): self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1))

    def sweep(self, now=None):
        """Returns names moved to the Trash. Files already there when first seen start their clock now (no surprise purge)."""
        now = time.time() if now is None else now; seen = self.data['seen']; moved = []
        for x in self.inboxes:
            for p in x.glob('*'):
                if p.is_file() and not p.name.startswith('.') and installer(p): seen.setdefault(str(p), now)
        for k, t in list(seen.items()):
            p = Path(k)
            if not p.is_file(): del seen[k]; continue  # installed and removed by the user, or moved
            if now - t < self.days * 86400: continue
            dst = self.trash / p.name
            if dst.exists(): dst = dst.with_stem(f'{dst.stem} {time.strftime("%H%M%S")}')
            shutil.move(str(p), str(dst))
            self.data['trashed'].append({'path': k, 'trash': str(dst), 'at': now}); del seen[k]; moved.append(p.name)
        self.save(); return moved

    def restore(self, i):
        t = self.data['trashed'][i]; src, dst = Path(t['trash']), Path(t['path'])
        if dst.exists(): raise FileExistsError(dst)
        if not src.exists(): raise FileNotFoundError('휴지통에서 이미 비워졌습니다')
        shutil.move(str(src), str(dst)); t['restored'] = time.time()
        self.data['seen'][str(dst)] = time.time()  # restart its clock instead of trashing it again next minute
        self.save()


if __name__ == '__main__':
    import tempfile
    d = Path(tempfile.mkdtemp()); inbox, trash = d / 'Downloads', d / 'Trash'; inbox.mkdir(); trash.mkdir()
    for n in ('app.dmg', 'Setup_tool.zip', 'lecture.zip', 'notes.pdf'): (inbox / n).write_text('x')
    e = Expiry(d / 'exp.json', [inbox], 3, trash)
    assert e.sweep(now=1000) == []
    assert sorted(e.sweep(now=1000 + 3 * 86400)) == ['Setup_tool.zip', 'app.dmg']
    assert (inbox / 'lecture.zip').exists() and (inbox / 'notes.pdf').exists() and (trash / 'app.dmg').exists()
    e.restore(0); assert (inbox / 'app.dmg').exists() and e.sweep(now=1000 + 3 * 86400) == []
    print('ok')
