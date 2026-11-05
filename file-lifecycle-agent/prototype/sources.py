"""Download source rules: macOS records where a file came from (kMDItemWhereFroms: file URL, then the page it was
clicked on). A course page such as ecampus .../course/view.php?id=12345 identifies the course, so once the user maps it
to a folder, every later download from that page goes there without asking. Rules live in a local JSON file."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import json, plistlib, re, subprocess


def where_froms(path):
    """[file URL, page URL, ...] that the browser stamped on the download; [] if none (AirDrop, non-browser files).
    Read from the extended attribute itself: Spotlight (mdls) may not have indexed a download that just finished."""
    try:
        r = subprocess.run(['xattr', '-px', 'com.apple.metadata:kMDItemWhereFroms', str(path)], capture_output=True, text=True, timeout=10)
        if r.returncode == 0: return [u for u in plistlib.loads(bytes.fromhex(''.join(r.stdout.split()))) if isinstance(u, str)]
    except (OSError, subprocess.TimeoutExpired, ValueError, plistlib.InvalidFileException): pass
    try: out = subprocess.run(['mdls', '-raw', '-name', 'kMDItemWhereFroms', str(path)], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired): return []
    return re.findall(r'"((?:https?|blob):[^"]+)"', out)


def source_keys(urls):
    """Stable keys from the page URLs (not the file URL): host + path + id parameter, e.g.
    'lms.example.edu/course/view.php?id=12345'. Pages without an id (chatgpt.com, blob:) give no key."""
    keys = []
    for u in urls[1:]:
        s = urlsplit(u); i = parse_qs(s.query).get('id')
        if s.scheme in ('http', 'https') and i: keys.append(f'{s.netloc}{s.path}?id={i[0]}')
    return keys


class Rules:
    def __init__(self, path):
        self.path = Path(path); self.map = json.loads(self.path.read_text()) if self.path.exists() else {}

    def match(self, keys):
        """First key with a rule wins; course pages are listed by the page itself, so order is the browser's."""
        return next(((k, self.map[k]) for k in keys if k in self.map), None)

    def learn(self, keys, pid):
        changed = {k: pid for k in keys if self.map.get(k) != pid}
        if changed: self.map.update(changed); self.path.write_text(json.dumps(self.map, ensure_ascii=False, indent=1))
        return changed


if __name__ == '__main__':
    assert source_keys(['https://x/pluginfile.php/1/a.pdf', 'https://lms.example.edu/course/view.php?id=12345']) == ['lms.example.edu/course/view.php?id=12345']
    assert source_keys(['blob:https://chatgpt.com/abc', 'https://chatgpt.com/']) == []
    print('ok')
